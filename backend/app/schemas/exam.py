"""Exam schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.utils.enums import ExamStatus, ExamType


class ExamCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200, examples=["NEET 2026"])
    code: str = Field(..., min_length=2, max_length=50, pattern=r"^[A-Za-z0-9_\-]+$", examples=["NEET"])
    description: Optional[str] = None
    exam_type: ExamType = ExamType.CUSTOM
    duration_minutes: Optional[int] = Field(None, ge=1, le=1440)
    passing_percentage: Optional[float] = Field(None, ge=0, le=100)
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None


class ExamUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = None
    exam_type: Optional[ExamType] = None
    duration_minutes: Optional[int] = Field(None, ge=1, le=1440)
    passing_percentage: Optional[float] = Field(None, ge=0, le=100)
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    is_active: Optional[bool] = None


class ExamResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    description: Optional[str] = None
    exam_type: str
    status: str
    duration_minutes: Optional[int] = None
    passing_percentage: Optional[float] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
