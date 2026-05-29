from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass

from fastapi import Depends
from sqlalchemy.orm import Session

from core.interpretation.data_views import CampusDataView
from core.interpretation.readers import RepositoryCampusDataReader
from core.services.backend_services import BackendServices
from core.services.service_factory import build_database_backend
from data.database import session_scope


def get_session() -> Generator[Session, None, None]:
    with session_scope() as session:
        yield session


def get_services(session: Session = Depends(get_session)) -> BackendServices:
    services, _ = build_database_backend(session)
    return services


# ── Internals shared by analytics deps ────────────────────────────────────

class Repos:
    """Thin holder so analytics can reach the repository layer directly."""
    def __init__(self, session: Session):
        from data.repositories import (
            CourseRepository,
            EnrollmentRepository,
            GradeRepository,
            StudentRepository,
        )
        self.student = StudentRepository(session)
        self.course = CourseRepository(session)
        self.enrollment = EnrollmentRepository(session)
        self.grade = GradeRepository(session)


def get_repos(session: Session = Depends(get_session)) -> Repos:
    return Repos(session)


def get_data_view(session: Session = Depends(get_session)) -> CampusDataView:
    repos = Repos(session)
    reader = RepositoryCampusDataReader(
        repos.student, repos.course, repos.enrollment, repos.grade
    )
    return CampusDataView(reader=reader)
