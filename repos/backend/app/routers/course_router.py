from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.models.models import Course, ClassCourse, ClassModel
from app.schemas.course_schema import (
    CourseCreate,
    CourseUpdate,
    CourseResponse,
    ClassCourseRequest,
    ClassCourseResponse,
)
from app.dependencies import get_db, get_current_user

router = APIRouter(prefix="/api/courses", tags=["courses"])


@router.get("", response_model=List[CourseResponse])
def list_courses(db: Session = Depends(get_db)):
    """Get all courses."""
    courses = db.query(Course).all()
    return courses


@router.post("", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(course: CourseCreate, db: Session = Depends(get_db)):
    """Create a new course."""
    db_course = Course(name=course.name)
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course


@router.put("/{course_id}", response_model=CourseResponse)
def update_course(course_id: int, course: CourseUpdate, db: Session = Depends(get_db)):
    """Update an existing course."""
    db_course = db.query(Course).filter(Course.id == course_id).first()
    if not db_course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    db_course.name = course.name
    db.commit()
    db.refresh(db_course)
    return db_course


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(course_id: int, db: Session = Depends(get_db)):
    """Delete a course."""
    db_course = db.query(Course).filter(Course.id == course_id).first()
    if not db_course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    db.delete(db_course)
    db.commit()
    return None


# Class-course association endpoints
class_course_router = APIRouter(prefix="/api/class-courses", tags=["class-courses"])


@class_course_router.get("", response_model=List[ClassCourseResponse])
def get_class_courses(class_id: int, db: Session = Depends(get_db)):
    """Get all courses associated with a class."""
    class_model = db.query(ClassModel).filter(ClassModel.id == class_id).first()
    if not class_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )

    class_courses = db.query(ClassCourse).filter(ClassCourse.class_id == class_id).all()
    return [cc.course for cc in class_courses]


@class_course_router.put("", response_model=dict)
def update_class_courses(request: ClassCourseRequest, db: Session = Depends(get_db)):
    """Update courses associated with a class."""
    class_model = db.query(ClassModel).filter(ClassModel.id == request.class_id).first()
    if not class_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )

    # Remove existing associations
    db.query(ClassCourse).filter(ClassCourse.class_id == request.class_id).delete()

    # Add new associations
    for course_id in request.course_ids:
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with id {course_id} not found"
            )
        db.add(ClassCourse(class_id=request.class_id, course_id=course_id))

    db.commit()
    return {"message": "Class courses updated successfully"}
