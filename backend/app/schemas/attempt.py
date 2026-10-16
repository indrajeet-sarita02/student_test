"""Attempt schemas: admin views, student test-taking views and answers."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.question import StudentQuestionView
from app.schemas.test import TestBrief


class AttemptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    test_id: int
    student_id: int
    attempt_number: int
    started_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    status: str
    score: float = 0.0
    max_score: float = 0.0
    percentage: float = 0.0
    submission_type: Optional[str] = None
    created_at: Optional[datetime] = None
    test_name: Optional[str] = None
    student_name: Optional[str] = None


class AnswerItem(BaseModel):
    question_id: int
    selected_option_id: Optional[int] = None
    selected_option_ids: Optional[List[int]] = None
    answer_text: Optional[str] = Field(None, max_length=5000)
    numerical_answer: Optional[str] = Field(None, max_length=50)
    is_marked_for_review: bool = False


class SaveAnswersRequest(BaseModel):
    answers: List[AnswerItem] = Field(default_factory=list, max_length=1000)


class SavedAnswerResponse(BaseModel):
    question_id: int
    selected_option_id: Optional[int] = None
    selected_option_ids: Optional[List[int]] = None
    answer_text: Optional[str] = None
    numerical_answer: Optional[str] = None
    is_marked_for_review: bool = False
    answered_at: Optional[datetime] = None


class SaveAnswersResponse(BaseModel):
    attempt_id: int
    saved: int
    answered_count: int
    remaining_count: int
    expires_at: Optional[datetime] = None


class StartAttemptResponse(BaseModel):
    attempt: AttemptResponse
    test: TestBrief
    questions: List[StudentQuestionView] = Field(default_factory=list)


class SubmitAttemptResponse(BaseModel):
    attempt: AttemptResponse
    result_id: Optional[int] = None
    score: float = 0.0
    max_score: float = 0.0
    percentage: float = 0.0
    pass_status: bool = False
    status: str


class AttemptAnswerAdminResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    question_id: int
    question_text: Optional[str] = None
    selected_option_id: Optional[int] = None
    selected_option_ids: Optional[List[int]] = None
    selected_option_text: Optional[str] = None
    answer_text: Optional[str] = None
    numerical_answer: Optional[str] = None
    is_marked_for_review: bool
    answered_at: Optional[datetime] = None
    is_correct: Optional[bool] = None
    marks_awarded: Optional[float] = None


class AttemptDetailResponse(BaseModel):
    attempt: AttemptResponse
    answers: List[AttemptAnswerAdminResponse] = Field(default_factory=list)
    result: Optional[dict] = None
