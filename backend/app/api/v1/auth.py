"""Authentication endpoints mounted at ``/api/v1/auth``.

Only ``/me``, ``/change-password`` (and ``/logout`` for token validation)
require a bearer access token; no permission guards apply to self-service
auth flows.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Request
from pydantic import Field
from sqlalchemy.orm import Session

from app.api.deps import get_access_payload, get_client_meta, get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    MeResponse,
    RefreshRequest,
    ResetPasswordRequest,
    TokenResponse,
)
from app.schemas.common import MessageResponse
from app.services import auth_service

router = APIRouter()


class ForgotPasswordResponse(MessageResponse):
    """Generic forgot-password payload.

    ``reset_token`` is a DEV-ONLY convenience: this environment has no SMTP,
    so when ``settings.debug`` is true the raw reset token is echoed back to
    ease local testing.  It is never returned when debug mode is off - the
    token is then only logged at INFO level for operators.
    """

    reset_token: Optional[str] = Field(
        None,
        description="Dev-only raw reset token; present only when debug mode is enabled.",
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in",
    description=(
        "Authenticate with a username **or** e-mail address (case-insensitive) "
        "and password, returning a fresh access/refresh token pair.  Failed "
        "attempts are rate limited to 5 per identifier+IP within 300 seconds."
    ),
    responses={
        401: {"description": "Invalid credentials."},
        403: {"description": "The account exists but is not active."},
        429: {"description": "Too many failed login attempts (RATE_LIMITED)."},
    },
)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    """POST /api/v1/auth/login - exchange credentials for a token pair."""
    client = get_client_meta(request)
    access_token, refresh_token = auth_service.login(
        db,
        identifier=payload.username,
        password=payload.password,
        client_ip=client["ip_address"],
    )
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description=(
        "Validate a refresh token and rotate it, issuing a brand-new "
        "access/refresh pair.  The referenced account must still be active."
    ),
    responses={
        401: {"description": "Refresh token is invalid, expired or the account is gone."},
        403: {"description": "The account is not active."},
    },
)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """POST /api/v1/auth/refresh - rotate a refresh token into a new pair."""
    access_token, refresh_token = auth_service.refresh_tokens(db, payload.refresh_token)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Log out",
    description=(
        "Validate the bearer access token and report success.  JWTs are "
        "stateless, so the client simply discards its tokens."
    ),
    responses={401: {"description": "Missing or invalid access token."}},
    dependencies=[Depends(get_access_payload)],
)
def logout() -> MessageResponse:
    """POST /api/v1/auth/logout - confirm token validity so the client can drop it."""
    return MessageResponse(message="Successfully logged out.")


@router.get(
    "/me",
    response_model=MeResponse,
    summary="Current user",
    description=(
        "Return the authenticated user's profile together with its roles, "
        "student profile and the permission codes resolved server-side."
    ),
    responses={
        401: {"description": "Authentication credentials were not provided or are invalid."},
        403: {"description": "The account is not active."},
    },
)
def me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MeResponse:
    """GET /api/v1/auth/me - inspect the caller's identity and permissions."""
    return auth_service.get_me(db, current_user)


@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="Change own password",
    description=(
        "Verify the current password, apply the (strength-checked) new one "
        "and record an audit entry."
    ),
    responses={
        401: {"description": "Current password is incorrect or credentials are missing."},
        403: {"description": "The account is not active."},
        422: {"description": "The new password does not meet the strength policy."},
    },
)
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    """POST /api/v1/auth/change-password - rotate the caller's own password."""
    auth_service.change_password(
        db,
        current_user,
        current_password=payload.current_password,
        new_password=payload.new_password,
        request=request,
    )
    return MessageResponse(message="Password updated successfully.")


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
    response_model_exclude_none=True,
    summary="Request a password reset",
    description=(
        "Always answer with the same generic message regardless of whether "
        "the e-mail exists, to prevent account enumeration.  When the account "
        "exists a single-use 30-minute reset token is issued.  **Dev-only**: "
        "with ``settings.debug`` enabled the raw token is echoed back as "
        "``reset_token`` because no SMTP server is available in this "
        "environment; in non-debug mode it is logged at INFO instead."
    ),
    responses={422: {"description": "Request validation failed."}},
)
def forgot_password(
    payload: ForgotPasswordRequest, db: Session = Depends(get_db)
) -> ForgotPasswordResponse:
    """POST /api/v1/auth/forgot-password - start the password reset flow."""
    raw_token = auth_service.forgot_password(db, email=str(payload.email))
    return ForgotPasswordResponse(
        success=True,
        message="If the account exists, a password reset instruction has been issued.",
        reset_token=raw_token if settings.debug and raw_token else None,
    )


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Reset password with token",
    description=(
        "Consume the single-use reset token (hashed at rest, 30-minute TTL), "
        "store the strength-checked new password and audit the change."
    ),
    responses={
        400: {"description": "Reset token is invalid, already used or expired."},
        422: {"description": "The new password does not meet the strength policy."},
    },
)
def reset_password(
    payload: ResetPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> MessageResponse:
    """POST /api/v1/auth/reset-password - finish the password reset flow."""
    auth_service.reset_password(
        db,
        token=payload.token,
        new_password=payload.new_password,
        request=request,
    )
    return MessageResponse(message="Password has been reset successfully.")
