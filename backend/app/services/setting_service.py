"""Domain logic for runtime settings (key/value configuration).

Settings are addressed by their canonical key (``^[a-z0-9_.\\-]{2,100}$``).
Mutations own their transaction: ids are obtained with ``flush`` and the
session commits only after the audit entry has been written.
"""

import re
from typing import Any, Dict, List, Optional, Protocol, Set, Tuple

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.models.setting import Setting
from app.services.audit_service import record_audit

# Canonical setting-key format enforced on every write.
SETTING_KEY_PATTERN = re.compile(r"^[a-z0-9_.\-]{2,100}$")


class SettingUpdatePayload(Protocol):
    """Structural contract of the PUT body.

    Declared here so this module never imports the API layer; optional fields
    are applied only when the client actually sent them (``model_fields_set``).
    """

    setting_value: str
    description: Optional[str]
    is_public: Optional[bool]
    model_fields_set: Set[str]


def validate_setting_key(setting_key: str) -> str:
    """Return ``setting_key`` when it matches the canonical pattern.

    Raises ``BadRequestError`` with code ``INVALID_SETTING_KEY`` otherwise.
    """
    if not isinstance(setting_key, str) or SETTING_KEY_PATTERN.match(setting_key) is None:
        raise BadRequestError(
            "Setting key must match ^[a-z0-9_.\\-]{2,100}$ "
            "(lowercase letters, digits, '_', '.', '-'; 2-100 characters).",
            code="INVALID_SETTING_KEY",
            details={"setting_key": setting_key},
        )
    return setting_key


def _snapshot(setting: Setting) -> Dict[str, Any]:
    """JSON-friendly before/after snapshot used for audit entries."""
    return {
        "setting_key": setting.setting_key,
        "setting_value": setting.setting_value,
        "description": setting.description,
        "is_public": setting.is_public,
        "updated_by": setting.updated_by,
    }


def list_settings(db: Session, *, public_only: bool = False) -> List[Setting]:
    """All settings ordered by key; optionally only the public ones."""
    stmt = select(Setting)
    if public_only:
        stmt = stmt.where(Setting.is_public.is_(True))
    stmt = stmt.order_by(Setting.setting_key.asc(), Setting.id.asc())
    return list(db.scalars(stmt).all())


def get_setting(db: Session, setting_key: str) -> Setting:
    """Fetch a setting by key or raise ``SETTING_NOT_FOUND`` (404)."""
    setting = db.scalar(select(Setting).where(Setting.setting_key == setting_key))
    if setting is None:
        raise NotFoundError(
            f"Setting '{setting_key}' was not found.",
            code="SETTING_NOT_FOUND",
            details={"setting_key": setting_key},
        )
    return setting


def upsert_setting(
    db: Session,
    setting_key: str,
    *,
    payload: SettingUpdatePayload,
    actor_id: int,
    request: Request,
) -> Tuple[Setting, str]:
    """Create the setting when the key is new, otherwise update it in place.

    Only the fields present in ``payload.model_fields_set`` are applied on
    update (``description: null`` clears the description); omitted fields keep
    their current value. Returns the setting plus the audit action performed
    (``"create"`` or ``"update"``).

    Raises ``INVALID_SETTING_KEY`` (400) for malformed keys and, on a rare
    concurrent-insert race for the unique key, ``SETTING_KEY_EXISTS`` (409).
    """
    validate_setting_key(setting_key)
    setting = db.scalar(select(Setting).where(Setting.setting_key == setting_key))

    if setting is None:
        setting = Setting(
            setting_key=setting_key,
            setting_value=payload.setting_value,
            description=payload.description,
            is_public=bool(payload.is_public)
            if payload.is_public is not None
            else False,
            updated_by=actor_id,
        )
        db.add(setting)
        try:
            db.flush()
        except IntegrityError as exc:  # unique(setting_key) raced with a concurrent insert
            db.rollback()
            raise ConflictError(
                f"Setting key '{setting_key}' already exists.",
                code="SETTING_KEY_EXISTS",
                details={"setting_key": setting_key},
            ) from exc
        record_audit(
            db,
            user_id=actor_id,
            module="settings",
            action="create",
            entity_type="setting",
            entity_id=setting.id,
            new_data=_snapshot(setting),
            request=request,
        )
        db.commit()
        return setting, "create"

    old_data = _snapshot(setting)
    setting.setting_value = payload.setting_value
    if "description" in payload.model_fields_set:
        setting.description = payload.description
    if "is_public" in payload.model_fields_set and payload.is_public is not None:
        setting.is_public = payload.is_public
    setting.updated_by = actor_id
    db.flush()
    record_audit(
        db,
        user_id=actor_id,
        module="settings",
        action="update",
        entity_type="setting",
        entity_id=setting.id,
        old_data=old_data,
        new_data=_snapshot(setting),
        request=request,
    )
    db.commit()
    return setting, "update"


def delete_setting(
    db: Session,
    setting: Setting,
    *,
    actor_id: int,
    request: Request,
) -> None:
    """Remove a setting; the audit entry is written in the same transaction."""
    record_audit(
        db,
        user_id=actor_id,
        module="settings",
        action="delete",
        entity_type="setting",
        entity_id=setting.id,
        old_data=_snapshot(setting),
        request=request,
    )
    db.delete(setting)
    db.commit()
