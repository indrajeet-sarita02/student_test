"""Audit trail helper used by services for administrative operations.

Failures while writing an audit entry must never break the main transaction,
so entries are appended with ``flush`` and any error is swallowed+logged.
"""

import json
import logging
from typing import Any, Dict, Optional

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog

logger = logging.getLogger("student_test.audit")


def _serialise(value: Any) -> Optional[Dict[str, Any]]:
    if value is None:
        return None
    try:
        return json.loads(json.dumps(value, default=str))
    except (TypeError, ValueError):  # pragma: no cover - defensive
        return {"repr": repr(value)}


def record_audit(
    db: Session,
    *,
    user_id: Optional[int],
    module: str,
    action: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    old_data: Optional[Any] = None,
    new_data: Optional[Any] = None,
    request: Optional[Request] = None,
) -> None:
    """Persist one audit row inside the caller's transaction."""
    ip_address = None
    user_agent = None
    if request is not None:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            ip_address = forwarded.split(",")[0].strip()
        elif request.client:
            ip_address = request.client.host
        ua = request.headers.get("user-agent")
        user_agent = ua[:300] if ua else None

    try:
        db.add(
            AuditLog(
                user_id=user_id,
                module=module,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                old_data=_serialise(old_data),
                new_data=_serialise(new_data),
                ip_address=ip_address,
                user_agent=user_agent,
            )
        )
        db.flush()
    except Exception:  # pragma: no cover - audit must not break the operation
        logger.exception("Failed to write audit log for %s.%s", module, action)
