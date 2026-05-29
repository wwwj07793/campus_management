"""FastAPI tests with isolated SQLite in-memory databases."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import core.models.mysqlDB  # noqa: F401
from api.app import create_app
from api.deps import get_services, get_session
from core.models.base import Base
from core.services.service_factory import build_database_backend
from tests.auth_helpers import auth_headers


@pytest.fixture
def client():
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
    with TestClient(app) as test_client:
        test_client.headers.update(auth_headers("teacher"))
        yield test_client


def _create_student(client, student_id="2025001", name="张三"):
    resp = client.post("/api/students", json={
        "student_id": student_id,
        "name": name,
        "gender": "男",
        "birth_date": "2005-03-15",
        "department": "电子信息工程学院",
        "grade": 2025,
    })
    assert resp.status_code == 201, resp.text
    return resp.json()


def _create_course(
    client,
    course_code="AI001",
    name="人工智能导论",
    teacher="李老师",
    schedule="周一1-2节",
):
    resp = client.post("/api/courses", json={
        "course_code": course_code,
        "name": name,
        "credit": 3,
        "teacher": teacher,
        "schedule": schedule,
        "capacity": 30,
    })
    assert resp.status_code == 201, resp.text
    return resp.json()


def _enroll(
    client,
    student_id="2025001",
    course_code="AI001",
    teacher="李老师",
    schedule="周一1-2节",
):
    resp = client.post("/api/enrollments", json={
        "student_id": student_id,
        "course_code": course_code,
        "teacher": teacher,
        "schedule": schedule,
    })
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_create_and_get_student(client):
    data = _create_student(client)
    assert data["student_id"] == "2025001"
    assert data["gpa"] == 0.0

    resp = client.get("/api/students/2025001")
    assert resp.status_code == 200
    assert resp.json()["name"] == "张三"


def test_create_duplicate_student_returns_409(client):
    _create_student(client, student_id="2025002", name="李四")

    resp = client.post("/api/students", json={
        "student_id": "2025002",
        "name": "王五",
        "gender": "男",
        "birth_date": "2004-01-10",
        "department": "文学院",
        "grade": 2024,
    })

    assert resp.status_code == 409
    assert "已存在" in resp.json()["detail"]


def test_list_search_update_and_delete_student(client):
    _create_student(client)

    resp = client.get("/api/students?department=电子信息工程学院")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = client.put("/api/students/2025001", json={"name": "张三丰"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "张三丰"

    resp = client.delete("/api/students/2025001")
    assert resp.status_code == 204

    resp = client.get("/api/students/2025001")
    assert resp.status_code == 404


def test_update_nonexistent_student_returns_404(client):
    resp = client.put("/api/students/9999999", json={"name": "不存在"})

    assert resp.status_code == 404


def test_student_validation_rejects_bad_input(client):
    resp = client.post("/api/students", json={
        "student_id": "123",
        "name": "",
        "gender": "X",
        "birth_date": "2005-03-15",
        "department": "EIE",
        "grade": 2025,
    })

    assert resp.status_code == 422


def test_course_create_and_list(client):
    _create_course(client)

    resp = client.get("/api/courses?code=AI001")

    assert resp.status_code == 200
    assert resp.json()[0]["course_code"] == "AI001"


def test_duplicate_course_returns_409(client):
    _create_course(client)

    resp = client.post("/api/courses", json={
        "course_code": "AI001",
        "name": "人工智能导论",
        "credit": 3,
        "teacher": "李老师",
        "schedule": "周一1-2节",
        "capacity": 30,
    })

    assert resp.status_code == 409


def test_enrollment_create_list_and_delete_with_query_params(client):
    _create_student(client)
    _create_course(client)
    _enroll(client)

    resp = client.get("/api/enrollments/students/2025001")
    assert resp.status_code == 200
    assert resp.json()[0]["course_code"] == "AI001"

    resp = client.delete(
        "/api/enrollments",
        params={
            "student_id": "2025001",
            "course_code": "AI001",
            "teacher": "李老师",
            "schedule": "周一1-2节",
        },
    )
    assert resp.status_code == 204

    resp = client.get("/api/enrollments/students/2025001")
    assert resp.status_code == 200
    assert resp.json() == []


def test_enrollment_time_conflict_returns_400(client):
    _create_student(client)
    _create_course(client, course_code="AI001", teacher="李老师", schedule="周一1-2节")
    _create_course(client, course_code="PY001", name="Python程序设计", teacher="王老师", schedule="周一1-2节")
    _enroll(client, course_code="AI001", teacher="李老师", schedule="周一1-2节")

    resp = client.post("/api/enrollments", json={
        "student_id": "2025001",
        "course_code": "PY001",
        "teacher": "王老师",
        "schedule": "周一1-2节",
    })

    assert resp.status_code == 400
    assert "时间冲突" in resp.json()["detail"]


def test_grade_recording_updates_gpa_and_analytics(client):
    _create_student(client)
    _create_course(client)
    _enroll(client)

    resp = client.post("/api/grades", json={
        "student_id": "2025001",
        "course_code": "AI001",
        "teacher": "李老师",
        "schedule": "周一1-2节",
        "score": 92,
    })
    assert resp.status_code == 201
    assert resp.json()["score"] == 92

    resp = client.get("/api/students/2025001")
    assert resp.status_code == 200
    assert round(resp.json()["gpa"], 2) == 3.7

    resp = client.get("/api/analytics/gpa-distribution")
    assert resp.status_code == 200
    assert resp.json()["count"] == 1


def test_grade_without_enrollment_returns_400(client):
    _create_student(client)
    _create_course(client)

    resp = client.post("/api/grades", json={
        "student_id": "2025001",
        "course_code": "AI001",
        "teacher": "李老师",
        "schedule": "周一1-2节",
        "score": 92,
    })

    assert resp.status_code == 400
    assert "未选" in resp.json()["detail"]


def test_analytics_overview_and_teacher_statistics(client):
    _create_student(client)
    _create_course(client)
    _enroll(client)

    resp = client.get("/api/analytics/overview")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1

    resp = client.get("/api/analytics/teacher-statistics")
    assert resp.status_code == 200
    assert resp.json()[0]["teacher"] == "李老师"
