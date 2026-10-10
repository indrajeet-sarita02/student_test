"""Report / dashboard schemas."""

from typing import List, Optional

from pydantic import BaseModel, Field


class DashboardReport(BaseModel):
    total_users: int = 0
    total_students: int = 0
    total_exams: int = 0
    total_tests: int = 0
    total_questions: int = 0
    published_tests: int = 0
    total_attempts: int = 0
    active_attempts: int = 0
    total_results: int = 0
    average_percentage: float = 0.0
    pass_rate: float = 0.0


class ExamReportRow(BaseModel):
    exam_id: int
    exam_name: str
    exam_code: str
    status: str
    subject_count: int = 0
    question_count: int = 0
    test_count: int = 0
    attempt_count: int = 0
    average_percentage: Optional[float] = None


class TestReportRow(BaseModel):
    test_id: int
    test_name: str
    test_code: str
    exam_id: int
    exam_name: Optional[str] = None
    status: str
    question_count: int = 0
    assigned_count: int = 0
    attempt_count: int = 0
    evaluated_count: int = 0
    average_percentage: Optional[float] = None
    highest_percentage: Optional[float] = None
    lowest_percentage: Optional[float] = None
    pass_rate: Optional[float] = None


class StudentReportRow(BaseModel):
    student_id: int
    student_name: str
    username: str
    tests_assigned: int = 0
    attempts_taken: int = 0
    tests_completed: int = 0
    average_percentage: Optional[float] = None
    best_percentage: Optional[float] = None
    average_score: Optional[float] = None
    rank: Optional[int] = None


class QuestionReportRow(BaseModel):
    question_id: int
    subject_id: int
    subject_name: Optional[str] = None
    question_type: str
    difficulty: str
    status: str
    times_used: int = 0
    times_answered: int = 0
    correct_count: int = 0
    incorrect_count: int = 0
    unattempted_count: int = 0
    accuracy: Optional[float] = None


class SubjectReportRow(BaseModel):
    subject_id: int
    subject_name: str
    exam_id: int
    exam_name: Optional[str] = None
    question_count: int = 0
    topic_count: int = 0
    attempt_count: int = 0
    average_percentage: Optional[float] = None
    accuracy: Optional[float] = None
