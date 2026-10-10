"""Runtime settings endpoints - admin CRUD plus the public subset.

Mounted by ``app.api.v1.router`` at ``/api/v1/settings``; every path below is
relative to that prefix. Settings are addressed by their canonical key
(``^[a-z0-9_.\\-]{2,100}$``) and are always stored as text. The response and
request models are defined locally in this module (no shared schema file is
added). Mutations delegate to ``app.services.setting_service`` which owns the
transaction and the audit entry.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Path, Request, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.permissions import require_permission
from app.db.session import get_db
from app.models.setting import Setting
from app.models.user import User
from app.schemas.common import ErrorResponse
from app.services import setting_service

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
        "description": "Setting not found (SETTING_NOT_FOUND).",
        "model": ErrorResponse,
    }
}
_BAD_REQUEST: Dict[int, Dict[str, Any]] = {
    400: {
        "description": (
            "Malformed setting key (INVALID_SETTING_KEY); keys must match "
            "^[a-z0-9_.\\-]{2,100}$."
        ),
        "model": ErrorResponse,
    }
}


class SettingResponse(BaseModel):
    """Serialised runtime setting row."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    setting_key: str
    setting_value: Optional[str] = None
    description: Optional[str] = None
    is_public: bool
    updated_by: Optional[int] = None
    updated_at: Optional[datetime] = None


class SettingUpdateRequest(BaseModel):
    """Body of ``PUT /settings/{setting_key}`` (upsert).

    ``description`` and ``is_public`` are only applied when the client
    actually sends them; an explicit ``null`` description clears it.
    """

    setting_value: str = Field(..., description="New value, stored as text.")
    description: Optional[str] = Field(
        None, description="Optional human-readable description."
    )
    is_public: Optional[bool] = Field(
        None, description="Whether the setting is exposed on GET /settings/public."
    )


@router.get(
    "/",
    response_model=List[SettingResponse],
    summary="List settings",
    description=(
        "Return every runtime setting ordered by key (public and private). "
        "Requires the `settings.view` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND},
    dependencies=[Depends(require_permission("settings.view"))],
)
def list_settings(db: Session = Depends(get_db)) -> List[Setting]:
    """Return all settings ordered by their key."""
    return setting_service.list_settings(db, public_only=False)


@router.get(
    "/public",
    response_model=List[SettingResponse],
    summary="List public settings",
    description=(
        "Return only settings flagged `is_public=true`, ordered by key. "
        "Available to any authenticated user; no permission is required."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND},
    dependencies=[Depends(get_current_user)],
)
def list_public_settings(db: Session = Depends(get_db)) -> List[Setting]:
    """Return the public subset of settings for an authenticated user."""
    return setting_service.list_settings(db, public_only=True)


@router.get(
    "/{setting_key}",
    response_model=SettingResponse,
    summary="Get setting",
    description=(
        "Return a single setting by its canonical key. Malformed keys return "
        "400 `INVALID_SETTING_KEY`, unknown keys 404 `SETTING_NOT_FOUND`. "
        "Requires the `settings.view` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND, **_BAD_REQUEST},
    dependencies=[Depends(require_permission("settings.view"))],
)
def get_setting(
    setting_key: str = Path(
        ...,
        description="Canonical setting key (^[a-z0-9_.\\-]{2,100}$).",
    ),
    db: Session = Depends(get_db),
) -> Setting:
    """Fetch one setting by key, validating the key format first."""
    setting_service.validate_setting_key(setting_key)
    return setting_service.get_setting(db, setting_key)


@router.put(
    "/{setting_key}",
    response_model=SettingResponse,
    summary="Create or update setting",
    description=(
        "Upsert a setting by key: creates it when absent (audit action "
        "`create`) or updates it in place (audit action `update` with "
        "`old_data`/`new_data`). Only the fields present in the body are "
        "applied on update. Malformed keys return 400 `INVALID_SETTING_KEY`. "
        "Requires the `settings.update` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND, **_BAD_REQUEST},
    dependencies=[Depends(require_permission("settings.update"))],
)
def upsert_setting(
    payload: SettingUpdateRequest,
    request: Request,
    setting_key: str = Path(
        ...,
        description="Canonical setting key (^[a-z0-9_.\\-]{2,100}$).",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Setting:
    """Create the setting when new, otherwise update the existing row."""
    setting_service.validate_setting_key(setting_key)
    setting, _action = setting_service.upsert_setting(
        db,
        setting_key,
        payload=payload,
        actor_id=current_user.id,
        request=request,
    )
    return setting


@router.delete(
    "/{setting_key}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete setting",
    description=(
        "Remove a setting by key. Writes a `delete` audit entry before the "
        "row is removed. Malformed keys return 400 `INVALID_SETTING_KEY`, "
        "unknown keys 404 `SETTING_NOT_FOUND`. Requires the `settings.update` "
        "permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND, **_BAD_REQUEST},
    dependencies=[Depends(require_permission("settings.update"))],
)
def delete_setting(
    request: Request,
    setting_key: str = Path(
        ...,
        description="Canonical setting key (^[a-z0-9_.\\-]{2,100}$).",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete an existing setting after validating its key."""
    setting_service.validate_setting_key(setting_key)
    setting = setting_service.get_setting(db, setting_key)
    setting_service.delete_setting(
        db,
        setting,
        actor_id=current_user.id,
        request=request,
    )
