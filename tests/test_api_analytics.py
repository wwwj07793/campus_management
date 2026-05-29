"""FastAPI analytics endpoint tests."""
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
from api.deps import get_data_view, get_repos, get_services, get_session
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

    def fake_data_view(s=Depends(fake_session)):
        from api.deps import Repos
        from core.interpretation.readers import RepositoryCampusDataReader
        from core.interpretation.data_views import CampusDataView
        repos = Repos(s)
        reader = RepositoryCampusDataReader(repos.student, repos.course, repos.enrollment, repos.grade)
        return CampusDataView(reader=reader)

    app = create_app()
    app.dependency_overrides[get_session] = fake_session
    app.dependency_overrides[get_services] = fake_services
    app.dependency_overrides[get_repos] = fake_repos
    app.dependency_overrides[get_data_view] = fake_data_view
    test_client = TestClient(app)
    test_client.headers.update(auth_headers("teacher"))
    return test_client


client = _make_client()


def _setup():
    """Create students, courses, enrollments, and grades for analytics."""
    for sid, name, dept, grade in [
        ("2025001", "张三", "电子信息工程学院", 2025),
        ("2025002", "李四", "电子信息工程学院", 2025),
        ("2025003", "王五", "计算机科学与技术学院", 2024),
    ]:
        client.post("/api/students", json={
            "student_id": sid, "name": name, "gender": "男",
            "birth_date": "2005-03-15", "department": dept, "grade": grade,
        })
    client.post("/api/courses", json={
        "course_code": "AI001", "name": "AI导论", "credit": 3,
        "teacher": "李老师", "schedule": "周一1-2节", "capacity": 30,
    })
    client.post("/api/courses", json={
        "course_code": "ML201", "name": "机器学习", "credit": 3,
        "teacher": "李老师", "schedule": "周三5-6节", "capacity": 20,
    })

    for sid in ["2025001", "2025002"]:
        client.post("/api/enrollments", json={
            "student_id": sid, "course_code": "AI001",
            "teacher": "李老师", "schedule": "周一1-2节",
        })

    client.post("/api/enrollments", json={
        "student_id": "2025002", "course_code": "ML201",
        "teacher": "李老师", "schedule": "周三5-6节",
    })

    client.post("/api/grades", json={
        "student_id": "2025001", "course_code": "AI001",
        "teacher": "李老师", "schedule": "周一1-2节", "score": 92,
    })
    client.post("/api/grades", json={
        "student_id": "2025002", "course_code": "AI001",
        "teacher": "李老师", "schedule": "周一1-2节", "score": 45,
    })
    client.post("/api/grades", json={
        "student_id": "2025002", "course_code": "ML201",
        "teacher": "李老师", "schedule": "周三5-6节", "score": 76,
    })


def test_overview():
    _setup()
    resp = client.get("/api/analytics/overview")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert data["by_department"]["电子信息工程学院"] == 2


def test_warnings():
    _setup()
    resp = client.get("/api/analytics/warnings")
    assert resp.status_code == 200
    warnings = resp.json()
    assert len(warnings) >= 1
    # 2025002 has a 45 score → should be in warnings
    assert any(w["student_id"] == "2025002" for w in warnings)


def test_gpa_distribution():
    _setup()
    resp = client.get("/api/analytics/gpa-distribution?department=电子信息工程学院")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 2


def test_score_distribution():
    _setup()
    resp = client.get("/api/analytics/score-distribution?course_code=AI001")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 2
    assert data["max"] == 92
    assert data["min"] == 45


def test_teacher_statistics():
    _setup()
    resp = client.get("/api/analytics/teacher-statistics")
    assert resp.status_code == 200
    stats = resp.json()
    assert any(s["teacher"] == "李老师" for s in stats)

    # 李老师的 stats — should work properly even though the DV is repo-based
    valid_count = [s for s in stats if s["teacher"] == "李老师" and s["course_count"] > 0]
    assert len(valid_count) > 0
