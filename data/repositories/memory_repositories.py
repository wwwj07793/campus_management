from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from core.models.Course import Course
from core.models.Student import Student


@dataclass
class MemoryEnrollment:
    student_id: str
    course_id: str
    student: Student
    course: Course


@dataclass
class MemoryGrade:
    id: str
    student_id: str
    course_id: str
    score: float
    student: Student
    course: Course


class MemoryStudentRepository:
    def __init__(self, students: dict[str, Student] | None = None):
        self.students = students if students is not None else {}

    def create(
        self,
        student_id: str,
        name: str,
        gender: str,
        birth_date: date | str,
        department: str,
        grade: int,
        gpa: float = 0.0,
    ) -> Student:
        student = Student(
            student_id=str(student_id),
            name=name,
            gender=gender,
            birth_date=birth_date,
            department=department,
            grade=int(grade),
        )
        student.gpa = float(gpa)
        self.students[student.student_id] = student
        return student

    def get_by_id(self, id: str) -> Student | None:
        return self.students.get(str(id))

    def get_by_student_id(self, student_id: str) -> Student | None:
        return self.students.get(str(student_id))

    def get_profile(self, student_id: str) -> Student | None:
        return self.get_by_student_id(student_id)

    def list_all(self) -> list[Student]:
        return sorted(self.students.values(), key=lambda student: student.student_id)

    def search(
        self,
        student_id: str | None = None,
        name: str | None = None,
        department: str | None = None,
        grade: int | None = None,
    ) -> list[Student]:
        result = []
        for student in self.students.values():
            if student_id and student_id not in str(student.student_id):
                continue
            if name and name not in student.name:
                continue
            if department and student.department != department:
                continue
            if grade is not None and int(student.grade) != int(grade):
                continue
            result.append(student)
        return sorted(result, key=lambda student: student.student_id)

    def update(self, lookup_student_id: str, **fields) -> Student | None:
        student = self.get_by_student_id(lookup_student_id)
        if student is None:
            return None
        old_student_id = student.student_id
        for key, value in fields.items():
            if not hasattr(student, key):
                continue
            if key == "grade":
                value = int(value)
            if key == "gpa":
                value = float(value)
            setattr(student, key, value)
        if old_student_id != student.student_id:
            self.students.pop(old_student_id, None)
            self.students[str(student.student_id)] = student
        return student

    def set_gpa(self, student_id: str, gpa: float) -> Student | None:
        return self.update(student_id, gpa=gpa)

    def delete(self, student_id: str) -> bool:
        return self.students.pop(str(student_id), None) is not None


class MemoryCourseRepository:
    def __init__(self, courses: dict[str, list[Course]] | None = None):
        self.courses = courses if courses is not None else {}

    def create(
        self,
        course_code: str,
        name: str,
        credit: int,
        teacher: str,
        schedule: str,
        capacity: int,
        current_count: int = 0,
        prerequisite_ids: list[str] | None = None,
    ) -> Course:
        course = Course(
            course_id=str(course_code),
            name=name,
            credit=int(credit),
            teacher=teacher,
            schedule=schedule,
            capacity=int(capacity),
            prerequisites=prerequisite_ids or [],
        )
        course.current_count = int(current_count)
        self.courses.setdefault(course.id, []).append(course)
        return course

    def get_by_id(self, id: str) -> Course | None:
        course_list = self.courses.get(str(id), [])
        return course_list[0] if course_list else None

    def get_by_identity(
        self,
        course_code: str,
        teacher: str,
        schedule: str,
    ) -> Course | None:
        for course in self.courses.get(str(course_code), []):
            if course.teacher == teacher and course.schedule == schedule:
                return course
        return None

    def list_by_code(self, course_code: str) -> list[Course]:
        return list(self.courses.get(str(course_code), []))

    def list_by_teacher(self, teacher: str) -> list[Course]:
        return [
            course
            for course_list in self.courses.values()
            for course in course_list
            if course.teacher == teacher
        ]

    def list_all(self) -> list[Course]:
        return [
            course
            for course_list in self.courses.values()
            for course in course_list
        ]

    def update(self, id: str, **fields) -> Course | None:
        course = self.get_by_id(id)
        if course is None:
            return None
        for key, value in fields.items():
            if key in {"credit", "capacity", "current_count"}:
                value = int(value)
            if hasattr(course, key):
                setattr(course, key, value)
        return course

    def delete(self, id: str) -> bool:
        course_list = self.courses.get(str(id), [])
        if not course_list:
            return False
        course_list.pop(0)
        if not course_list:
            self.courses.pop(str(id), None)
        return True


class MemoryEnrollmentRepository:
    def __init__(
        self,
        student_repo: MemoryStudentRepository,
        course_repo: MemoryCourseRepository,
    ):
        self.student_repo = student_repo
        self.course_repo = course_repo
        self.enrollments: dict[tuple[str, str], MemoryEnrollment] = {}

    def create(
        self,
        student_id: str,
        course_id: str,
        update_course_count: bool = True,
    ) -> MemoryEnrollment:
        student = self.student_repo.get_by_id(student_id)
        course = self.course_repo.get_by_id(course_id)
        if student is None:
            raise ValueError("学生不存在")
        if course is None:
            raise ValueError("课程不存在")
        if self.get(student_id, course_id) is not None:
            raise ValueError("学生已经选过该课程")
        if update_course_count and course.current_count >= course.capacity:
            raise ValueError("课程容量已满")

        enrollment = MemoryEnrollment(
            student_id=str(student_id),
            course_id=str(course_id),
            student=student,
            course=course,
        )
        self.enrollments[(str(student_id), str(course_id))] = enrollment
        student.enrolled_courses[str(course.id)] = None
        course.enrolled_students.add(student)
        if update_course_count:
            course.current_count += 1
        return enrollment

    def get(self, student_id: str, course_id: str) -> MemoryEnrollment | None:
        return self.enrollments.get((str(student_id), str(course_id)))

    def exists(self, student_id: str, course_id: str) -> bool:
        return self.get(student_id, course_id) is not None

    def list_by_student_id(self, student_id: str) -> list[MemoryEnrollment]:
        return [
            enrollment
            for enrollment in self.enrollments.values()
            if enrollment.student_id == str(student_id)
        ]

    def list_by_student_number(self, student_number: str) -> list[MemoryEnrollment]:
        return self.list_by_student_id(student_number)

    def list_by_course_id(self, course_id: str) -> list[MemoryEnrollment]:
        return [
            enrollment
            for enrollment in self.enrollments.values()
            if enrollment.course_id == str(course_id)
        ]

    def list_all(self) -> list[MemoryEnrollment]:
        return list(self.enrollments.values())

    def delete(
        self,
        student_id: str,
        course_id: str,
        update_course_count: bool = True,
    ) -> bool:
        enrollment = self.enrollments.pop((str(student_id), str(course_id)), None)
        if enrollment is None:
            return False
        enrollment.student.enrolled_courses.pop(str(course_id), None)
        enrollment.course.enrolled_students.discard(enrollment.student)
        if update_course_count:
            enrollment.course.current_count = max(enrollment.course.current_count - 1, 0)
        return True


class MemoryGradeRepository:
    def __init__(
        self,
        enrollment_repo: MemoryEnrollmentRepository,
    ):
        self.enrollment_repo = enrollment_repo
        self.grades: dict[tuple[str, str], MemoryGrade] = {}

    def create(self, student_id: str, course_id: str, score: float) -> MemoryGrade:
        enrollment = self.enrollment_repo.get(student_id, course_id)
        if enrollment is None:
            raise ValueError("成绩必须对应已有选课记录")
        grade = MemoryGrade(
            id=f"{student_id}:{course_id}",
            student_id=str(student_id),
            course_id=str(course_id),
            score=float(score),
            student=enrollment.student,
            course=enrollment.course,
        )
        self.grades[(str(student_id), str(course_id))] = grade
        enrollment.student.enrolled_courses[str(course_id)] = float(score)
        return grade

    def get(self, student_id: str, course_id: str) -> MemoryGrade | None:
        return self.grades.get((str(student_id), str(course_id)))

    def upsert(self, student_id: str, course_id: str, score: float) -> MemoryGrade:
        grade = self.get(student_id, course_id)
        if grade is None:
            return self.create(student_id, course_id, score)
        grade.score = float(score)
        grade.student.enrolled_courses[str(course_id)] = float(score)
        return grade

    def list_by_student_id(self, student_id: str) -> list[MemoryGrade]:
        return [
            grade
            for grade in self.grades.values()
            if grade.student_id == str(student_id)
        ]

    def list_by_student_number(self, student_number: str) -> list[MemoryGrade]:
        return self.list_by_student_id(student_number)

    def list_by_course_id(self, course_id: str) -> list[MemoryGrade]:
        return [
            grade
            for grade in self.grades.values()
            if grade.course_id == str(course_id)
        ]

    def list_all(self) -> list[MemoryGrade]:
        return list(self.grades.values())

    def delete(self, student_id: str, course_id: str) -> bool:
        grade = self.grades.pop((str(student_id), str(course_id)), None)
        if grade is None:
            return False
        grade.student.enrolled_courses[str(course_id)] = None
        return True
