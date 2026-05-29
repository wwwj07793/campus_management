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


def make_acceptance_client() -> TestClient:
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
    test_client = TestClient(app)
    test_client.headers.update(auth_headers("teacher"))
    return test_client


def test_frontend_backed_business_acceptance_flow():
    client = make_acceptance_client()

    index = client.get("/")
    assert index.status_code == 200
    assert "frontend-demo" not in index.text
    assert "app.js" in index.text

    student = {
        "student_id": "2025001",
        "name": "张三",
        "gender": "男",
        "birth_date": "2005-03-15",
        "department": "电子信息工程学院",
        "grade": 2025,
    }
    course = {
        "course_code": "AI001",
        "name": "人工智能导论",
        "credit": 3,
        "teacher": "李老师",
        "schedule": "周一1-2节",
        "capacity": 30,
    }
    conflict_course = {
        "course_code": "PY001",
        "name": "Python程序设计",
        "credit": 2,
        "teacher": "王老师",
        "schedule": "周一1-2节",
        "capacity": 30,
    }

    resp = client.post("/api/students", json=student)
    assert resp.status_code == 201, resp.text
    assert resp.json()["gpa"] == 0.0

    resp = client.put("/api/students/2025001", json={"department": "计算机学院"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["department"] == "计算机学院"

    resp = client.post("/api/courses", json=course)
    assert resp.status_code == 201, resp.text
    course_id = resp.json()["id"]

    resp = client.put(f"/api/courses/{course_id}", json={"capacity": 40})
    assert resp.status_code == 200, resp.text
    assert resp.json()["capacity"] == 40

    enrollment = {
        "student_id": "2025001",
        "course_code": "AI001",
        "teacher": "李老师",
        "schedule": "周一1-2节",
    }
    resp = client.post("/api/enrollments", json=enrollment)
    assert resp.status_code == 201, resp.text
    assert resp.json()["course_name"] == "人工智能导论"

    grade = {**enrollment, "score": 88}
    resp = client.post("/api/grades", json=grade)
    assert resp.status_code == 201, resp.text
    assert resp.json()["schedule"] == "周一1-2节"

    student_detail = client.get("/api/students/2025001")
    assert student_detail.status_code == 200
    assert round(student_detail.json()["gpa"], 2) == 3.30

    assert client.get("/api/enrollments/students/2025001").json()[0]["course_code"] == "AI001"
    assert client.get("/api/grades/students/2025001").json()[0]["score"] == 88.0

    overview = client.get("/api/analytics/overview")
    assert overview.status_code == 200
    assert overview.json()["total"] == 1

    gpa_stats = client.get("/api/analytics/gpa-distribution")
    assert gpa_stats.status_code == 200
    assert gpa_stats.json()["count"] == 1

    resp = client.post("/api/courses", json=conflict_course)
    assert resp.status_code == 201, resp.text
    resp = client.post("/api/enrollments", json={
        "student_id": "2025001",
        "course_code": "PY001",
        "teacher": "王老师",
        "schedule": "周一1-2节",
    })
    assert resp.status_code == 400
    assert "时间冲突" in resp.json()["detail"]

    resp = client.delete("/api/grades", params=enrollment)
    assert resp.status_code == 204

    resp = client.delete("/api/enrollments", params=enrollment)
    assert resp.status_code == 204

    resp = client.delete(f"/api/courses/{course_id}")
    assert resp.status_code == 204

    resp = client.delete("/api/students/2025001")
    assert resp.status_code == 204
