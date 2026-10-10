"""Date/time helpers. All application date-times are stored as UTC."""

from datetime import datetime, timezone
from typing import Optional


def utcnow() -> datetime:
    """Return the current timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


def ensure_utc(value: Optional[datetime]) -> Optional[datetime]:
    """Attach/convert a datetime to UTC so comparisons never fail."""
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def to_naive_utc(value: Optional[datetime]) -> Optional[datetime]:
    """Convert to naive UTC (PostgreSQL ``TIMESTAMP WITH TIME ZONE`` round-trips
    fine either way, but this keeps stored values uniform)."""
    value = ensure_utc(value)
    return None if value is None else value.astimezone(timezone.utc).replace(tzinfo=None)


def iso(value: Optional[datetime]) -> Optional[str]:
    value = ensure_utc(value)
    return None if value is None else value.isoformat()
