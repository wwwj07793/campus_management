from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from core.cache import CacheKeys, invalidate_course_related
from core.models.mysqlDB import CourseDB
from data.repositories.cache_sync import (
    cache_call_after_commit,
    cache_delete_after_commit,
    cache_delete_prefix_after_commit,
    cache_set_after_commit,
    cached_model_by_id,
    cached_models_by_ids,
)


class CourseRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        course_code: str,
        name: str,
        credit: int,
        teacher: str,
        schedule: str,
        capacity: int,
        current_count: int = 0,
        prerequisite_ids: list[int] | None = None,
    ) -> CourseDB:
        course = CourseDB(
            course_code=str(course_code),
            name=name,
            credit=int(credit),
            teacher=teacher,
            schedule=schedule,
            capacity=int(capacity),
            current_count=int(current_count),
        )
        if prerequisite_ids:
            prerequisites = self.list_by_ids(prerequisite_ids)
            course.prerequisites.extend(prerequisites)

        self.session.add(course)
        self.session.flush()
        self._sync_course_cache(course)
        self._invalidate_course_collections(course.course_code, course.teacher)
        return course

    def get_by_id(self, id: int) -> CourseDB | None:
        return cached_model_by_id(
            self.session,
            CacheKeys.course_db_id(id),
            CourseDB,
            lambda: self.session.get(CourseDB, id),
        )

    def get_by_identity(
        self,
        course_code: str,
        teacher: str,
        schedule: str,
    ) -> CourseDB | None:
        course_code = str(course_code)
        return cached_model_by_id(
            self.session,
            CacheKeys.course_db_identity(course_code, teacher, schedule),
            CourseDB,
            lambda: self.session.scalars(
                select(CourseDB).where(
                    CourseDB.course_code == course_code,
                    CourseDB.teacher == teacher,
                    CourseDB.schedule == schedule,
                )
            ).first(),
            validator=lambda course: (
                course.course_code == course_code
                and course.teacher == teacher
                and course.schedule == schedule
            ),
        )

    def get_with_prerequisites(self, id: int) -> CourseDB | None:
        course = self.get_by_id(id)
        if course is None:
            return None
        course.prerequisites
        return course

    def list_by_code(self, course_code: str) -> list[CourseDB]:
        course_code = str(course_code)
        return cached_models_by_ids(
            self.session,
            CacheKeys.course_db_code(course_code),
            CourseDB,
            lambda: self.session.scalars(
                select(CourseDB)
                .where(CourseDB.course_code == course_code)
                .order_by(CourseDB.teacher, CourseDB.schedule)
            ),
        )

    def list_by_teacher(self, teacher: str) -> list[CourseDB]:
        return cached_models_by_ids(
            self.session,
            CacheKeys.course_db_teacher(teacher),
            CourseDB,
            lambda: self.session.scalars(
                select(CourseDB)
                .where(CourseDB.teacher == teacher)
                .order_by(CourseDB.course_code, CourseDB.schedule)
            ),
        )

    def list_by_ids(self, ids: list[int]) -> list[CourseDB]:
        if not ids:
            return []
        return cached_models_by_ids(
            self.session,
            CacheKeys.course_db_ids(ids),
            CourseDB,
            lambda: self.session.scalars(
                select(CourseDB).where(CourseDB.id.in_(ids))
            ),
        )

    def list_all(self) -> list[CourseDB]:
        return cached_models_by_ids(
            self.session,
            CacheKeys.COURSE_DB_ALL,
            CourseDB,
            lambda: self.session.scalars(
                select(CourseDB).order_by(CourseDB.course_code, CourseDB.teacher)
            ),
        )

    def update(self, id: int, **fields) -> CourseDB | None:
        course = self.get_by_id(id)
        if course is None:
            return None

        old_course_code = course.course_code
        old_teacher = course.teacher
        old_schedule = course.schedule
        allowed_fields = {
            "course_code",
            "name",
            "credit",
            "teacher",
            "schedule",
            "capacity",
            "current_count",
        }
        for key, value in fields.items():
            if key not in allowed_fields:
                continue
            if key in {"credit", "capacity", "current_count"}:
                value = int(value)
            setattr(course, key, value)

        self.session.flush()
        if (
            old_course_code != course.course_code
            or old_teacher != course.teacher
            or old_schedule != course.schedule
        ):
            cache_delete_after_commit(
                self.session,
                CacheKeys.course_db_identity(
                    old_course_code,
                    old_teacher,
                    old_schedule,
                )
            )
            self._invalidate_course_collections(old_course_code, old_teacher)
        self._sync_course_cache(course)
        self._invalidate_course_collections(course.course_code, course.teacher)
        return course

    def add_prerequisite(self, course_id: int, prerequisite_course_id: int) -> bool:
        course = self.get_with_prerequisites(course_id)
        prerequisite = self.get_by_id(prerequisite_course_id)
        if course is None or prerequisite is None:
            return False
        if prerequisite not in course.prerequisites:
            course.prerequisites.append(prerequisite)
        self.session.flush()
        self._sync_course_cache(course)
        self._invalidate_course_collections(course.course_code, course.teacher)
        return True

    def remove_prerequisite(self, course_id: int, prerequisite_course_id: int) -> bool:
        course = self.get_with_prerequisites(course_id)
        prerequisite = self.get_by_id(prerequisite_course_id)
        if course is None or prerequisite is None:
            return False
        if prerequisite in course.prerequisites:
            course.prerequisites.remove(prerequisite)
        self.session.flush()
        self._sync_course_cache(course)
        self._invalidate_course_collections(course.course_code, course.teacher)
        return True

    def increase_current_count(self, id: int, amount: int = 1) -> CourseDB | None:
        course = self.get_by_id(id)
        if course is None:
            return None
        course.current_count += int(amount)
        self.session.flush()
        self._sync_course_cache(course)
        self._invalidate_course_collections(course.course_code, course.teacher)
        return course

    def decrease_current_count(self, id: int, amount: int = 1) -> CourseDB | None:
        course = self.get_by_id(id)
        if course is None:
            return None
        course.current_count -= int(amount)
        self.session.flush()
        self._sync_course_cache(course)
        self._invalidate_course_collections(course.course_code, course.teacher)
        return course

    def delete(self, id: int) -> bool:
        course = self.get_by_id(id)
        if course is None:
            return False
        database_id = course.id
        course_code = course.course_code
        teacher = course.teacher
        schedule = course.schedule
        self.session.delete(course)
        self.session.flush()
        cache_delete_after_commit(self.session, CacheKeys.course_db_id(database_id))
        cache_delete_after_commit(
            self.session,
            CacheKeys.course_db_identity(course_code, teacher, schedule),
        )
        self._invalidate_course_collections(course_code, teacher)
        return True

    def _sync_course_cache(self, course: CourseDB) -> None:
        cache_set_after_commit(self.session, CacheKeys.course_db_id(course.id), course.id)
        cache_set_after_commit(
            self.session,
            CacheKeys.course_db_identity(
                course.course_code,
                course.teacher,
                course.schedule,
            ),
            course.id,
        )

    def _invalidate_course_collections(
        self,
        course_code: str | None = None,
        teacher: str | None = None,
    ) -> None:
        cache_delete_after_commit(self.session, CacheKeys.COURSE_DB_ALL)
        cache_delete_prefix_after_commit(self.session, CacheKeys.COURSE_DB_IDS_PREFIX)
        if course_code is not None:
            cache_delete_after_commit(self.session, CacheKeys.course_db_code(course_code))
            cache_call_after_commit(
                self.session,
                lambda course_code=course_code: invalidate_course_related(course_code),
            )
        if teacher is not None:
            cache_delete_after_commit(self.session, CacheKeys.course_db_teacher(teacher))
