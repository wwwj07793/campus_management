from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

import core.models.mysqlDB  # noqa: F401
from core.cache import CacheKeys, cache
from core.models.base import Base
from data.repositories import (
    CourseRepository,
    EnrollmentRepository,
    GradeRepository,
    StudentRepository,
)


VALID_GENDER = "男"


def make_session_factory():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def setup_function():
    cache.clear()


def teardown_function():
    cache.clear()


def seed_student(students: StudentRepository, student_id: str = "2025001"):
    return students.create(
        student_id=student_id,
        name=f"Student {student_id}",
        gender=VALID_GENDER,
        birth_date="2005-01-01",
        department="Engineering",
        grade=2025,
    )


def seed_course(
    courses: CourseRepository,
    course_code: str = "AI001",
    teacher: str = "Teacher Li",
    schedule: str = "Mon 1-2",
    capacity: int = 30,
):
    return courses.create(
        course_code=course_code,
        name=f"Course {course_code}",
        credit=3,
        teacher=teacher,
        schedule=schedule,
        capacity=capacity,
    )


def test_student_repository_api_crud_and_search_across_sessions():
    Session = make_session_factory()

    first_session = Session()
    students = StudentRepository(first_session)
    student = seed_student(students)
    second_student = seed_student(students, "2025002")
    first_session.commit()
    first_session.close()

    read_session = Session()
    students = StudentRepository(read_session)

    assert students.get_by_id(student.id).student_id == "2025001"
    assert students.get_by_student_id("2025002").id == second_student.id
    assert [item.student_id for item in students.list_all()] == ["2025001", "2025002"]
    assert [item.student_id for item in students.search(name="Student 2025001")] == [
        "2025001"
    ]
    assert [item.student_id for item in students.search(department="Engineering")] == [
        "2025001",
        "2025002",
    ]

    students.update(
        "2025001",
        name="Alice",
        department="Math",
        birth_date="2005-03-01",
        grade="2026",
        gpa="3.5",
    )
    read_session.commit()

    assert students.get_by_student_id("2025001").name == "Alice"
    assert students.get_by_student_id("2025001").department == "Math"
    assert students.set_gpa("2025001", 3.8).gpa == 3.8
    assert students.delete("2025002") is True
    assert students.delete("missing") is False
    read_session.commit()

    final_session = Session()
    students = StudentRepository(final_session)
    assert [item.student_id for item in students.list_all()] == ["2025001"]
    assert students.get_by_student_id("2025002") is None
    final_session.close()
    read_session.close()


def test_course_repository_api_crud_prerequisites_and_indexes():
    Session = make_session_factory()
    session = Session()
    courses = CourseRepository(session)

    prerequisite = seed_course(courses, "BASE1", "Teacher Base", "Fri 1-2")
    course = courses.create(
        course_code="AI001",
        name="Intro AI",
        credit="3",
        teacher="Teacher Li",
        schedule="Mon 1-2",
        capacity="30",
        prerequisite_ids=[prerequisite.id],
    )
    session.commit()

    assert courses.get_by_id(course.id).course_code == "AI001"
    assert courses.get_by_identity("AI001", "Teacher Li", "Mon 1-2").id == course.id
    assert [item.id for item in courses.list_by_code("AI001")] == [course.id]
    assert [item.id for item in courses.list_by_teacher("Teacher Li")] == [course.id]
    assert {item.id for item in courses.list_by_ids([course.id, prerequisite.id])} == {
        course.id,
        prerequisite.id,
    }
    assert courses.get_with_prerequisites(course.id).prerequisites[0].id == prerequisite.id

    courses.remove_prerequisite(course.id, prerequisite.id)
    courses.add_prerequisite(course.id, prerequisite.id)
    courses.update(course.id, name="Advanced AI", capacity=40, credit=4)
    session.commit()

    assert courses.get_by_id(course.id).name == "Advanced AI"
    assert courses.get_by_id(course.id).capacity == 40

    assert courses.delete(prerequisite.id) is True
    assert courses.delete(99999) is False
    session.commit()

    assert courses.get_by_id(prerequisite.id) is None
    session.close()


def test_enrollment_repository_api_flow_and_course_count():
    Session = make_session_factory()
    session = Session()
    students = StudentRepository(session)
    courses = CourseRepository(session)
    enrollments = EnrollmentRepository(session)

    student = seed_student(students)
    course = seed_course(courses, capacity=2)
    session.commit()

    enrollment = enrollments.create_by_business_keys(
        "2025001",
        "AI001",
        "Teacher Li",
        "Mon 1-2",
    )
    session.commit()

    assert enrollment is not None
    assert enrollments.exists(student.id, course.id) is True
    assert courses.get_by_id(course.id).current_count == 1
    assert enrollments.get(student.id, course.id).course_id == course.id
    assert [item.course_id for item in enrollments.list_by_student_id(student.id)] == [
        course.id
    ]
    assert [item.course_id for item in enrollments.list_by_student_number("2025001")] == [
        course.id
    ]
    assert [item.student_id for item in enrollments.list_by_course_id(course.id)] == [
        student.id
    ]

    assert enrollments.delete_by_business_keys(
        "2025001",
        "AI001",
        "Teacher Li",
        "Mon 1-2",
    ) is True
    session.commit()

    assert enrollments.exists(student.id, course.id) is False
    assert courses.get_by_id(course.id).current_count == 0
    assert enrollments.delete_by_business_keys(
        "2025001",
        "AI001",
        "Teacher Li",
        "Mon 1-2",
    ) is False
    session.close()


def test_grade_repository_api_flow_and_enrollment_guard():
    Session = make_session_factory()
    session = Session()
    students = StudentRepository(session)
    courses = CourseRepository(session)
    enrollments = EnrollmentRepository(session)
    grades = GradeRepository(session)

    student = seed_student(students)
    course = seed_course(courses)
    session.commit()

    try:
        grades.upsert(student.id, course.id, 95)
    except ValueError as exc:
        assert "已有选课记录" in str(exc)
        session.rollback()
    else:
        raise AssertionError("未选课时不能录入成绩")

    enrollments.create(student.id, course.id)
    grade = grades.upsert_by_business_keys(
        "2025001",
        "AI001",
        "Teacher Li",
        "Mon 1-2",
        95,
    )
    session.commit()

    assert grade is not None
    assert grades.get(student.id, course.id).score == 95
    assert grades.list_by_student_number("2025001")[0].course.course_code == "AI001"
    assert grades.list_by_student_id(student.id)[0].score == 95
    assert grades.list_by_course_id(course.id)[0].student.student_id == "2025001"

    updated_grade = grades.upsert(student.id, course.id, 88)
    session.commit()

    assert updated_grade.id == grade.id
    assert grades.get(student.id, course.id).score == 88
    assert grades.delete(student.id, course.id) is True
    assert grades.delete(student.id, course.id) is False
    session.commit()

    assert grades.get(student.id, course.id) is None
    session.close()


def test_database_constraints_are_enforced_for_api_boundaries():
    Session = make_session_factory()
    session = Session()
    students = StudentRepository(session)
    courses = CourseRepository(session)
    enrollments = EnrollmentRepository(session)
    grades = GradeRepository(session)

    student = seed_student(students)
    course = seed_course(courses, capacity=1)
    session.commit()

    try:
        students.create(
            student_id="2025001",
            name="Duplicate",
            gender=VALID_GENDER,
            birth_date="2005-01-01",
            department="Engineering",
            grade=2025,
        )
    except IntegrityError:
        session.rollback()
    else:
        raise AssertionError("重复学号应由数据库唯一约束拒绝")

    enrollments.create(student.id, course.id)
    session.commit()

    try:
        grades.upsert(student.id, course.id, 101)
    except IntegrityError:
        session.rollback()
    else:
        raise AssertionError("非法成绩应由数据库检查约束拒绝")

    assert enrollments.create_by_business_keys(
        "missing",
        "AI001",
        "Teacher Li",
        "Mon 1-2",
    ) is None
    assert grades.upsert_by_business_keys(
        "missing",
        "AI001",
        "Teacher Li",
        "Mon 1-2",
        90,
    ) is None

    session.close()


def test_committed_cache_is_readable_from_new_api_session():
    Session = make_session_factory()

    write_session = Session()
    students = StudentRepository(write_session)
    courses = CourseRepository(write_session)
    enrollments = EnrollmentRepository(write_session)
    grades = GradeRepository(write_session)

    student = seed_student(students)
    course = seed_course(courses)
    enrollments.create(student.id, course.id)
    grade = grades.upsert(student.id, course.id, 91)
    write_session.commit()
    write_session.close()

    assert cache.get(CacheKeys.student_db_student_id("2025001")) == student.id
    assert cache.get(CacheKeys.course_db_identity("AI001", "Teacher Li", "Mon 1-2")) is None
    assert cache.get(CacheKeys.grade_db_pair(student.id, course.id)) == grade.id

    read_session = Session()
    students = StudentRepository(read_session)
    courses = CourseRepository(read_session)
    grades = GradeRepository(read_session)

    assert students.get_by_student_id("2025001").id == student.id
    assert courses.get_by_identity("AI001", "Teacher Li", "Mon 1-2").id == course.id
    assert cache.get(CacheKeys.course_db_identity("AI001", "Teacher Li", "Mon 1-2")) == course.id
    assert grades.get(student.id, course.id).score == 91

    read_session.close()
