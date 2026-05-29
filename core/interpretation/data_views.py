from __future__ import annotations

from collections import defaultdict
from typing import Any


def iter_course_objects(courses):
    for value in courses.values():
        if isinstance(value, (list, tuple, set)):
            yield from value
        else:
            yield value


def _student_key(student: Any) -> str:
    return str(getattr(student, "student_id", getattr(student, "id")))


def _course_key(course: Any) -> str:
    if isinstance(course, str):
        return course
    if hasattr(course, "course_code"):
        return str(course.course_code)
    if hasattr(course, "course_id"):
        return str(course.course_id)
    return str(course.id)


def _course_id(course: Any) -> Any:
    return getattr(course, "id")


def _enrollment_student(enrollment: Any) -> Any:
    return getattr(enrollment, "student", None)


def _enrollment_course(enrollment: Any) -> Any:
    return getattr(enrollment, "course", None)


def _grade_student(grade: Any) -> Any:
    return getattr(grade, "student", None)


def _grade_course(grade: Any) -> Any:
    return getattr(grade, "course", None)


def _grade_score(grade: Any) -> Any:
    return getattr(grade, "score", None)


def _to_student_mapping(students: list[Any] | dict[str, Any]) -> dict[str, Any]:
    if isinstance(students, dict):
        return students
    return {_student_key(student): student for student in students}


def _to_course_mapping(courses: list[Any] | dict[str, Any]) -> dict[str, list[Any]]:
    if isinstance(courses, dict):
        result = {}
        for key, value in courses.items():
            if isinstance(value, (list, tuple, set)):
                result[str(key)] = list(value)
            else:
                result[str(key)] = [value]
        return result

    result = defaultdict(list)
    for course in courses:
        result[_course_key(course)].append(course)
    return result


def student_indexes(students):
    students = _to_student_mapping(students)
    by_department = defaultdict(list)
    by_grade = defaultdict(list)
    by_department_grade = defaultdict(lambda: defaultdict(list))

    for student in students.values():
        department = student.department
        grade = student.grade
        by_department[department].append(student)
        by_grade[grade].append(student)
        by_department_grade[department][grade].append(student)

    return {
        "by_department": by_department,
        "by_grade": by_grade,
        "by_department_grade": by_department_grade,
    }


def student_counts(students):
    students = _to_student_mapping(students)
    indexes = student_indexes(students)
    by_department = defaultdict(int)
    by_grade = defaultdict(int)
    by_department_grade = defaultdict(lambda: defaultdict(int))

    for department, department_students in indexes["by_department"].items():
        by_department[department] = len(department_students)
    for grade, grade_students in indexes["by_grade"].items():
        by_grade[grade] = len(grade_students)
    for department, grades in indexes["by_department_grade"].items():
        for grade, grade_students in grades.items():
            by_department_grade[department][grade] = len(grade_students)

    return {
        "total": len(students),
        "by_department": by_department,
        "by_grade": by_grade,
        "by_department_grade": by_department_grade,
    }


def students_by_scope(students, departments=None, grades=None):
    students = _to_student_mapping(students)
    departments = set(departments or [])
    grades = set(grades or [])

    result = []
    for student in students.values():
        if departments and student.department not in departments:
            continue
        if grades and student.grade not in grades:
            continue
        result.append(student)
    return result


def courses_by_teacher(courses):
    courses = _to_course_mapping(courses)
    result = defaultdict(list)
    for course in iter_course_objects(courses):
        result[course.teacher].append(course)
    return result


def teacher_statistics(courses):
    courses = _to_course_mapping(courses)
    grouped_courses = courses_by_teacher(courses)
    result = defaultdict(lambda: [0, 0, 0, 0.0])

    for teacher, teacher_courses in grouped_courses.items():
        total_credit = sum(course.credit for course in teacher_courses)
        selected_count = sum(course.current_count for course in teacher_courses)
        course_count = len(teacher_courses)
        all_count = 0

        for course in teacher_courses:
            same_code_courses = courses.get(_course_key(course), [])
            all_count += sum(item.current_count for item in same_code_courses)

        select_rate = selected_count / all_count if all_count else 0.0
        result[teacher] = [total_credit, selected_count, course_count, select_rate]

    return result


def students_by_course_for_scope(students, departments=None, grades=None):
    result = defaultdict(list)
    for student in students_by_scope(students, departments, grades):
        for course_id in getattr(student, "enrolled_courses", {}):
            result[course_id].append(student)
    return result


def courses_for_student(student, courses):
    courses = _to_course_mapping(courses)
    result = {}
    for course_id in getattr(student, "enrolled_courses", {}):
        course_list = courses.get(str(course_id), [])
        if course_list:
            result[str(course_id)] = course_list[0]
    return result


def scores_for_students(students):
    scores = []
    for student in students:
        for score in getattr(student, "enrolled_courses", {}).values():
            try:
                score = float(score)
            except (TypeError, ValueError):
                continue
            if 0 <= score <= 100:
                scores.append(score)
    return scores


def gpas_for_scope(students, departments=None, grades=None):
    return [
        student.gpa
        for student in students_by_scope(students, departments, grades)
    ]


class _LegacyReader:
    def __init__(self, students, courses):
        self._students = _to_student_mapping(students)
        self._courses = _to_course_mapping(courses)

    def list_students(self):
        return list(self._students.values())

    def list_courses(self):
        return list(iter_course_objects(self._courses))

    def list_enrollments(self):
        return []

    def list_grades(self):
        return []


class CampusDataView:
    def __init__(self, students=None, courses=None, reader=None):
        if reader is None:
            if students is None or courses is None:
                raise ValueError("CampusDataView 需要 reader，或 students + courses")
            reader = _LegacyReader(students, courses)
        self.reader = reader

    @property
    def students(self):
        return _to_student_mapping(self.reader.list_students())

    @property
    def courses(self):
        return _to_course_mapping(self.reader.list_courses())

    def student_indexes(self):
        return student_indexes(self.reader.list_students())

    def student_counts(self):
        return student_counts(self.reader.list_students())

    def students_by_scope(self, departments=None, grades=None):
        return students_by_scope(self.reader.list_students(), departments, grades)

    def courses_by_teacher(self):
        return courses_by_teacher(self.reader.list_courses())

    def teacher_statistics(self):
        return teacher_statistics(self.reader.list_courses())

    def students_by_course_for_scope(self, departments=None, grades=None):
        enrollments = self.reader.list_enrollments()
        if not enrollments:
            return students_by_course_for_scope(
                self.reader.list_students(),
                departments,
                grades,
            )

        departments = set(departments or [])
        grades = set(grades or [])
        result = defaultdict(list)
        for enrollment in enrollments:
            student = _enrollment_student(enrollment)
            course = _enrollment_course(enrollment)
            if student is None or course is None:
                continue
            if departments and student.department not in departments:
                continue
            if grades and student.grade not in grades:
                continue
            result[_course_key(course)].append(student)
        return result

    def courses_for_student(self, student):
        enrollments = self.reader.list_enrollments()
        if not enrollments:
            return courses_for_student(student, self.reader.list_courses())

        result = {}
        student_id = getattr(student, "id")
        for enrollment in enrollments:
            if getattr(enrollment, "student_id") != student_id:
                continue
            course = _enrollment_course(enrollment)
            if course is not None:
                result[_course_key(course)] = course
        return result

    def scores_for_students(self, students):
        grades = self.reader.list_grades()
        if not grades:
            return scores_for_students(students)

        student_ids = {getattr(student, "id") for student in students}
        scores = []
        for grade in grades:
            if getattr(grade, "student_id") not in student_ids:
                continue
            try:
                score = float(_grade_score(grade))
            except (TypeError, ValueError):
                continue
            if 0 <= score <= 100:
                scores.append(score)
        return scores

    def gpas_for_scope(self, departments=None, grades=None):
        return gpas_for_scope(self.reader.list_students(), departments, grades)

    def scores_for_course(self, course_code, departments=None, grades=None):
        scoped_students = self.students_by_scope(departments, grades)
        scoped_student_ids = {getattr(student, "id") for student in scoped_students}
        result = []
        for grade in self.reader.list_grades():
            course = _grade_course(grade)
            if course is None or _course_key(course) != str(course_code):
                continue
            if getattr(grade, "student_id") not in scoped_student_ids:
                continue
            result.append(_grade_score(grade))
        return result
