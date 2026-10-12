"""Role management service: CRUD, permission assignment and safety guards.

System roles (``is_system_role``) are protected from deletion, and roles with
assigned users cannot be removed (``409 ROLE_IN_USE``).
"""

from typing import Any, Dict, List, Optional

from fastapi import Request
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import UserRole
from app.repositories import user_repository as user_repo
from app.schemas.permission import PermissionModuleResponse, PermissionResponse
from app.schemas.role import RoleCreate, RolePermissionsUpdate, RoleUpdate
from app.services.audit_service import record_audit
from app.utils.pagination import PaginationParams, paginate

# Columns exposed to ``?sort_by=`` on the role list endpoint.
_ROLE_SORTABLE = {
    "id": Role.id,
    "name": Role.name,
    "code": Role.code,
    "created_at": Role.created_at,
}
DEFAULT_ROLE_SORT = "created_at"


def _snapshot(role: Role) -> Dict[str, Any]:
    """JSON-friendly view of a role used as audit old/new data."""
    return {
        "name": role.name,
        "code": role.code,
        "description": role.description,
        "is_system_role": role.is_system_role,
        "is_active": role.is_active,
        "permissions": sorted(permission.code for permission in role.permissions),
    }


def _resolve_permissions(db: Session, permission_ids: List[int]) -> List[Permission]:
    permissions = user_repo.get_permissions_by_ids(db, permission_ids)
    if len({permission.id for permission in permissions}) != len(set(permission_ids)):
        raise BadRequestError(
            "One or more selected permissions were not found.",
            code="PERMISSION_NOT_FOUND",
            details={"permission_ids": list(permission_ids)},
        )
    return permissions


def get_role(db: Session, role_id: int) -> Role:
    """Load a role or raise ``404 ROLE_NOT_FOUND``."""
    role = db.get(Role, role_id)
    if role is None:
        raise NotFoundError("Role was not found.", code="ROLE_NOT_FOUND")
    return role


def list_roles(db: Session, params: PaginationParams) -> Dict[str, Any]:
    """Paginated role list with a free-text search across name and code."""
    stmt = select(Role)
    if params.search:
        pattern = f"%{params.search}%"
        stmt = stmt.where(or_(Role.name.ilike(pattern), Role.code.ilike(pattern)))

    sort_by = (params.sort_by or "").strip()
    if not sort_by:
        sort_column, descending = _ROLE_SORTABLE[DEFAULT_ROLE_SORT], True
    else:
        if sort_by not in _ROLE_SORTABLE:
            raise BadRequestError(
                "Unsupported sort field.",
                code="INVALID_SORT_BY",
                details={"allowed": sorted(_ROLE_SORTABLE)},
            )
        sort_column = _ROLE_SORTABLE[sort_by]
        descending = params.sort_order == "desc"

    stmt = stmt.order_by(
        sort_column.desc() if descending else sort_column.asc(),
        Role.id.desc() if descending else Role.id.asc(),
    )
    return paginate(db, stmt, params)


def create_role(
    db: Session, payload: RoleCreate, *, actor_id: int, request: Optional[Request] = None
) -> Role:
    """Create a role with a unique code and its initial permission set."""
    existing = db.scalar(
        select(Role.id).where(func.lower(Role.code) == payload.code.strip().lower())
    )
    if existing is not None:
        raise ConflictError("Role code already exists.", code="ROLE_CODE_EXISTS")

    permissions = _resolve_permissions(db, payload.permission_ids)
    role = Role(
        name=payload.name,
        code=payload.code.strip(),
        description=payload.description,
        is_active=payload.is_active,
        permissions=permissions,
    )
    db.add(role)
    db.flush()
    record_audit(
        db,
        user_id=actor_id,
        module="role",
        action="create",
        entity_type="role",
        entity_id=role.id,
        new_data=_snapshot(role),
        request=request,
    )
    db.commit()
    return role


def update_role(
    db: Session,
    role_id: int,
    payload: RoleUpdate,
    *,
    actor_id: int,
    request: Optional[Request] = None,
) -> Role:
    """Update name/description/is_active.

    ``RoleUpdate`` deliberately exposes no ``code`` field, so the code of a
    system role can never be altered through this endpoint.
    """
    role = get_role(db, role_id)
    old_data = _snapshot(role)

    if payload.name is not None:
        role.name = payload.name
    if payload.description is not None:
        role.description = payload.description
    if payload.is_active is not None:
        role.is_active = payload.is_active

    record_audit(
        db,
        user_id=actor_id,
        module="role",
        action="update",
        entity_type="role",
        entity_id=role.id,
        old_data=old_data,
        new_data=_snapshot(role),
        request=request,
    )
    db.commit()
    return role


def delete_role(
    db: Session, role_id: int, *, actor_id: int, request: Optional[Request] = None
) -> None:
    """Delete an unused role; system roles and roles in use raise ``409``."""
    role = get_role(db, role_id)
    if role.is_system_role:
        raise ConflictError("System role cannot be deleted.", code="SYSTEM_ROLE")

    assigned_users = db.scalar(
        select(func.count()).select_from(UserRole).where(UserRole.role_id == role.id)
    )
    if int(assigned_users or 0) > 0:
        raise ConflictError(
            "Role is assigned to users and cannot be deleted.", code="ROLE_IN_USE"
        )

    record_audit(
        db,
        user_id=actor_id,
        module="role",
        action="delete",
        entity_type="role",
        entity_id=role.id,
        old_data=_snapshot(role),
        request=request,
    )
    db.delete(role)
    db.commit()


def update_role_permissions(
    db: Session,
    role_id: int,
    payload: RolePermissionsUpdate,
    *,
    actor_id: int,
    request: Optional[Request] = None,
) -> Role:
    """Replace the role's permission set (empty list removes every permission)."""
    role = get_role(db, role_id)
    old_data = _snapshot(role)
    role.permissions = _resolve_permissions(db, payload.permission_ids)
    record_audit(
        db,
        user_id=actor_id,
        module="role",
        action="update",
        entity_type="role",
        entity_id=role.id,
        old_data=old_data,
        new_data=_snapshot(role),
        request=request,
    )
    db.commit()
    return role


def list_permissions(db: Session) -> List[Permission]:
    """Return the whole permission catalogue ordered by module then action."""
    stmt = select(Permission).order_by(
        Permission.module.asc(), Permission.action.asc(), Permission.code.asc()
    )
    return list(db.scalars(stmt).all())


def list_permission_modules(db: Session) -> List[PermissionModuleResponse]:
    """Group the permission catalogue by module for the RBAC matrix UI."""
    grouped: Dict[str, List[Permission]] = {}
    for permission in list_permissions(db):
        grouped.setdefault(permission.module, []).append(permission)
    return [
        PermissionModuleResponse(
            module=module,
            permissions=[PermissionResponse.model_validate(item) for item in items],
        )
        for module, items in sorted(grouped.items())
    ]
