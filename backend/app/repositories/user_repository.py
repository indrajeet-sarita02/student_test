"""Data-access helpers for the user/role/permission domain.

Pure query functions consumed by :mod:`app.services.auth_service` and
:mod:`app.services.user_service`.  The repository never raises domain errors
and never commits - transaction control belongs to the service layer.
"""

from typing import List, Optional, Sequence

from sqlalchemy import distinct, func, or_, select
from sqlalchemy.orm import Session

from app.core.permissions import SUPER_ADMIN_ROLE
from app.models.attempt import Attempt
from app.models.exam import Exam
from app.models.permission import Permission
from app.models.question import Question
from app.models.role import Role
from app.models.test import Test
from app.models.user import User, UserRole


def get_by_id(db: Session, user_id: int) -> Optional[User]:
    """Return the user with ``user_id`` or ``None`` when it does not exist."""
    return db.get(User, user_id)


def get_by_identifier(db: Session, identifier: str) -> Optional[User]:
    """Case-insensitive lookup by username **or** e-mail address."""
    value = (identifier or "").strip().lower()
    if not value:
        return None
    stmt = (
        select(User)
        .where(or_(func.lower(User.username) == value, func.lower(User.email) == value))
        .limit(1)
    )
    return db.scalar(stmt)


def get_by_email(db: Session, email: str) -> Optional[User]:
    """Case-insensitive lookup by e-mail address only."""
    value = (email or "").strip().lower()
    if not value:
        return None
    stmt = select(User).where(func.lower(User.email) == value).limit(1)
    return db.scalar(stmt)


def username_exists(db: Session, username: str, exclude_user_id: Optional[int] = None) -> bool:
    """Whether a (case-insensitive) username is already taken."""
    value = (username or "").strip().lower()
    stmt = select(User.id).where(func.lower(User.username) == value)
    if exclude_user_id is not None:
        stmt = stmt.where(User.id != exclude_user_id)
    return db.scalar(stmt.limit(1)) is not None


def email_exists(db: Session, email: str, exclude_user_id: Optional[int] = None) -> bool:
    """Whether a (case-insensitive) e-mail address is already taken."""
    value = (email or "").strip().lower()
    stmt = select(User.id).where(func.lower(User.email) == value)
    if exclude_user_id is not None:
        stmt = stmt.where(User.id != exclude_user_id)
    return db.scalar(stmt.limit(1)) is not None


def get_roles_by_ids(db: Session, role_ids: Sequence[int]) -> List[Role]:
    """Fetch roles for ``role_ids`` (deduplicated); missing IDs are simply absent."""
    unique_ids = list(dict.fromkeys(role_ids))
    if not unique_ids:
        return []
    stmt = select(Role).where(Role.id.in_(unique_ids)).order_by(Role.id)
    return list(db.scalars(stmt).all())


def get_permissions_by_ids(db: Session, permission_ids: Sequence[int]) -> List[Permission]:
    """Fetch permissions for ``permission_ids`` (deduplicated); missing IDs are absent."""
    unique_ids = list(dict.fromkeys(permission_ids))
    if not unique_ids:
        return []
    stmt = select(Permission).where(Permission.id.in_(unique_ids)).order_by(Permission.id)
    return list(db.scalars(stmt).all())


def count_super_admins(db: Session) -> int:
    """Number of users holding the ``SUPER_ADMIN`` role assignment."""
    stmt = (
        select(func.count(distinct(UserRole.user_id)))
        .join(Role, Role.id == UserRole.role_id)
        .where(Role.code == SUPER_ADMIN_ROLE)
    )
    return int(db.scalar(stmt) or 0)


def owns_content(db: Session, user_id: int) -> bool:
    """Whether the user authored/owns rows that must survive their deletion.

    Checked entities: test attempts (``student_id``) plus authored exams,
    questions and tests (``created_by``).
    """
    probes = (
        select(Attempt.id).where(Attempt.student_id == user_id).limit(1),
        select(Exam.id).where(Exam.created_by == user_id).limit(1),
        select(Question.id).where(Question.created_by == user_id).limit(1),
        select(Test.id).where(Test.created_by == user_id).limit(1),
    )
    return any(db.scalar(probe) is not None for probe in probes)
