"""Centralised application errors.

Every error raised through :class:`AppError` is rendered by the handlers in
``app.main`` using the standard envelope::

    {"success": false, "error": {"code": "...", "message": "..."}}
"""

from typing import Any, Dict, Optional


class AppError(Exception):
    """Base class for all expected (non 500) application errors."""

    status_code: int = 400
    default_code: str = "APP_ERROR"

    def __init__(
        self,
        message: str,
        *,
        code: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code or self.default_code
        self.status_code = status_code or self.status_code
        self.details = details or {}

    def to_payload(self) -> Dict[str, Any]:
        error: Dict[str, Any] = {"code": self.code, "message": self.message}
        if self.details:
            error["details"] = self.details
        return {"success": False, "error": error}


class BadRequestError(AppError):
    status_code = 400
    default_code = "BAD_REQUEST"


class UnauthorizedError(AppError):
    status_code = 401
    default_code = "UNAUTHORIZED"


class ForbiddenError(AppError):
    status_code = 403
    default_code = "FORBIDDEN"


class NotFoundError(AppError):
    status_code = 404
    default_code = "NOT_FOUND"


class ConflictError(AppError):
    status_code = 409
    default_code = "CONFLICT"


class ValidationAppError(AppError):
    status_code = 422
    default_code = "VALIDATION_ERROR"


class TooManyRequestsError(AppError):
    status_code = 429
    default_code = "TOO_MANY_REQUESTS"
