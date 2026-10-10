"""``results`` - evaluated outcome of an attempt."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, Numeric, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IDMixin, TimestampMixin


class Result(IDMixin, TimestampMixin, Base):
    __tablename__ = "results"
    __table_args__ = (
        Index("ix_results_attempt_id", "attempt_id"),
        Index("ix_results_student_id", "student_id"),
        Index("ix_results_test_id", "test_id"),
    )

    attempt_id: Mapped[int] = mapped_column(
        ForeignKey("attempts.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id", ondelete="CASCADE"), nullable=False)
    score: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False, default=0.0, server_default="0")
    max_score: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False, default=0.0, server_default="0")
    percentage: Mapped[float] = mapped_column(
        Numeric(5, 2), nullable=False, default=0.0, server_default="0"
    )
    correct_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    incorrect_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    unanswered_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    rank: Mapped[Optional[int]] = mapped_column(SmallInteger)
    percentile: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    pass_status: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    attempt: Mapped["Attempt"] = relationship("Attempt", back_populates="result")  # noqa: F821
    student: Mapped["User"] = relationship("User", lazy="selectin")  # noqa: F821
    test: Mapped["Test"] = relationship("Test", lazy="selectin")  # noqa: F821
