"""Role administration endpoints mounted at ``/api/v1/roles``.

Every path below is relative to the prefix declared in
``app.api.v1.router``.  Role mutations are guarded by the ``role.*`` RBAC
permission codes; system roles are protected from deletion and roles that are
still assigned to users cannot be removed.
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends, Path, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.permissions import require_permission
from app.db.session import get_db
from app.models.role import Role
from app.models.user import User
from app.schemas.common import ErrorResponse
from app.schemas.role import RoleCreate, RolePermissionsUpdate, RoleResponse, RoleUpdate
from app.services import role_service
from app.utils.pagination import Page, PaginationParams

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
    404: {"description": "Role not found (ROLE_NOT_FOUND).", "model": ErrorResponse}
}
_CONFLICT: Dict[int, Dict[str, Any]] = {
    409: {
        "description": "Role code already exists (ROLE_CODE_EXISTS), the role "
        "is a protected system role (SYSTEM_ROLE) or it is still assigned to "
        "users (ROLE_IN_USE).",
        "model": ErrorResponse,
    }
}
_BAD_REQUEST: Dict[int, Dict[str, Any]] = {
    400: {
        "description": "Unsupported `sort_by` (INVALID_SORT_BY) or one or more "
        "permission ids do not exist (PERMISSION_NOT_FOUND).",
        "model": ErrorResponse,
    }
}


@router.get(
    "/",
    response_model=Page[RoleResponse],
    summary="List roles",
    description=(
        "Return a paginated, sortable list of roles with their permissions. "
        "Supports the shared `search` keyword over the role name and code. "
        "Sortable by id, name, code and created_at; the default order is "
        "`name` ascending. Requires the `role.view` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND, **_BAD_REQUEST},
    dependencies=[Depends(require_permission("role.view"))],
)
def list_roles(
    db: Session = Depends(get_db),
    params: PaginationParams = Depends(),
) -> Any:
    """List roles with pagination and free-text search."""
    return role_service.list_roles(db, params)


@router.post(
    "/",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create role",
    description=(
        "Create a role with a unique `code` (409 `ROLE_CODE_EXISTS`) and an "
        "initial set of `permission_ids` (400 `PERMISSION_NOT_FOUND` when any "
        "id is unknown). Writes a `role.create` audit entry. Requires the "
        "`role.create` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_CONFLICT, **_BAD_REQUEST},
    dependencies=[Depends(require_permission("role.create"))],
)
def create_role(
    payload: RoleCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Role:
    """Create a role and attach its initial permissions."""
    return role_service.create_role(
        db, payload, actor_id=current_user.id, request=request
    )


@router.get(
    "/{role_id}",
    response_model=RoleResponse,
    summary="Get role",
    description=(
        "Return a single role including its permission list. Unknown ids "
        "return 404 `ROLE_NOT_FOUND`. Requires the `role.view` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND},
    dependencies=[Depends(require_permission("role.view"))],
)
def get_role(
    role_id: int = Path(..., ge=1, description="Unique role ID."),
    db: Session = Depends(get_db),
) -> Role:
    """Fetch one role by numeric ID."""
    return role_service.get_role(db, role_id)


@router.put(
    "/{role_id}",
    response_model=RoleResponse,
    summary="Update role",
    description=(
        "Update the mutable `name`, `description` and `is_active` fields. The "
        "`code` is immutable, which protects system roles. Writes an audit "
        "entry with the old and new values. Unknown ids return 404 "
        "`ROLE_NOT_FOUND`. Requires the `role.update` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND},
    dependencies=[Depends(require_permission("role.update"))],
)
def update_role(
    payload: RoleUpdate,
    request: Request,
    role_id: int = Path(..., ge=1, description="Unique role ID."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Role:
    """Update the mutable fields of an existing role."""
    return role_service.update_role(
        db, role_id, payload, actor_id=current_user.id, request=request
    )


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete role",
    description=(
        "Delete an unused role. System roles are protected (409 `SYSTEM_ROLE`) "
        "and roles still assigned to users cannot be removed (409 "
        "`ROLE_IN_USE`). Writes a `role.delete` audit entry. Unknown ids return "
        "404 `ROLE_NOT_FOUND`. Requires the `role.delete` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND, **_CONFLICT},
    dependencies=[Depends(require_permission("role.delete"))],
)
def delete_role(
    request: Request,
    role_id: int = Path(..., ge=1, description="Unique role ID."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a role that is neither a system role nor assigned to users."""
    role_service.delete_role(db, role_id, actor_id=current_user.id, request=request)


@router.put(
    "/{role_id}/permissions",
    response_model=RoleResponse,
    summary="Set role permissions",
    description=(
        "Replace the role's entire permission set with `permission_ids`. An "
        "empty list removes every permission; unknown ids raise 400 "
        "`PERMISSION_NOT_FOUND`. Writes a `role.update` audit entry. Unknown "
        "role ids return 404 `ROLE_NOT_FOUND`. Requires the `role.update` "
        "permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND, **_BAD_REQUEST},
    dependencies=[Depends(require_permission("role.update"))],
)
def set_role_permissions(
    payload: RolePermissionsUpdate,
    request: Request,
    role_id: int = Path(..., ge=1, description="Unique role ID."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Role:
    """Replace the permission set of an existing role."""
    return role_service.update_role_permissions(
        db, role_id, payload, actor_id=current_user.id, request=request
    )
