"""FastAPI dependencies: authentication, current user, pagination."""

from typing import List, Optional

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.jwt import decode_token, get_token_subject
from app.db.session import get_db
from app.models.user import User
from app.utils.enums import UserStatus

bearer_scheme = HTTPBearer(auto_error=False, scheme_name="Bearer")


def get_access_payload(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> dict:
    if credentials is None or not credentials.credentials:
        raise UnauthorizedError("Authentication credentials were not provided.", code="MISSING_TOKEN")
    return decode_token(credentials.credentials, expected_type="access")


def get_current_user(
    payload: dict = Depends(get_access_payload),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the authenticated, active user from the bearer access token."""
    user_id = get_token_subject(payload)
    if user_id is None:
        raise UnauthorizedError("Token subject is invalid.", code="TOKEN_INVALID")

    user = db.get(User, user_id)
    if user is None:
        raise UnauthorizedError("Account no longer exists.", code="USER_NOT_FOUND")
    if user.status != UserStatus.ACTIVE.value:
        raise ForbiddenError("Account is not active.", code="ACCOUNT_INACTIVE")
    return user


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Same as :func:`get_current_user` but returns ``None`` when anonymous."""
    if credentials is None or not credentials.credentials:
        return None
    try:
        payload = decode_token(credentials.credentials, expected_type="access")
        user_id = get_token_subject(payload)
        if user_id is None:
            return None
        user = db.get(User, user_id)
        if user is None or user.status != UserStatus.ACTIVE.value:
            return None
        return user
    except UnauthorizedError:
        return None


def get_client_meta(request: Request) -> dict:
    """Best-effort client metadata for audit logging."""
    user_agent = request.headers.get("user-agent")
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
    else:
        ip = request.client.host if request.client else None
    return {"ip_address": ip, "user_agent": user_agent[:300] if user_agent else None}
