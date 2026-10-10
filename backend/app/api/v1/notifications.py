"""Notification endpoints.

Mounted at ``/api/v1/notifications`` by ``app.api.v1.router``. Listing is
restricted to the caller's own notifications unless the caller explicitly
requests everyone's (``all=true``) *and* holds the ``notification.create``
permission.
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Path, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.permissions import has_any_permission, require_permission
from app.db.session import get_db
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import (
    NotificationBulkCreate,
    NotificationCreate,
    NotificationResponse,
)
from app.services import notification_service
from app.utils.pagination import Page, PaginationParams

router = APIRouter()


class UnreadCountResponse(BaseModel):
    """Unread notification counter for the authenticated user."""

    count: int = Field(..., description="Number of unread notifications of the caller.")


class ReadAllResponse(BaseModel):
    """Result of marking every own notification as read."""

    updated: int = Field(..., description="Notifications flipped from unread to read.")


class NotificationBulkCreateResponse(BaseModel):
    """Result of a bulk notification creation."""

    created: int = Field(..., description="Notifications actually created.")
    skipped: int = Field(..., description="Requested user ids that do not exist.")


@router.get(
    "/",
    response_model=Page[NotificationResponse],
    summary="List notifications",
    description=(
        "Paginated notifications of the caller. Pass ``all=true`` to list every "
        "user's notifications; that mode only takes effect when the caller also "
        "holds the ``notification.create`` permission, otherwise the listing "
        "stays restricted to the caller's own rows. Supports the ``is_read``, "
        "``type`` and ``search`` filters plus the standard pagination/sorting "
        "parameters (default order: ``created_at`` descending)."
    ),
    responses={
        401: {"description": "Not authenticated."},
        403: {"description": "Account is not active."},
        404: {"description": "Resource not found."},
    },
)
def list_notifications(
    all_users: bool = Query(
        False,
        alias="all",
        description="Request everyone's notifications (requires notification.create).",
    ),
    is_read: Optional[bool] = Query(None, description="Filter by read state."),
    notification_type: Optional[str] = Query(
        None, alias="type", max_length=30, description="Filter by notification type."
    ),
    params: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Return one page of notifications visible to the caller."""
    include_all = all_users and has_any_permission(
        db, current_user, ["notification.create"]
    )
    return notification_service.list_notifications(
        db,
        params,
        viewer_id=current_user.id,
        include_all=include_all,
        is_read=is_read,
        notification_type=notification_type,
    )


@router.get(
    "/unread-count",
    response_model=UnreadCountResponse,
    summary="Unread notification count",
    description=(
        "Number of unread notifications belonging to the authenticated user. "
        "Any authenticated user may call this endpoint - no extra permission "
        "is required."
    ),
    responses={
        401: {"description": "Not authenticated."},
        403: {"description": "Account is not active."},
        404: {"description": "Resource not found."},
    },
)
def unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UnreadCountResponse:
    """Return the caller's unread notification counter."""
    return UnreadCountResponse(count=notification_service.count_unread(db, current_user.id))


@router.patch(
    "/read-all",
    response_model=ReadAllResponse,
    summary="Mark all own notifications as read",
    description=(
        "Flips ``is_read`` to ``true`` for every unread notification of the "
        "authenticated user and reports how many rows changed. Other users' "
        "notifications are never touched."
    ),
    responses={
        401: {"description": "Not authenticated."},
        403: {"description": "Account is not active."},
        404: {"description": "Resource not found."},
    },
)
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReadAllResponse:
    """Mark all of the caller's notifications as read."""
    updated = notification_service.mark_all_read(db, current_user.id)
    return ReadAllResponse(updated=updated)


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    summary="Mark a notification as read",
    description=(
        "Sets ``is_read`` to ``true`` for one of the caller's own "
        "notifications. The operation is idempotent - repeating it still "
        "returns 200 with the current state. Notifications owned by other "
        "users (or unknown ids) return 404 ``NOTIFICATION_NOT_FOUND``."
    ),
    responses={
        401: {"description": "Not authenticated."},
        403: {"description": "Account is not active."},
        404: {"description": "Notification not found or owned by another user."},
    },
)
def mark_notification_read(
    notification_id: int = Path(..., description="Id of the notification to mark read."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Notification:
    """Mark one of the caller's notifications as read (idempotent)."""
    notification = notification_service.get_owned_notification(
        db, notification_id, owner_id=current_user.id
    )
    return notification_service.mark_read(db, notification)


@router.post(
    "/",
    response_model=NotificationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a notification",
    description=(
        "Creates a single in-app notification for ``user_id`` inside one "
        "transaction and writes a ``notification``/``create`` audit entry. The "
        "target user must exist, otherwise 404 ``USER_NOT_FOUND`` is returned."
    ),
    responses={
        401: {"description": "Not authenticated."},
        403: {"description": "Missing the ``notification.create`` permission."},
        404: {"description": "Target user not found."},
    },
    dependencies=[Depends(require_permission("notification.create"))],
)
def create_notification(
    payload: NotificationCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Notification:
    """Create one notification for a user."""
    return notification_service.create_notification(
        db, payload, actor_id=current_user.id, request=request
    )


@router.post(
    "/bulk",
    response_model=NotificationBulkCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Bulk create notifications",
    description=(
        "Creates one identical notification for each requested user id in a "
        "single transaction. Ids without a matching user are skipped and "
        "reported under ``skipped``. One audit entry records the resulting "
        "counts."
    ),
    responses={
        401: {"description": "Not authenticated."},
        403: {"description": "Missing the ``notification.create`` permission."},
        404: {"description": "Resource not found."},
    },
    dependencies=[Depends(require_permission("notification.create"))],
)
def bulk_create_notifications(
    payload: NotificationBulkCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationBulkCreateResponse:
    """Create notifications for many users at once."""
    counts = notification_service.create_notifications_bulk(
        db, payload, actor_id=current_user.id, request=request
    )
    return NotificationBulkCreateResponse(**counts)
