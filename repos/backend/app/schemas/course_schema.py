from pydantic import BaseModel


class CourseBase(BaseModel):
    """Base course schema with common fields."""
    name: str


class CourseCreate(CourseBase):
    """Schema for creating a course."""
    pass


class CourseUpdate(CourseBase):
    """Schema for updating a course."""
    pass


class CourseResponse(CourseBase):
    """Schema for course response."""
    id: int

    class Config:
        from_attributes = True


class ClassCourseRequest(BaseModel):
    """Schema for updating class-course associations."""
    class_id: int
    course_ids: list[int]


class ClassCourseResponse(BaseModel):
    """Schema for class-course association response."""
    id: int
    name: str

    class Config:
        from_attributes = True
