import pytest
import sys
import os

# Set environment variables before importing app modules
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base
from app.dependencies import get_db
from app.models.models import Config, Teacher, Course, ClassModel, Student, StudentClass, Term, TermSetting, ScoreRecord, TeacherClass, ClassCourse
from app.utils.security import hash_password
import bcrypt


# Test database URL (in-memory SQLite)
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Create admin config
    admin_config = Config(
        key="admin_username",
        value="admin"
    )
    pw_hash = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
    admin_pw = Config(key="admin_password_hash", value=pw_hash)
    jwt_secret = Config(key="jwt_secret_key", value="test-secret-key")
    settlement_code = Config(key="settlement_code", value="TEST123")
    init_code = Config(key="init_code", value="INIT456")
    reasons = Config(key="reasons", value='["考试","作业","荣誉","其他"]')

    db.add_all([admin_config, admin_pw, jwt_secret, settlement_code, init_code, reasons])
    db.commit()

    yield db

    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """Create a test client."""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def admin_token(client):
    """Get admin authentication token."""
    response = client.post("/api/auth/login", json={
        "username": "admin",
        "password": "admin123",
        "role": "admin"
    })
    return response.json()["token"]


@pytest.fixture(scope="function")
def teacher(db):
    """Create a test teacher."""
    teacher = Teacher(
        name="测试教师",
        password=hash_password("teacher123"),
        created_at=None
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return teacher


@pytest.fixture(scope="function")
def teacher_token(client, teacher):
    """Get teacher authentication token."""
    response = client.post("/api/auth/login", json={
        "username": "测试教师",
        "password": "teacher123",
        "role": "teacher"
    })
    return response.json()["token"]


@pytest.fixture(scope="function")
def course(db):
    """Create a test course."""
    course = Course(name="数学")
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


@pytest.fixture(scope="function")
def class_model(db, course):
    """Create a test class with course association."""
    class_model = ClassModel(name="初三(1)班", code="CS001", is_active=False)
    db.add(class_model)
    db.flush()

    # Associate with course
    cc = ClassCourse(class_id=class_model.id, course_id=course.id)
    db.add(cc)
    db.commit()
    db.refresh(class_model)
    return class_model


@pytest.fixture(scope="function")
def student(db, class_model):
    """Create a test student."""
    student = Student(name="张三", student_no="S001")
    db.add(student)
    db.flush()

    sc = StudentClass(
        student_id=student.id,
        class_id=class_model.id,
        is_active=False,
        current_score=0
    )
    db.add(sc)
    db.commit()
    db.refresh(student)
    return student


@pytest.fixture(scope="function")
def term(db):
    """Create a test term."""
    from datetime import date
    term = Term(name="2025-2026学年上学期", year="2025-2026")
    db.add(term)
    db.flush()

    term_setting = TermSetting(
        term_id=term.id,
        start_date=date(2025, 9, 1),
        end_date=date(2026, 1, 15)
    )
    db.add(term_setting)
    db.commit()
    db.refresh(term)
    return term
