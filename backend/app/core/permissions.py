"""Server-side RBAC helpers.

Permissions are resolved from the database on every protected request - they
are never trusted from the JWT payload.
"""

from typing import Iterable, Set

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError
from app.db.session import get_db
from app.models.user import User
from app.api.deps import get_current_user

SUPER_ADMIN_ROLE = "SUPER_ADMIN"
SUPER_PERMISSION = "*"


def get_permission_codes(db: Session, user: User) -> Set[str]:
    """All permission codes granted to a user through their active roles."""
    codes: Set[str] = set()
    for role in user.roles:
        if not role.is_active:
            continue
        if role.code == SUPER_ADMIN_ROLE:
            return {SUPER_PERMISSION}
        for permission in role.permissions:
            codes.add(permission.code)
    return codes


def has_any_permission(db: Session, user: User, codes: Iterable[str]) -> bool:
    granted = get_permission_codes(db, user)
    if SUPER_PERMISSION in granted:
        return True
    requested = list(codes)
    return any(code in granted for code in requested)


def has_all_permissions(db: Session, user: User, codes: Iterable[str]) -> bool:
    granted = get_permission_codes(db, user)
    if SUPER_PERMISSION in granted:
        return True
    return all(code in granted for code in codes)


def require_permission(*codes: str):
    """Dependency factory: allow the request when the user holds ANY of ``codes``.

    Usage::

        @router.post("/", dependencies=[Depends(require_permission("question.create"))])
    """
    if not codes:
        raise ValueError("require_permission() needs at least one permission code")

    def dependency(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> User:
        if not has_any_permission(db, current_user, codes):
            raise ForbiddenError(
                f"Missing permission: one of {', '.join(codes)}.",
                code="PERMISSION_DENIED",
                details={"required_permissions": list(codes)},
            )
        return current_user

    return dependency


def require_all_permissions(*codes: str):
    """Dependency factory: allow the request only when the user holds ALL codes.

    Used by composite operations that touch more than one module (e.g. a test
    import that creates both a test and question-bank rows).

    Usage::

        @router.post("/import", dependencies=[Depends(require_all_permissions("test.create", "question.create"))])
    """
    if not codes:
        raise ValueError("require_all_permissions() needs at least one permission code")

    def dependency(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> User:
        if not has_all_permissions(db, current_user, codes):
            raise ForbiddenError(
                f"Missing permission: all of {', '.join(codes)} are required.",
                code="PERMISSION_DENIED",
                details={"required_permissions": list(codes)},
            )
        return current_user

    return dependency


def require_role(*role_codes: str):
    """Dependency factory restricted to specific role codes (e.g. SUPER_ADMIN)."""

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if not set(role_codes) & set(current_user.role_codes):
            raise ForbiddenError(
                f"Access restricted to roles: {', '.join(role_codes)}.",
                code="ROLE_DENIED",
                details={"required_roles": list(role_codes)},
            )
        return current_user

    return dependency
