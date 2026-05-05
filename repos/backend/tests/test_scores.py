"""Test cases for score management endpoints."""
import pytest
from datetime import datetime


class TestScoreOperations:
    """Test score add/deduct operations."""

    def test_add_score(self, client, teacher_token, student, course, class_model, db):
        """Test adding score to a student."""
        # Associate teacher with class
        from app.models.models import TeacherClass
        tc = TeacherClass(teacher_id=1, class_id=class_model.id)
        db.add(tc)
        db.commit()

        response = client.post(
            "/api/scores",
            headers={"Authorization": f"Bearer {teacher_token}"},
            json={
                "student_id": student.id,
                "class_id": class_model.id,
                "course_id": course.id,
                "value": 10,
                "reason": "考试",
                "score_at": "2026-04-14T10:00:00"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["value"] == 10
        assert data["reason"] == "考试"


class TestScoreDetails:
    """Test score details endpoint."""

    def test_get_score_details(self, client, teacher_token, student, course, class_model, db):
        """Test getting score details for a student."""
        # Associate teacher with class
        from app.models.models import TeacherClass
        tc = TeacherClass(teacher_id=1, class_id=class_model.id)
        db.add(tc)
        db.commit()

        # Create a score record
        response = client.post(
            "/api/scores",
            headers={"Authorization": f"Bearer {teacher_token}"},
            json={
                "student_id": student.id,
                "class_id": class_model.id,
                "course_id": course.id,
                "value": 10,
                "reason": "考试",
                "score_at": "2026-04-14T10:00:00"
            }
        )
        assert response.status_code == 201

        # Get score details
        response = client.get(
            f"/api/scores?student_id={student.id}",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1


class TestRankings:
    """Test ranking endpoints."""

    def test_get_rankings(self, client, teacher_token, student, course, class_model, db):
        """Test getting rankings for a class."""
        # Associate teacher with class
        from app.models.models import TeacherClass
        tc = TeacherClass(teacher_id=1, class_id=class_model.id)
        db.add(tc)
        db.commit()

        # Add some scores
        client.post(
            "/api/scores",
            headers={"Authorization": f"Bearer {teacher_token}"},
            json={
                "student_id": student.id,
                "class_id": class_model.id,
                "course_id": course.id,
                "value": 100,
                "reason": "考试",
                "score_at": "2026-04-14T10:00:00"
            }
        )

        # Get rankings
        response = client.get(
            f"/api/rankings?class_id={class_model.id}&period=total",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
