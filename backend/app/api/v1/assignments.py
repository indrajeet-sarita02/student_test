"""Assignment endpoints - list, assign (single/bulk), fetch and revoke.

Mounted by ``app.api.v1.router`` at ``/api/v1/assignments``; every path below
is relative to that prefix. All routes are guarded by the ``test.assign`` RBAC
permission code.
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Path, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.permissions import require_permission
from app.db.session import get_db
from app.models.assignment import TestAssignment
from app.models.user import User
from app.repositories import test_repository
from app.schemas.assignment import (
    AssignmentBulkResponse,
    AssignmentCreate,
    AssignmentResponse,
    TestAssignmentBulkRequest,
)
from app.schemas.common import ErrorResponse
from app.services import assignment_service
from app.utils.pagination import Page, PaginationParams

router = APIRouter()

_UNAUTHORIZED: Dict[int, Dict[str, Any]] = {
    401: {
        "description": "Missing, expired or invalid access token.",
        "model": ErrorResponse,
    }
}
_FORBIDDEN: Dict[int, Dict[str, Any]] = {
    403: {
        "description": "Authenticated user lacks the required permission.",
        "model": ErrorResponse,
    }
}
_NOT_FOUND: Dict[int, Dict[str, Any]] = {
    404: {
        "description": "Test or assignment not found "
        "(TEST_NOT_FOUND / ASSIGNMENT_NOT_FOUND).",
        "model": ErrorResponse,
    }
}
_BAD_REQUEST: Dict[int, Dict[str, Any]] = {
    400: {
        "description": "Target user is not a student (USER_NOT_A_STUDENT).",
        "model": ErrorResponse,
    }
}
_CONFLICT: Dict[int, Dict[str, Any]] = {
    409: {
        "description": "Test is not published (TEST_NOT_PUBLISHED), the student "
        "is already assigned (ALREADY_ASSIGNED) or the assignment has attempts "
        "(ASSIGNMENT_HAS_ATTEMPTS).",
        "model": ErrorResponse,
    }
}


@router.get(
    "/",
    response_model=Page[AssignmentResponse],
    summary="List assignments",
    description=(
        "Return a paginated, sortable list of test assignments enriched with "
        "the test and student names. Supports the `test_id`, `student_id` and "
        "shared `status` filters. Sortable by id, status, created_at and "
        "updated_at (unknown columns fall back to created_at desc). Requires "
        "the `test.assign` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND},
    dependencies=[Depends(require_permission("test.assign"))],
)
def list_assignments(
    db: Session = Depends(get_db),
    params: PaginationParams = Depends(),
    test_id: Optional[int] = Query(None, ge=1, description="Filter by test id."),
    student_id: Optional[int] = Query(
        None, ge=1, description="Filter by student id."
    ),
) -> Any:
    """List assignments with pagination and test/student/status filters."""
    return assignment_service.list_assignments(
        db, params, test_id=test_id, student_id=student_id
    )


@router.post(
    "/",
    response_model=AssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Assign test to student",
    description=(
        "Assign a `PUBLISHED` test to a student. The test must be published "
        "(409 `TEST_NOT_PUBLISHED`); the user must exist and hold the `STUDENT` "
        "role (400 `USER_NOT_A_STUDENT`); the pair must not already be assigned "
        "(409 `ALREADY_ASSIGNED`). A `TEST_ASSIGNED` notification is created "
        "and an `assignment.assign` audit entry is written. Requires the "
        "`test.assign` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND, **_CONFLICT, **_BAD_REQUEST},
    dependencies=[Depends(require_permission("test.assign"))],
)
def create_assignment(
    payload: AssignmentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TestAssignment:
    """Assign a published test to one student and notify them."""
    return assignment_service.create_assignment(
        db, payload, user_id=current_user.id, request=request
    )


@router.post(
    "/bulk",
    response_model=AssignmentBulkResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Assign test to many students",
    description=(
        "Assign a `PUBLISHED` test to many students in a single transaction. "
        "The test must be published (409 `TEST_NOT_PUBLISHED`); users that do "
        "not exist, do not hold the `STUDENT` role or are already assigned are "
        "counted under `skipped` instead of failing the request. A "
        "`TEST_ASSIGNED` notification is created for every new assignment and "
        "one `assignment.bulk_assign` audit entry is written. Requires the "
        "`test.assign` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND, **_CONFLICT},
    dependencies=[Depends(require_permission("test.assign"))],
)
def bulk_assign(
    payload: TestAssignmentBulkRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AssignmentBulkResponse:
    """Assign a published test to many students, skipping invalid/duplicates."""
    result = assignment_service.bulk_assign(
        db, payload, user_id=current_user.id, request=request
    )
    return AssignmentBulkResponse(
        created=result["created"],
        skipped=result["skipped"],
        assignments=result.get("assignments", []),
    )


@router.get(
    "/{assignment_id}",
    response_model=AssignmentResponse,
    summary="Get assignment",
    description=(
        "Return one assignment enriched with the test and student names. "
        "Unknown ids return 404 `ASSIGNMENT_NOT_FOUND`. Requires the "
        "`test.assign` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND},
    dependencies=[Depends(require_permission("test.assign"))],
)
def get_assignment(
    assignment_id: int = Path(..., ge=1, description="Unique assignment ID."),
    db: Session = Depends(get_db),
) -> TestAssignment:
    """Fetch one assignment by ID."""
    assignment = assignment_service.get_assignment(db, assignment_id)
    return test_repository.decorate_assignment(assignment)


@router.delete(
    "/{assignment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke assignment",
    description=(
        "Delete an assignment. Refused with 409 `ASSIGNMENT_HAS_ATTEMPTS` when "
        "the student already has attempts for the test so history is "
        "preserved. Writes an audit entry. Requires the `test.assign` "
        "permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND, **_CONFLICT},
    dependencies=[Depends(require_permission("test.assign"))],
)
def delete_assignment(
    request: Request,
    assignment_id: int = Path(..., ge=1, description="Unique assignment ID."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete an assignment unless the student already has attempts."""
    assignment_service.delete_assignment(
        db, assignment_id, user_id=current_user.id, request=request
    )
