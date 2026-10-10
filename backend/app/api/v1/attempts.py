"""Admin attempt endpoints (read-only).

Mounted by ``app.api.v1.router`` at ``/api/v1/attempts``; paths are relative to
that prefix. Every route requires the ``attempt.view`` permission. The owning
service (``attempt_service``) raises ``ATTEMPT_NOT_FOUND`` for unknown ids; the
router shapes the enriched admin payloads (including recomputed per-question
correctness) so the persistent answer rows are never mutated on read.
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.core.permissions import require_permission
from app.db.session import get_db
from app.repositories import attempt_repository
from app.schemas.attempt import (
    AttemptAnswerAdminResponse,
    AttemptDetailResponse,
    AttemptResponse,
)
from app.services import attempt_service
from app.utils.pagination import Page, PaginationParams

router = APIRouter()

_UNAUTHORIZED: Dict[int, Dict[str, Any]] = {
    401: {"description": "Missing, expired or invalid access token."}
}
_FORBIDDEN: Dict[int, Dict[str, Any]] = {
    403: {"description": "Authenticated user lacks the required permission."}
}
_NOT_FOUND: Dict[int, Dict[str, Any]] = {
    404: {"description": "Attempt not found (ATTEMPT_NOT_FOUND)."}
}


@router.get(
    "/",
    response_model=Page[AttemptResponse],
    summary="List attempts",
    description=(
        "Paginated list of attempts across all students. Supports `test_id`, "
        "`student_id` and `status` filters plus the shared `search` keyword "
        "(test name / student name / username). Each row includes the test and "
        "student names. Requires the `attempt.view` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN},
    dependencies=[Depends(require_permission("attempt.view"))],
)
def list_attempts(
    test_id: Optional[int] = Query(None, ge=1, description="Filter by test id."),
    student_id: Optional[int] = Query(None, ge=1, description="Filter by student id."),
    db: Session = Depends(get_db),
    params: PaginationParams = Depends(),
) -> Any:
    """Return one page of attempts with test/student names.

    The ``status`` filter is supplied through the shared ``PaginationParams``
    dependency (``?status=SUBMITTED``) and applied by the service.
    """
    return attempt_service.list_attempts(
        db,
        params,
        test_id=test_id,
        student_id=student_id,
    )


@router.get(
    "/{attempt_id}/answers",
    response_model=list[AttemptAnswerAdminResponse],
    summary="List attempt answers",
    description=(
        "All persisted answers of one attempt. When the attempt has been "
        "evaluated each row additionally reports `is_correct` and "
        "`marks_awarded`; before evaluation those fields are null. Correctness "
        "is recomputed from the current test configuration and is not "
        "persisted. Returns 404 `ATTEMPT_NOT_FOUND` for unknown ids. Requires "
        "the `attempt.view` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND},
    dependencies=[Depends(require_permission("attempt.view"))],
)
def list_attempt_answers(
    attempt_id: int = Path(..., ge=1, description="Unique attempt ID."),
    db: Session = Depends(get_db),
) -> Any:
    """Return the enriched answer rows of an attempt."""
    return attempt_service.get_attempt_answers(db, attempt_id)


@router.get(
    "/{attempt_id}",
    response_model=AttemptDetailResponse,
    summary="Get attempt detail",
    description=(
        "Attempt summary plus every answer enriched with `is_correct` and "
        "`marks_awarded` (once evaluated) and the associated result. Returns "
        "404 `ATTEMPT_NOT_FOUND` for unknown ids. Requires the `attempt.view` "
        "permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND},
    dependencies=[Depends(require_permission("attempt.view"))],
)
def get_attempt_detail(
    attempt_id: int = Path(..., ge=1, description="Unique attempt ID."),
    db: Session = Depends(get_db),
) -> AttemptDetailResponse:
    """Return one attempt with its enriched answers and result."""
    attempt = attempt_service.get_attempt_detail(db, attempt_id)
    answers = attempt_service.get_attempt_answers(db, attempt_id)
    result = attempt_repository.get_result_by_attempt(db, attempt_id)
    return AttemptDetailResponse(
        attempt=AttemptResponse.model_validate(attempt),
        answers=[
            AttemptAnswerAdminResponse.model_validate(answer) for answer in answers
        ],
        result=(
            attempt_service.result_payload(result).model_dump()
            if result is not None
            else None
        ),
    )
