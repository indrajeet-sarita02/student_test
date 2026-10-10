"""Subject endpoints - CRUD for the syllabus areas inside an exam.

Mounted by ``app.api.v1.router`` at ``/api/v1/subjects``; every path below is
relative to that prefix. Subjects belong to the exam module, so all actions
use the ``exam.*`` permission codes.
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Path, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.permissions import require_permission
from app.db.session import get_db
from app.models.subject import Subject
from app.models.user import User
from app.repositories import exam_repository
from app.schemas.common import ErrorResponse
from app.schemas.subject import SubjectCreate, SubjectResponse, SubjectUpdate
from app.services import exam_service
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
    404: {
        "description": "Subject or parent exam not found "
        "(SUBJECT_NOT_FOUND / EXAM_NOT_FOUND).",
        "model": ErrorResponse,
    }
}
_CONFLICT: Dict[int, Dict[str, Any]] = {
    409: {
        "description": "Subject code already used inside the exam "
        "(SUBJECT_CODE_EXISTS).",
        "model": ErrorResponse,
    }
}


@router.get(
    "/",
    response_model=Page[SubjectResponse],
    summary="List subjects",
    description=(
        "Return a paginated, sortable list of subjects. Supports the "
        "`exam_id`, `is_active` and free-text `search` (name/code) filters. "
        "Sortable by id, name, code and created_at (unknown columns fall back "
        "to created_at desc). Requires the `exam.view` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN},
    dependencies=[Depends(require_permission("exam.view"))],
)
def list_subjects(
    db: Session = Depends(get_db),
    params: PaginationParams = Depends(),
    exam_id: Optional[int] = Query(
        None, ge=1, description="Only subjects belonging to this exam."
    ),
    is_active: Optional[bool] = Query(
        None, description="Filter by the active flag (true/false)."
    ),
) -> Any:
    """List subjects with pagination, exam and search filters."""
    stmt = exam_repository.build_subject_list_stmt(
        params, exam_id=exam_id, is_active=is_active
    )
    return paginate(db, stmt, params)


@router.post(
    "/",
    response_model=SubjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create subject",
    description=(
        "Create a subject inside an existing exam. The exam must exist "
        "(404 `EXAM_NOT_FOUND`) and the `(exam_id, code)` pair must be unique "
        "(409 `SUBJECT_CODE_EXISTS`). Writes a `subject.create` audit entry. "
        "Requires the `exam.create` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND, **_CONFLICT},
    dependencies=[Depends(require_permission("exam.create"))],
)
def create_subject(
    payload: SubjectCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Subject:
    """Create a subject under an existing exam."""
    return exam_service.create_subject(
        db, payload, user_id=current_user.id, request=request
    )


@router.get(
    "/{subject_id}",
    response_model=SubjectResponse,
    summary="Get subject",
    description=(
        "Return a single subject by numeric ID. 404 `SUBJECT_NOT_FOUND` when "
        "the subject does not exist. Requires the `exam.view` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND},
    dependencies=[Depends(require_permission("exam.view"))],
)
def get_subject(
    subject_id: int = Path(..., ge=1, description="Unique subject ID."),
    db: Session = Depends(get_db),
) -> Subject:
    """Fetch one subject by ID."""
    return exam_service.get_subject(db, subject_id)


@router.put(
    "/{subject_id}",
    response_model=SubjectResponse,
    summary="Update subject",
    description=(
        "Apply the provided (non-null) fields to the subject. The `code` is "
        "immutable (it is part of the per-exam uniqueness constraint). "
        "Writes an audit entry with the old and new values. "
        "Requires the `exam.update` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND},
    dependencies=[Depends(require_permission("exam.update"))],
)
def update_subject(
    payload: SubjectUpdate,
    request: Request,
    subject_id: int = Path(..., ge=1, description="Unique subject ID."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Subject:
    """Update the mutable fields of an existing subject."""
    return exam_service.update_subject(
        db, subject_id, payload, user_id=current_user.id, request=request
    )


@router.delete(
    "/{subject_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete subject",
    description=(
        "Remove a subject. When it still owns topics or questions it is only "
        "soft-deactivated (`is_active=false`, action `deactivate`); an empty "
        "subject is hard-deleted (action `delete`). Both paths are audited. "
        "Requires the `exam.delete` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND},
    dependencies=[Depends(require_permission("exam.delete"))],
)
def delete_subject(
    request: Request,
    subject_id: int = Path(..., ge=1, description="Unique subject ID."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Soft-deactivate or hard-delete a subject depending on its contents."""
    exam_service.delete_subject(
        db, subject_id, user_id=current_user.id, request=request
    )
