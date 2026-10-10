"""Declarative base and reusable column mixins for every ORM model."""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import JSON as SqliteJSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# BIGSERIAL primary keys. The sqlite variant keeps local/unit tests possible.
BigIntPK = BigInteger().with_variant(Integer, "sqlite")
# JSONB storage with a portable fallback.  ``none_as_null=True`` stores a Python
# ``None`` as SQL NULL rather than the JSON scalar ``null``; the latter breaks
# jsonb functions such as ``jsonb_array_length`` (see report_service).
Jsonb = JSONB(none_as_null=True).with_variant(SqliteJSON(none_as_null=True), "sqlite")


class Base(DeclarativeBase):
    """Shared declarative base for all application models."""


class IDMixin:
    """``id BIGSERIAL PRIMARY KEY``."""

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)


class TimestampMixin:
    """``created_at`` / ``updated_at`` audit timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class ActiveMixin:
    """Soft-disable flag instead of physical deletion."""

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")


class AuditMixin:
    """``created_by`` / ``updated_by`` operator references (nullable)."""

    created_by: Mapped[Optional[int]] = mapped_column(
        BigIntPK, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    updated_by: Mapped[Optional[int]] = mapped_column(
        BigIntPK, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
