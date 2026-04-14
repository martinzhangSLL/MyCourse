from datetime import datetime
from pydantic import BaseModel, Field


class ScoreCreate(BaseModel):
    """Schema for creating a new score record."""
    student_id: int = Field(..., gt=0)
    value: int = Field(..., description="Score value, positive for add, negative for subtract")
    reason: str = Field(..., min_length=1, max_length=200)
    course_id: int = Field(..., gt=0)
    score_at: datetime = Field(..., description="Time when the score was given")


class ScoreResponse(BaseModel):
    """Schema for score record response."""
    id: int
    student_id: int
    value: int
    reason: str
    course_id: int
    teacher_id: int
    score_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class ScoreDetailResponse(BaseModel):
    """Schema for detailed score record response with joined data."""
    id: int
    student_id: int
    student_name: str
    student_no: str
    value: int
    reason: str
    course_name: str
    teacher_name: str
    score_at: datetime

    class Config:
        from_attributes = True
