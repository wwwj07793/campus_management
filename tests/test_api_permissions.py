from __future__ import annotations

import sys
from pathlib import Path

from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import core.models.mysqlDB  # noqa: F401
from api.deps import get_services, get_session
from core.models.base import Base
from core.services.service_factory import build_database_backend
from main import create_app
from tests.auth_helpers import auth_headers


def make_client(role: str | None = "teacher") -> TestClient:
    engine = create_engine(
        "sqlite://",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_session():
        session = TestSession()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def override_services(session=Depends(override_session)):
        services, _ = build_database_backend(session)
        return services

    app = create_app()
    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_services] = override_services
    client = TestClient(app)
    if role is not None:
        client.headers.update(auth_headers(role))
    return client


def test_protected_api_requires_login():
    client = make_client(role=None)

    response = client.get("/api/courses")

    assert response.status_code == 401


def test_student_cannot_manage_students_or_grades():
    client = make_client(role="student")

    student_response = client.get("/api/students")
    grade_response = client.post("/api/grades", json={
        "student_id": "2025001",
        "course_code": "AI001",
        "teacher": "李老师",
        "schedule": "周一1-2节",
        "score": 90,
    })

    assert student_response.status_code == 403
    assert grade_response.status_code == 403


def test_student_can_read_courses():
    client = make_client(role="student")

    response = client.get("/api/courses")

    assert response.status_code == 200
