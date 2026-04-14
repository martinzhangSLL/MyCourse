from pydantic import BaseModel, Field


class StudentCreate(BaseModel):
    """Schema for creating a new student."""
    name: str = Field(..., min_length=1, max_length=50)
    student_no: str = Field(..., min_length=1, max_length=20)
    class_id: int = Field(..., gt=0)


class StudentUpdate(BaseModel):
    """Schema for updating an existing student."""
    name: str | None = Field(None, min_length=1, max_length=50)
    student_no: str | None = Field(None, min_length=1, max_length=20)


class StudentResponse(BaseModel):
    """Schema for student response with current score."""
    id: int
    name: str
    student_no: str
    current_score: int

    class Config:
        from_attributes = True


class StudentImportResponse(BaseModel):
    """Schema for import response."""
    imported: int
    message: str
