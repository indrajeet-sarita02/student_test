"""``exams`` - top level container for subjects, topics and questions."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, Index, Numeric, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import ActiveMixin, AuditMixin, Base, IDMixin, TimestampMixin


class Exam(IDMixin, TimestampMixin, AuditMixin, ActiveMixin, Base):
    __tablename__ = "exams"
    __table_args__ = (
        Index("ix_exams_status", "status"),
        Index("ix_exams_exam_type", "exam_type"),
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    exam_type: Mapped[str] = mapped_column(String(30), nullable=False, default="CUSTOM")
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="DRAFT", server_default="DRAFT"
    )
    duration_minutes: Mapped[Optional[int]] = mapped_column(SmallInteger)
    passing_percentage: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    start_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    end_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    subjects: Mapped[List["Subject"]] = relationship(  # noqa: F821
        "Subject",
        back_populates="exam",
        lazy="selectin",
        order_by="Subject.sort_order",
    )
