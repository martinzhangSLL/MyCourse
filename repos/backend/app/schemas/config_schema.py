from datetime import date
from typing import List

from pydantic import BaseModel, Field


# ============ Term Schemas ============

class TermBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    year: str = Field(..., min_length=1, max_length=20)
    start_date: date
    end_date: date


class TermCreate(TermBase):
    pass


class TermUpdate(BaseModel):
    start_date: date
    end_date: date


class TermResponse(BaseModel):
    id: int
    name: str
    year: str
    start_date: date
    end_date: date

    class Config:
        from_attributes = True


# ============ Config Schemas ============

class ReasonsResponse(BaseModel):
    reasons: List[str]


class CodesResponse(BaseModel):
    settlement_code: str
    init_code: str


class CodesUpdate(BaseModel):
    settlement_code: str = Field(..., min_length=1)
    init_code: str = Field(..., min_length=1)
