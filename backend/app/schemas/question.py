"""Question bank schemas.

``QuestionResponse`` is the admin/author view and contains ``is_correct``.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.utils.enums import Difficulty, QuestionStatus, QuestionType


class OptionCreate(BaseModel):
    option_text: str = Field(..., min_length=1)
    option_order: int = Field(1, ge=1, le=20)
    is_correct: bool = False


class OptionUpdate(BaseModel):
    id: Optional[int] = None
    option_text: str = Field(..., min_length=1)
    option_order: int = Field(1, ge=1, le=20)
    is_correct: bool = False


class OptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    question_id: int
    option_text: str
    option_order: int
    is_correct: bool


class QuestionCreate(BaseModel):
    subject_id: int
    topic_id: Optional[int] = None
    question_type: QuestionType
    question_text: str = Field(..., min_length=2)
    explanation: Optional[str] = None
    difficulty: Difficulty = Difficulty.MEDIUM
    marks: float = Field(4.0, ge=0, le=1000)
    negative_marks: float = Field(0.0, ge=0, le=1000)
    status: QuestionStatus = QuestionStatus.DRAFT
    source: Optional[str] = Field(None, max_length=100)
    options: List[OptionCreate] = Field(default_factory=list)


class QuestionUpdate(BaseModel):
    topic_id: Optional[int] = None
    question_type: Optional[QuestionType] = None
    question_text: Optional[str] = Field(None, min_length=2)
    explanation: Optional[str] = None
    difficulty: Optional[Difficulty] = None
    marks: Optional[float] = Field(None, ge=0, le=1000)
    negative_marks: Optional[float] = Field(None, ge=0, le=1000)
    status: Optional[QuestionStatus] = None
    source: Optional[str] = Field(None, max_length=100)
    options: Optional[List[OptionUpdate]] = None


class QuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subject_id: int
    topic_id: Optional[int] = None
    question_type: str
    question_text: str
    explanation: Optional[str] = None
    difficulty: str
    marks: float
    negative_marks: float
    status: str
    source: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    options: List[OptionResponse] = Field(default_factory=list)


class QuestionImportItem(BaseModel):
    subject_id: int
    topic_id: Optional[int] = None
    question_type: QuestionType = QuestionType.SINGLE_CHOICE
    question_text: str
    explanation: Optional[str] = None
    difficulty: Difficulty = Difficulty.MEDIUM
    marks: float = Field(4.0, ge=0)
    negative_marks: float = Field(0.0, ge=0)
    options: List[OptionCreate] = Field(default_factory=list)


class QuestionImportRequest(BaseModel):
    questions: List[QuestionImportItem] = Field(..., min_length=1, max_length=500)


class QuestionImportResponse(BaseModel):
    imported: int = 0
    failed: int = 0
    errors: List[str] = Field(default_factory=list)
