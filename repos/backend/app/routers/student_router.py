from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.models.models import Student, StudentClass, ClassModel
from app.schemas.student_schema import (
    StudentCreate,
    StudentUpdate,
    StudentResponse,
    StudentImportResponse,
)
from app.utils.excel import read_student_import

router = APIRouter(prefix="/api/students", tags=["students"])

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


@router.get("", response_model=list[StudentResponse])
def list_students(
    class_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get students by class_id, including their current scores.
    If class_id is not provided, returns all students.
    """
    query = db.query(Student)

    if class_id is not None:
        # Filter by class and get current_score from StudentClass
        query = (
            db.query(Student, StudentClass.current_score)
            .join(StudentClass, Student.id == StudentClass.student_id)
            .filter(StudentClass.class_id == class_id)
        )
        results = query.all()
        return [
            StudentResponse(
                id=student.id,
                name=student.name,
                student_no=student.student_no,
                current_score=current_score,
            )
            for student, current_score in results
        ]
    else:
        # Return all students without scores
        students = query.all()
        return [
            StudentResponse(
                id=s.id,
                name=s.name,
                student_no=s.student_no,
                current_score=0,
            )
            for s in students
        ]


@router.post("", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
def create_student(
    student_data: StudentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a new student and associate with a class."""
    # Check if class exists
    class_model = db.query(ClassModel).filter(ClassModel.id == student_data.class_id).first()
    if not class_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found",
        )

    # Check if student with same student_no already exists
    existing_student = (
        db.query(Student)
        .filter(Student.student_no == student_data.student_no)
        .first()
    )
    if existing_student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student with this student number already exists",
        )

    # Create student
    student = Student(
        name=student_data.name,
        student_no=student_data.student_no,
    )
    db.add(student)
    db.flush()  # Get the student ID

    # Create student-class association
    student_class = StudentClass(
        student_id=student.id,
        class_id=student_data.class_id,
        is_active=False,
        current_score=0,
    )
    db.add(student_class)
    db.commit()
    db.refresh(student)

    return StudentResponse(
        id=student.id,
        name=student.name,
        student_no=student.student_no,
        current_score=0,
    )


@router.post("/import", response_model=StudentImportResponse)
async def import_students(
    file: UploadFile = File(...),
    class_id: int = Form(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Import students from Excel file.
    Only allowed for inactive (not activated) classes.
    """
    # Check if class exists and is not active
    class_model = db.query(ClassModel).filter(ClassModel.id == class_id).first()
    if not class_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found",
        )

    if class_model.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot import students to an activated class",
        )

    # Read Excel file
    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件大小超过5MB限制"
        )
    try:
        students_data = read_student_import(file_content)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    if not students_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No student data found in Excel file",
        )

    imported_count = 0
    for name, student_no in students_data:
        # Check if student with same student_no exists
        existing_student = (
            db.query(Student)
            .filter(Student.student_no == student_no)
            .first()
        )

        if existing_student:
            # Associate existing student with class
            existing_association = (
                db.query(StudentClass)
                .filter(
                    StudentClass.student_id == existing_student.id,
                    StudentClass.class_id == class_id,
                )
                .first()
            )
            if not existing_association:
                student_class = StudentClass(
                    student_id=existing_student.id,
                    class_id=class_id,
                    is_active=False,
                    current_score=0,
                )
                db.add(student_class)
                imported_count += 1
        else:
            # Create new student
            student = Student(
                name=name,
                student_no=student_no,
            )
            db.add(student)
            db.flush()

            # Create student-class association
            student_class = StudentClass(
                student_id=student.id,
                class_id=class_id,
                is_active=False,
                current_score=0,
            )
            db.add(student_class)
            imported_count += 1

    db.commit()

    return StudentImportResponse(
        imported=imported_count,
        message=f"Successfully imported {imported_count} students",
    )


@router.put("/{student_id}", response_model=StudentResponse)
def update_student(
    student_id: int,
    student_data: StudentUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Update an existing student's information."""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    if student_data.name is not None:
        student.name = student_data.name
    if student_data.student_no is not None:
        # Check if new student_no conflicts with another student
        existing = (
            db.query(Student)
            .filter(Student.student_no == student_data.student_no, Student.id != student_id)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student number already exists",
            )
        student.student_no = student_data.student_no

    db.commit()
    db.refresh(student)

    # Get current_score from StudentClass
    student_class = (
        db.query(StudentClass)
        .filter(StudentClass.student_id == student_id)
        .first()
    )
    current_score = student_class.current_score if student_class else 0

    return StudentResponse(
        id=student.id,
        name=student.name,
        student_no=student.student_no,
        current_score=current_score,
    )


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Delete a student and their associated records."""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    # Delete student-class associations first
    db.query(StudentClass).filter(StudentClass.student_id == student_id).delete()

    # Delete score records
    from app.models.models import ScoreRecord
    db.query(ScoreRecord).filter(ScoreRecord.student_id == student_id).delete()

    # Delete student
    db.delete(student)
    db.commit()
