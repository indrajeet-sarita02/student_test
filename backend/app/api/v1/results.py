"""Result endpoints: listing, single fetch, publication and CSV export.

Mounted by ``app.api.v1.router`` at ``/api/v1/results``; paths are relative to
that prefix. Publication is a privileged action guarded by ``result.publish``
and notifies the student through a :class:`~app.models.notification.Notification`
row created in the same transaction.
"""

import csv
import io
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Path, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.permissions import require_permission
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories import attempt_repository
from app.schemas.result import ResultResponse
from app.services import attempt_service
from app.utils.pagination import Page, PaginationParams

router = APIRouter()

#: Hard cap on exported rows so a report request can never exhaust memory.
EXPORT_LIMIT = 5000

_UNAUTHORIZED: Dict[int, Dict[str, Any]] = {
    401: {"description": "Missing, expired or invalid access token."}
}
_FORBIDDEN: Dict[int, Dict[str, Any]] = {
    403: {"description": "Authenticated user lacks the required permission."}
}
_NOT_FOUND: Dict[int, Dict[str, Any]] = {
    404: {"description": "Result not found (RESULT_NOT_FOUND)."}
}
_CONFLICT: Dict[int, Dict[str, Any]] = {
    409: {"description": "Result already published (RESULT_ALREADY_PUBLISHED)."}
}


@router.get(
    "/",
    response_model=Page[ResultResponse],
    summary="List results",
    description=(
        "Paginated result listing with `test_id`, `student_id` and `published` "
        "(true => `published_at` is not null) filters plus a `search` keyword "
        "over the student's name/username. Rows include the test name, student "
        "name and attempt number. Requires the `result.view` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN},
    dependencies=[Depends(require_permission("result.view"))],
)
def list_results(
    test_id: Optional[int] = Query(None, ge=1, description="Filter by test id."),
    student_id: Optional[int] = Query(None, ge=1, description="Filter by student id."),
    published: Optional[bool] = Query(
        None, description="Filter by publication state (true = published only)."
    ),
    db: Session = Depends(get_db),
    params: PaginationParams = Depends(),
) -> Any:
    """Return one page of results."""
    return attempt_service.list_results(
        db,
        params,
        test_id=test_id,
        student_id=student_id,
        published=published,
    )


@router.get(
    "/export",
    summary="Export results as CSV",
    description=(
        "Stream up to 5000 results matching the same filters as the list "
        "endpoint as a UTF-8 CSV attachment (`results.csv`). Columns: "
        "`result_id, test_id, test_name, student_id, student_name, email, "
        "attempt_number, score, max_score, percentage, correct, incorrect, "
        "unanswered, rank, pass_status, published_at`. Requires the "
        "`result.export` permission."
    ),
    responses={
        **_UNAUTHORIZED,
        **_FORBIDDEN,
        200: {
            "content": {"text/csv": {}},
            "description": "CSV attachment of matching results.",
        },
    },
    dependencies=[Depends(require_permission("result.export"))],
)
def export_results(
    test_id: Optional[int] = Query(None, ge=1, description="Filter by test id."),
    student_id: Optional[int] = Query(None, ge=1, description="Filter by student id."),
    published: Optional[bool] = Query(None, description="Filter by publication state."),
    db: Session = Depends(get_db),
    params: PaginationParams = Depends(),
) -> StreamingResponse:
    """Build and stream a CSV of the filtered results."""
    stmt = attempt_repository.build_result_list_stmt(
        params, test_id=test_id, student_id=student_id, published=published
    ).limit(EXPORT_LIMIT)
    results = db.scalars(stmt).all()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "result_id",
            "test_id",
            "test_name",
            "student_id",
            "student_name",
            "email",
            "attempt_number",
            "score",
            "max_score",
            "percentage",
            "correct",
            "incorrect",
            "unanswered",
            "rank",
            "pass_status",
            "published_at",
        ]
    )
    for result in results:
        student = result.student
        test = result.test
        writer.writerow(
            [
                result.id,
                result.test_id,
                test.name if test else "",
                result.student_id,
                student.full_name if student else "",
                student.email if student else "",
                result.attempt.attempt_number if result.attempt else "",
                f"{float(result.score or 0):.2f}",
                f"{float(result.max_score or 0):.2f}",
                f"{float(result.percentage or 0):.2f}",
                result.correct_count,
                result.incorrect_count,
                result.unanswered_count,
                result.rank if result.rank is not None else "",
                "PASS" if result.pass_status else "FAIL",
                result.published_at.isoformat() if result.published_at else "",
            ]
        )

    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=results.csv"},
    )


@router.get(
    "/{result_id}",
    response_model=ResultResponse,
    summary="Get result",
    description=(
        "One result including test/student names and attempt number. Returns "
        "404 `RESULT_NOT_FOUND` for unknown ids. Requires the `result.view` "
        "permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND},
    dependencies=[Depends(require_permission("result.view"))],
)
def get_result(
    result_id: int = Path(..., ge=1, description="Unique result ID."),
    db: Session = Depends(get_db),
) -> Any:
    """Return one result."""
    result = attempt_service.get_result(db, result_id)
    return attempt_service.result_payload(result)


@router.post(
    "/{result_id}/publish",
    response_model=ResultResponse,
    summary="Publish result",
    description=(
        "Publish a result by stamping `published_at`, creating a "
        "`RESULT_PUBLISHED` notification for the student and writing an audit "
        "entry - all in one transaction. Re-publishing returns 409 "
        "`RESULT_ALREADY_PUBLISHED`. Requires the `result.publish` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND, **_CONFLICT},
    dependencies=[Depends(require_permission("result.publish"))],
)
def publish_result(
    request: Request,
    result_id: int = Path(..., ge=1, description="Unique result ID."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Publish one result and notify the student."""
    result = attempt_service.publish_result(
        db, result_id, user_id=current_user.id, request=request
    )
    return attempt_service.result_payload(result)
