"""Aggregate report endpoints mounted at ``/api/v1/reports``.

All routes are read-only and guarded by the ``report.view`` permission.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.core.permissions import require_permission
from app.db.session import get_db
from app.schemas.common import ErrorResponse
from app.schemas.report import (
    DashboardReport,
    ExamReportRow,
    QuestionReportRow,
    StudentReportRow,
    SubjectReportRow,
    TestReportRow,
)
from app.services import report_service

router = APIRouter()

_UNAUTHORIZED: Dict[int, Dict[str, Any]] = {
    401: {"description": "Missing, expired or invalid access token.", "model": ErrorResponse}
}
_FORBIDDEN: Dict[int, Dict[str, Any]] = {
    403: {"description": "Authenticated user lacks the required permission.", "model": ErrorResponse}
}
_NOT_FOUND: Dict[int, Dict[str, Any]] = {
    404: {"description": "Student not found.", "model": ErrorResponse}
}


@router.get(
    "/dashboard",
    response_model=DashboardReport,
    summary="Dashboard summary",
    description=(
        "High-level counts (users, exams, tests, questions, attempts, "
        "results) plus the global average percentage and pass rate. Requires "
        "`report.view`."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN},
    dependencies=[Depends(require_permission("report.view"))],
)
def dashboard(db: Session = Depends(get_db)) -> DashboardReport:
    """Return the aggregate dashboard report."""
    return report_service.dashboard_report(db)


@router.get(
    "/exams",
    response_model=List[ExamReportRow],
    summary="Per-exam report",
    description=(
        "One row per exam with subject/question/test/attempt counts and the "
        "average percentage. Requires `report.view`."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN},
    dependencies=[Depends(require_permission("report.view"))],
)
def exam_report(db: Session = Depends(get_db)) -> List[ExamReportRow]:
    """Return the per-exam aggregate report."""
    return report_service.exams_report(db)


@router.get(
    "/tests",
    response_model=List[TestReportRow],
    summary="Per-test report",
    description=(
        "One row per test with assignment/attempt/evaluation counts and score "
        "statistics. Optionally filtered by `exam_id`. Requires `report.view`."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN},
    dependencies=[Depends(require_permission("report.view"))],
)
def test_report(
    db: Session = Depends(get_db),
    exam_id: Optional[int] = Query(None, ge=1, description="Filter by exam."),
) -> List[TestReportRow]:
    """Return the per-test aggregate report."""
    return report_service.tests_report(db, exam_id=exam_id)


@router.get(
    "/students/{student_id}",
    response_model=StudentReportRow,
    summary="Per-student report",
    description=(
        "Return the report row for one student: assignments, attempts, "
        "completed tests and score statistics. Unknown ids return 404 "
        "`USER_NOT_FOUND`. Requires `report.view`."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND},
    dependencies=[Depends(require_permission("report.view"))],
)
def student_report(
    student_id: int = Path(..., ge=1, description="Student user ID."),
    db: Session = Depends(get_db),
) -> StudentReportRow:
    """Return the aggregate report for one student."""
    return report_service.student_report(db, student_id=student_id)


@router.get(
    "/questions",
    response_model=List[QuestionReportRow],
    summary="Per-question report",
    description=(
        "One row per question with usage and (objective) accuracy stats. "
        "Optionally filtered by `subject_id`. Requires `report.view`."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN},
    dependencies=[Depends(require_permission("report.view"))],
)
def question_report(
    db: Session = Depends(get_db),
    subject_id: Optional[int] = Query(None, ge=1, description="Filter by subject."),
) -> List[QuestionReportRow]:
    """Return the per-question aggregate report."""
    return report_service.questions_report(db, subject_id=subject_id)


@router.get(
    "/subjects",
    response_model=List[SubjectReportRow],
    summary="Per-subject report",
    description=(
        "One row per subject with question/topic/attempt counts and accuracy. "
        "Optionally filtered by `exam_id`. Requires `report.view`."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN},
    dependencies=[Depends(require_permission("report.view"))],
)
def subject_report(
    db: Session = Depends(get_db),
    exam_id: Optional[int] = Query(None, ge=1, description="Filter by exam."),
) -> List[SubjectReportRow]:
    """Return the per-subject aggregate report."""
    return report_service.subjects_report(db, exam_id=exam_id)
