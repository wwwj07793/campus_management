"""FastAPI grade endpoint tests."""
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
from tests.auth_helpers import auth_headers


def _make_client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def fake_session():
        s = Session()
        try: yield s; s.commit()
        except Exception: s.rollback(); raise
        finally: s.close()

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


def _setup():
    client.post("/api/students", json={
        "student_id": "2025001", "name": "张三", "gender": "男",
        "birth_date": "2005-03-15", "department": "电子信息工程学院", "grade": 2025,
    })
    client.post("/api/courses", json={
        "course_code": "AI001", "name": "人工智能导论", "credit": 3,
        "teacher": "李老师", "schedule": "周一1-2节", "capacity": 30,
    })
    client.post("/api/courses", json={
        "course_code": "PY001", "name": "Python程序设计", "credit": 4,
        "teacher": "王老师", "schedule": "周二3-4节", "capacity": 25,
    })
    client.post("/api/enrollments", json={
        "student_id": "2025001", "course_code": "AI001",
        "teacher": "李老师", "schedule": "周一1-2节",
    })
    client.post("/api/enrollments", json={
        "student_id": "2025001", "course_code": "PY001",
        "teacher": "王老师", "schedule": "周二3-4节",
    })


def test_record_and_list_grades():
    _setup()

    resp = client.post("/api/grades", json={
        "student_id": "2025001", "course_code": "AI001",
        "teacher": "李老师", "schedule": "周一1-2节", "score": 92,
    })
    assert resp.status_code == 201
    assert resp.json()["score"] == 92

    resp = client.post("/api/grades", json={
        "student_id": "2025001", "course_code": "PY001",
        "teacher": "王老师", "schedule": "周二3-4节", "score": 88,
    })
    assert resp.status_code == 201

    resp = client.get("/api/grades/students/2025001")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_course_grades():
    _setup()
    client.post("/api/grades", json={
        "student_id": "2025001", "course_code": "AI001",
        "teacher": "李老师", "schedule": "周一1-2节", "score": 92,
    })

    resp = client.get("/api/grades/courses/AI001")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["course_code"] == "AI001"
    assert resp.json()[0]["student_id"] == "2025001"


def test_grade_without_enrollment_rejected():
    _setup()
    resp = client.post("/api/grades", json={
        "student_id": "9999999", "course_code": "AI001",
        "teacher": "李老师", "schedule": "周一1-2节", "score": 80,
    })
    assert resp.status_code == 404


def test_grade_score_range_validation():
    resp = client.post("/api/grades", json={
        "student_id": "2025001", "course_code": "AI001",
        "teacher": "李老师", "schedule": "周一1-2节", "score": 150,
    })
    assert resp.status_code == 422


def test_update_and_delete_grade():
    _setup()
    payload = {
        "student_id": "2025001",
        "course_code": "AI001",
        "teacher": "李老师",
        "schedule": "周一1-2节",
        "score": 78,
    }
    resp = client.post("/api/grades", json=payload)
    assert resp.status_code == 201

    updated = {**payload, "score": 95}
    resp = client.put("/api/grades", json=updated)
    assert resp.status_code == 200
    assert resp.json()["score"] == 95

    resp = client.delete("/api/grades", params={
        "student_id": "2025001",
        "course_code": "AI001",
        "teacher": "李老师",
        "schedule": "周一1-2节",
    })
    assert resp.status_code == 204

    resp = client.get("/api/grades/students/2025001")
    assert resp.status_code == 200
    assert all(g["course_code"] != "AI001" for g in resp.json())
