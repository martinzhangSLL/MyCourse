from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.dependencies import get_db, get_current_user
from app.models.models import ScoreRecord, StudentClass, ClassCourse, Course, Teacher, TeacherClass, ClassModel, Student
from app.schemas.score_schema import ScoreCreate, ScoreResponse, ScoreDetailResponse
from app.schemas.class_schema import ClassBasic

router = APIRouter(prefix="/api/scores", tags=["scores"])


# Teacher endpoints for score management page
teacher_score_router = APIRouter(prefix="/api/teacher", tags=["teacher-scores"])


@teacher_score_router.get("/classes", response_model=List[ClassBasic])
def get_teacher_classes(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get all classes assigned to the current teacher.
    Used for the class dropdown in the scores page.
    """
    if current_user["role"] != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can access this endpoint"
        )

    teacher_id = current_user["id"]

    # Get all classes assigned to this teacher
    teacher_classes = (
        db.query(TeacherClass)
        .filter(TeacherClass.teacher_id == teacher_id)
        .all()
    )

    class_ids = [tc.class_id for tc in teacher_classes]
    if not class_ids:
        return []
    classes = db.query(ClassModel).filter(ClassModel.id.in_(class_ids)).all()

    return [
        ClassBasic(
            id=c.id,
            name=c.name,
        )
        for c in classes
    ]


@teacher_score_router.get("/class-courses", response_model=List)
def get_teacher_class_courses(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get all courses associated with a specific class.
    Only accessible if the teacher is assigned to that class.
    """
    if current_user["role"] != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can access this endpoint"
        )

    teacher_id = current_user["id"]

    # Verify teacher is assigned to this class
    teacher_class = (
        db.query(TeacherClass)
        .filter(TeacherClass.teacher_id == teacher_id, TeacherClass.class_id == class_id)
        .first()
    )
    if not teacher_class:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this class"
        )

    # Get courses for this class
    class_courses = (
        db.query(ClassCourse)
        .filter(ClassCourse.class_id == class_id)
        .all()
    )

    return [
        {"id": cc.course_id, "name": cc.course.name}
        for cc in class_courses
        if cc.course
    ]


@router.post("", response_model=ScoreResponse, status_code=status.HTTP_201_CREATED)
def create_score(
    score_data: ScoreCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Create a new score record (add or subtract points).
    Positive value = add points, Negative value = subtract points.
    Also updates the student's current_score in student_class table.
    """
    if current_user["role"] != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can create score records"
        )

    # Verify student exists
    student_class = (
        db.query(StudentClass)
        .filter(StudentClass.student_id == score_data.student_id)
        .first()
    )
    if not student_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )

    # Verify course exists
    course = db.query(Course).filter(Course.id == score_data.course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    # Get teacher_id from current user
    teacher_id = current_user["id"]

    # Create score record
    score_record = ScoreRecord(
        student_id=score_data.student_id,
        value=score_data.value,
        reason=score_data.reason,
        course_id=score_data.course_id,
        teacher_id=teacher_id,
        score_at=score_data.score_at,
    )
    db.add(score_record)

    # Update student's current_score
    student_class.current_score += score_data.value

    db.commit()
    db.refresh(score_record)

    return ScoreRecord(
        id=score_record.id,
        student_id=score_record.student_id,
        value=score_record.value,
        reason=score_record.reason,
        course_id=score_record.course_id,
        teacher_id=score_record.teacher_id,
        score_at=score_record.score_at,
        created_at=score_record.created_at,
    )


@router.get("/student/{student_id}", response_model=List[ScoreResponse])
def get_student_scores(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get all score records for a specific student."""
    scores = (
        db.query(ScoreRecord)
        .filter(ScoreRecord.student_id == student_id)
        .order_by(ScoreRecord.score_at.desc())
        .all()
    )
    return scores


@router.get("", response_model=List[ScoreDetailResponse])
def list_scores(
    class_id: Optional[int] = Query(None, description="Class ID filter"),
    student_id: Optional[int] = Query(None, description="Student ID filter"),
    course_id: Optional[int] = Query(None, description="Course ID filter"),
    start: Optional[datetime] = Query(None, description="Start datetime filter (ISO format)"),
    end: Optional[datetime] = Query(None, description="End datetime filter (ISO format)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get score records with optional filters.

    Supports filtering by:
    - class_id: Filter by specific class
    - student_id: Filter by specific student
    - course_id: Filter by specific course
    - start: Filter records from this datetime
    - end: Filter records until this datetime
    """
    query = db.query(ScoreRecord)

    # Filter by class_id (via StudentClass)
    if class_id is not None:
        query = query.join(
            StudentClass,
            ScoreRecord.student_id == StudentClass.student_id
        ).filter(StudentClass.class_id == class_id)

    # Filter by student_id
    if student_id is not None:
        query = query.filter(ScoreRecord.student_id == student_id)

    # Filter by course_id
    if course_id is not None:
        query = query.filter(ScoreRecord.course_id == course_id)

    # Filter by start datetime
    if start is not None:
        query = query.filter(ScoreRecord.score_at >= start)

    # Filter by end datetime
    if end is not None:
        query = query.filter(ScoreRecord.score_at <= end)

    # Order by score_at descending (most recent first)
    query = query.order_by(ScoreRecord.score_at.desc())

    score_records = query.all()

    # Build response with joined data
    result = []
    for record in score_records:
        student = db.query(Student).filter(Student.id == record.student_id).first()
        course = db.query(Course).filter(Course.id == record.course_id).first()
        teacher = db.query(Teacher).filter(Teacher.id == record.teacher_id).first()

        result.append(ScoreDetailResponse(
            id=record.id,
            student_id=record.student_id,
            student_name=student.name if student else "",
            student_no=student.student_no if student else "",
            value=record.value,
            reason=record.reason or "",
            course_name=course.name if course else "",
            teacher_name=teacher.name if teacher else "",
            score_at=record.score_at,
        ))

    return result
