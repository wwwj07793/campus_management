from __future__ import annotations

from core.interpretation import CampusDataView, RepositoryCampusDataReader
from core.services.backend_services import build_backend_services
from data.repositories.memory_repositories import (
    MemoryCourseRepository,
    MemoryEnrollmentRepository,
    MemoryGradeRepository,
    MemoryStudentRepository,
)


def build_memory_backend(students=None, courses=None):
    student_repo = MemoryStudentRepository(students)
    course_repo = MemoryCourseRepository(courses)
    enrollment_repo = MemoryEnrollmentRepository(student_repo, course_repo)
    grade_repo = MemoryGradeRepository(enrollment_repo)
    services = build_backend_services(
        student_repo,
        course_repo,
        enrollment_repo,
        grade_repo,
    )
    reader = RepositoryCampusDataReader(
        student_repo,
        course_repo,
        enrollment_repo,
        grade_repo,
    )
    return services, CampusDataView(reader=reader)


def build_database_backend(session):
    from data.repositories import (
        CourseRepository,
        EnrollmentRepository,
        GradeRepository,
        StudentRepository,
    )

    student_repo = StudentRepository(session)
    course_repo = CourseRepository(session)
    enrollment_repo = EnrollmentRepository(session)
    grade_repo = GradeRepository(session)
    services = build_backend_services(
        student_repo,
        course_repo,
        enrollment_repo,
        grade_repo,
    )
    reader = RepositoryCampusDataReader(
        student_repo,
        course_repo,
        enrollment_repo,
        grade_repo,
    )
    return services, CampusDataView(reader=reader)
