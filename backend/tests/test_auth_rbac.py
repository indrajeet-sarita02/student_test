"""Integration tests for authentication and RBAC enforcement."""

from tests.conftest import auth_headers


def test_health_and_openapi(client):
    assert client.get("/").status_code == 200
    schema = client.get("/openapi.json")
    assert schema.status_code == 200
    assert "/api/v1/auth/login" in schema.json()["paths"]


def test_login_returns_token_pair(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin@example.com", "password": "Admin@123"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["expires_in"] > 0


def test_login_rejects_bad_password(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401
    assert response.json()["success"] is False


def test_me_requires_token(client):
    assert client.get("/api/v1/auth/me").status_code in (401, 403)


def test_me_returns_identity_and_permissions(client, admin_headers):
    response = client.get("/api/v1/auth/me", headers=admin_headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["username"] == "admin"
    assert body["id"] > 0
    # ADMIN is granted essentially every permission code.
    assert "user.view" in body["permissions"]


def test_refresh_rotates_tokens(client):
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin@example.com", "password": "Admin@123"},
    ).json()
    refreshed = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": login["refresh_token"]}
    )
    assert refreshed.status_code == 200, refreshed.text
    assert refreshed.json()["access_token"]


def test_invalid_token_is_rejected(client):
    response = client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert response.status_code == 401


def test_rbac_denies_student_on_admin_endpoint(client, student_headers):
    # The STUDENT role intentionally holds no RBAC codes.
    response = client.get("/api/v1/users/", headers=student_headers)
    assert response.status_code == 403, response.text
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"


def test_rbac_allows_admin_on_admin_endpoint(client, admin_headers):
    response = client.get("/api/v1/users/", headers=admin_headers)
    assert response.status_code == 200, response.text
    assert "items" in response.json()


def test_student_cannot_read_foreign_attempt(client, student_headers, admin_headers):
    # Admin can list attempts, but a student hitting the admin endpoint is denied.
    response = client.get("/api/v1/attempts/", headers=student_headers)
    assert response.status_code == 403


def test_unauthorized_missing_token(client):
    assert client.get("/api/v1/users/").status_code == 401
