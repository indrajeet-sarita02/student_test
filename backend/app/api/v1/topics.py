"""Topic endpoints - CRUD for the optional hierarchy below a subject.

Mounted by ``app.api.v1.router`` at ``/api/v1/topics``; every path below is
relative to that prefix. Topics belong to the exam module, so all actions use
the ``exam.*`` permission codes.
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Path, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.permissions import require_permission
from app.db.session import get_db
from app.models.topic import Topic
from app.models.user import User
from app.repositories import exam_repository
from app.schemas.common import ErrorResponse
from app.schemas.topic import TopicCreate, TopicResponse, TopicUpdate
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
        "description": "Topic or parent subject not found "
        "(TOPIC_NOT_FOUND / SUBJECT_NOT_FOUND).",
        "model": ErrorResponse,
    }
}
_BAD_REQUEST: Dict[int, Dict[str, Any]] = {
    400: {
        "description": "Parent topic is invalid (INVALID_PARENT_TOPIC).",
        "model": ErrorResponse,
    }
}


@router.get(
    "/",
    response_model=Page[TopicResponse],
    summary="List topics",
    description=(
        "Return a paginated, sortable list of topics. Supports the "
        "`subject_id`, `parent_topic_id`, `is_active` and free-text `search` "
        "filters. Sortable by id, name and created_at (unknown columns fall "
        "back to created_at desc). Requires the `exam.view` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN},
    dependencies=[Depends(require_permission("exam.view"))],
)
def list_topics(
    db: Session = Depends(get_db),
    params: PaginationParams = Depends(),
    subject_id: Optional[int] = Query(
        None, ge=1, description="Only topics belonging to this subject."
    ),
    parent_topic_id: Optional[int] = Query(
        None, ge=1, description="Only direct children of this parent topic."
    ),
    is_active: Optional[bool] = Query(
        None, description="Filter by the active flag (true/false)."
    ),
) -> Any:
    """List topics with pagination, hierarchy and search filters."""
    stmt = exam_repository.build_topic_list_stmt(
        params,
        subject_id=subject_id,
        parent_topic_id=parent_topic_id,
        is_active=is_active,
    )
    return paginate(db, stmt, params)


@router.post(
    "/",
    response_model=TopicResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create topic",
    description=(
        "Create a topic inside an existing subject. The subject must exist "
        "(404 `SUBJECT_NOT_FOUND`) and an optional `parent_topic_id` must "
        "belong to the same subject (400 `INVALID_PARENT_TOPIC`). Writes a "
        "`topic.create` audit entry. Requires the `exam.create` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND, **_BAD_REQUEST},
    dependencies=[Depends(require_permission("exam.create"))],
)
def create_topic(
    payload: TopicCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Topic:
    """Create a topic, optionally nested under a parent of the same subject."""
    return exam_service.create_topic(
        db, payload, user_id=current_user.id, request=request
    )


@router.get(
    "/{topic_id}",
    response_model=TopicResponse,
    summary="Get topic",
    description=(
        "Return a single topic by numeric ID. 404 `TOPIC_NOT_FOUND` when the "
        "topic does not exist. Requires the `exam.view` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND},
    dependencies=[Depends(require_permission("exam.view"))],
)
def get_topic(
    topic_id: int = Path(..., ge=1, description="Unique topic ID."),
    db: Session = Depends(get_db),
) -> Topic:
    """Fetch one topic by ID."""
    return exam_service.get_topic(db, topic_id)


@router.put(
    "/{topic_id}",
    response_model=TopicResponse,
    summary="Update topic",
    description=(
        "Apply the provided (non-null) fields to the topic. A supplied "
        "`parent_topic_id` is re-validated: it must exist, belong to the same "
        "subject and not create a hierarchy cycle (400 `INVALID_PARENT_TOPIC`). "
        "Writes an audit entry with the old and new values. "
        "Requires the `exam.update` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND, **_BAD_REQUEST},
    dependencies=[Depends(require_permission("exam.update"))],
)
def update_topic(
    payload: TopicUpdate,
    request: Request,
    topic_id: int = Path(..., ge=1, description="Unique topic ID."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Topic:
    """Update the mutable fields of an existing topic."""
    return exam_service.update_topic(
        db, topic_id, payload, user_id=current_user.id, request=request
    )


@router.delete(
    "/{topic_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete topic",
    description=(
        "Remove a topic. When it still owns child topics or questions it is "
        "only soft-deactivated (`is_active=false`, action `deactivate`); an "
        "empty topic is hard-deleted (action `delete`). Both paths are "
        "audited. Requires the `exam.delete` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND},
    dependencies=[Depends(require_permission("exam.delete"))],
)
def delete_topic(
    request: Request,
    topic_id: int = Path(..., ge=1, description="Unique topic ID."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Soft-deactivate or hard-delete a topic depending on its contents."""
    exam_service.delete_topic(
        db, topic_id, user_id=current_user.id, request=request
    )
