from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Teacher(Base):
    __tablename__ = "teacher"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    teacher_classes = relationship("TeacherClass", back_populates="teacher")
    score_records = relationship("ScoreRecord", back_populates="teacher")


class ClassModel(Base):
    __tablename__ = "class_table"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    teacher_classes = relationship("TeacherClass", back_populates="class_model")
    class_courses = relationship("ClassCourse", back_populates="class_model")
    student_classes = relationship("StudentClass", back_populates="class_model")


class TeacherClass(Base):
    __tablename__ = "teacher_class"

    teacher_id = Column(Integer, ForeignKey("teacher.id"), primary_key=True)
    class_id = Column(Integer, ForeignKey("class_table.id"), primary_key=True)

    # Relationships
    teacher = relationship("Teacher", back_populates="teacher_classes")
    class_model = relationship("ClassModel", back_populates="teacher_classes")


class Course(Base):
    __tablename__ = "course"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)

    # Relationships
    class_courses = relationship("ClassCourse", back_populates="course")
    score_records = relationship("ScoreRecord", back_populates="course")


class ClassCourse(Base):
    __tablename__ = "class_course"

    class_id = Column(Integer, ForeignKey("class_table.id"), primary_key=True)
    course_id = Column(Integer, ForeignKey("course.id"), primary_key=True)

    # Relationships
    class_model = relationship("ClassModel", back_populates="class_courses")
    course = relationship("Course", back_populates="class_courses")


class Student(Base):
    __tablename__ = "student"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    student_no = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    student_classes = relationship("StudentClass", back_populates="student")
    score_records = relationship("ScoreRecord", back_populates="student")


class StudentClass(Base):
    __tablename__ = "student_class"

    student_id = Column(Integer, ForeignKey("student.id"), primary_key=True)
    class_id = Column(Integer, ForeignKey("class_table.id"), primary_key=True)
    is_active = Column(Boolean, default=False)
    current_score = Column(Integer, default=0)

    # Relationships
    student = relationship("Student", back_populates="student_classes")
    class_model = relationship("ClassModel", back_populates="student_classes")


class ScoreRecord(Base):
    __tablename__ = "score_record"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("student.id"), nullable=False)
    value = Column(Integer, nullable=False)
    reason = Column(String(200))
    course_id = Column(Integer, ForeignKey("course.id"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("teacher.id"), nullable=False)
    score_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    student = relationship("Student", back_populates="score_records")
    course = relationship("Course", back_populates="score_records")
    teacher = relationship("Teacher", back_populates="score_records")


class Term(Base):
    __tablename__ = "term"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    year = Column(String(20), nullable=False)

    # Relationships
    term_settings = relationship("TermSetting", back_populates="term")


class TermSetting(Base):
    __tablename__ = "term_setting"

    id = Column(Integer, primary_key=True)
    term_id = Column(Integer, ForeignKey("term.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    # Relationships
    term = relationship("Term", back_populates="term_settings")


class Config(Base):
    __tablename__ = "config"

    key = Column(String(50), primary_key=True)
    value = Column(String(255), nullable=False)
