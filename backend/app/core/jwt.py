"""JWT creation / validation helpers (PyJWT)."""

from typing import Any, Dict, Optional

import jwt
from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.core.exceptions import UnauthorizedError


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_token(
    subject: int,
    token_type: str = "access",
    expires_delta: Optional[timedelta] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> str:
    if expires_delta is None:
        expires_delta = (
            timedelta(minutes=settings.access_token_expire_minutes)
            if token_type == "access"
            else timedelta(days=settings.refresh_token_expire_days)
        )
    now = _now()
    payload: Dict[str, Any] = {
        "sub": str(subject),
        "type": token_type,
        "iat": now,
        "nbf": now,
        "exp": now + expires_delta,
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(subject: int, extra: Optional[Dict[str, Any]] = None) -> str:
    return create_token(subject, "access", extra=extra)


def create_refresh_token(subject: int, extra: Optional[Dict[str, Any]] = None) -> str:
    return create_token(subject, "refresh", extra=extra)


def decode_token(token: str, expected_type: str = "access") -> Dict[str, Any]:
    """Decode and validate a JWT, raising ``401`` on any failure."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "iat", "sub"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise UnauthorizedError("Token has expired.", code="TOKEN_EXPIRED") from exc
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("Token is invalid.", code="TOKEN_INVALID") from exc

    if payload.get("type") != expected_type:
        raise UnauthorizedError(
            f"Expected a {expected_type} token.",
            code="TOKEN_TYPE_MISMATCH",
        )
    return payload


def get_token_subject(payload: Dict[str, Any]) -> Optional[int]:
    try:
        return int(payload.get("sub"))
    except (TypeError, ValueError):
        return None
