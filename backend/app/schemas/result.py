"""Result schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    attempt_id: int
    student_id: int
    test_id: int
    score: float
    max_score: float
    percentage: float
    correct_count: int
    incorrect_count: int
    unanswered_count: int
    rank: Optional[int] = None
    percentile: Optional[float] = None
    pass_status: bool
    published_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    test_name: Optional[str] = None
    student_name: Optional[str] = None
    attempt_number: Optional[int] = None


class ReviewAnswer(BaseModel):
    question_id: int
    question_text: str
    question_type: str
    your_answer: Optional[str] = None
    correct_answer: Optional[str] = None
    is_correct: Optional[bool] = None
    marks_awarded: float = 0.0
    marks_possible: float = 0.0
    explanation: Optional[str] = None
    options: List[dict] = Field(default_factory=list)


class ResultReviewResponse(BaseModel):
    result: ResultResponse
    answers: List[ReviewAnswer] = Field(default_factory=list)
