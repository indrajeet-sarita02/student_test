"""``test_assignments`` - which students may take which test."""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, SmallInteger, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, BigIntPK, IDMixin, TimestampMixin


class TestAssignment(IDMixin, TimestampMixin, Base):
    __tablename__ = "test_assignments"
    __table_args__ = (
        UniqueConstraint("test_id", "student_id", name="uq_test_assignments_test_student"),
        Index("ix_test_assignments_test_id", "test_id"),
        Index("ix_test_assignments_student_id", "student_id"),
    )

    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    assigned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    available_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    available_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    max_attempts: Mapped[Optional[int]] = mapped_column(SmallInteger)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="ASSIGNED", server_default="ASSIGNED"
    )

    test: Mapped["Test"] = relationship("Test", back_populates="assignments")  # noqa: F821
    student: Mapped["User"] = relationship("User", lazy="selectin")  # noqa: F821
