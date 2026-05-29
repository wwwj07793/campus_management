__all__ = [
    "CourseRepository",
    "EnrollmentRepository",
    "GradeRepository",
    "MemoryCourseRepository",
    "MemoryEnrollmentRepository",
    "MemoryGradeRepository",
    "MemoryStudentRepository",
    "StudentRepository",
]


def __getattr__(name):
    if name == "StudentRepository":
        from data.repositories.student_repository import StudentRepository

        return StudentRepository
    if name == "CourseRepository":
        from data.repositories.course_repository import CourseRepository

        return CourseRepository
    if name == "EnrollmentRepository":
        from data.repositories.enrollment_repository import EnrollmentRepository

        return EnrollmentRepository
    if name == "GradeRepository":
        from data.repositories.grade_repository import GradeRepository

        return GradeRepository
    if name == "MemoryStudentRepository":
        from data.repositories.memory_repositories import MemoryStudentRepository

        return MemoryStudentRepository
    if name == "MemoryCourseRepository":
        from data.repositories.memory_repositories import MemoryCourseRepository

        return MemoryCourseRepository
    if name == "MemoryEnrollmentRepository":
        from data.repositories.memory_repositories import MemoryEnrollmentRepository

        return MemoryEnrollmentRepository
    if name == "MemoryGradeRepository":
        from data.repositories.memory_repositories import MemoryGradeRepository

        return MemoryGradeRepository
    raise AttributeError(name)
