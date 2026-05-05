"""Test cases for course management endpoints."""
import pytest


class TestCourseCRUD:
    """Test course CRUD operations."""

    def test_list_courses_empty(self, client, admin_token):
        """Test listing courses when none exist."""
        response = client.get(
            "/api/courses",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200

    def test_create_course(self, client, admin_token):
        """Test creating a new course."""
        response = client.post(
            "/api/courses",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "物理"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "物理"

    def test_create_course_duplicate(self, client, admin_token, course):
        """Test creating course with duplicate name."""
        response = client.post(
            "/api/courses",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": course.name}
        )
        assert response.status_code == 201  # Allow duplicate names

    def test_update_course(self, client, admin_token, course):
        """Test updating a course."""
        response = client.put(
            f"/api/courses/{course.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "物理 updated"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "物理 updated"

    def test_delete_course(self, client, admin_token, course):
        """Test deleting a course."""
        response = client.delete(
            f"/api/courses/{course.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 204


class TestClassCourseAssociation:
    """Test class-course association endpoints."""

    def test_get_class_courses(self, client, admin_token, class_model):
        """Test getting courses associated with a class."""
        response = client.get(
            f"/api/class-courses?class_id={class_model.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_update_class_courses(self, client, admin_token, class_model, db):
        """Test updating courses associated with a class."""
        from app.models.models import Course
        new_course = Course(name="化学")
        db.add(new_course)
        db.commit()

        response = client.put(
            "/api/class-courses",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "class_id": class_model.id,
                "course_ids": [new_course.id]
            }
        )
        assert response.status_code == 200
