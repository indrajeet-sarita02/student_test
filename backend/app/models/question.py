"""``questions`` and ``question_options`` (the question bank)."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import ActiveMixin, AuditMixin, Base, IDMixin, TimestampMixin
from app.db.base import Jsonb


class Question(IDMixin, TimestampMixin, AuditMixin, ActiveMixin, Base):
    __tablename__ = "questions"
    __table_args__ = (
        Index("ix_questions_subject_id", "subject_id"),
        Index("ix_questions_topic_id", "topic_id"),
        Index("ix_questions_status", "status"),
        Index("ix_questions_question_type", "question_type"),
    )

    subject_id: Mapped[int] = mapped_column(
        ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False
    )
    topic_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("topics.id", ondelete="SET NULL"), nullable=True
    )
    question_type: Mapped[str] = mapped_column(String(30), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[Optional[str]] = mapped_column(Text)
    difficulty: Mapped[str] = mapped_column(
        String(15), nullable=False, default="MEDIUM", server_default="MEDIUM"
    )
    marks: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False, default=4.0, server_default="0")
    negative_marks: Mapped[float] = mapped_column(
        Numeric(6, 2), nullable=False, default=0.0, server_default="0"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="DRAFT", server_default="DRAFT"
    )
    source: Mapped[Optional[str]] = mapped_column(String(100))
    # Free-form labels used for filtering/searching the question bank.
    tags = mapped_column(Jsonb, nullable=True)
    # Optional image / media payload.
    media: Mapped[Optional[str]] = mapped_column(Text)
    metadata_json = mapped_column(Jsonb, nullable=True)

    subject: Mapped["Subject"] = relationship("Subject", back_populates="questions")  # noqa: F821
    topic: Mapped[Optional["Topic"]] = relationship("Topic", lazy="selectin")  # noqa: F821
    options: Mapped[List["QuestionOption"]] = relationship(
        "QuestionOption",
        back_populates="question",
        lazy="selectin",
        order_by="QuestionOption.option_order",
        cascade="all, delete-orphan",
    )


class QuestionOption(IDMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "question_options"
    __table_args__ = (
        UniqueConstraint("question_id", "option_order", name="uq_question_options_order"),
        Index("ix_question_options_question_id", "question_id"),
    )

    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )
    option_text: Mapped[str] = mapped_column(Text, nullable=False)
    option_order: Mapped[int] = mapped_column(nullable=False, default=1, server_default="1")
    is_correct: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    question: Mapped["Question"] = relationship("Question", back_populates="options")
