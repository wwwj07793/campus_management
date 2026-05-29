import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from core.services.service_factory import build_memory_backend


def test_memory_backend_enrollment_grade_and_data_view_flow():
    services, data_view = build_memory_backend()

    student = services.students.create_student(
        student_id="2025001",
        name="张三",
        gender="男",
        birth_date="2005-01-01",
        department="电子信息工程学院",
        grade=2025,
    )
    course = services.courses.create_course(
        course_code="AI001",
        name="人工智能导论",
        credit=3,
        teacher="李老师",
        schedule="周一1-2节",
        capacity=30,
    )

    enrollment = services.enrollments.enroll(
        student_id="2025001",
        course_code_value="AI001",
        teacher="李老师",
        schedule="周一1-2节",
    )
    grade = services.grades.record_grade(
        student_id="2025001",
        course_code_value="AI001",
        teacher="李老师",
        schedule="周一1-2节",
        score=92,
    )

    assert enrollment.student_id == student.id
    assert enrollment.course_id == course.id
    assert course.current_count == 1
    assert grade.score == 92
    assert round(student.gpa, 2) == 3.7
    assert data_view.student_counts()["total"] == 1
    assert data_view.scores_for_students([student]) == [92.0]


def test_memory_backend_validates_time_conflict_and_prerequisites():
    services, _ = build_memory_backend()

    services.students.create_student(
        student_id="2025001",
        name="张三",
        gender="男",
        birth_date="2005-01-01",
        department="电子信息工程学院",
        grade=2025,
    )
    services.courses.create_course(
        course_code="AI001",
        name="人工智能导论",
        credit=3,
        teacher="李老师",
        schedule="周一1-2节",
        capacity=30,
    )
    services.courses.create_course(
        course_code="ML201",
        name="机器学习",
        credit=3,
        teacher="王老师",
        schedule="周二1-2节",
        capacity=30,
        prerequisite_ids=["AI001"],
    )
    services.courses.create_course(
        course_code="PY001",
        name="Python程序设计",
        credit=3,
        teacher="赵老师",
        schedule="周一1-2节",
        capacity=30,
    )

    try:
        services.enrollments.enroll("2025001", "ML201", "王老师", "周二1-2节")
    except ValueError as exc:
        assert "先修课" in str(exc)
    else:
        raise AssertionError("未满足先修课时不应该允许选课")

    services.enrollments.enroll("2025001", "AI001", "李老师", "周一1-2节")

    try:
        services.enrollments.enroll("2025001", "PY001", "赵老师", "周一1-2节")
    except ValueError as exc:
        assert "时间冲突" in str(exc)
    else:
        raise AssertionError("时间冲突时不应该允许选课")

    enrollment = services.enrollments.enroll("2025001", "ML201", "王老师", "周二1-2节")

    assert enrollment.course_id == "ML201"
