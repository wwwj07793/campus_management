from fastapi.testclient import TestClient

from main import create_app


def test_frontend_index_is_served():
    client = TestClient(create_app())

    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "校园数据管理系统" in response.text


def test_frontend_static_assets_are_served():
    client = TestClient(create_app())

    app_js = client.get("/app.js")
    styles = client.get("/styles.css")

    assert app_js.status_code == 200
    assert "javascript" in app_js.headers["content-type"]
    assert "const api =" in app_js.text
    assert "/api/auth/login" in app_js.text
    assert "writePermissions" in app_js.text
    assert "updateStudent" in app_js.text
    assert "edit-student" in app_js.text
    assert "applyFieldErrors" in app_js.text
    assert "sort-table" in app_js.text
    assert "renderPagination" in app_js.text
    assert styles.status_code == 200
    assert "text/css" in styles.headers["content-type"]
    assert ".workspace" in styles.text
    assert ".field-error" in styles.text
    assert ".pagination" in styles.text


def test_frontend_spa_route_falls_back_to_index():
    client = TestClient(create_app())

    response = client.get("/students")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert '<script src="./app.js"></script>' in response.text
    assert "student123" in response.text


def test_health_endpoint_is_available_without_login():
    client = TestClient(create_app())

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
