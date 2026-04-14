from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class TeacherBasic(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class CourseBasic(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class ClassBasic(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class ClassCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    code: str = Field(..., min_length=1, max_length=20)
    teacher_ids: Optional[List[int]] = []
    course_ids: Optional[List[int]] = []


class ClassUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    code: Optional[str] = Field(None, min_length=1, max_length=20)
    teacher_ids: Optional[List[int]] = None
    course_ids: Optional[List[int]] = None


class ClassResponse(BaseModel):
    id: int
    name: str
    code: str
    is_active: bool
    teachers: List[TeacherBasic] = []
    courses: List[CourseBasic] = []
    created_at: datetime

    class Config:
        from_attributes = True
