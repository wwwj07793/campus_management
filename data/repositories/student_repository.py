from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from core.cache import (
    CacheKeys,
    invalidate_student_index_related,
    invalidate_student_related,
)
from core.models.mysqlDB import StudentDB
from data.repositories.cache_sync import (
    cache_call_after_commit,
    cache_delete_after_commit,
    cache_delete_prefix_after_commit,
    cache_set_after_commit,
    cached_model_by_id,
    cached_models_by_ids,
)


def _as_date(value: date | str) -> date:
    if isinstance(value, date):
        return value
    return datetime.strptime(value, "%Y-%m-%d").date()


class StudentRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        student_id: str,
        name: str,
        gender: str,
        birth_date: date | str,
        department: str,
        grade: int,
        gpa: float = 0.0,
    ) -> StudentDB:
        student = StudentDB(
            student_id=str(student_id),
            name=name,
            gender=gender,
            birth_date=_as_date(birth_date),
            department=department,
            grade=int(grade),
            gpa=float(gpa),
        )
        self.session.add(student)
        self.session.flush()
        self._sync_student_cache(student)
        self._invalidate_student_collections(student.department)
        return student

    def get_by_id(self, id: int) -> StudentDB | None:
        return cached_model_by_id(
            self.session,
            CacheKeys.student_db_id(id),
            StudentDB,
            lambda: self.session.get(StudentDB, id),
        )

    def get_by_student_id(self, student_id: str) -> StudentDB | None:
        student_id = str(student_id)
        return cached_model_by_id(
            self.session,
            CacheKeys.student_db_student_id(student_id),
            StudentDB,
            lambda: self.session.scalars(
                select(StudentDB).where(StudentDB.student_id == student_id)
            ).first(),
            validator=lambda student: student.student_id == student_id,
        )

    def get_profile(self, student_id: str) -> StudentDB | None:
        student = self.get_by_student_id(student_id)
        if student is None:
            return None
        student.enrollments
        student.grades
        return student

    def list_all(self) -> list[StudentDB]:
        return cached_models_by_ids(
            self.session,
            CacheKeys.STUDENT_DB_ALL,
            StudentDB,
            lambda: self.session.scalars(
                select(StudentDB).order_by(StudentDB.student_id)
            ),
        )

    def search(
        self,
        student_id: str | None = None,
        name: str | None = None,
        department: str | None = None,
        grade: int | None = None,
    ) -> list[StudentDB]:
        cache_key = CacheKeys.student_db_search(student_id, name, department, grade)

        def query_students():
            stmt = select(StudentDB)
            if student_id:
                stmt = stmt.where(StudentDB.student_id.like(f"%{student_id}%"))
            if name:
                stmt = stmt.where(StudentDB.name.like(f"%{name}%"))
            if department:
                stmt = stmt.where(StudentDB.department == department)
            if grade is not None:
                stmt = stmt.where(StudentDB.grade == int(grade))
            stmt = stmt.order_by(StudentDB.student_id)
            return self.session.scalars(stmt)

        return cached_models_by_ids(
            self.session,
            cache_key,
            StudentDB,
            query_students,
        )

    def update(self, lookup_student_id: str, **fields) -> StudentDB | None:
        student = self.get_by_student_id(lookup_student_id)
        if student is None:
            return None

        old_student_id = student.student_id
        old_department = student.department
        allowed_fields = {
            "student_id",
            "name",
            "gender",
            "birth_date",
            "department",
            "grade",
            "gpa",
        }
        for key, value in fields.items():
            if key not in allowed_fields:
                continue
            if key == "birth_date":
                value = _as_date(value)
            if key == "grade":
                value = int(value)
            if key == "gpa":
                value = float(value)
            setattr(student, key, value)

        self.session.flush()
        if old_student_id != student.student_id:
            cache_delete_after_commit(
                self.session,
                CacheKeys.student_db_student_id(old_student_id),
            )
            cache_call_after_commit(
                self.session,
                lambda old_student_id=old_student_id: invalidate_student_related(
                    old_student_id
                ),
            )
        if old_department != student.department:
            cache_call_after_commit(
                self.session,
                lambda old_department=old_department: invalidate_student_index_related(
                    old_department
                ),
            )
        self._sync_student_cache(student)
        self._invalidate_student_collections(student.department)
        cache_call_after_commit(
            self.session,
            lambda student_id=student.student_id: invalidate_student_related(student_id),
        )
        return student

    def set_gpa(self, student_id: str, gpa: float) -> StudentDB | None:
        return self.update(student_id, gpa=gpa)

    def delete(self, student_id: str) -> bool:
        student = self.get_by_student_id(student_id)
        if student is None:
            return False

        database_id = student.id
        student_number = student.student_id
        department = student.department
        self.session.delete(student)
        self.session.flush()
        cache_delete_after_commit(self.session, CacheKeys.student_db_id(database_id))
        cache_delete_after_commit(
            self.session,
            CacheKeys.student_db_student_id(student_number),
        )
        self._invalidate_student_collections(department)
        cache_call_after_commit(
            self.session,
            lambda student_number=student_number: invalidate_student_related(
                student_number
            ),
        )
        return True

    def _sync_student_cache(self, student: StudentDB) -> None:
        cache_set_after_commit(self.session, CacheKeys.student_db_id(student.id), student.id)
        cache_set_after_commit(
            self.session,
            CacheKeys.student_db_student_id(student.student_id),
            student.id,
        )

    def _invalidate_student_collections(self, department: str | None = None) -> None:
        cache_delete_after_commit(self.session, CacheKeys.STUDENT_DB_ALL)
        cache_delete_prefix_after_commit(self.session, CacheKeys.STUDENT_DB_SEARCH_PREFIX)
        cache_call_after_commit(
            self.session,
            lambda department=department: invalidate_student_index_related(department),
        )
