"""FastAPI enrollment endpoint tests."""
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


def _setup_fixtures():
    """Create a student and a course, return their identities."""
    client.post("/api/students", json={
        "student_id": "2025001", "name": "张三", "gender": "男",
        "birth_date": "2005-03-15", "department": "电子信息工程学院", "grade": 2025,
    })
    client.post("/api/students", json={
        "student_id": "2025002", "name": "李四", "gender": "女",
        "birth_date": "2005-07-20", "department": "计算机科学与技术学院", "grade": 2025,
    })
    client.post("/api/courses", json={
        "course_code": "AI001", "name": "人工智能导论", "credit": 3,
        "teacher": "李老师", "schedule": "周一1-2节", "capacity": 30,
    })


_enroll_payload = {
    "student_id": "2025001",
    "course_code": "AI001",
    "teacher": "李老师",
    "schedule": "周一1-2节",
}


def test_enroll_and_list():
    _setup_fixtures()
    resp = client.post("/api/enrollments", json=_enroll_payload)
    assert resp.status_code == 201
    assert resp.json()["course_code"] == "AI001"

    resp = client.get("/api/enrollments/students/2025001")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_drop():
    _setup_fixtures()
    client.post("/api/enrollments", json=_enroll_payload)
    resp = client.delete("/api/enrollments", params=_enroll_payload)
    assert resp.status_code == 204

    resp = client.get("/api/enrollments/students/2025001")
    assert len(resp.json()) == 0


def test_enroll_nonexistent_student():
    resp = client.post("/api/enrollments", json={
        **_enroll_payload, "student_id": "9999999",
    })
    assert resp.status_code == 404


def test_list_course_students():
    _setup_fixtures()
    client.post("/api/enrollments", json=_enroll_payload)
    client.post("/api/enrollments", json={
        **_enroll_payload, "student_id": "2025002",
    })

    resp = client.get("/api/enrollments/courses/AI001")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_drop_nonexistent():
    # Fresh student + course with unique IDs to avoid cross-test pollution
    client.post("/api/students", json={
        "student_id": "7000001", "name": "测试", "gender": "男",
        "birth_date": "2005-01-01", "department": "文学院", "grade": 2025,
    })
    client.post("/api/courses", json={
        "course_code": "ZZ999", "name": "测试课程", "credit": 1,
        "teacher": "测试老师", "schedule": "周五9-10节", "capacity": 1,
    })
    resp = client.delete("/api/enrollments", params={
        "student_id": "7000001", "course_code": "ZZ999",
        "teacher": "测试老师", "schedule": "周五9-10节",
    })
    assert resp.status_code == 404
