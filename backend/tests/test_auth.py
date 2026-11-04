"""
Unit & Security Tests for Authentication, JWT, and RBAC.
"""
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "AI Fake Identity" in data["service"]


def test_login_success():
    # Login with pre-seeded officer
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "officer@docai.gov", "password": "Officer@123456"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "officer@docai.gov"
    assert data["user"]["role"] == "OFFICER"


def test_login_invalid_password():
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "officer@docai.gov", "password": "WrongPassword!"}
    )
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "HTTP_401"


def test_protected_route_unauthorized():
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_protected_route_with_valid_token():
    # 1. Login
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "supervisor@docai.gov", "password": "Supervisor@123456"}
    )
    token = login_res.json()["access_token"]

    # 2. Query /me
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "supervisor@docai.gov"
    assert data["role"] == "SUPERVISOR"
