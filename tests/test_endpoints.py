import json

import jwt
import pytest
from django.conf import settings
from django.test import Client


@pytest.fixture
def client():
    return Client()


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


@pytest.mark.django_db
class TestLoginEndpoint:
    def test_login_success(self, client, operator_user):
        response = client.post(
            "/v1/auth/login",
            data=json.dumps({"username": "operator", "password": "operator123"}),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "Bearer"

    def test_login_returns_valid_jwt(self, client, operator_user):
        response = client.post(
            "/v1/auth/login",
            data=json.dumps({"username": "operator", "password": "operator123"}),
            content_type="application/json",
        )

        data = response.json()
        payload = jwt.decode(
            data["access_token"],
            settings.JWT_SECRET_KEY,
            algorithms=["HS256"],
        )

        assert payload["username"] == "operator"
        assert payload["type"] == "access"
        assert "Operators" in payload["groups"]
        assert "permissions" in payload

    def test_login_includes_permissions(self, client, operator_user):
        response = client.post(
            "/v1/auth/login",
            data=json.dumps({"username": "operator", "password": "operator123"}),
            content_type="application/json",
        )

        data = response.json()
        payload = jwt.decode(
            data["access_token"],
            settings.JWT_SECRET_KEY,
            algorithms=["HS256"],
        )

        assert "devices.view" in payload["permissions"]
        assert "devices.add" in payload["permissions"]

    def test_login_viewer_has_limited_permissions(self, client, viewer_user):
        response = client.post(
            "/v1/auth/login",
            data=json.dumps({"username": "viewer", "password": "viewer123"}),
            content_type="application/json",
        )

        data = response.json()
        payload = jwt.decode(
            data["access_token"],
            settings.JWT_SECRET_KEY,
            algorithms=["HS256"],
        )

        assert "devices.view" in payload["permissions"]
        assert "devices.add" not in payload["permissions"]
        assert "devices.change" not in payload["permissions"]

    def test_login_superuser_has_all_permissions(self, client, superuser):
        response = client.post(
            "/v1/auth/login",
            data=json.dumps({"username": "admin", "password": "admin123"}),
            content_type="application/json",
        )

        data = response.json()
        payload = jwt.decode(
            data["access_token"],
            settings.JWT_SECRET_KEY,
            algorithms=["HS256"],
        )

        assert "devices.view" in payload["permissions"]
        assert "devices.add" in payload["permissions"]
        assert "devices.change" in payload["permissions"]

    def test_login_invalid_password(self, client, operator_user):
        response = client.post(
            "/v1/auth/login",
            data=json.dumps({"username": "operator", "password": "wrongpassword"}),
            content_type="application/json",
        )

        assert response.status_code == 401
        assert response.json()["error"] == "Invalid credentials"

    def test_login_invalid_username(self, client):
        response = client.post(
            "/v1/auth/login",
            data=json.dumps({"username": "nonexistent", "password": "password"}),
            content_type="application/json",
        )

        assert response.status_code == 401
        assert response.json()["error"] == "Invalid credentials"

    def test_login_missing_username(self, client):
        response = client.post(
            "/v1/auth/login",
            data=json.dumps({"password": "password"}),
            content_type="application/json",
        )

        assert response.status_code == 400
        assert "required" in response.json()["error"].lower()

    def test_login_missing_password(self, client):
        response = client.post(
            "/v1/auth/login",
            data=json.dumps({"username": "operator"}),
            content_type="application/json",
        )

        assert response.status_code == 400
        assert "required" in response.json()["error"].lower()

    def test_login_invalid_json(self, client):
        response = client.post(
            "/v1/auth/login",
            data="not json",
            content_type="application/json",
        )

        assert response.status_code == 400
        assert "Invalid JSON" in response.json()["error"]

    def test_login_inactive_user(self, client, inactive_user):
        response = client.post(
            "/v1/auth/login",
            data=json.dumps({"username": "inactive", "password": "inactive123"}),
            content_type="application/json",
        )

        assert response.status_code == 401


@pytest.mark.django_db
class TestRefreshEndpoint:
    def test_refresh_success(self, client, operator_user):
        # First login to get tokens
        login_response = client.post(
            "/v1/auth/login",
            data=json.dumps({"username": "operator", "password": "operator123"}),
            content_type="application/json",
        )
        refresh_token = login_response.json()["refresh_token"]

        # Then refresh
        response = client.post(
            "/v1/auth/refresh",
            data=json.dumps({"refresh_token": refresh_token}),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "Bearer"

    def test_refresh_returns_valid_jwt(self, client, operator_user):
        # First login
        login_response = client.post(
            "/v1/auth/login",
            data=json.dumps({"username": "operator", "password": "operator123"}),
            content_type="application/json",
        )
        refresh_token = login_response.json()["refresh_token"]

        # Refresh
        response = client.post(
            "/v1/auth/refresh",
            data=json.dumps({"refresh_token": refresh_token}),
            content_type="application/json",
        )

        data = response.json()
        payload = jwt.decode(
            data["access_token"],
            settings.JWT_SECRET_KEY,
            algorithms=["HS256"],
        )

        assert payload["username"] == "operator"
        assert payload["type"] == "access"
        assert "permissions" in payload

    def test_refresh_missing_token(self, client):
        response = client.post(
            "/v1/auth/refresh",
            data=json.dumps({}),
            content_type="application/json",
        )

        assert response.status_code == 400
        assert "required" in response.json()["error"].lower()

    def test_refresh_invalid_token(self, client):
        response = client.post(
            "/v1/auth/refresh",
            data=json.dumps({"refresh_token": "invalid.token.here"}),
            content_type="application/json",
        )

        assert response.status_code == 401

    def test_refresh_with_access_token_fails(self, client, operator_user):
        # Login to get access token
        login_response = client.post(
            "/v1/auth/login",
            data=json.dumps({"username": "operator", "password": "operator123"}),
            content_type="application/json",
        )
        access_token = login_response.json()["access_token"]

        # Try to use access token as refresh token
        response = client.post(
            "/v1/auth/refresh",
            data=json.dumps({"refresh_token": access_token}),
            content_type="application/json",
        )

        assert response.status_code == 401
        assert "Invalid token type" in response.json()["error"]

    def test_refresh_invalid_json(self, client):
        response = client.post(
            "/v1/auth/refresh",
            data="not json",
            content_type="application/json",
        )

        assert response.status_code == 400
        assert "Invalid JSON" in response.json()["error"]
