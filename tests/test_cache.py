import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from core.cache import CacheKeys, MemoryCache


def test_cache_get_set_and_delete():
    cache = MemoryCache()

    cache.set("student_report:2025001", {"gpa": 3.7})

    assert cache.get("student_report:2025001") == {"gpa": 3.7}

    cache.delete("student_report:2025001")

    assert cache.get("student_report:2025001") is None


def test_cache_prefix_invalidation():
    cache = MemoryCache()

    cache.set("department_gpa:电子信息工程学院", [3.7, 2.8])
    cache.set("department_gpa:计算机科学与技术学院", [3.5])
    cache.set("warning_students", ["2025007"])

    deleted_count = cache.delete_prefix("department_gpa:")

    assert deleted_count == 2
    assert cache.get("department_gpa:电子信息工程学院") is None
    assert cache.get("department_gpa:计算机科学与技术学院") is None
    assert cache.get("warning_students") == ["2025007"]


def test_cache_ttl_expires_value():
    cache = MemoryCache()

    cache.set("gpa_distribution", [1, 2, 3], ttl_seconds=0.01)
    time.sleep(0.02)

    assert cache.get("gpa_distribution") is None


def test_cache_get_or_set_uses_factory_once():
    cache = MemoryCache()
    calls = {"count": 0}

    def build_value():
        calls["count"] += 1
        return ["AI001", "ML201"]

    first = cache.get_or_set(CacheKeys.TEACHER_COURSE_INDEX, build_value)
    second = cache.get_or_set(CacheKeys.TEACHER_COURSE_INDEX, build_value)

    assert first == ["AI001", "ML201"]
    assert second == ["AI001", "ML201"]
    assert calls["count"] == 1
