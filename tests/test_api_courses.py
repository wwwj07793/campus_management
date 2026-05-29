"""FastAPI course endpoint tests."""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import core.models.mysqlDB  # noqa: F401
from api.app import create_app
from api.deps import get_repos, get_services, get_session
from core.models.base import Base
from core.services.service_factory import build_database_backend
from data.repositories import CourseRepository, StudentRepository
from tests.auth_helpers import auth_headers


def _make_client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def fake_session():
        s = Session()
        try:
            yield s
            s.commit()
        except Exception:
            s.rollback()
            raise
        finally:
            s.close()

    def fake_services(s=Depends(fake_session)):
        svc, _ = build_database_backend(s)
        return svc

    def fake_repos(s=Depends(fake_session)):
        from api.deps import Repos
        return Repos(s)

    app = create_app()
    app.dependency_overrides[get_session] = fake_session
    app.dependency_overrides[get_services] = fake_services
    app.dependency_overrides[get_repos] = fake_repos
    test_client = TestClient(app)
    test_client.headers.update(auth_headers("teacher"))
    return test_client


client = _make_client()


def _course_payload(code="AI001", **kw):
    return {
        "course_code": code,
        "name": "人工智能导论",
        "credit": 3,
        "teacher": "李老师",
        "schedule": "周一1-2节",
        "capacity": 30,
        **kw,
    }


def test_create_and_list():
    resp = client.post("/api/courses", json=_course_payload())
    assert resp.status_code == 201
    assert resp.json()["course_code"] == "AI001"

    resp = client.get("/api/courses")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_list_by_code_returns_all_sections():
    client.post("/api/courses", json=_course_payload(code="PY001", teacher="王老师", schedule="周二3-4节"))
    client.post("/api/courses", json=_course_payload(code="PY001", teacher="张老师", schedule="周三1-2节"))

    resp = client.get("/api/courses?code=PY001")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_by_teacher():
    resp = client.get("/api/courses?teacher=李老师")
    assert resp.status_code == 200
    for c in resp.json():
        assert c["teacher"] == "李老师"


def test_create_duplicate_rejected():
    client.post("/api/courses", json=_course_payload(code="ML201"))
    resp = client.post("/api/courses", json=_course_payload(code="ML201"))
    assert resp.status_code == 409


def test_get_update_and_delete_course():
    resp = client.post("/api/courses", json=_course_payload(
        code="DB101",
        teacher="赵老师",
        schedule="周四5-6节",
    ))
    assert resp.status_code == 201
    course_id = resp.json()["id"]

    resp = client.get(f"/api/courses/{course_id}")
    assert resp.status_code == 200
    assert resp.json()["course_code"] == "DB101"

    resp = client.put(f"/api/courses/{course_id}", json={
        "name": "数据库系统",
        "capacity": 45,
    })
    assert resp.status_code == 200
    assert resp.json()["name"] == "数据库系统"
    assert resp.json()["capacity"] == 45

    resp = client.delete(f"/api/courses/{course_id}")
    assert resp.status_code == 204

    resp = client.get(f"/api/courses/{course_id}")
    assert resp.status_code == 404
