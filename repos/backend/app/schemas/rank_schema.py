from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class RankBase(BaseModel):
    """Base rank schema with common fields."""
    name: str
    min_score: int
    max_score: Optional[int] = None
    image_url: str
    display_order: int = 0


class RankCreate(RankBase):
    """Schema for creating a rank."""
    pass


class RankUpdate(BaseModel):
    """Schema for updating a rank."""
    name: Optional[str] = None
    min_score: Optional[int] = None
    max_score: Optional[int] = None
    image_url: Optional[str] = None
    display_order: Optional[int] = None


class RankResponse(RankBase):
    """Schema for rank response."""
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True