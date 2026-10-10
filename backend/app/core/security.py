"""Password hashing (Argon2id via pwdlib) and small helpers around it."""

import re
import secrets
from typing import Optional

from pwdlib import PasswordHash

from app.core.config import settings
from app.core.exceptions import ValidationAppError

_password_hash = PasswordHash.recommended()  # Argon2id

MIN_PASSWORD_LENGTH = 8


def hash_password(password: str) -> str:
    return _password_hash.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    if not password_hash or not password:
        return False
    try:
        return _password_hash.verify(password, password_hash)
    except Exception:  # malformed hash stored in DB
        return False


def needs_rehash(password_hash: str) -> bool:
    try:
        return _password_hash.check_needs_rehash(password_hash)
    except Exception:
        return False


def validate_password_strength(password: str) -> None:
    """Reject trivial passwords with a field-level validation error."""
    problems = []
    if len(password or "") < MIN_PASSWORD_LENGTH:
        problems.append(f"must be at least {MIN_PASSWORD_LENGTH} characters long")
    if not re.search(r"[A-Za-z]", password or ""):
        problems.append("must contain at least one letter")
    if not re.search(r"[0-9]", password or ""):
        problems.append("must contain at least one digit")
    if problems:
        raise ValidationAppError(
            "Password " + ", ".join(problems),
            code="WEAK_PASSWORD",
            details={"field": "password"},
        )


def generate_reset_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """One-way hash used when a token is persisted (never store raw tokens)."""
    from hashlib import sha256

    return sha256(token.encode("utf-8")).hexdigest()


def constant_time_equals(a: Optional[str], b: Optional[str]) -> bool:
    return secrets.compare_digest(a or "", b or "")
