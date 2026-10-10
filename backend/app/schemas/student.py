"""Student test-taking response schemas.

These payloads are deliberately answer-key free: ``StudentQuestionView`` (from
``app.schemas.question``) never exposes ``is_correct`` or the explanation.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.attempt import AttemptResponse
from app.schemas.question import StudentQuestionView
from app.schemas.test import TestBrief


class StudentTestItem(BaseModel):
    """One assigned test as shown on the student's dashboard."""

    test: TestBrief
    assignment_id: int
    assignment_status: str
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None
    max_attempts: Optional[int] = None
    attempts_used: int = 0
    attempts_remaining: int = 0
    can_attempt: bool = False
    last_attempt_id: Optional[int] = None
    last_attempt_status: Optional[str] = None
    best_percentage: Optional[float] = None
    unavailable_reason: Optional[str] = None


class StudentAttemptAnswer(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    question_id: int
    selected_option_id: Optional[int] = None
    selected_option_ids: Optional[List[int]] = None
    answer_text: Optional[str] = None
    numerical_answer: Optional[str] = None
    is_marked_for_review: bool = False
    answered_at: Optional[datetime] = None


class StudentAttemptResponse(BaseModel):
    """Active-attempt payload: questions plus the answers saved so far."""

    attempt: AttemptResponse
    test: TestBrief
    questions: List[StudentQuestionView] = Field(default_factory=list)
    answers: List[StudentAttemptAnswer] = Field(default_factory=list)
    remaining_seconds: Optional[int] = Field(
        None, description="Seconds left before the server-side timer expires."
    )


class StudentQuestionReview(BaseModel):
    """Post-submission review of a single question (answer key included)."""

    question_id: int
    question_text: str
    question_type: str
    options: List[dict] = Field(default_factory=list)
    selected_option_id: Optional[int] = None
    selected_option_ids: Optional[List[int]] = None
    numerical_answer: Optional[str] = None
    correct_option_ids: List[int] = Field(default_factory=list)
    correct_text: Optional[str] = None
    is_correct: Optional[bool] = None
    marks_awarded: float = 0.0
    marks_possible: float = 0.0
    explanation: Optional[str] = None
