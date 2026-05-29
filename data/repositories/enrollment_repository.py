from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from core.cache import (
    CacheKeys,
    invalidate_course_related,
    invalidate_student_related,
)
from core.models.mysqlDB import CourseDB, EnrollmentDB, StudentDB
from data.repositories.cache_sync import (
    cache_call_after_commit,
    cache_delete_after_commit,
    cache_set_after_commit,
    cached_model_by_composite_key,
    cached_models_by_composite_keys,
)


class EnrollmentRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        student_id: int,
        course_id: int,
        update_course_count: bool = True,
    ) -> EnrollmentDB:
        student = self.session.get(StudentDB, student_id)
        if student is None:
            raise ValueError("学生不存在")

        if self.get(student_id, course_id) is not None:
            raise ValueError("学生已经选过该课程")

        course_stmt = select(CourseDB).where(CourseDB.id == course_id)
        if update_course_count:
            course_stmt = course_stmt.with_for_update()
        course = self.session.scalars(course_stmt).first()
        if course is None:
            raise ValueError("课程不存在")
        if update_course_count and course.current_count >= course.capacity:
            raise ValueError("课程容量已满")

        enrollment = EnrollmentDB(student_id=student_id, course_id=course_id)
        self.session.add(enrollment)
        if update_course_count:
            course.current_count += 1
        self.session.flush()
        self._sync_enrollment_cache(enrollment)
        self._invalidate_enrollment_collections(student_id, course_id, student, course)
        return enrollment

    def create_by_business_keys(
        self,
        student_number: str,
        course_code: str,
        teacher: str,
        schedule: str,
    ) -> EnrollmentDB | None:
        student = self.session.scalars(
            select(StudentDB).where(StudentDB.student_id == str(student_number))
        ).first()
        course = self.session.scalars(
            select(CourseDB).where(
                CourseDB.course_code == str(course_code),
                CourseDB.teacher == teacher,
                CourseDB.schedule == schedule,
            )
        ).first()
        if student is None or course is None:
            return None
        return self.create(student.id, course.id)

    def get(self, student_id: int, course_id: int) -> EnrollmentDB | None:
        return cached_model_by_composite_key(
            self.session,
            CacheKeys.enrollment_db_pair(student_id, course_id),
            EnrollmentDB,
            lambda: self.session.scalars(
                select(EnrollmentDB).where(
                    EnrollmentDB.student_id == student_id,
                    EnrollmentDB.course_id == course_id,
                )
            ).first(),
        )

    def exists(self, student_id: int, course_id: int) -> bool:
        return self.get(student_id, course_id) is not None

    def list_by_student_id(self, student_id: int) -> list[EnrollmentDB]:
        return cached_models_by_composite_keys(
            self.session,
            CacheKeys.enrollment_db_student(student_id),
            EnrollmentDB,
            lambda: self.session.scalars(
                select(EnrollmentDB)
                .options(selectinload(EnrollmentDB.course))
                .where(EnrollmentDB.student_id == student_id)
            ),
        )

    def list_by_student_number(self, student_number: str) -> list[EnrollmentDB]:
        student_number = str(student_number)
        return cached_models_by_composite_keys(
            self.session,
            CacheKeys.enrollment_db_student_number(student_number),
            EnrollmentDB,
            lambda: self.session.scalars(
                select(EnrollmentDB)
                .join(EnrollmentDB.student)
                .options(selectinload(EnrollmentDB.course))
                .where(StudentDB.student_id == student_number)
            ),
        )

    def list_by_course_id(self, course_id: int) -> list[EnrollmentDB]:
        return cached_models_by_composite_keys(
            self.session,
            CacheKeys.enrollment_db_course(course_id),
            EnrollmentDB,
            lambda: self.session.scalars(
                select(EnrollmentDB)
                .options(selectinload(EnrollmentDB.student))
                .where(EnrollmentDB.course_id == course_id)
            ),
        )

    def delete(
        self,
        student_id: int,
        course_id: int,
        update_course_count: bool = True,
    ) -> bool:
        enrollment = self.get(student_id, course_id)
        if enrollment is None:
            return False
        student = self.session.get(StudentDB, student_id)
        course = self.session.get(CourseDB, course_id)
        if update_course_count:
            if course is not None:
                course.current_count = max(course.current_count - 1, 0)
        self.session.delete(enrollment)
        self.session.flush()
        cache_delete_after_commit(
            self.session,
            CacheKeys.enrollment_db_pair(student_id, course_id),
        )
        self._invalidate_enrollment_collections(student_id, course_id, student, course)
        return True

    def delete_by_business_keys(
        self,
        student_number: str,
        course_code: str,
        teacher: str,
        schedule: str,
    ) -> bool:
        stmt = (
            select(EnrollmentDB)
            .join(EnrollmentDB.student)
            .join(EnrollmentDB.course)
            .where(
                StudentDB.student_id == str(student_number),
                CourseDB.course_code == str(course_code),
                CourseDB.teacher == teacher,
                CourseDB.schedule == schedule,
            )
        )
        enrollment = self.session.scalars(stmt).first()
        if enrollment is None:
            return False
        return self.delete(enrollment.student_id, enrollment.course_id)

    def _sync_enrollment_cache(self, enrollment: EnrollmentDB) -> None:
        cache_set_after_commit(
            self.session,
            CacheKeys.enrollment_db_pair(
                enrollment.student_id,
                enrollment.course_id,
            ),
            (enrollment.student_id, enrollment.course_id),
        )

    def _invalidate_enrollment_collections(
        self,
        student_id: int,
        course_id: int,
        student: StudentDB | None = None,
        course: CourseDB | None = None,
    ) -> None:
        student = student or self.session.get(StudentDB, student_id)
        course = course or self.session.get(CourseDB, course_id)

        cache_delete_after_commit(self.session, CacheKeys.enrollment_db_student(student_id))
        cache_delete_after_commit(self.session, CacheKeys.enrollment_db_course(course_id))
        cache_delete_after_commit(self.session, CacheKeys.grade_db_pair(student_id, course_id))
        cache_delete_after_commit(self.session, CacheKeys.grade_db_student(student_id))
        cache_delete_after_commit(self.session, CacheKeys.grade_db_course(course_id))
        cache_delete_after_commit(self.session, CacheKeys.course_db_id(course_id))

        if student is not None:
            cache_delete_after_commit(
                self.session,
                CacheKeys.enrollment_db_student_number(student.student_id),
            )
            cache_delete_after_commit(
                self.session,
                CacheKeys.grade_db_student_number(student.student_id),
            )
            cache_call_after_commit(
                self.session,
                lambda student_id=student.student_id: invalidate_student_related(student_id),
            )
        if course is not None:
            cache_delete_after_commit(
                self.session,
                CacheKeys.course_db_identity(
                    course.course_code,
                    course.teacher,
                    course.schedule,
                )
            )
            cache_delete_after_commit(
                self.session,
                CacheKeys.course_db_code(course.course_code),
            )
            cache_delete_after_commit(
                self.session,
                CacheKeys.course_db_teacher(course.teacher),
            )
            cache_call_after_commit(
                self.session,
                lambda course_code=course.course_code: invalidate_course_related(
                    course_code
                ),
            )
