from sqlalchemy import create_engine
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


def make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    return Session()


def setup_function():
    cache.clear()


def teardown_function():
    cache.clear()


def test_student_repository_updates_and_invalidates_cache():
    session = make_session()
    students = StudentRepository(session)

    student = students.create(
        student_id="2025001",
        name="Alice",
        gender=VALID_GENDER,
        birth_date="2005-01-01",
        department="Engineering",
        grade=2025,
    )

    assert cache.get(CacheKeys.student_db_student_id("2025001")) is None
    session.commit()

    assert cache.get(CacheKeys.student_db_student_id("2025001")) == student.id
    assert students.get_by_student_id("2025001").name == "Alice"

    assert [item.student_id for item in students.list_all()] == ["2025001"]
    assert cache.get(CacheKeys.STUDENT_DB_ALL) == [student.id]

    students.create(
        student_id="2025002",
        name="Bob",
        gender=VALID_GENDER,
        birth_date="2005-02-01",
        department="Engineering",
        grade=2025,
    )

    assert cache.get(CacheKeys.STUDENT_DB_ALL) == [student.id]
    session.commit()

    assert cache.get(CacheKeys.STUDENT_DB_ALL) is None
    assert [item.student_id for item in students.list_all()] == ["2025001", "2025002"]

    students.update("2025001", student_id="2025999", department="Math")
    session.commit()

    assert cache.get(CacheKeys.student_db_student_id("2025001")) is None
    assert students.get_by_student_id("2025999").department == "Math"

    session.close()


def test_enrollment_and_grade_repositories_sync_related_cache():
    session = make_session()
    students = StudentRepository(session)
    courses = CourseRepository(session)
    enrollments = EnrollmentRepository(session)
    grades = GradeRepository(session)

    student = students.create(
        student_id="2025001",
        name="Alice",
        gender=VALID_GENDER,
        birth_date="2005-01-01",
        department="Engineering",
        grade=2025,
    )
    course = courses.create(
        course_code="AI001",
        name="Intro AI",
        credit=3,
        teacher="Teacher Li",
        schedule="Mon 1-2",
        capacity=30,
    )
    session.commit()

    cache.set(CacheKeys.student_grades("2025001"), ["stale"])
    cache.set(CacheKeys.course_summary("AI001"), {"stale": True})

    enrollment = enrollments.create(student.id, course.id)
    session.commit()

    assert enrollment.student_id == student.id
    assert cache.get(CacheKeys.student_grades("2025001")) is None
    assert cache.get(CacheKeys.course_summary("AI001")) is None

    enrollments.list_by_student_id(student.id)
    assert cache.get(CacheKeys.enrollment_db_student(student.id)) == [
        (student.id, course.id)
    ]

    grade = grades.upsert(student.id, course.id, 92)
    session.commit()
    assert cache.get(CacheKeys.grade_db_pair(student.id, course.id)) == grade.id

    assert grades.list_by_student_id(student.id)[0].score == 92
    assert cache.get(CacheKeys.grade_db_student(student.id)) == [grade.id]

    cache.set(CacheKeys.student_grades("2025001"), ["stale"])
    grades.upsert(student.id, course.id, 88)
    session.commit()

    assert cache.get(CacheKeys.student_grades("2025001")) is None
    assert cache.get(CacheKeys.grade_db_student(student.id)) is None
    assert grades.list_by_student_id(student.id)[0].score == 88

    session.close()


def test_repository_cache_actions_are_discarded_on_rollback():
    session = make_session()
    students = StudentRepository(session)

    student = students.create(
        student_id="2025001",
        name="Alice",
        gender=VALID_GENDER,
        birth_date="2005-01-01",
        department="Engineering",
        grade=2025,
    )

    session.rollback()

    assert cache.get(CacheKeys.student_db_student_id("2025001")) is None
    assert students.get_by_student_id("2025001") is None
    assert student.id is not None

    session.close()


def test_enrollment_repository_rejects_duplicate_and_full_course():
    session = make_session()
    students = StudentRepository(session)
    courses = CourseRepository(session)
    enrollments = EnrollmentRepository(session)

    first_student = students.create(
        student_id="2025001",
        name="Alice",
        gender=VALID_GENDER,
        birth_date="2005-01-01",
        department="Engineering",
        grade=2025,
    )
    second_student = students.create(
        student_id="2025002",
        name="Bob",
        gender=VALID_GENDER,
        birth_date="2005-02-01",
        department="Engineering",
        grade=2025,
    )
    course = courses.create(
        course_code="AI001",
        name="Intro AI",
        credit=3,
        teacher="Teacher Li",
        schedule="Mon 1-2",
        capacity=1,
    )
    session.commit()

    enrollments.create(first_student.id, course.id)
    session.commit()

    try:
        enrollments.create(first_student.id, course.id)
    except ValueError as exc:
        assert "已经选过" in str(exc)
        session.rollback()
    else:
        raise AssertionError("重复选课应该被拒绝")

    try:
        enrollments.create(second_student.id, course.id)
    except ValueError as exc:
        assert "容量已满" in str(exc)
        session.rollback()
    else:
        raise AssertionError("课程满员后应该拒绝继续选课")

    session.close()


def test_course_repository_invalidates_old_identity_indexes_after_update():
    session = make_session()
    courses = CourseRepository(session)

    course = courses.create(
        course_code="AI001",
        name="Intro AI",
        credit=3,
        teacher="Teacher Li",
        schedule="Mon 1-2",
        capacity=30,
    )
    session.commit()

    assert [item.id for item in courses.list_by_code("AI001")] == [course.id]
    assert [item.id for item in courses.list_by_teacher("Teacher Li")] == [course.id]
    assert cache.get(CacheKeys.course_db_code("AI001")) == [course.id]
    assert cache.get(CacheKeys.course_db_teacher("Teacher Li")) == [course.id]

    courses.update(
        course.id,
        course_code="ML001",
        teacher="Teacher Wang",
        schedule="Tue 3-4",
    )
    session.commit()

    assert cache.get(CacheKeys.course_db_code("AI001")) is None
    assert cache.get(CacheKeys.course_db_teacher("Teacher Li")) is None
    assert courses.get_by_identity("AI001", "Teacher Li", "Mon 1-2") is None
    assert courses.get_by_identity("ML001", "Teacher Wang", "Tue 3-4").id == course.id

    session.close()
