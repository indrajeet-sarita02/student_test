"""``subjects`` - grouped syllabus areas inside an exam."""

from typing import List, Optional

from sqlalchemy import ForeignKey, Index, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import ActiveMixin, Base, IDMixin, TimestampMixin


class Subject(IDMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "subjects"
    __table_args__ = (
        UniqueConstraint("exam_id", "code", name="uq_subjects_exam_code"),
        Index("ix_subjects_exam_id", "exam_id"),
    )

    exam_id: Mapped[int] = mapped_column(
        ForeignKey("exams.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0, server_default="0")

    exam: Mapped["Exam"] = relationship("Exam", back_populates="subjects")  # noqa: F821
    topics: Mapped[List["Topic"]] = relationship(  # noqa: F821
        "Topic",
        back_populates="subject",
        lazy="selectin",
        order_by="Topic.sort_order",
    )
    questions: Mapped[List["Question"]] = relationship(  # noqa: F821
        "Question",
        back_populates="subject",
        lazy="raise",
    )
