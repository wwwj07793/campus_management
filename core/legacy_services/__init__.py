"""Legacy in-memory command-line services.

These modules are kept as a learning-stage reference and for the historical
memory-flow tests. New backend work should use ``core.services``.
"""

from core.legacy_services.Course import CourseManage
from core.legacy_services.Grade import GradeManage
from core.legacy_services.Student import StudentManage

__all__ = [
    "CourseManage",
    "GradeManage",
    "StudentManage",
]
