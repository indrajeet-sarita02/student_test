"""Exam endpoints - CRUD plus the ``publish`` / ``archive`` lifecycle actions.

Mounted by ``app.api.v1.router`` at ``/api/v1/exams``; every path below is
relative to that prefix.
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Path, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.permissions import require_permission
from app.db.session import get_db
from app.models.exam import Exam
from app.models.user import User
from app.repositories import exam_repository
from app.schemas.common import ErrorResponse
from app.schemas.exam import ExamCreate, ExamResponse, ExamUpdate
from app.services import exam_service
from app.utils.enums import ExamType
from app.utils.pagination import Page, PaginationParams, paginate

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
    404: {"description": "Exam not found (EXAM_NOT_FOUND).", "model": ErrorResponse}
}
_CONFLICT: Dict[int, Dict[str, Any]] = {
    409: {
        "description": "Exam code already in use (EXAM_CODE_EXISTS).",
        "model": ErrorResponse,
    }
}
_BAD_REQUEST: Dict[int, Dict[str, Any]] = {
    400: {
        "description": "Exam cannot perform the action in its current state.",
        "model": ErrorResponse,
    }
}


@router.get(
    "/",
    response_model=Page[ExamResponse],
    summary="List exams",
    description=(
        "Return a paginated, sortable list of exams. Supports free-text "
        "`search` over name/code/description plus the `status`, `exam_type` "
        "and `is_active` filters. Sortable by id, name, code, created_at and "
        "status (unknown columns fall back to created_at desc). "
        "Requires the `exam.view` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN},
    dependencies=[Depends(require_permission("exam.view"))],
)
def list_exams(
    db: Session = Depends(get_db),
    params: PaginationParams = Depends(),
    exam_type: Optional[ExamType] = Query(
        None, description="Filter by exam type (NEET, JEE, UPSC, SSC, CUSTOM)."
    ),
    is_active: Optional[bool] = Query(
        None, description="Filter by the active flag (true/false)."
    ),
) -> Any:
    """List exams with pagination, search, status/type/active filters."""
    stmt = exam_repository.build_exam_list_stmt(
        params,
        exam_type=exam_type.value if exam_type is not None else None,
        is_active=is_active,
    )
    return paginate(db, stmt, params)


@router.post(
    "/",
    response_model=ExamResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create exam",
    description=(
        "Create a new exam in `DRAFT` status. The `code` must be unique "
        "(409 `EXAM_CODE_EXISTS`). Writes an `exam.create` audit entry. "
        "Requires the `exam.create` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_CONFLICT},
    dependencies=[Depends(require_permission("exam.create"))],
)
def create_exam(
    payload: ExamCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Exam:
    """Create a new DRAFT exam with a globally unique code."""
    return exam_service.create_exam(
        db, payload, user_id=current_user.id, request=request
    )


@router.get(
    "/{exam_id}",
    response_model=ExamResponse,
    summary="Get exam",
    description=(
        "Return a single exam by numeric ID. 404 `EXAM_NOT_FOUND` when the "
        "exam does not exist. Requires the `exam.view` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND},
    dependencies=[Depends(require_permission("exam.view"))],
)
def get_exam(
    exam_id: int = Path(..., ge=1, description="Unique exam ID."),
    db: Session = Depends(get_db),
) -> Exam:
    """Fetch one exam by ID."""
    return exam_service.get_exam(db, exam_id)


@router.put(
    "/{exam_id}",
    response_model=ExamResponse,
    summary="Update exam",
    description=(
        "Apply the provided (non-null) fields to the exam. `code` is "
        "immutable and `status` changes only through the publish/archive "
        "actions. Writes an audit entry with the old and new values. "
        "Requires the `exam.update` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND},
    dependencies=[Depends(require_permission("exam.update"))],
)
def update_exam(
    payload: ExamUpdate,
    request: Request,
    exam_id: int = Path(..., ge=1, description="Unique exam ID."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Exam:
    """Update the mutable fields of an existing exam."""
    return exam_service.update_exam(
        db, exam_id, payload, user_id=current_user.id, request=request
    )


@router.delete(
    "/{exam_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete exam",
    description=(
        "Remove an exam. When the exam still owns subjects it is "
        "only soft-deactivated (`is_active=false`, action `deactivate`) so "
        "historic data is preserved; an empty exam is hard-deleted "
        "(action `delete`). Both paths are audited. "
        "Requires the `exam.delete` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND},
    dependencies=[Depends(require_permission("exam.delete"))],
)
def delete_exam(
    request: Request,
    exam_id: int = Path(..., ge=1, description="Unique exam ID."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Soft-deactivate or hard-delete an exam depending on its contents."""
    exam_service.delete_exam(db, exam_id, user_id=current_user.id, request=request)


@router.post(
    "/{exam_id}/publish",
    response_model=ExamResponse,
    summary="Publish exam",
    description=(
        "Move the exam to `PUBLISHED`. The exam must be active and own at "
        "least one subject, otherwise 400 `EXAM_INACTIVE` / "
        "`EXAM_HAS_NO_SUBJECTS` is returned. Writes an audit entry. "
        "Requires the `exam.publish` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND, **_BAD_REQUEST},
    dependencies=[Depends(require_permission("exam.publish"))],
)
def publish_exam(
    request: Request,
    exam_id: int = Path(..., ge=1, description="Unique exam ID."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Exam:
    """Publish an active exam that has at least one subject."""
    return exam_service.publish_exam(
        db, exam_id, user_id=current_user.id, request=request
    )


@router.post(
    "/{exam_id}/archive",
    response_model=ExamResponse,
    summary="Archive exam",
    description=(
        "Move the exam to `ARCHIVED`; data and history remain intact. "
        "Writes an audit entry. Requires the `exam.update` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND},
    dependencies=[Depends(require_permission("exam.update"))],
)
def archive_exam(
    request: Request,
    exam_id: int = Path(..., ge=1, description="Unique exam ID."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Exam:
    """Archive an exam (status becomes ARCHIVED)."""
    return exam_service.archive_exam(
        db, exam_id, user_id=current_user.id, request=request
    )
