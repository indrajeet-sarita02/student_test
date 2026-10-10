"""Domain logic for in-app notifications.

Read helpers build the statements consumed by the API layer; mutations own
their transaction: they ``flush`` to obtain ids and call ``commit`` only after
every step (payload validation and the audit entry) has succeeded.
"""

from typing import Any, Dict, Optional, Set

from fastapi import Request
from sqlalchemy import Select, asc, desc, func, or_, select, update
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationBulkCreate, NotificationCreate
from app.services.audit_service import record_audit
from app.utils.pagination import PaginationParams, paginate

# Columns whitelisted for ``?sort_by=`` on the list endpoint.
SORTABLE_COLUMNS: Set[str] = {"id", "created_at", "is_read", "title"}


def _apply_sort(stmt: Select, params: PaginationParams) -> Select:
    """Apply whitelisted sorting.

    Unknown or absent ``sort_by`` values fall back to ``created_at`` descending
    (newest first) and the primary key is always used as a tie-breaker so
    pagination stays stable.
    """
    if params.sort_by in SORTABLE_COLUMNS:
        column = getattr(Notification, params.sort_by)
        direction = desc if params.sort_order == "desc" else asc
    else:
        column, direction = Notification.created_at, desc
    return stmt.order_by(direction(column), direction(Notification.id))


def list_notifications(
    db: Session,
    params: PaginationParams,
    *,
    viewer_id: int,
    include_all: bool = False,
    is_read: Optional[bool] = None,
    notification_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Paginated notification listing, restricted to ``viewer_id`` unless
    ``include_all`` is set by the caller.

    Filters: ``is_read`` (exact), ``type`` (case-insensitive exact) and the
    shared ``search`` keyword against title/message.
    """
    stmt = select(Notification)
    if not include_all:
        stmt = stmt.where(Notification.user_id == viewer_id)
    if is_read is not None:
        stmt = stmt.where(Notification.is_read.is_(bool(is_read)))
    if notification_type and notification_type.strip():
        stmt = stmt.where(
            func.upper(Notification.type) == notification_type.strip().upper()
        )
    if params.search:
        pattern = f"%{params.search}%"
        stmt = stmt.where(
            or_(
                Notification.title.ilike(pattern),
                Notification.message.ilike(pattern),
            )
        )
    return paginate(db, _apply_sort(stmt, params), params)


def count_unread(db: Session, user_id: int) -> int:
    """Number of unread notifications belonging to ``user_id``."""
    total = db.scalar(
        select(func.count())
        .select_from(Notification)
        .where(Notification.user_id == user_id, Notification.is_read.is_(False))
    )
    return int(total or 0)


def get_owned_notification(db: Session, notification_id: int, *, owner_id: int) -> Notification:
    """Fetch a notification that must belong to ``owner_id``.

    Raises ``NotFoundError`` with code ``NOTIFICATION_NOT_FOUND`` when the row
    does not exist or belongs to somebody else (never leak other users' rows).
    """
    notification = db.scalar(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == owner_id,
        )
    )
    if notification is None:
        raise NotFoundError(
            "Notification was not found.",
            code="NOTIFICATION_NOT_FOUND",
            details={"notification_id": notification_id},
        )
    return notification


def mark_read(db: Session, notification: Notification) -> Notification:
    """Idempotently set ``is_read`` on an already-loaded notification.

    Marking an already-read notification simply returns the current state
    without writing anything.
    """
    if not notification.is_read:
        notification.is_read = True
        db.flush()
        db.commit()
    return notification


def mark_all_read(db: Session, user_id: int) -> int:
    """Mark every unread notification of ``user_id`` as read.

    Returns the number of rows actually flipped to ``is_read = true``.
    """
    result = db.execute(
        update(Notification)
        .where(Notification.user_id == user_id, Notification.is_read.is_(False))
        .values(is_read=True)
    )
    db.commit()
    return int(result.rowcount or 0)


def create_notification(
    db: Session,
    payload: NotificationCreate,
    *,
    actor_id: int,
    request: Request,
) -> Notification:
    """Create one notification for ``payload.user_id`` and audit the change.

    Raises ``NotFoundError`` with code ``USER_NOT_FOUND`` when the target user
    does not exist. Commits only after the audit entry has been flushed.
    """
    target = db.get(User, payload.user_id)
    if target is None:
        raise NotFoundError(
            f"User {payload.user_id} was not found.",
            code="USER_NOT_FOUND",
            details={"user_id": payload.user_id},
        )

    notification = Notification(
        user_id=target.id,
        title=payload.title,
        message=payload.message,
        type=payload.type.value,
        is_read=False,
    )
    db.add(notification)
    db.flush()
    record_audit(
        db,
        user_id=actor_id,
        module="notification",
        action="create",
        entity_type="notification",
        entity_id=notification.id,
        new_data={
            "user_id": notification.user_id,
            "title": notification.title,
            "message": notification.message,
            "type": notification.type,
        },
        request=request,
    )
    db.commit()
    return notification


def create_notifications_bulk(
    db: Session,
    payload: NotificationBulkCreate,
    *,
    actor_id: int,
    request: Request,
) -> Dict[str, int]:
    """Create one notification per requested user id in a single transaction.

    Ids that do not resolve to an existing user are skipped and reported under
    ``skipped``; a single audit entry records the resulting counts.
    """
    existing_ids = set(
        db.scalars(select(User.id).where(User.id.in_(payload.user_ids))).all()
    )

    created = 0
    skipped = 0
    for user_id in payload.user_ids:
        if user_id not in existing_ids:
            skipped += 1
            continue
        db.add(
            Notification(
                user_id=user_id,
                title=payload.title,
                message=payload.message,
                type=payload.type.value,
                is_read=False,
            )
        )
        created += 1

    db.flush()
    record_audit(
        db,
        user_id=actor_id,
        module="notification",
        action="create",
        entity_type="notification",
        new_data={
            "created": created,
            "skipped": skipped,
            "title": payload.title,
            "type": payload.type.value,
            "requested": len(payload.user_ids),
        },
        request=request,
    )
    db.commit()
    return {"created": created, "skipped": skipped}
