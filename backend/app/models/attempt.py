"""``attempts`` and ``attempt_answers`` - historical test-taking records."""

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
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, BigIntPK, IDMixin, Jsonb, TimestampMixin


class Attempt(IDMixin, TimestampMixin, Base):
    __tablename__ = "attempts"
    __table_args__ = (
        UniqueConstraint("test_id", "student_id", "attempt_number", name="uq_attempts_test_student_no"),
        Index("ix_attempts_test_id", "test_id"),
        Index("ix_attempts_student_id", "student_id"),
        Index("ix_attempts_status", "status"),
    )

    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    attempt_number: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1, server_default="1")
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="STARTED", server_default="STARTED"
    )
    score: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False, default=0.0, server_default="0")
    max_score: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False, default=0.0, server_default="0")
    percentage: Mapped[float] = mapped_column(
        Numeric(5, 2), nullable=False, default=0.0, server_default="0"
    )
    submission_type: Mapped[Optional[str]] = mapped_column(String(20))

    test: Mapped["Test"] = relationship("Test", lazy="selectin")  # noqa: F821
    student: Mapped["User"] = relationship("User", lazy="selectin")  # noqa: F821
    answers: Mapped[List["AttemptAnswer"]] = relationship(
        "AttemptAnswer",
        back_populates="attempt",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    result: Mapped[Optional["Result"]] = relationship(  # noqa: F821
        "Result",
        back_populates="attempt",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def is_expired(self) -> bool:
        from app.utils.datetime import ensure_utc, utcnow

        return bool(self.expires_at) and ensure_utc(self.expires_at) <= utcnow()


class AttemptAnswer(IDMixin, Base):
    __tablename__ = "attempt_answers"
    __table_args__ = (
        UniqueConstraint("attempt_id", "question_id", name="uq_attempt_answers_attempt_question"),
        Index("ix_attempt_answers_attempt_id", "attempt_id"),
        Index("ix_attempt_answers_question_id", "question_id"),
    )

    attempt_id: Mapped[int] = mapped_column(
        ForeignKey("attempts.id", ondelete="CASCADE"), nullable=False
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )
    selected_option_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("question_options.id", ondelete="SET NULL"), nullable=True
    )
    # JSON array of selected option IDs for multi-correct questions.
    selected_option_ids = mapped_column(Jsonb, nullable=True)
    answer_text: Mapped[Optional[str]] = mapped_column(String)
    numerical_answer: Mapped[Optional[str]] = mapped_column(String(50))
    is_marked_for_review: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    answered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    attempt: Mapped["Attempt"] = relationship("Attempt", back_populates="answers")
    question: Mapped["Question"] = relationship("Question", lazy="selectin")  # noqa: F821
    selected_option: Mapped[Optional["QuestionOption"]] = relationship(  # noqa: F821
        "QuestionOption", lazy="selectin"
    )
