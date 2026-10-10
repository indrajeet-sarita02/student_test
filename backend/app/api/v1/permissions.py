"""Permission catalogue endpoints mounted at ``/api/v1/permissions``.

Every path below is relative to the prefix declared in
``app.api.v1.router``.  The catalogue is read-only and is exposed so the
frontend can render role/permission matrices; both endpoints require the
``permission.view`` permission.
"""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.permissions import require_permission
from app.db.session import get_db
from app.models.permission import Permission
from app.schemas.common import ErrorResponse
from app.schemas.permission import PermissionModuleResponse, PermissionResponse
from app.services import role_service

router = APIRouter()

_UNAUTHORIZED = {
    401: {
        "description": "Missing, expired or invalid access token.",
        "model": ErrorResponse,
    }
}
_FORBIDDEN = {
    403: {
        "description": "Authenticated user lacks the required permission.",
        "model": ErrorResponse,
    }
}
_NOT_FOUND = {
    404: {"description": "Resource not found.", "model": ErrorResponse}
}


@router.get(
    "/",
    response_model=List[PermissionResponse],
    summary="List permissions",
    description=(
        "Return the full permission catalogue ordered by module, then action. "
        "Requires the `permission.view` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND},
    dependencies=[Depends(require_permission("permission.view"))],
)
def list_permissions(db: Session = Depends(get_db)) -> List[Permission]:
    """Return every permission ordered by module and action."""
    return role_service.list_permissions(db)


@router.get(
    "/modules",
    response_model=List[PermissionModuleResponse],
    summary="List permissions grouped by module",
    description=(
        "Return the permission catalogue grouped by module, with the modules "
        "and their permissions sorted alphabetically. Requires the "
        "`permission.view` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND},
    dependencies=[Depends(require_permission("permission.view"))],
)
def list_permission_modules(
    db: Session = Depends(get_db),
) -> List[PermissionModuleResponse]:
    """Return the permission catalogue grouped by module."""
    return role_service.list_permission_modules(db)
