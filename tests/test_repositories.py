import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import core.models.mysqlDB  # noqa: F401
from core.models.base import Base
from data.repositories import (
    CourseRepository,
    EnrollmentRepository,
    GradeRepository,
    StudentRepository,
)


def make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    return Session()


def test_repositories_create_enrollment_and_grade_flow():
    session = make_session()

    students = StudentRepository(session)
    courses = CourseRepository(session)
    enrollments = EnrollmentRepository(session)
    grades = GradeRepository(session)

    student = students.create(
        student_id="2025001",
        name="张三",
        gender="男",
        birth_date="2005-01-01",
        department="电子信息工程学院",
        grade=2025,
    )
    course = courses.create(
        course_code="AI001",
        name="人工智能导论",
        credit=3,
        teacher="李老师",
        schedule="周一1-2节",
        capacity=30,
    )

    enrollment = enrollments.create(student.id, course.id)
    grade = grades.upsert(student.id, course.id, 92)

    assert enrollment.student_id == student.id
    assert enrollment.course_id == course.id
    assert course.current_count == 1
    assert grade.score == 92
    assert grades.list_by_student_number("2025001")[0].course.course_code == "AI001"

    session.close()


def test_grade_requires_existing_enrollment():
    session = make_session()

    students = StudentRepository(session)
    courses = CourseRepository(session)
    grades = GradeRepository(session)

    student = students.create(
        student_id="2025001",
        name="张三",
        gender="男",
        birth_date="2005-01-01",
        department="电子信息工程学院",
        grade=2025,
    )
    course = courses.create(
        course_code="AI001",
        name="人工智能导论",
        credit=3,
        teacher="李老师",
        schedule="周一1-2节",
        capacity=30,
    )

    try:
        grades.upsert(student.id, course.id, 92)
    except ValueError as exc:
        assert "已有选课记录" in str(exc)
    else:
        raise AssertionError("未选课时不应该允许录入成绩")

    session.close()
