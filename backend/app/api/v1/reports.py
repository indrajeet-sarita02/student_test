"""Aggregate report endpoints mounted at ``/api/v1/reports``.

All routes are read-only. The JSON endpoints require the ``report.view``
permission; the CSV export variants require ``report.export``.
"""

import csv
import io
from typing import Any, Dict, List, Optional, Sequence

from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import Response
from pydantic import BaseModel
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

_CSV_MEDIA_TYPE = "text/csv"


def _csv_response(
    model: type[BaseModel], rows: Sequence[Any], filename: str
) -> Response:
    """Serialise report rows to a CSV download using the schema's field order."""
    columns = list(model.model_fields.keys())
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow(model.model_validate(row).model_dump())
    return Response(
        content=buffer.getvalue(),
        media_type=_CSV_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


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


_CSV_RESPONSES = {
    200: {
        "content": {_CSV_MEDIA_TYPE: {}},
        "description": "CSV attachment with one row per record.",
    },
    **_UNAUTHORIZED,
    **_FORBIDDEN,
}


@router.get(
    "/exams/export",
    summary="Export per-exam report (CSV)",
    description=(
        "Download the per-exam aggregate report as a CSV attachment. Requires "
        "the `report.export` permission."
    ),
    responses=_CSV_RESPONSES,
    dependencies=[Depends(require_permission("report.export"))],
)
def export_exam_report(db: Session = Depends(get_db)) -> Response:
    """Return the per-exam report as CSV."""
    return _csv_response(ExamReportRow, report_service.exams_report(db), "exams_report.csv")


@router.get(
    "/tests/export",
    summary="Export per-test report (CSV)",
    description=(
        "Download the per-test aggregate report as a CSV attachment. "
        "Optionally filtered by `exam_id`. Requires the `report.export` "
        "permission."
    ),
    responses=_CSV_RESPONSES,
    dependencies=[Depends(require_permission("report.export"))],
)
def export_test_report(
    db: Session = Depends(get_db),
    exam_id: Optional[int] = Query(None, ge=1, description="Filter by exam."),
) -> Response:
    """Return the per-test report as CSV."""
    return _csv_response(
        TestReportRow,
        report_service.tests_report(db, exam_id=exam_id),
        "tests_report.csv",
    )


@router.get(
    "/students/{student_id}/export",
    summary="Export per-student report (CSV)",
    description=(
        "Download one student's aggregate report as a CSV attachment. Unknown "
        "ids return 404 `USER_NOT_FOUND`. Requires the `report.export` "
        "permission."
    ),
    responses={**_CSV_RESPONSES, **_NOT_FOUND},
    dependencies=[Depends(require_permission("report.export"))],
)
def export_student_report(
    student_id: int = Path(..., ge=1, description="Student user ID."),
    db: Session = Depends(get_db),
) -> Response:
    """Return the per-student report as CSV."""
    return _csv_response(
        StudentReportRow,
        [report_service.student_report(db, student_id=student_id)],
        f"student_{student_id}_report.csv",
    )


@router.get(
    "/questions/export",
    summary="Export per-question report (CSV)",
    description=(
        "Download the per-question aggregate report as a CSV attachment. "
        "Optionally filtered by `subject_id`. Requires the `report.export` "
        "permission."
    ),
    responses=_CSV_RESPONSES,
    dependencies=[Depends(require_permission("report.export"))],
)
def export_question_report(
    db: Session = Depends(get_db),
    subject_id: Optional[int] = Query(None, ge=1, description="Filter by subject."),
) -> Response:
    """Return the per-question report as CSV."""
    return _csv_response(
        QuestionReportRow,
        report_service.questions_report(db, subject_id=subject_id),
        "questions_report.csv",
    )


@router.get(
    "/subjects/export",
    summary="Export per-subject report (CSV)",
    description=(
        "Download the per-subject aggregate report as a CSV attachment. "
        "Optionally filtered by `exam_id`. Requires the `report.export` "
        "permission."
    ),
    responses=_CSV_RESPONSES,
    dependencies=[Depends(require_permission("report.export"))],
)
def export_subject_report(
    db: Session = Depends(get_db),
    exam_id: Optional[int] = Query(None, ge=1, description="Filter by exam."),
) -> Response:
    """Return the per-subject report as CSV."""
    return _csv_response(
        SubjectReportRow,
        report_service.subjects_report(db, exam_id=exam_id),
        "subjects_report.csv",
    )
