"""``topics`` - optional hierarchy below a subject."""

from typing import List, Optional

from sqlalchemy import ForeignKey, Index, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import ActiveMixin, Base, IDMixin, TimestampMixin


class Topic(IDMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "topics"
    __table_args__ = (Index("ix_topics_subject_id", "subject_id"),)

    subject_id: Mapped[int] = mapped_column(
        ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False
    )
    parent_topic_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("topics.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0, server_default="0")

    subject: Mapped["Subject"] = relationship("Subject", back_populates="topics")  # noqa: F821
    parent: Mapped[Optional["Topic"]] = relationship(
        "Topic", back_populates="children", remote_side="Topic.id"
    )
    children: Mapped[List["Topic"]] = relationship(
        "Topic", back_populates="parent", lazy="selectin"
    )
