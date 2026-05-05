"""Test cases for configuration endpoints."""
import pytest
from datetime import date


class TestReasons:
    """Test score reasons configuration."""

    def test_get_reasons(self, client, admin_token):
        """Test getting reasons list."""
        response = client.get(
            "/api/config/reasons",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "reasons" in data
        assert isinstance(data["reasons"], list)

    def test_update_reasons(self, client, admin_token):
        """Test updating reasons list."""
        new_reasons = ["考试", "作业", "课堂表现", "课外活动"]
        response = client.put(
            "/api/config/reasons",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"reasons": new_reasons}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["reasons"] == new_reasons

        # Verify it was saved
        response = client.get(
            "/api/config/reasons",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.json()["reasons"] == new_reasons

    def test_update_reasons_teacher_forbidden(self, client, teacher_token):
        """Test that teacher cannot update reasons."""
        response = client.put(
            "/api/config/reasons",
            headers={"Authorization": f"Bearer {teacher_token}"},
            json={"reasons": ["test"]}
        )
        assert response.status_code == 403


class TestCodes:
    """Test settlement and init codes configuration."""

    def test_get_codes(self, client, admin_token):
        """Test getting codes."""
        response = client.get(
            "/api/config/codes",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "settlement_code" in data
        assert "init_code" in data

    def test_update_codes(self, client, admin_token):
        """Test updating codes."""
        response = client.put(
            "/api/config/codes",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "settlement_code": "NEW_SETTLE",
                "init_code": "NEW_INIT"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["settlement_code"] == "NEW_SETTLE"
        assert data["init_code"] == "NEW_INIT"

    def test_get_codes_teacher_forbidden(self, client, teacher_token):
        """Test that teacher cannot get codes."""
        response = client.get(
            "/api/config/codes",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        assert response.status_code == 403


class TestTerms:
    """Test term configuration."""

    def test_get_terms_empty(self, client, admin_token):
        """Test getting terms when none exist."""
        response = client.get(
            "/api/config/terms",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert response.json() == []

    def test_create_term(self, client, admin_token):
        """Test creating a term."""
        response = client.post(
            "/api/config/terms",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "2025-2026学年下学期",
                "year": "2025-2026",
                "start_date": "2026-02-01",
                "end_date": "2026-07-15"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "2025-2026学年下学期"
        assert data["year"] == "2025-2026"

    def test_update_term(self, client, admin_token, term):
        """Test updating a term."""
        response = client.put(
            f"/api/config/terms/{term.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "start_date": "2025-09-01",
                "end_date": "2026-01-20"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["end_date"] == "2026-01-20"

    def test_delete_term(self, client, admin_token, term):
        """Test deleting a term."""
        response = client.delete(
            f"/api/config/terms/{term.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 204

    def test_create_term_teacher_forbidden(self, client, teacher_token):
        """Test that teacher cannot create terms."""
        response = client.post(
            "/api/config/terms",
            headers={"Authorization": f"Bearer {teacher_token}"},
            json={
                "name": "test",
                "year": "test",
                "start_date": "2025-01-01",
                "end_date": "2025-12-31"
            }
        )
        assert response.status_code == 403
