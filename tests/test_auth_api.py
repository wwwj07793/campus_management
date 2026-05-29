from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import core.models.mysqlDB  # noqa: F401
from api.deps import get_session
from core.models.base import Base
from main import create_app


def make_client() -> TestClient:
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

    app = create_app()
    app.dependency_overrides[get_session] = override_session
    return TestClient(app)


def test_login_returns_token_and_me_uses_it():
    client = make_client()

    response = client.post("/api/auth/login", json={
        "username": "teacher",
        "password": "teacher123",
        "role": "teacher",
    })

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["user"]["role"] == "teacher"

    me = client.get("/api/auth/me", headers={
        "Authorization": f"Bearer {data['access_token']}",
    })
    assert me.status_code == 200
    assert me.json()["username"] == "teacher"


def test_login_rejects_wrong_password_and_wrong_role():
    client = make_client()

    bad_password = client.post("/api/auth/login", json={
        "username": "teacher",
        "password": "bad",
        "role": "teacher",
    })
    wrong_role = client.post("/api/auth/login", json={
        "username": "teacher",
        "password": "teacher123",
        "role": "student",
    })

    assert bad_password.status_code == 401
    assert wrong_role.status_code == 403


def test_me_requires_bearer_token():
    client = make_client()

    response = client.get("/api/auth/me")

    assert response.status_code == 401
