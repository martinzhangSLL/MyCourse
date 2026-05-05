"""
Functional Test Script for MyCourse System
Tests all major functionalities via API calls
"""
import httpx
import json
from datetime import date, datetime

BASE_URL = "http://localhost:8001"
TEST_RESULTS = []


def log_test(name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    TEST_RESULTS.append({"name": name, "status": status, "detail": detail})
    print(f"[{status}] {name}" + (f": {detail}" if detail else ""))


def get_admin_token():
    """Get admin authentication token."""
    response = httpx.post(f"{BASE_URL}/api/auth/login", json={
        "username": "admin",
        "password": "admin123",
        "role": "admin"
    })
    if response.status_code == 200:
        return response.json()["token"]
    return None


def test_health():
    """Test API health."""
    try:
        response = httpx.get(f"{BASE_URL}/docs")
        log_test("API Health Check", response.status_code == 200)
    except Exception as e:
        log_test("API Health Check", False, str(e))


def test_admin_login():
    """Test admin login."""
    token = get_admin_token()
    log_test("Admin Login", token is not None)


def test_config_reasons(token):
    """Test reasons configuration."""
    # GET
    response = httpx.get(
        f"{BASE_URL}/api/config/reasons",
        headers={"Authorization": f"Bearer {token}"}
    )
    log_test("Get Reasons", response.status_code == 200)

    # PUT
    response = httpx.put(
        f"{BASE_URL}/api/config/reasons",
        headers={"Authorization": f"Bearer {token}"},
        json={"reasons": ["考试", "作业", "荣誉"]}
    )
    log_test("Update Reasons", response.status_code == 200)


def test_config_codes(token):
    """Test codes configuration."""
    response = httpx.get(
        f"{BASE_URL}/api/config/codes",
        headers={"Authorization": f"Bearer {token}"}
    )
    log_test("Get Codes", response.status_code == 200)


def test_terms_crud(token):
    """Test term CRUD."""
    # CREATE
    response = httpx.post(
        f"{BASE_URL}/api/config/terms",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "2025-2026学年上学期",
            "year": "2025-2026",
            "start_date": "2025-09-01",
            "end_date": "2026-01-15"
        }
    )
    term_id = response.json().get("id") if response.status_code == 201 else None
    log_test("Create Term", response.status_code == 201)

    # LIST
    response = httpx.get(
        f"{BASE_URL}/api/config/terms",
        headers={"Authorization": f"Bearer {token}"}
    )
    log_test("List Terms", response.status_code == 200 and len(response.json()) > 0)

    # DELETE
    if term_id:
        response = httpx.delete(
            f"{BASE_URL}/api/config/terms/{term_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        log_test("Delete Term", response.status_code == 204)


def test_courses_crud(token):
    """Test course CRUD."""
    # CREATE
    response = httpx.post(
        f"{BASE_URL}/api/courses",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "测试课程"}
    )
    course_id = response.json().get("id") if response.status_code == 201 else None
    log_test("Create Course", response.status_code == 201)

    # LIST
    response = httpx.get(
        f"{BASE_URL}/api/courses",
        headers={"Authorization": f"Bearer {token}"}
    )
    log_test("List Courses", response.status_code == 200)

    # DELETE
    if course_id:
        response = httpx.delete(
            f"{BASE_URL}/api/courses/{course_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        log_test("Delete Course", response.status_code == 204)

    return course_id


def test_classes_crud(token, course_id):
    """Test class CRUD with course association."""
    # CREATE with course
    response = httpx.post(
        f"{BASE_URL}/api/classes",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "测试班级",
            "code": f"TEST{int(datetime.now().timestamp())}",
            "teacher_ids": [],
            "course_ids": [course_id] if course_id else []
        }
    )
    class_id = response.json().get("id") if response.status_code == 201 else None
    log_test("Create Class with Course", response.status_code == 201)

    # LIST
    response = httpx.get(
        f"{BASE_URL}/api/classes",
        headers={"Authorization": f"Bearer {token}"}
    )
    log_test("List Classes", response.status_code == 200 and len(response.json()) > 0)

    # ACTIVATE
    if class_id:
        response = httpx.put(
            f"{BASE_URL}/api/classes/{class_id}/activate",
            headers={"Authorization": f"Bearer {token}"}
        )
        log_test("Activate Class", response.status_code == 200)

    # Return class_id BEFORE deletion so it can be used in student tests
    return class_id


def test_student_crud(token, class_id):
    """Test student CRUD."""
    # CREATE
    response = httpx.post(
        f"{BASE_URL}/api/students",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "测试学生",
            "student_no": f"TEST{int(datetime.now().timestamp())}",
            "class_id": class_id
        }
    )
    student_id = response.json().get("id") if response.status_code == 201 else None
    log_test("Create Student", response.status_code == 201)

    # LIST
    if class_id:
        response = httpx.get(
            f"{BASE_URL}/api/students?class_id={class_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        log_test("List Students", response.status_code == 200)

    # DELETE
    if student_id:
        response = httpx.delete(
            f"{BASE_URL}/api/students/{student_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        log_test("Delete Student", response.status_code == 204)


def test_student_template_download(token):
    """Test student import template download."""
    response = httpx.get(
        f"{BASE_URL}/api/students/template",
        headers={"Authorization": f"Bearer {token}"}
    )
    log_test("Download Student Template", response.status_code == 200)


def test_auth_required_endpoints(token):
    """Test that protected endpoints require auth."""
    # Try to access without token
    response = httpx.get(f"{BASE_URL}/api/classes")
    log_test("Classes Without Auth", response.status_code in [401, 403])

    # Access with token
    response = httpx.get(
        f"{BASE_URL}/api/classes",
        headers={"Authorization": f"Bearer {token}"}
    )
    log_test("Classes With Auth", response.status_code == 200)


def main():
    print("=" * 60)
    print("MyCourse System - Functional Test")
    print("=" * 60)

    # Test health
    test_health()

    # Get token
    token = get_admin_token()
    if not token:
        print("\nFailed to get admin token. Aborting tests.")
        return

    print("\n--- Testing Config Endpoints ---")
    test_config_reasons(token)
    test_config_codes(token)
    test_terms_crud(token)

    print("\n--- Testing Course Endpoints ---")
    course_id = test_courses_crud(token)

    print("\n--- Testing Class Endpoints ---")
    class_id = test_classes_crud(token, course_id)

    print("\n--- Testing Student Endpoints ---")
    test_student_template_download(token)
    test_student_crud(token, class_id)

    print("\n--- Testing Auth ---")
    test_auth_required_endpoints(token)

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for r in TEST_RESULTS if r["status"] == "PASS")
    failed = sum(1 for r in TEST_RESULTS if r["status"] == "FAIL")

    for result in TEST_RESULTS:
        status_icon = "[PASS]" if result["status"] == "PASS" else "[FAIL]"
        print(f"  {status_icon} {result['name']}")

    print(f"\nTotal: {len(TEST_RESULTS)} | Passed: {passed} | Failed: {failed}")


if __name__ == "__main__":
    main()
