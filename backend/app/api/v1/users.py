"""User administration endpoints mounted at ``/api/v1/users``.

Every path below is relative to the prefix declared in
``app.api.v1.router``.  All list/mutation operations are guarded by the
``user.*`` RBAC permission codes resolved server-side; the credentials of a
newly created account are hashed in the service layer and never returned.
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Path, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.permissions import require_permission
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import ErrorResponse
from app.schemas.user import (
    AssignRolesRequest,
    UserCreate,
    UserPermissionsResponse,
    UserResponse,
    UserStatusUpdate,
    UserUpdate,
)
from app.services import user_service
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
    404: {"description": "User not found (USER_NOT_FOUND).", "model": ErrorResponse}
}
_CONFLICT: Dict[int, Dict[str, Any]] = {
    409: {
        "description": "Username or e-mail already in use "
        "(USERNAME_ALREADY_EXISTS / EMAIL_ALREADY_EXISTS).",
        "model": ErrorResponse,
    }
}
_BAD_REQUEST: Dict[int, Dict[str, Any]] = {
    400: {
        "description": "Unsupported `sort_by` (INVALID_SORT_BY) or one or more "
        "role ids do not exist (ROLE_NOT_FOUND / PERMISSION_NOT_FOUND).",
        "model": ErrorResponse,
    }
}


@router.get(
    "/",
    response_model=Page[UserResponse],
    summary="List users",
    description=(
        "Return a paginated, sortable list of users. Supports the shared "
        "`search` keyword (username, e-mail, first or last name), the `status` "
        "filter and the `role_id` filter. Sortable by id, username, email, "
        "created_at and status; the default order is `created_at` descending. "
        "Requires the `user.view` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND, **_BAD_REQUEST},
    dependencies=[Depends(require_permission("user.view"))],
)
def list_users(
    db: Session = Depends(get_db),
    params: PaginationParams = Depends(),
    role_id: Optional[int] = Query(
        None, ge=1, description="Only users holding this role id."
    ),
) -> Any:
    """List users with pagination, search, status and role filters."""
    return user_service.list_users(db, params, role_id=role_id)


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create user",
    description=(
        "Create a user with a unique `username` and `email` (409 "
        "`USERNAME_ALREADY_EXISTS` / `EMAIL_ALREADY_EXISTS`), a hashed "
        "password and the given `role_ids` (400 `ROLE_NOT_FOUND` when any id "
        "is unknown). An optional `student_profile` is created; its payload "
        "alias `class` maps to the model's `class_name`. Writes a `user.create` "
        "audit entry. Requires the `user.create` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_CONFLICT, **_BAD_REQUEST},
    dependencies=[Depends(require_permission("user.create"))],
)
def create_user(
    payload: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    """Create a user with credentials, roles and optional student profile."""
    return user_service.create_user(
        db, payload, actor_id=current_user.id, request=request
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user",
    description=(
        "Return a single user, including their roles and student profile. "
        "Unknown ids return 404 `USER_NOT_FOUND`. Requires the `user.view` "
        "permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND},
    dependencies=[Depends(require_permission("user.view"))],
)
def get_user(
    user_id: int = Path(..., ge=1, description="Unique user ID."),
    db: Session = Depends(get_db),
) -> User:
    """Fetch one user by numeric ID."""
    return user_service.get_user(db, user_id)


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user",
    description=(
        "Apply the provided (non-null) fields to the user, re-hashing the "
        "password when supplied and enforcing e-mail uniqueness (409 "
        "`EMAIL_ALREADY_EXISTS`). A supplied `student_profile` is merged into "
        "the existing profile. Writes an audit entry with the old and new "
        "values. Requires the `user.update` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND, **_CONFLICT},
    dependencies=[Depends(require_permission("user.update"))],
)
def update_user(
    payload: UserUpdate,
    request: Request,
    user_id: int = Path(..., ge=1, description="Unique user ID."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    """Update the mutable fields of an existing user."""
    return user_service.update_user(
        db, user_id, payload, actor_id=current_user.id, request=request
    )


@router.patch(
    "/{user_id}/status",
    response_model=UserResponse,
    summary="Change user status",
    description=(
        "Set the account status (ACTIVE, INACTIVE, SUSPENDED or PENDING). "
        "Writes a `user.status_change` audit entry. Unknown ids return 404 "
        "`USER_NOT_FOUND`. Requires the `user.update` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND},
    dependencies=[Depends(require_permission("user.update"))],
)
def update_user_status(
    payload: UserStatusUpdate,
    request: Request,
    user_id: int = Path(..., ge=1, description="Unique user ID."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    """Switch the account status of an existing user."""
    return user_service.update_user_status(
        db, user_id, payload, actor_id=current_user.id, request=request
    )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user",
    description=(
        "Remove a user. Deleting your own account is rejected with 403 "
        "`SELF_ACTION`. When the user owns exams or questions, "
        "or is the last holder of the SUPER_ADMIN role, the account is instead "
        "deactivated (`status=INACTIVE`, action `deactivate`); otherwise it is "
        "hard-deleted (action `delete`). Both paths are audited. Requires the "
        "`user.delete` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND},
    dependencies=[Depends(require_permission("user.delete"))],
)
def delete_user(
    request: Request,
    user_id: int = Path(..., ge=1, description="Unique user ID."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Hard-delete a user, or deactivate when deletion would lose history."""
    user_service.delete_user(db, user_id, actor_id=current_user.id, request=request)


@router.post(
    "/{user_id}/roles",
    response_model=UserResponse,
    summary="Assign user roles",
    description=(
        "Replace the user's entire role set with `role_ids`. An empty list "
        "removes every role; unknown ids raise 400 `ROLE_NOT_FOUND`. Writes a "
        "`user.update` audit entry. Requires the `user.update` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND, **_BAD_REQUEST},
    dependencies=[Depends(require_permission("user.update"))],
)
def assign_user_roles(
    payload: AssignRolesRequest,
    request: Request,
    user_id: int = Path(..., ge=1, description="Unique user ID."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    """Replace the role set of an existing user."""
    return user_service.assign_roles(
        db, user_id, payload, actor_id=current_user.id, request=request
    )


@router.get(
    "/{user_id}/permissions",
    response_model=UserPermissionsResponse,
    summary="Get user permissions",
    description=(
        "Resolve the effective permission codes the user is granted through "
        "their active roles, together with the role codes themselves. A "
        "SUPER_ADMIN resolves to the wildcard `*`. Unknown ids return 404 "
        "`USER_NOT_FOUND`. Requires the `user.view` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND},
    dependencies=[Depends(require_permission("user.view"))],
)
def get_user_permissions(
    user_id: int = Path(..., ge=1, description="Unique user ID."),
    db: Session = Depends(get_db),
) -> UserPermissionsResponse:
    """Return the resolved permission codes and roles for one user."""
    return user_service.get_user_permissions(db, user_id)
