from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from core.cache import (
    CacheKeys,
    invalidate_course_related,
    invalidate_student_related,
)
from core.models.mysqlDB import CourseDB, EnrollmentDB, GradeDB, StudentDB
from data.repositories.cache_sync import (
    cache_call_after_commit,
    cache_delete_after_commit,
    cache_set_after_commit,
    cached_model_by_id,
    cached_models_by_ids,
)


class GradeRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, student_id: int, course_id: int, score: float) -> GradeDB:
        grade = GradeDB(
            student_id=student_id,
            course_id=course_id,
            score=float(score),
        )
        self.session.add(grade)
        self.session.flush()
        self._sync_grade_cache(grade)
        self._invalidate_grade_collections(student_id, course_id)
        return grade

    def get(self, student_id: int, course_id: int) -> GradeDB | None:
        return cached_model_by_id(
            self.session,
            CacheKeys.grade_db_pair(student_id, course_id),
            GradeDB,
            lambda: self.session.scalars(
                select(GradeDB).where(
                    GradeDB.student_id == student_id,
                    GradeDB.course_id == course_id,
                )
            ).first(),
            validator=lambda grade: (
                grade.student_id == student_id
                and grade.course_id == course_id
            ),
        )

    def upsert(self, student_id: int, course_id: int, score: float) -> GradeDB:
        enrollment = self.session.scalars(
            select(EnrollmentDB).where(
                EnrollmentDB.student_id == student_id,
                EnrollmentDB.course_id == course_id,
            )
        ).first()
        if enrollment is None:
            raise ValueError("成绩必须对应已有选课记录")

        grade = self.get(student_id, course_id)
        if grade is None:
            grade = self.create(student_id, course_id, score)
        else:
            grade.score = float(score)
            self.session.flush()
            self._sync_grade_cache(grade)
            self._invalidate_grade_collections(student_id, course_id)
        return grade

    def upsert_by_business_keys(
        self,
        student_number: str,
        course_code: str,
        teacher: str,
        schedule: str,
        score: float,
    ) -> GradeDB | None:
        enrollment = self.session.scalars(
            select(EnrollmentDB)
            .join(EnrollmentDB.student)
            .join(EnrollmentDB.course)
            .where(
                StudentDB.student_id == str(student_number),
                CourseDB.course_code == str(course_code),
                CourseDB.teacher == teacher,
                CourseDB.schedule == schedule,
            )
        ).first()
        if enrollment is None:
            return None
        return self.upsert(enrollment.student_id, enrollment.course_id, score)

    def list_by_student_id(self, student_id: int) -> list[GradeDB]:
        return cached_models_by_ids(
            self.session,
            CacheKeys.grade_db_student(student_id),
            GradeDB,
            lambda: self.session.scalars(
                select(GradeDB)
                .options(selectinload(GradeDB.course))
                .where(GradeDB.student_id == student_id)
            ),
        )

    def list_by_student_number(self, student_number: str) -> list[GradeDB]:
        student_number = str(student_number)
        return cached_models_by_ids(
            self.session,
            CacheKeys.grade_db_student_number(student_number),
            GradeDB,
            lambda: self.session.scalars(
                select(GradeDB)
                .join(GradeDB.student)
                .options(selectinload(GradeDB.course))
                .where(StudentDB.student_id == student_number)
            ),
        )

    def list_by_course_id(self, course_id: int) -> list[GradeDB]:
        return cached_models_by_ids(
            self.session,
            CacheKeys.grade_db_course(course_id),
            GradeDB,
            lambda: self.session.scalars(
                select(GradeDB)
                .options(selectinload(GradeDB.student))
                .where(GradeDB.course_id == course_id)
            ),
        )

    def delete(self, student_id: int, course_id: int) -> bool:
        grade = self.get(student_id, course_id)
        if grade is None:
            return False
        database_id = grade.id
        self.session.delete(grade)
        self.session.flush()
        cache_delete_after_commit(self.session, CacheKeys.grade_db_pair(student_id, course_id))
        cache_delete_after_commit(self.session, CacheKeys.grade_db_id(database_id))
        self._invalidate_grade_collections(student_id, course_id)
        return True

    def _sync_grade_cache(self, grade: GradeDB) -> None:
        cache_set_after_commit(
            self.session,
            CacheKeys.grade_db_pair(grade.student_id, grade.course_id),
            grade.id,
        )
        cache_set_after_commit(self.session, CacheKeys.grade_db_id(grade.id), grade.id)

    def _invalidate_grade_collections(self, student_id: int, course_id: int) -> None:
        student = self.session.get(StudentDB, student_id)
        course = self.session.get(CourseDB, course_id)

        cache_delete_after_commit(self.session, CacheKeys.grade_db_student(student_id))
        cache_delete_after_commit(self.session, CacheKeys.grade_db_course(course_id))
        if student is not None:
            cache_delete_after_commit(
                self.session,
                CacheKeys.grade_db_student_number(student.student_id),
            )
            cache_call_after_commit(
                self.session,
                lambda student_id=student.student_id: invalidate_student_related(student_id),
            )
        if course is not None:
            cache_call_after_commit(
                self.session,
                lambda course_code=course.course_code: invalidate_course_related(
                    course_code
                ),
            )
