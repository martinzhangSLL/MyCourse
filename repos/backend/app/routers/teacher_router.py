from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.models.models import Teacher
from app.schemas.teacher_schema import TeacherCreate, TeacherUpdate, TeacherResponse
from app.utils.security import hash_password
from app.dependencies import get_db

router = APIRouter(prefix="/api/teachers", tags=["teachers"])


@router.get("", response_model=list[TeacherResponse])
def list_teachers(db: Session = Depends(get_db)):
    """Get all teachers."""
    teachers = db.query(Teacher).all()
    return teachers


@router.post("", response_model=TeacherResponse, status_code=status.HTTP_201_CREATED)
def create_teacher(teacher_data: TeacherCreate, db: Session = Depends(get_db)):
    """Create a new teacher with hashed password."""
    hashed_password = hash_password(teacher_data.password)
    teacher = Teacher(
        name=teacher_data.name,
        password=hashed_password
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return teacher


@router.put("/{teacher_id}", response_model=TeacherResponse)
def update_teacher(teacher_id: int, teacher_data: TeacherUpdate, db: Session = Depends(get_db)):
    """Update a teacher (including password)."""
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )

    hashed_password = hash_password(teacher_data.password)
    teacher.name = teacher_data.name
    teacher.password = hashed_password

    db.commit()
    db.refresh(teacher)
    return teacher


@router.delete("/{teacher_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_teacher(teacher_id: int, db: Session = Depends(get_db)):
    """Delete a teacher."""
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )

    db.delete(teacher)
    db.commit()
    return None
