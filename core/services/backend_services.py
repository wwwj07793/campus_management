from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from data.repositories.interfaces import (
    CourseRepositoryProtocol,
    EnrollmentRepositoryProtocol,
    GradeRepositoryProtocol,
    StudentRepositoryProtocol,
)


class BusinessRuleError(ValueError):
    status_code = 400


class NotFoundError(BusinessRuleError):
    status_code = 404


class ConflictError(BusinessRuleError):
    status_code = 409


class ValidationError(BusinessRuleError):
    status_code = 400


def score_to_gpa(score: float) -> float:
    score = float(score)
    if 95 <= score <= 100:
        return 4.0
    if 90 <= score <= 94:
        return 3.7
    if 85 <= score <= 89:
        return 3.3
    if 80 <= score <= 84:
        return 3.0
    if 75 <= score <= 79:
        return 2.7
    if 70 <= score <= 74:
        return 2.3
    if 65 <= score <= 69:
        return 2.0
    if 60 <= score <= 64:
        return 1.0
    return 0.0


def object_id(item: Any) -> Any:
    return getattr(item, "id")


def student_number(student: Any) -> str:
    return str(getattr(student, "student_id"))


def course_code(course: Any) -> str:
    if isinstance(course, str):
        return course
    if hasattr(course, "course_code"):
        return str(course.course_code)
    if hasattr(course, "course_id"):
        return str(course.course_id)
    return str(course.id)


def course_id(course: Any) -> Any:
    return getattr(course, "id")


def course_credit(course: Any) -> int:
    return int(getattr(course, "credit"))


def enrollment_course(enrollment: Any) -> Any:
    return getattr(enrollment, "course", None)


def grade_course(grade: Any) -> Any:
    return getattr(grade, "course", None)


@dataclass
class BackendServices:
    students: "StudentBusinessService"
    courses: "CourseBusinessService"
    enrollments: "EnrollmentBusinessService"
    grades: "GradeBusinessService"


class StudentBusinessService:
    def __init__(self, student_repo: StudentRepositoryProtocol):
        self.student_repo = student_repo

    def create_student(
        self,
        student_id: str,
        name: str,
        gender: str,
        birth_date,
        department: str,
        grade: int,
    ) -> Any:
        if self.student_repo.get_by_student_id(student_id) is not None:
            raise ConflictError("学生已存在")
        return self.student_repo.create(
            student_id=student_id,
            name=name,
            gender=gender,
            birth_date=birth_date,
            department=department,
            grade=grade,
        )

    def get_student(self, student_id: str) -> Any | None:
        return self.student_repo.get_by_student_id(student_id)

    def search_students(self, **filters) -> list[Any]:
        return self.student_repo.search(**filters)

    def update_student(self, student_id: str, **fields) -> Any | None:
        return self.student_repo.update(student_id, **fields)

    def delete_student(self, student_id: str) -> bool:
        return self.student_repo.delete(student_id)


class CourseBusinessService:
    def __init__(self, course_repo: CourseRepositoryProtocol):
        self.course_repo = course_repo

    def create_course(
        self,
        course_code: str,
        name: str,
        credit: int,
        teacher: str,
        schedule: str,
        capacity: int,
        prerequisite_ids: list[Any] | None = None,
    ) -> Any:
        if self.course_repo.get_by_identity(course_code, teacher, schedule) is not None:
            raise ConflictError("课程已存在")
        return self.course_repo.create(
            course_code=course_code,
            name=name,
            credit=credit,
            teacher=teacher,
            schedule=schedule,
            capacity=capacity,
            prerequisite_ids=prerequisite_ids,
        )

    def get_course(self, course_code: str, teacher: str, schedule: str) -> Any | None:
        return self.course_repo.get_by_identity(course_code, teacher, schedule)

    def list_courses(self) -> list[Any]:
        return self.course_repo.list_all()

    def update_course(self, id: Any, **fields) -> Any | None:
        return self.course_repo.update(id, **fields)

    def delete_course(self, id: Any) -> bool:
        return self.course_repo.delete(id)


class EnrollmentBusinessService:
    def __init__(
        self,
        student_repo: StudentRepositoryProtocol,
        course_repo: CourseRepositoryProtocol,
        enrollment_repo: EnrollmentRepositoryProtocol,
    ):
        self.student_repo = student_repo
        self.course_repo = course_repo
        self.enrollment_repo = enrollment_repo

    def enroll(
        self,
        student_id: str,
        course_code_value: str,
        teacher: str,
        schedule: str,
    ) -> Any:
        student = self.student_repo.get_by_student_id(student_id)
        if student is None:
            raise NotFoundError("学生不存在")

        course = self.course_repo.get_by_identity(course_code_value, teacher, schedule)
        if course is None:
            raise NotFoundError("课程不存在")

        if getattr(course, "current_count") >= getattr(course, "capacity"):
            raise ValidationError("课程容量已满")

        if self._has_time_conflict(student, course):
            raise ValidationError("选课时间冲突")

        if not self._has_prerequisites(student, course):
            raise ValidationError("未满足先修课要求")

        return self.enrollment_repo.create(object_id(student), course_id(course))

    def drop(
        self,
        student_id: str,
        course_code_value: str,
        teacher: str,
        schedule: str,
    ) -> bool:
        student = self.student_repo.get_by_student_id(student_id)
        if student is None:
            raise NotFoundError("学生不存在")
        course = self.course_repo.get_by_identity(course_code_value, teacher, schedule)
        if course is None:
            raise NotFoundError("课程不存在")
        return self.enrollment_repo.delete(object_id(student), course_id(course))

    def _has_time_conflict(self, student: Any, target_course: Any) -> bool:
        for enrollment in self.enrollment_repo.list_by_student_id(object_id(student)):
            enrolled_course = enrollment_course(enrollment)
            if enrolled_course is None:
                continue
            if getattr(enrolled_course, "schedule") == getattr(target_course, "schedule"):
                return True
        return False

    def _has_prerequisites(self, student: Any, target_course: Any) -> bool:
        prerequisites = getattr(target_course, "prerequisites", None) or []
        if not prerequisites:
            return True

        selected_codes = {
            course_code(enrollment_course(enrollment))
            for enrollment in self.enrollment_repo.list_by_student_id(object_id(student))
            if enrollment_course(enrollment) is not None
        }
        required_codes = {
            course_code(prerequisite)
            for prerequisite in prerequisites
        }
        return required_codes.issubset(selected_codes)


class GradeBusinessService:
    def __init__(
        self,
        student_repo: StudentRepositoryProtocol,
        course_repo: CourseRepositoryProtocol,
        enrollment_repo: EnrollmentRepositoryProtocol,
        grade_repo: GradeRepositoryProtocol,
    ):
        self.student_repo = student_repo
        self.course_repo = course_repo
        self.enrollment_repo = enrollment_repo
        self.grade_repo = grade_repo

    def record_grade(
        self,
        student_id: str,
        course_code_value: str,
        teacher: str,
        schedule: str,
        score: float,
    ) -> Any:
        score = float(score)
        if not 0 <= score <= 100:
            raise ValidationError("成绩必须在0到100之间")

        student = self.student_repo.get_by_student_id(student_id)
        if student is None:
            raise NotFoundError("学生不存在")
        course = self.course_repo.get_by_identity(course_code_value, teacher, schedule)
        if course is None:
            raise NotFoundError("课程不存在")
        if not self.enrollment_repo.exists(object_id(student), course_id(course)):
            raise ValidationError("学生未选该课程，不能录入成绩")

        grade = self.grade_repo.upsert(object_id(student), course_id(course), score)
        self.recalculate_gpa(student_id)
        return grade

    def delete_grade(
        self,
        student_id: str,
        course_code_value: str,
        teacher: str,
        schedule: str,
    ) -> bool:
        student = self.student_repo.get_by_student_id(student_id)
        if student is None:
            raise NotFoundError("学生不存在")
        course = self.course_repo.get_by_identity(course_code_value, teacher, schedule)
        if course is None:
            raise NotFoundError("课程不存在")
        deleted = self.grade_repo.delete(object_id(student), course_id(course))
        if deleted:
            self.recalculate_gpa(student_id)
        return deleted

    def recalculate_gpa(self, student_id: str) -> float:
        student = self.student_repo.get_by_student_id(student_id)
        if student is None:
            raise NotFoundError("学生不存在")

        grades = self.grade_repo.list_by_student_id(object_id(student))
        total_credit = 0
        weighted_gpa = 0.0
        for grade in grades:
            course = grade_course(grade)
            if course is None:
                continue
            credit = course_credit(course)
            total_credit += credit
            weighted_gpa += score_to_gpa(float(grade.score)) * credit

        gpa = weighted_gpa / total_credit if total_credit else 0.0
        self.student_repo.set_gpa(student_id, gpa)
        return gpa


def build_backend_services(
    student_repo: StudentRepositoryProtocol,
    course_repo: CourseRepositoryProtocol,
    enrollment_repo: EnrollmentRepositoryProtocol,
    grade_repo: GradeRepositoryProtocol,
) -> BackendServices:
    return BackendServices(
        students=StudentBusinessService(student_repo),
        courses=CourseBusinessService(course_repo),
        enrollments=EnrollmentBusinessService(
            student_repo,
            course_repo,
            enrollment_repo,
        ),
        grades=GradeBusinessService(
            student_repo,
            course_repo,
            enrollment_repo,
            grade_repo,
        ),
    )
