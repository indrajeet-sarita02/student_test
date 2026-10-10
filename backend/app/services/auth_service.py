"""Authentication service: login, token refresh and password lifecycle.

Failed logins are throttled with a small **in-process** sliding-window
counter (module-level mapping of ``identifier|ip`` -> failure timestamps).
The platform has no cache/Redis by design, so the limiter intentionally
lives in process memory; stale timestamps are pruned on every access.
"""

import logging
import time
from datetime import timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import (
    BadRequestError,
    ForbiddenError,
    TooManyRequestsError,
    UnauthorizedError,
)
from app.core.jwt import create_access_token, create_refresh_token, decode_token, get_token_subject
from app.core.permissions import get_permission_codes
from app.core.security import (
    generate_reset_token,
    hash_password,
    hash_token,
    validate_password_strength,
    verify_password,
)
from app.models.password_reset import PasswordResetToken
from app.models.user import User
from app.repositories import user_repository as user_repo
from app.schemas.auth import MeResponse
from app.schemas.role import RoleBrief
from app.schemas.user import StudentProfileResponse
from app.services.audit_service import record_audit
from app.utils.datetime import ensure_utc, utcnow
from app.utils.enums import UserStatus

logger = logging.getLogger("student_test.auth")

RATE_LIMIT_WINDOW_SECONDS = 300
RATE_LIMIT_MAX_FAILURES = 5
RESET_TOKEN_TTL_MINUTES = 30
# Safety valve so a flood of distinct identifiers cannot grow the dict forever.
_RATE_LIMIT_MAX_KEYS = 10_000

# key -> timestamps (epoch seconds) of failed attempts inside the window.
_failed_logins: Dict[str, List[float]] = {}


def _rate_key(identifier: str, client_ip: Optional[str]) -> str:
    return f"{(identifier or '').strip().lower()}|{client_ip or '-'}"


def _window_stamps(key: str, now: float) -> List[float]:
    """Return (and persist) the failure timestamps still inside the window."""
    stamps = [stamp for stamp in _failed_logins.get(key, []) if now - stamp < RATE_LIMIT_WINDOW_SECONDS]
    if stamps:
        _failed_logins[key] = stamps
    else:
        _failed_logins.pop(key, None)
    return stamps


def _check_rate_limit(key: str) -> None:
    """Raise ``429`` when the key already exhausted its failure budget."""
    if len(_window_stamps(key, time.time())) >= RATE_LIMIT_MAX_FAILURES:
        raise TooManyRequestsError(
            "Too many failed attempts. Please wait a few minutes and try again.",
            code="RATE_LIMITED",
        )


def _record_failure(key: str) -> None:
    """Register one failed attempt, pruning expired entries as a side effect."""
    now = time.time()
    if len(_failed_logins) >= _RATE_LIMIT_MAX_KEYS:
        for stale_key in list(_failed_logins):
            _window_stamps(stale_key, now)
    stamps = _window_stamps(key, now)
    stamps.append(now)
    _failed_logins[key] = stamps


def _clear_failures(key: str) -> None:
    _failed_logins.pop(key, None)


def _clear_failures_for(*identifiers: str) -> None:
    """Drop counters for the given identifiers on any client (password reset)."""
    prefixes = {f"{(value or '').strip().lower()}|" for value in identifiers if value}
    for key in list(_failed_logins):
        if any(key.startswith(prefix) for prefix in prefixes):
            _failed_logins.pop(key, None)


def login(db: Session, *, identifier: str, password: str, client_ip: Optional[str]) -> Tuple[str, str]:
    """Authenticate username-or-email + password and issue a fresh token pair.

    Unknown users and bad passwords both raise the same generic ``401`` so
    the response never discloses which accounts exist.  Successful logins
    refresh ``last_login_at`` and clear the caller's failure counter.
    """
    key = _rate_key(identifier, client_ip)
    _check_rate_limit(key)

    user = user_repo.get_by_identifier(db, identifier)
    if user is None or not verify_password(user.password_hash, password):
        _record_failure(key)
        raise UnauthorizedError("Invalid credentials.", code="INVALID_CREDENTIALS")
    if user.status != UserStatus.ACTIVE.value:
        raise ForbiddenError("Account is not active.", code="ACCOUNT_INACTIVE")

    _clear_failures(key)
    user.last_login_at = utcnow()
    db.commit()
    return create_access_token(user.id), create_refresh_token(user.id)


def refresh_tokens(db: Session, refresh_token: str) -> Tuple[str, str]:
    """Validate a refresh token and rotate it for a brand-new token pair."""
    payload = decode_token(refresh_token, expected_type="refresh")
    user_id = get_token_subject(payload)
    if user_id is None:
        raise UnauthorizedError("Token subject is invalid.", code="TOKEN_INVALID")

    user = user_repo.get_by_id(db, user_id)
    if user is None:
        raise UnauthorizedError("Account no longer exists.", code="USER_NOT_FOUND")
    if user.status != UserStatus.ACTIVE.value:
        raise ForbiddenError("Account is not active.", code="ACCOUNT_INACTIVE")
    return create_access_token(user.id), create_refresh_token(user.id)


def get_me(db: Session, user: User) -> MeResponse:
    """Build the ``/auth/me`` payload: profile, roles and resolved permissions."""
    profile = (
        StudentProfileResponse.model_validate(user.student_profile)
        if user.student_profile
        else None
    )
    return MeResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        mobile=user.mobile,
        status=user.status,
        is_verified=user.is_verified,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        roles=[RoleBrief.model_validate(role) for role in user.roles],
        permissions=sorted(get_permission_codes(db, user)),
        student_profile=profile,
    )


def change_password(
    db: Session,
    user: User,
    *,
    current_password: str,
    new_password: str,
    request=None,
) -> None:
    """Verify the current password, apply the new one and audit the change."""
    if not verify_password(user.password_hash, current_password):
        raise UnauthorizedError("Current password is incorrect.", code="CURRENT_PASSWORD_INVALID")
    validate_password_strength(new_password)

    user.password_hash = hash_password(new_password)
    record_audit(
        db,
        user_id=user.id,
        module="auth",
        action="change_password",
        entity_type="user",
        entity_id=user.id,
        new_data={"password_changed": True},
        request=request,
    )
    db.commit()


def forgot_password(db: Session, *, email: str) -> Optional[str]:
    """Issue a single-use reset token when the address exists.

    Always behaves as if the account existed (no enumeration).  Returns the
    raw token so the router can surface it in debug mode; because there is no
    SMTP in this environment, non-debug deployments log it at INFO instead.
    """
    user = user_repo.get_by_email(db, email)
    if user is None:
        logger.info("Password reset requested for an unknown address.")
        return None

    raw_token = generate_reset_token()
    db.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=hash_token(raw_token),
            expires_at=utcnow() + timedelta(minutes=RESET_TOKEN_TTL_MINUTES),
        )
    )
    db.commit()

    if not settings.debug:
        logger.info("Password reset token for user_id=%s: %s", user.id, raw_token)
    return raw_token


def reset_password(db: Session, *, token: str, new_password: str, request=None) -> None:
    """Consume a valid reset token and store the new password hash."""
    validate_password_strength(new_password)

    token_hash = hash_token(token)
    stmt = select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
    reset_row = db.scalar(stmt)
    now = utcnow()
    if (
        reset_row is None
        or reset_row.used_at is not None
        or (ensure_utc(reset_row.expires_at) or now) <= now
    ):
        raise BadRequestError("Reset link is invalid or has expired.", code="RESET_TOKEN_INVALID")

    user = user_repo.get_by_id(db, reset_row.user_id)
    if user is None:
        raise BadRequestError("Reset link is invalid or has expired.", code="RESET_TOKEN_INVALID")

    user.password_hash = hash_password(new_password)
    reset_row.used_at = now
    _clear_failures_for(user.username, user.email)
    record_audit(
        db,
        user_id=user.id,
        module="auth",
        action="reset_password",
        entity_type="user",
        entity_id=user.id,
        new_data={"password_changed": True},
        request=request,
    )
    db.commit()
