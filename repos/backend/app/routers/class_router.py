from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from typing import List

from app.models.models import ClassModel, TeacherClass, ClassCourse, StudentClass, Teacher, Course
from app.schemas.class_schema import ClassCreate, ClassUpdate, ClassResponse, TeacherBasic, CourseBasic
from app.dependencies import get_db

router = APIRouter(prefix="/api/classes", tags=["classes"])


def build_class_response(class_model: ClassModel) -> ClassResponse:
    """Build ClassResponse from ClassModel with nested teachers and courses."""
    teachers = [
        TeacherBasic(id=tc.teacher_id, name=tc.teacher.name)
        for tc in class_model.teacher_classes
        if tc.teacher
    ]
    courses = [
        CourseBasic(id=cc.course_id, name=cc.course.name)
        for cc in class_model.class_courses
        if cc.course
    ]
    return ClassResponse(
        id=class_model.id,
        name=class_model.name,
        code=class_model.code,
        is_active=class_model.is_active,
        teachers=teachers,
        courses=courses,
        created_at=class_model.created_at,
    )


@router.get("", response_model=List[ClassResponse])
def list_classes(db: Session = Depends(get_db)):
    """Get all classes with associated teachers and courses."""
    classes = db.query(ClassModel).all()
    return [build_class_response(c) for c in classes]


@router.post("", response_model=ClassResponse, status_code=status.HTTP_201_CREATED)
def create_class(class_data: ClassCreate, db: Session = Depends(get_db)):
    """Create a new class with associated teachers and courses."""
    # Check if code already exists
    existing = db.query(ClassModel).filter(ClassModel.code == class_data.code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Class code already exists"
        )

    # Create class model
    class_model = ClassModel(
        name=class_data.name,
        code=class_data.code,
        is_active=False,
    )
    db.add(class_model)
    db.flush()  # Get the class id

    # Associate teachers
    if class_data.teacher_ids:
        for teacher_id in class_data.teacher_ids:
            teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
            if teacher:
                teacher_class = TeacherClass(teacher_id=teacher_id, class_id=class_model.id)
                db.add(teacher_class)

    # Associate courses
    if class_data.course_ids:
        for course_id in class_data.course_ids:
            course = db.query(Course).filter(Course.id == course_id).first()
            if course:
                class_course = ClassCourse(class_id=class_model.id, course_id=course_id)
                db.add(class_course)

    db.commit()
    db.refresh(class_model)
    return build_class_response(class_model)


@router.get("/{class_id}", response_model=ClassResponse)
def get_class(class_id: int, db: Session = Depends(get_db)):
    """Get a class by ID."""
    class_model = db.query(ClassModel).filter(ClassModel.id == class_id).first()
    if not class_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    return build_class_response(class_model)


@router.put("/{class_id}", response_model=ClassResponse)
def update_class(class_id: int, class_data: ClassUpdate, db: Session = Depends(get_db)):
    """Update a class."""
    class_model = db.query(ClassModel).filter(ClassModel.id == class_id).first()
    if not class_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )

    # Update basic fields
    if class_data.name is not None:
        class_model.name = class_data.name
    if class_data.code is not None:
        # Check if new code already exists for another class
        existing = db.query(ClassModel).filter(
            ClassModel.code == class_data.code,
            ClassModel.id != class_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Class code already exists"
            )
        class_model.code = class_data.code

    # Update teacher associations
    if class_data.teacher_ids is not None:
        # Remove existing associations
        db.query(TeacherClass).filter(TeacherClass.class_id == class_id).delete()

        # Add new associations
        for teacher_id in class_data.teacher_ids:
            teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
            if teacher:
                teacher_class = TeacherClass(teacher_id=teacher_id, class_id=class_id)
                db.add(teacher_class)

    # Update course associations
    if class_data.course_ids is not None:
        # Remove existing associations
        db.query(ClassCourse).filter(ClassCourse.class_id == class_id).delete()

        # Add new associations
        for course_id in class_data.course_ids:
            course = db.query(Course).filter(Course.id == course_id).first()
            if course:
                class_course = ClassCourse(class_id=class_id, course_id=course_id)
                db.add(class_course)

    db.commit()
    db.refresh(class_model)
    return build_class_response(class_model)


@router.delete("/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_class(class_id: int, db: Session = Depends(get_db)):
    """Delete a class (logical delete - just mark as inactive)."""
    class_model = db.query(ClassModel).filter(ClassModel.id == class_id).first()
    if not class_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )

    # Logical delete: set is_active to False
    class_model.is_active = False
    db.commit()

    return None


@router.put("/{class_id}/activate", response_model=ClassResponse)
def activate_class(class_id: int, db: Session = Depends(get_db)):
    """Activate a class and all its students."""
    class_model = db.query(ClassModel).filter(ClassModel.id == class_id).first()
    if not class_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )

    # Activate the class
    class_model.is_active = True

    # Activate all students in this class
    db.query(StudentClass).filter(StudentClass.class_id == class_id).update(
        {StudentClass.is_active: True},
        synchronize_session=False
    )

    db.commit()
    db.refresh(class_model)
    return build_class_response(class_model)
