"""Test cases for student management endpoints."""
import pytest
import io


class TestStudentCRUD:
    """Test student CRUD operations."""

    def test_list_students_empty(self, client, admin_token, class_model):
        """Test listing students when none exist."""
        response = client.get(
            f"/api/students?class_id={class_model.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert response.json() == []

    def test_create_student(self, client, admin_token, class_model):
        """Test creating a new student."""
        response = client.post(
            "/api/students",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "李四",
                "student_no": "S002",
                "class_id": class_model.id
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "李四"
        assert data["student_no"] == "S002"
        assert data["current_score"] == 0

    def test_create_student_duplicate_number(self, client, admin_token, class_model, student):
        """Test creating student with duplicate student number."""
        response = client.post(
            "/api/students",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "王五",
                "student_no": student.student_no,  # Same number
                "class_id": class_model.id
            }
        )
        assert response.status_code == 400

    def test_update_student(self, client, admin_token, student):
        """Test updating a student."""
        response = client.put(
            f"/api/students/{student.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "张三 updated",
                "student_no": student.student_no
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "张三 updated"

    def test_delete_student(self, client, admin_token, student):
        """Test deleting a student."""
        response = client.delete(
            f"/api/students/{student.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 204


class TestStudentImport:
    """Test student Excel import."""

    def test_import_students_template(self, client, admin_token):
        """Test downloading student import template."""
        response = client.get(
            "/api/students/template",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/vnd.openxmlformats")

    def test_import_students_success(self, client, admin_token, class_model):
        """Test importing students from Excel."""
        # Create Excel content
        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active
        ws.append(["学生姓名", "学生学号"])
        ws.append(["王五", "S003"])
        ws.append(["赵六", "S004"])

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        response = client.post(
            "/api/students/import",
            headers={"Authorization": f"Bearer {admin_token}"},
            data={"class_id": class_model.id},
            files={"file": ("students.xlsx", buffer, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["imported"] == 2


class TestStudentScore:
    """Test student score functionality."""

    def test_student_current_score(self, client, admin_token, class_model, student, db):
        """Test that student has current score."""
        # Update student score
        from app.models.models import StudentClass
        sc = db.query(StudentClass).filter(
            StudentClass.student_id == student.id,
            StudentClass.class_id == class_model.id
        ).first()
        sc.current_score = 100
        db.commit()

        response = client.get(
            f"/api/students?class_id={class_model.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["current_score"] == 100
