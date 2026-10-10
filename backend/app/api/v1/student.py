"""Student test-taking endpoints mounted at ``/api/v1/student``.

These routes are **ownership-based**: they require an authenticated user but no
RBAC permission.  A student can only see and act on their own assignments,
attempts and results.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Path, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.attempt import (
    AttemptResponse,
    SaveAnswersRequest,
    SaveAnswersResponse,
    StartAttemptResponse,
    SubmitAttemptResponse,
)
from app.schemas.common import ErrorResponse
from app.schemas.result import ResultResponse, ResultReviewResponse
from app.schemas.student import StudentAttemptResponse, StudentTestItem
from app.services import attempt_service
from app.utils.enums import SubmissionType
from app.utils.pagination import Page, PaginationParams

router = APIRouter()

_UNAUTHORIZED: Dict[int, Dict[str, Any]] = {
    401: {"description": "Missing, expired or invalid access token.", "model": ErrorResponse}
}
_FORBIDDEN: Dict[int, Dict[str, Any]] = {
    403: {"description": "The resource does not belong to the authenticated student.", "model": ErrorResponse}
}
_NOT_FOUND: Dict[int, Dict[str, Any]] = {
    404: {"description": "Test, attempt or result not found.", "model": ErrorResponse}
}
_BAD_REQUEST: Dict[int, Dict[str, Any]] = {
    400: {
        "description": "Attempt is not active, has expired or the test is not available.",
        "model": ErrorResponse,
    }
}


@router.get(
    "/tests",
    response_model=List[StudentTestItem],
    summary="List my tests",
    description=(
        "Tests currently visible to the authenticated student (assigned, or "
        "open tests), decorated with attempt counts and availability. Optional "
        "`search` over name/code."
    ),
    responses={**_UNAUTHORIZED},
)
def list_my_tests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    search: Optional[str] = Query(None, description="Search test name or code."),
) -> List[StudentTestItem]:
    """Return the student's visible tests."""
    return attempt_service.list_student_tests(
        db, student_id=current_user.id, search=search
    )


@router.get(
    "/tests/{test_id}",
    response_model=StudentTestItem,
    summary="Get one of my tests",
    description="Return the dashboard row for one visible test.",
    responses={**_UNAUTHORIZED, **_NOT_FOUND},
)
def get_my_test(
    test_id: int = Path(..., ge=1, description="Unique test ID."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StudentTestItem:
    """Return one visible test for the student."""
    return attempt_service.get_student_test(db, test_id, student_id=current_user.id)


@router.post(
    "/tests/{test_id}/start",
    response_model=StartAttemptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start or resume a test",
    description=(
        "Validate eligibility/availability/attempt budget, then resume the "
        "open attempt or create a new one with a server-side `expires_at`. "
        "Returns the questions **without** the answer key."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND, **_BAD_REQUEST},
)
def start_test(
    request: Request,
    test_id: int = Path(..., ge=1, description="Unique test ID."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Start or resume an attempt on a test."""
    return attempt_service.start_attempt(
        db, test_id, student_id=current_user.id, request=request
    )


@router.get(
    "/attempts",
    response_model=Page[AttemptResponse],
    summary="List my attempts",
    description="Paginated list of the authenticated student's attempts.",
    responses={**_UNAUTHORIZED},
)
def list_my_attempts(
    db: Session = Depends(get_db),
    params: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
) -> Any:
    """List the student's attempts."""
    return attempt_service.list_student_attempts(
        db, params, student_id=current_user.id
    )


@router.get(
    "/attempts/{attempt_id}",
    response_model=StudentAttemptResponse,
    summary="Get my attempt",
    description=(
        "Return an attempt with its questions and the answers saved so far, "
        "plus the remaining server-side time. Only the owning student may "
        "read it."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND},
)
def get_my_attempt(
    attempt_id: int = Path(..., ge=1, description="Unique attempt ID."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Return the active attempt payload."""
    return attempt_service.get_active_attempt(
        db, attempt_id, student_id=current_user.id
    )


@router.put(
    "/attempts/{attempt_id}/answers",
    response_model=SaveAnswersResponse,
    summary="Save answers",
    description=(
        "Upsert the provided answers for a still-active attempt. Rejects "
        "answers after `expires_at`, for a submitted attempt or for questions "
        "outside the test."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND, **_BAD_REQUEST},
)
def save_my_answers(
    payload: SaveAnswersRequest,
    request: Request,
    attempt_id: int = Path(..., ge=1, description="Unique attempt ID."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Persist the submitted answers."""
    return attempt_service.save_answers(
        db,
        attempt_id,
        payload,
        student_id=current_user.id,
        request=request,
    )


@router.post(
    "/attempts/{attempt_id}/submit",
    response_model=SubmitAttemptResponse,
    summary="Submit my attempt",
    description=(
        "Evaluate the attempt, create its result and mark it `EVALUATED`. "
        "A duplicate submission is rejected with 409 "
        "`ATTEMPT_ALREADY_SUBMITTED`."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND, **_BAD_REQUEST},
)
def submit_my_attempt(
    request: Request,
    attempt_id: int = Path(..., ge=1, description="Unique attempt ID."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Submit and evaluate the student's attempt."""
    result = attempt_service.submit_attempt(
        db,
        attempt_id,
        student_id=current_user.id,
        request=request,
        submit_type=SubmissionType.MANUAL,
    )
    attempt = attempt_service.get_attempt_detail(db, attempt_id)
    return {
        "attempt": attempt,
        "result_id": result.id,
        "score": float(result.score or 0),
        "max_score": float(result.max_score or 0),
        "percentage": float(result.percentage or 0),
        "pass_status": result.pass_status,
        "status": attempt.status,
    }


@router.get(
    "/results",
    response_model=List[ResultResponse],
    summary="List my results",
    description=(
        "Return the authenticated student's results (published or not), "
        "optionally filtered by `test_id`."
    ),
    responses={**_UNAUTHORIZED},
)
def list_my_results(
    db: Session = Depends(get_db),
    params: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    test_id: Optional[int] = Query(None, ge=1, description="Filter by test."),
) -> List[ResultResponse]:
    """List the student's results."""
    return attempt_service.list_student_results(
        db, params, student_id=current_user.id, test_id=test_id
    )


@router.get(
    "/results/{result_id}/review",
    response_model=ResultReviewResponse,
    summary="Review my result",
    description=(
        "Return the student's own result together with the per-question "
        "answer key and marks."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND},
)
def review_my_result(
    result_id: int = Path(..., ge=1, description="Unique result ID."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Return the owner-restricted answer-key review."""
    return attempt_service.review_result(
        db, result_id, student_id=current_user.id
    )
