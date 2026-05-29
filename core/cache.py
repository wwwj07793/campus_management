from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from time import monotonic
from typing import Any, Callable


@dataclass
class CacheItem:
    value: Any
    expires_at: float | None = None

    def is_expired(self, now: float | None = None) -> bool:
        if self.expires_at is None:
            return False
        return (now or monotonic()) >= self.expires_at


class MemoryCache:
    """Small in-process cache for query results and derived indexes.

    The cache is not a source of truth. Database writes should invalidate
    affected keys after commit, then queries can rebuild cached values.
    """

    def __init__(self, default_ttl_seconds: float | None = None):
        self.default_ttl_seconds = default_ttl_seconds
        self._items: dict[str, CacheItem] = {}
        self._lock = RLock()

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            item = self._items.get(key)
            if item is None:
                return default
            if item.is_expired():
                self._items.pop(key, None)
                return default
            return item.value

    def set(self, key: str, value: Any, ttl_seconds: float | None = None) -> Any:
        ttl = self.default_ttl_seconds if ttl_seconds is None else ttl_seconds
        expires_at = None if ttl is None else monotonic() + ttl
        with self._lock:
            self._items[key] = CacheItem(value=value, expires_at=expires_at)
        return value

    def get_or_set(
        self,
        key: str,
        factory: Callable[[], Any],
        ttl_seconds: float | None = None,
    ) -> Any:
        cached = self.get(key, default=None)
        if cached is not None:
            return cached

        value = factory()
        self.set(key, value, ttl_seconds=ttl_seconds)
        return value

    def delete(self, key: str) -> None:
        with self._lock:
            self._items.pop(key, None)

    def delete_many(self, keys: list[str] | tuple[str, ...] | set[str]) -> None:
        with self._lock:
            for key in keys:
                self._items.pop(key, None)

    def delete_prefix(self, prefix: str) -> int:
        with self._lock:
            matched_keys = [
                key
                for key in self._items
                if key.startswith(prefix)
            ]
            for key in matched_keys:
                self._items.pop(key, None)
            return len(matched_keys)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()

    def cleanup_expired(self) -> int:
        now = monotonic()
        with self._lock:
            expired_keys = [
                key
                for key, item in self._items.items()
                if item.is_expired(now)
            ]
            for key in expired_keys:
                self._items.pop(key, None)
            return len(expired_keys)

    def keys(self) -> list[str]:
        self.cleanup_expired()
        with self._lock:
            return list(self._items.keys())


class CacheKeys:
    """Centralized cache key builders used by services and data views."""

    WARNING_STUDENTS = "warning_students"
    GPA_DISTRIBUTION = "gpa_distribution"
    TEACHER_COURSE_INDEX = "index:teacher_courses"
    STUDENT_COUNT = "student_count"
    STUDENT_DB_ALL = "db:student:all"
    STUDENT_DB_SEARCH_PREFIX = "db:student:search:"
    COURSE_DB_ALL = "db:course:all"
    COURSE_DB_IDS_PREFIX = "db:course:ids:"
    COURSE_DB_CODE_PREFIX = "db:course:code:"
    COURSE_DB_TEACHER_PREFIX = "db:course:teacher:"
    ENROLLMENT_DB_STUDENT_PREFIX = "db:enrollment:student:"
    ENROLLMENT_DB_STUDENT_NUMBER_PREFIX = "db:enrollment:student_number:"
    ENROLLMENT_DB_COURSE_PREFIX = "db:enrollment:course:"
    GRADE_DB_STUDENT_PREFIX = "db:grade:student:"
    GRADE_DB_STUDENT_NUMBER_PREFIX = "db:grade:student_number:"
    GRADE_DB_COURSE_PREFIX = "db:grade:course:"

    @staticmethod
    def student_report(student_id: str) -> str:
        return f"student_report:{student_id}"

    @staticmethod
    def student_grades(student_id: str) -> str:
        return f"student_grades:{student_id}"

    @staticmethod
    def course_summary(course_code: str) -> str:
        return f"course_summary:{course_code}"

    @staticmethod
    def department_gpa(department: str) -> str:
        return f"department_gpa:{department}"

    @staticmethod
    def department_students(department: str) -> str:
        return f"department_students:{department}"

    @staticmethod
    def student_db_id(id: int) -> str:
        return f"db:student:id:{id}"

    @staticmethod
    def student_db_student_id(student_id: str) -> str:
        return f"db:student:student_id:{student_id}"

    @staticmethod
    def student_db_search(
        student_id: str | None = None,
        name: str | None = None,
        department: str | None = None,
        grade: int | None = None,
    ) -> str:
        return (
            f"{CacheKeys.STUDENT_DB_SEARCH_PREFIX}"
            f"student_id={student_id or ''}|"
            f"name={name or ''}|"
            f"department={department or ''}|"
            f"grade={'' if grade is None else grade}"
        )

    @staticmethod
    def course_db_id(id: int) -> str:
        return f"db:course:id:{id}"

    @staticmethod
    def course_db_identity(course_code: str, teacher: str, schedule: str) -> str:
        return f"db:course:identity:{course_code}|{teacher}|{schedule}"

    @staticmethod
    def course_db_code(course_code: str) -> str:
        return f"{CacheKeys.COURSE_DB_CODE_PREFIX}{course_code}"

    @staticmethod
    def course_db_teacher(teacher: str) -> str:
        return f"{CacheKeys.COURSE_DB_TEACHER_PREFIX}{teacher}"

    @staticmethod
    def course_db_ids(ids: list[int] | tuple[int, ...]) -> str:
        normalized_ids = ",".join(str(id) for id in sorted(ids))
        return f"{CacheKeys.COURSE_DB_IDS_PREFIX}{normalized_ids}"

    @staticmethod
    def enrollment_db_pair(student_id: int, course_id: int) -> str:
        return f"db:enrollment:pair:{student_id}:{course_id}"

    @staticmethod
    def enrollment_db_student(student_id: int) -> str:
        return f"{CacheKeys.ENROLLMENT_DB_STUDENT_PREFIX}{student_id}"

    @staticmethod
    def enrollment_db_student_number(student_number: str) -> str:
        return f"{CacheKeys.ENROLLMENT_DB_STUDENT_NUMBER_PREFIX}{student_number}"

    @staticmethod
    def enrollment_db_course(course_id: int) -> str:
        return f"{CacheKeys.ENROLLMENT_DB_COURSE_PREFIX}{course_id}"

    @staticmethod
    def grade_db_pair(student_id: int, course_id: int) -> str:
        return f"db:grade:pair:{student_id}:{course_id}"

    @staticmethod
    def grade_db_id(id: int) -> str:
        return f"db:grade:id:{id}"

    @staticmethod
    def grade_db_student(student_id: int) -> str:
        return f"{CacheKeys.GRADE_DB_STUDENT_PREFIX}{student_id}"

    @staticmethod
    def grade_db_student_number(student_number: str) -> str:
        return f"{CacheKeys.GRADE_DB_STUDENT_NUMBER_PREFIX}{student_number}"

    @staticmethod
    def grade_db_course(course_id: int) -> str:
        return f"{CacheKeys.GRADE_DB_COURSE_PREFIX}{course_id}"


cache = MemoryCache(default_ttl_seconds=300)


def invalidate_student_related(student_id: str) -> None:
    cache.delete_many(
        {
            CacheKeys.student_report(student_id),
            CacheKeys.student_grades(student_id),
            CacheKeys.WARNING_STUDENTS,
            CacheKeys.GPA_DISTRIBUTION,
        }
    )
    cache.delete_prefix("department_gpa:")


def invalidate_course_related(course_code: str) -> None:
    cache.delete_many(
        {
            CacheKeys.course_summary(course_code),
            CacheKeys.TEACHER_COURSE_INDEX,
        }
    )


def invalidate_student_index_related(department: str | None = None) -> None:
    cache.delete(CacheKeys.STUDENT_COUNT)
    if department:
        cache.delete(CacheKeys.department_students(department))
    else:
        cache.delete_prefix("department_students:")
