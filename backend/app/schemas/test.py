"""Test assembly schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.utils.enums import TestStatus


class TestCreate(BaseModel):
    exam_id: int
    name: str = Field(..., min_length=2, max_length=200)
    code: str = Field(..., min_length=2, max_length=50, pattern=r"^[A-Za-z0-9_\-]+$")
    description: Optional[str] = None
    instructions: Optional[str] = None
    duration_minutes: int = Field(180, ge=1, le=1440)
    total_marks: float = Field(0.0, ge=0)
    passing_marks: Optional[float] = Field(None, ge=0)
    negative_marking_enabled: bool = True
    negative_marks: float = Field(1.0, ge=0)
    randomize_questions: bool = False
    randomize_options: bool = False
    max_attempts: int = Field(1, ge=1, le=100)
    scheduled_start_at: Optional[datetime] = None
    scheduled_end_at: Optional[datetime] = None


class TestUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = None
    instructions: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, ge=1, le=1440)
    total_marks: Optional[float] = Field(None, ge=0)
    passing_marks: Optional[float] = Field(None, ge=0)
    negative_marking_enabled: Optional[bool] = None
    negative_marks: Optional[float] = Field(None, ge=0)
    randomize_questions: Optional[bool] = None
    randomize_options: Optional[bool] = None
    max_attempts: Optional[int] = Field(None, ge=1, le=100)
    scheduled_start_at: Optional[datetime] = None
    scheduled_end_at: Optional[datetime] = None


class TestQuestionAdd(BaseModel):
    question_id: int
    question_order: Optional[int] = Field(None, ge=1, le=1000)
    marks_override: Optional[float] = Field(None, ge=0)
    negative_marks_override: Optional[float] = Field(None, ge=0)


class TestQuestionsBulkAdd(BaseModel):
    question_ids: List[int] = Field(..., min_length=1, max_length=500)
    start_order: int = Field(1, ge=1, le=1000)


class TestQuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    test_id: int
    question_id: int
    question_order: int
    marks_override: Optional[float] = None
    negative_marks_override: Optional[float] = None
    question_text: Optional[str] = None
    question_type: Optional[str] = None
    subject_id: Optional[int] = None
    difficulty: Optional[str] = None


class TestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    exam_id: int
    name: str
    code: str
    description: Optional[str] = None
    instructions: Optional[str] = None
    duration_minutes: int
    total_marks: float
    passing_marks: Optional[float] = None
    negative_marking_enabled: bool
    negative_marks: float
    randomize_questions: bool
    randomize_options: bool
    max_attempts: int
    status: str
    scheduled_start_at: Optional[datetime] = None
    scheduled_end_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    question_count: Optional[int] = None
    assigned_count: Optional[int] = None


class TestImportResponse(BaseModel):
    """Result of a successful ``POST /tests/import`` (XLSX upload)."""

    test_id: int
    test_code: str
    name: str
    status: str
    questions_created: int
    subjects_created: int
    topics_created: int
    total_marks: float


class TestBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    exam_id: int
    name: str
    code: str
    duration_minutes: int
    total_marks: float
    passing_marks: Optional[float] = None
    status: str
    scheduled_start_at: Optional[datetime] = None
    scheduled_end_at: Optional[datetime] = None
    instructions: Optional[str] = None
