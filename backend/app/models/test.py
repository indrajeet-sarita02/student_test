"""``tests`` and ``test_questions`` (test assembly)."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import AuditMixin, Base, BigIntPK, IDMixin, TimestampMixin


class Test(IDMixin, TimestampMixin, AuditMixin, Base):
    __tablename__ = "tests"
    __table_args__ = (
        Index("ix_tests_exam_id", "exam_id"),
        Index("ix_tests_status", "status"),
    )

    exam_id: Mapped[int] = mapped_column(
        ForeignKey("exams.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    instructions: Mapped[Optional[str]] = mapped_column(Text)
    duration_minutes: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=180)
    total_marks: Mapped[float] = mapped_column(
        Numeric(8, 2), nullable=False, default=0.0, server_default="0"
    )
    passing_marks: Mapped[Optional[float]] = mapped_column(Numeric(8, 2))
    negative_marking_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    negative_marks: Mapped[float] = mapped_column(
        Numeric(6, 2), nullable=False, default=1.0, server_default="0"
    )
    randomize_questions: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    randomize_options: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    max_attempts: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1, server_default="1")
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="DRAFT", server_default="DRAFT"
    )
    scheduled_start_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    scheduled_end_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    exam: Mapped["Exam"] = relationship("Exam", back_populates="tests")  # noqa: F821
    test_questions: Mapped[List["TestQuestion"]] = relationship(
        "TestQuestion",
        back_populates="test",
        lazy="selectin",
        order_by="TestQuestion.question_order",
        cascade="all, delete-orphan",
    )
    assignments: Mapped[List["TestAssignment"]] = relationship(  # noqa: F821
        "TestAssignment",
        back_populates="test",
        lazy="raise",
        cascade="all, delete-orphan",
    )


class TestQuestion(Base):
    __tablename__ = "test_questions"
    __table_args__ = (
        UniqueConstraint("test_id", "question_id", name="uq_test_questions_test_question"),
        UniqueConstraint("test_id", "question_order", name="uq_test_questions_test_order"),
        Index("ix_test_questions_test_id", "test_id"),
        Index("ix_test_questions_question_id", "question_id"),
    )

    id: Mapped[int] = mapped_column(
        BigIntPK,
        primary_key=True,
        autoincrement=True,
    )
    test_id: Mapped[int] = mapped_column(
        ForeignKey("tests.id", ondelete="CASCADE"), nullable=False
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )
    question_order: Mapped[int] = mapped_column(nullable=False, default=1, server_default="1")
    marks_override: Mapped[Optional[float]] = mapped_column(Numeric(6, 2))
    negative_marks_override: Mapped[Optional[float]] = mapped_column(Numeric(6, 2))

    test: Mapped["Test"] = relationship("Test", back_populates="test_questions")
    question: Mapped["Question"] = relationship("Question", lazy="selectin")  # noqa: F821
