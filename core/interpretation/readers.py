from __future__ import annotations

from typing import Any, Protocol

class CampusDataReader(Protocol):
    def list_students(self) -> list[Any]: ...
    def list_courses(self) -> list[Any]: ...
    def list_enrollments(self) -> list[Any]: ...
    def list_grades(self) -> list[Any]: ...


class MemoryCampusDataReader:
    def __init__(
        self,
        students: dict[str, Any],
        courses: dict[str, Any],
        enrollments: list[Any] | None = None,
        grades: list[Any] | None = None,
    ):
        self._students = students
        self._courses = courses
        self._enrollments = enrollments
        self._grades = grades

    def list_students(self) -> list[Any]:
        return list(self._students.values())

    def list_courses(self) -> list[Any]:
        courses = []
        for value in self._courses.values():
            if isinstance(value, (list, tuple, set)):
                courses.extend(value)
            else:
                courses.append(value)
        return courses

    def list_enrollments(self) -> list[Any]:
        if self._enrollments is not None:
            return self._enrollments
        return []

    def list_grades(self) -> list[Any]:
        if self._grades is not None:
            return self._grades
        return []


class RepositoryCampusDataReader:
    def __init__(
        self,
        student_repo,
        course_repo,
        enrollment_repo=None,
        grade_repo=None,
    ):
        self.student_repo = student_repo
        self.course_repo = course_repo
        self.enrollment_repo = enrollment_repo
        self.grade_repo = grade_repo

    def list_students(self) -> list[Any]:
        return self.student_repo.list_all()

    def list_courses(self) -> list[Any]:
        return self.course_repo.list_all()

    def list_enrollments(self) -> list[Any]:
        if self.enrollment_repo is None:
            return []
        if hasattr(self.enrollment_repo, "list_all"):
            return self.enrollment_repo.list_all()
        enrollments = []
        for student in self.list_students():
            enrollments.extend(self.enrollment_repo.list_by_student_id(student.id))
        return enrollments

    def list_grades(self) -> list[Any]:
        if self.grade_repo is None:
            return []
        if hasattr(self.grade_repo, "list_all"):
            return self.grade_repo.list_all()
        grades = []
        for student in self.list_students():
            grades.extend(self.grade_repo.list_by_student_id(student.id))
        return grades
