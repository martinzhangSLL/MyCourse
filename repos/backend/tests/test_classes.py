"""Test cases for class management endpoints."""
import pytest


class TestClassCRUD:
    """Test class CRUD operations."""

    def test_list_classes_empty(self, client, admin_token):
        """Test listing classes when none exist."""
        response = client.get(
            "/api/classes",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert response.json() == []

    def test_create_class(self, client, admin_token, course):
        """Test creating a new class."""
        response = client.post(
            "/api/classes",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "初三(2)班",
                "code": "CS002",
                "teacher_ids": [],
                "course_ids": [course.id]
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "初三(2)班"
        assert data["code"] == "CS002"
        assert data["is_active"] == False
        assert len(data["courses"]) == 1

    def test_create_class_duplicate_code(self, client, admin_token, class_model):
        """Test creating class with duplicate code."""
        response = client.post(
            "/api/classes",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "新班级",
                "code": class_model.code,  # Same code
                "teacher_ids": [],
                "course_ids": []
            }
        )
        assert response.status_code == 400

    def test_get_class(self, client, admin_token, class_model):
        """Test getting a single class."""
        response = client.get(
            f"/api/classes/{class_model.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == class_model.name

    def test_update_class(self, client, admin_token, class_model, course):
        """Test updating a class."""
        response = client.put(
            f"/api/classes/{class_model.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "初三(1)班 updated",
                "code": class_model.code,
                "course_ids": [course.id]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "初三(1)班 updated"

    def test_delete_class(self, client, admin_token, class_model):
        """Test deleting (deactivating) a class."""
        response = client.delete(
            f"/api/classes/{class_model.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 204

    def test_activate_class(self, client, admin_token, class_model, student):
        """Test activating a class."""
        response = client.put(
            f"/api/classes/{class_model.id}/activate",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] == True


class TestClassCourseAssociation:
    """Test class-course many-to-many relationship."""

    def test_create_class_with_multiple_courses(self, client, admin_token, course, db):
        """Test creating a class with multiple courses."""
        # Create additional courses
        from app.models.models import Course
        course2 = Course(name="物理")
        course3 = Course(name="化学")
        db.add_all([course2, course3])
        db.commit()

        response = client.post(
            "/api/classes",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "初三(3)班",
                "code": "CS003",
                "teacher_ids": [],
                "course_ids": [course.id, course2.id, course3.id]
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert len(data["courses"]) == 3

    def test_update_class_courses(self, client, admin_token, class_model, course, db):
        """Test updating class-course associations."""
        from app.models.models import Course
        new_course = Course(name="物理")
        db.add(new_course)
        db.commit()

        response = client.put(
            f"/api/classes/{class_model.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": class_model.name,
                "code": class_model.code,
                "course_ids": [course.id, new_course.id]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["courses"]) == 2
