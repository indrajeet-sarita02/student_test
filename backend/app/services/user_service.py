"""User management service: CRUD, role assignment, status and deletion policy.

The service owns each transaction: ids are obtained with ``flush()`` and the
session is committed exactly once at the end of a successful mutation.
"""

from typing import Any, Dict, List, Optional

from fastapi import Request
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.exceptions import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
)
from app.core.permissions import SUPER_ADMIN_ROLE, get_permission_codes
from app.core.security import hash_password
from app.models.profile import StudentProfile
from app.models.role import Role
from app.models.user import User
from app.repositories import user_repository as user_repo
from app.schemas.user import (
    AssignRolesRequest,
    StudentProfileCreate,
    UserCreate,
    UserPermissionsResponse,
    UserStatusUpdate,
    UserUpdate,
)
from app.services.audit_service import record_audit
from app.utils.enums import UserStatus
from app.utils.pagination import PaginationParams, paginate

# Columns exposed to ``?sort_by=`` on the user list endpoint.
_USER_SORTABLE = {
    "id": User.id,
    "username": User.username,
    "email": User.email,
    "created_at": User.created_at,
    "status": User.status,
}
DEFAULT_USER_SORT = "created_at"


def _snapshot(user: User) -> Dict[str, Any]:
    """JSON-friendly view of a user used as audit old/new data."""
    profile = user.student_profile
    return {
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "mobile": user.mobile,
        "status": user.status,
        "is_verified": user.is_verified,
        "roles": [role.code for role in user.roles],
        "student_profile": (
            {
                "student_code": profile.student_code,
                "date_of_birth": profile.date_of_birth,
                "gender": profile.gender,
                "institution": profile.institution,
                "class_name": profile.class_name,
                "roll_number": profile.roll_number,
            }
            if profile
            else None
        ),
    }


def _build_profile(payload: StudentProfileCreate) -> StudentProfile:
    """Map the ``class`` alias (schema attr ``class_name``) onto the ORM model."""
    return StudentProfile(
        student_code=payload.student_code,
        date_of_birth=payload.date_of_birth,
        gender=payload.gender.value if payload.gender else None,
        institution=payload.institution,
        class_name=payload.class_name,
        roll_number=payload.roll_number,
    )


def _resolve_roles(db: Session, role_ids: List[int]) -> List[Role]:
    roles = user_repo.get_roles_by_ids(db, role_ids)
    if len({role.id for role in roles}) != len(set(role_ids)):
        raise BadRequestError(
            "One or more selected roles were not found.",
            code="ROLE_NOT_FOUND",
            details={"role_ids": list(role_ids)},
        )
    return roles


def get_user(db: Session, user_id: int) -> User:
    """Load a user or raise ``404 USER_NOT_FOUND``."""
    user = user_repo.get_by_id(db, user_id)
    if user is None:
        raise NotFoundError("User was not found.", code="USER_NOT_FOUND")
    return user


def list_users(
    db: Session, params: PaginationParams, role_id: Optional[int] = None
) -> Dict[str, Any]:
    """Paginated user list with free-text search, status/role filters and sorting."""
    stmt = select(User)

    if params.search:
        pattern = f"%{params.search}%"
        stmt = stmt.where(
            or_(
                User.username.ilike(pattern),
                User.email.ilike(pattern),
                User.first_name.ilike(pattern),
                User.last_name.ilike(pattern),
            )
        )
    if params.status:
        stmt = stmt.where(User.status == params.status)
    if role_id is not None:
        stmt = stmt.where(User.roles.any(Role.id == role_id))

    sort_by = (params.sort_by or "").strip()
    if not sort_by:
        sort_column, descending = _USER_SORTABLE[DEFAULT_USER_SORT], True
    else:
        if sort_by not in _USER_SORTABLE:
            raise BadRequestError(
                "Unsupported sort field.",
                code="INVALID_SORT_BY",
                details={"allowed": sorted(_USER_SORTABLE)},
            )
        sort_column = _USER_SORTABLE[sort_by]
        descending = params.sort_order == "desc"

    stmt = stmt.order_by(
        sort_column.desc() if descending else sort_column.asc(), User.id.desc() if descending else User.id.asc()
    )
    return paginate(db, stmt, params)


def create_user(
    db: Session, payload: UserCreate, *, actor_id: int, request: Optional[Request] = None
) -> User:
    """Create a user with unique credentials, optional roles/profile and an audit entry."""
    if user_repo.username_exists(db, payload.username):
        raise ConflictError("Username is already in use.", code="USERNAME_ALREADY_EXISTS")
    if user_repo.email_exists(db, str(payload.email)):
        raise ConflictError("Email is already in use.", code="EMAIL_ALREADY_EXISTS")

    roles = _resolve_roles(db, payload.role_ids)
    user = User(
        username=payload.username,
        email=str(payload.email),
        password_hash=hash_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
        mobile=payload.mobile,
        status=payload.status.value,
        is_verified=payload.is_verified,
        roles=roles,
    )
    if payload.student_profile is not None:
        user.student_profile = _build_profile(payload.student_profile)

    db.add(user)
    db.flush()
    record_audit(
        db,
        user_id=actor_id,
        module="user",
        action="create",
        entity_type="user",
        entity_id=user.id,
        new_data=_snapshot(user),
        request=request,
    )
    db.commit()
    return user


def update_user(
    db: Session,
    user_id: int,
    payload: UserUpdate,
    *,
    actor_id: int,
    request: Optional[Request] = None,
) -> User:
    """Apply non-None fields, re-hash a supplied password and merge the student profile."""
    user = get_user(db, user_id)
    old_data = _snapshot(user)

    if payload.email is not None and str(payload.email).lower() != user.email.lower():
        if user_repo.email_exists(db, str(payload.email), exclude_user_id=user.id):
            raise ConflictError("Email is already in use.", code="EMAIL_ALREADY_EXISTS")
        user.email = str(payload.email)
    if payload.first_name is not None:
        user.first_name = payload.first_name
    if payload.last_name is not None:
        user.last_name = payload.last_name
    if payload.mobile is not None:
        user.mobile = payload.mobile
    if payload.is_verified is not None:
        user.is_verified = payload.is_verified
    if payload.password is not None:
        user.password_hash = hash_password(payload.password)

    if payload.student_profile is not None:
        incoming = payload.student_profile
        profile = user.student_profile
        if profile is None:
            user.student_profile = _build_profile(incoming)
        else:
            for field in ("student_code", "date_of_birth", "institution", "class_name", "roll_number"):
                value = getattr(incoming, field)
                if value is not None:
                    setattr(profile, field, value)
            if incoming.gender is not None:
                profile.gender = incoming.gender.value

    record_audit(
        db,
        user_id=actor_id,
        module="user",
        action="update",
        entity_type="user",
        entity_id=user.id,
        old_data=old_data,
        new_data=_snapshot(user),
        request=request,
    )
    db.commit()
    return user


def update_user_status(
    db: Session,
    user_id: int,
    payload: UserStatusUpdate,
    *,
    actor_id: int,
    request: Optional[Request] = None,
) -> User:
    """Switch the account status (ACTIVE/INACTIVE/SUSPENDED/PENDING) with an audit entry."""
    user = get_user(db, user_id)
    old_status = user.status
    user.status = payload.status.value
    record_audit(
        db,
        user_id=actor_id,
        module="user",
        action="status_change",
        entity_type="user",
        entity_id=user.id,
        old_data={"status": old_status},
        new_data={"status": user.status},
        request=request,
    )
    db.commit()
    return user


def delete_user(
    db: Session, user_id: int, *, actor_id: int, request: Optional[Request] = None
) -> bool:
    """Delete or deactivate a user.

    Returns ``True`` when the account was only deactivated.  Deactivation
    (never deletion) is applied when the user owns content (exams, questions)
    or is the last holder of the ``SUPER_ADMIN`` role.
    Self-deletion is rejected with ``403 SELF_ACTION``.
    """
    if user_id == actor_id:
        raise ForbiddenError("You cannot delete your own account.", code="SELF_ACTION")

    user = get_user(db, user_id)
    is_last_super_admin = any(role.code == SUPER_ADMIN_ROLE for role in user.roles) and (
        user_repo.count_super_admins(db) <= 1
    )

    if user_repo.owns_content(db, user_id) or is_last_super_admin:
        old_data = _snapshot(user)
        user.status = UserStatus.INACTIVE.value
        record_audit(
            db,
            user_id=actor_id,
            module="user",
            action="deactivate",
            entity_type="user",
            entity_id=user.id,
            old_data=old_data,
            new_data=_snapshot(user),
            request=request,
        )
        db.commit()
        return True

    record_audit(
        db,
        user_id=actor_id,
        module="user",
        action="delete",
        entity_type="user",
        entity_id=user.id,
        old_data=_snapshot(user),
        request=request,
    )
    db.delete(user)
    db.commit()
    return False


def assign_roles(
    db: Session,
    user_id: int,
    payload: AssignRolesRequest,
    *,
    actor_id: int,
    request: Optional[Request] = None,
) -> User:
    """Replace the user's entire role set (empty ``role_ids`` removes all roles)."""
    user = get_user(db, user_id)
    old_data = _snapshot(user)
    user.roles = _resolve_roles(db, payload.role_ids)
    record_audit(
        db,
        user_id=actor_id,
        module="user",
        action="update",
        entity_type="user",
        entity_id=user.id,
        old_data=old_data,
        new_data=_snapshot(user),
        request=request,
    )
    db.commit()
    return user


def get_user_permissions(db: Session, user_id: int) -> UserPermissionsResponse:
    """Resolved permission codes plus the role codes they were granted through."""
    user = get_user(db, user_id)
    return UserPermissionsResponse(
        user_id=user.id,
        permissions=sorted(get_permission_codes(db, user)),
        roles=sorted(role.code for role in user.roles),
    )
