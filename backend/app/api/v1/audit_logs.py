"""Audit log endpoints.

Mounted at ``/api/v1/audit-logs`` by ``app.api.v1.router``. The response model
is defined locally in this module (no shared schema file is added).
"""

from datetime import date, datetime, time, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Path, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Select, asc, desc, func, or_, select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.core.permissions import require_permission
from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.utils.pagination import Page, PaginationParams, paginate

router = APIRouter()

# Columns whitelisted for ``?sort_by=`` on the list endpoint.
SORTABLE_COLUMNS = {"id", "created_at", "module", "action"}


class AuditLogResponse(BaseModel):
    """Serialised audit-log row including the acting user's username."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: Optional[int] = None
    username: Optional[str] = Field(None, description="Username of the acting user.")
    module: str
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    old_data: Optional[Any] = None
    new_data: Optional[Any] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: Optional[datetime] = None


def _start_of_day(value: date) -> datetime:
    """Lower bound of an inclusive UTC date filter."""
    return datetime.combine(value, time.min, tzinfo=timezone.utc)


def _end_of_day(value: date) -> datetime:
    """Upper bound of an inclusive UTC date filter."""
    return datetime.combine(value, time.max, tzinfo=timezone.utc)


def _apply_sort(stmt: Select, params: PaginationParams) -> Select:
    """Apply whitelisted sorting.

    Unknown or absent ``sort_by`` values fall back to ``created_at``
    descending; the primary key is always used as a tie-breaker.
    """
    if params.sort_by in SORTABLE_COLUMNS:
        column = getattr(AuditLog, params.sort_by)
        direction = desc if params.sort_order == "desc" else asc
    else:
        column, direction = AuditLog.created_at, desc
    return stmt.order_by(direction(column), direction(AuditLog.id))


def _build_statement(
    params: PaginationParams,
    *,
    module: Optional[str],
    action: Optional[str],
    entity_type: Optional[str],
    entity_id: Optional[int],
    user_id: Optional[int],
    date_from: Optional[date],
    date_to: Optional[date],
) -> Select:
    """Assemble the filtered ``SELECT`` for the audit-log listing."""
    stmt = select(AuditLog).outerjoin(AuditLog.user)

    if module and module.strip():
        stmt = stmt.where(func.lower(AuditLog.module) == module.strip().lower())
    if action and action.strip():
        stmt = stmt.where(func.lower(AuditLog.action) == action.strip().lower())
    if entity_type and entity_type.strip():
        stmt = stmt.where(
            func.lower(AuditLog.entity_type) == entity_type.strip().lower()
        )
    if entity_id is not None:
        stmt = stmt.where(AuditLog.entity_id == entity_id)
    if user_id is not None:
        stmt = stmt.where(AuditLog.user_id == user_id)
    if date_from is not None:
        stmt = stmt.where(AuditLog.created_at >= _start_of_day(date_from))
    if date_to is not None:
        stmt = stmt.where(AuditLog.created_at <= _end_of_day(date_to))
    if params.search:
        pattern = f"%{params.search}%"
        stmt = stmt.where(
            or_(
                AuditLog.module.ilike(pattern),
                AuditLog.action.ilike(pattern),
                AuditLog.entity_type.ilike(pattern),
                AuditLog.ip_address.ilike(pattern),
                User.username.ilike(pattern),
            )
        )
    return stmt


def _serialize(log: AuditLog) -> Dict[str, Any]:
    """Convert an ORM audit row into the API payload (joins the username)."""
    return {
        "id": log.id,
        "user_id": log.user_id,
        "username": log.user.username if log.user is not None else None,
        "module": log.module,
        "action": log.action,
        "entity_type": log.entity_type,
        "entity_id": log.entity_id,
        "old_data": log.old_data,
        "new_data": log.new_data,
        "ip_address": log.ip_address,
        "user_agent": log.user_agent,
        "created_at": log.created_at,
    }


def _get_audit_log_or_404(db: Session, audit_id: int) -> AuditLog:
    """Fetch one audit row or raise ``AUDIT_LOG_NOT_FOUND`` (404)."""
    log = db.get(AuditLog, audit_id)
    if log is None:
        raise NotFoundError(
            "Audit log entry was not found.",
            code="AUDIT_LOG_NOT_FOUND",
            details={"audit_id": audit_id},
        )
    return log


@router.get(
    "/",
    response_model=Page[AuditLogResponse],
    summary="List audit log entries",
    description=(
        "Paginated audit trail with filters for ``module``, ``action``, "
        "``entity_type``, ``entity_id``, ``user_id``, the inclusive "
        "``date_from``/``date_to`` window on ``created_at`` (UTC) and the "
        "shared ``search`` keyword (module, action, entity type, IP address or "
        "username). Default order: ``created_at`` descending."
    ),
    responses={
        401: {"description": "Not authenticated."},
        403: {"description": "Missing the ``audit.view`` permission."},
        404: {"description": "Resource not found."},
    },
    dependencies=[Depends(require_permission("audit.view"))],
)
def list_audit_logs(
    module: Optional[str] = Query(None, max_length=50, description="Filter by module."),
    action: Optional[str] = Query(None, max_length=50, description="Filter by action."),
    entity_type: Optional[str] = Query(
        None, max_length=50, description="Filter by entity type."
    ),
    entity_id: Optional[int] = Query(None, description="Filter by entity id."),
    user_id: Optional[int] = Query(None, description="Filter by acting user id."),
    date_from: Optional[date] = Query(
        None, description="Inclusive lower bound (UTC) on created_at."
    ),
    date_to: Optional[date] = Query(
        None, description="Inclusive upper bound (UTC) on created_at."
    ),
    params: PaginationParams = Depends(),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Return one page of matching audit-log entries."""
    stmt = _build_statement(
        params,
        module=module,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=user_id,
        date_from=date_from,
        date_to=date_to,
    )
    page = paginate(db, _apply_sort(stmt, params), params)
    page["items"] = [_serialize(row) for row in page["items"]]
    return page


@router.get(
    "/{audit_id}",
    response_model=AuditLogResponse,
    summary="Get an audit log entry",
    description=(
        "Single audit-log entry including the acting user's username and the "
        "recorded ``old_data``/``new_data`` snapshots. Unknown ids return 404 "
        "``AUDIT_LOG_NOT_FOUND``."
    ),
    responses={
        401: {"description": "Not authenticated."},
        403: {"description": "Missing the ``audit.view`` permission."},
        404: {"description": "Audit log entry not found."},
    },
    dependencies=[Depends(require_permission("audit.view"))],
)
def get_audit_log(
    audit_id: int = Path(..., description="Id of the audit-log entry."),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Return one audit-log entry by id."""
    return _serialize(_get_audit_log_or_404(db, audit_id))
