"""Test cases for authentication endpoints."""
import pytest


class TestAdminLogin:
    """Test admin login functionality."""

    def test_login_success(self, client):
        """Test successful admin login."""
        response = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin123",
            "role": "admin"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["user"]["role"] == "admin"
        assert data["user"]["name"] == "admin"

    def test_login_wrong_password(self, client):
        """Test login with wrong password."""
        response = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "wrongpassword",
            "role": "admin"
        })
        assert response.status_code == 401

    def test_login_wrong_username(self, client):
        """Test login with wrong username."""
        response = client.post("/api/auth/login", json={
            "username": "wronguser",
            "password": "admin123",
            "role": "admin"
        })
        assert response.status_code == 401

    def test_login_missing_role(self, client):
        """Test login without role."""
        response = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        assert response.status_code == 422


class TestTeacherLogin:
    """Test teacher login functionality."""

    def test_login_success(self, client, teacher):
        """Test successful teacher login."""
        response = client.post("/api/auth/login", json={
            "username": "测试教师",
            "password": "teacher123",
            "role": "teacher"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["user"]["role"] == "teacher"
        assert data["user"]["name"] == "测试教师"

    def test_login_wrong_password(self, client, teacher):
        """Test teacher login with wrong password."""
        response = client.post("/api/auth/login", json={
            "username": "测试教师",
            "password": "wrongpassword",
            "role": "teacher"
        })
        assert response.status_code == 401


class TestGetCurrentUser:
    """Test get current user endpoint."""

    def test_get_me_admin(self, client, admin_token):
        """Test getting current admin user."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "admin"
        assert data["name"] == "admin"

    def test_get_me_teacher(self, client, teacher_token):
        """Test getting current teacher user."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "teacher"

    def test_get_me_unauthorized(self, client):
        """Test getting user without token."""
        response = client.get("/api/auth/me")
        assert response.status_code == 403
