"""``student_profiles`` - optional profile for users with the STUDENT role."""

from datetime import date
from typing import Optional

from sqlalchemy import Date, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, BigIntPK, IDMixin, TimestampMixin


class StudentProfile(IDMixin, TimestampMixin, Base):
    __tablename__ = "student_profiles"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_student_profiles_user_id"),
        UniqueConstraint("student_code", name="uq_student_profiles_student_code"),
    )

    user_id: Mapped[int] = mapped_column(
        BigIntPK,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_code: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date)
    gender: Mapped[Optional[str]] = mapped_column(String(20))
    institution: Mapped[Optional[str]] = mapped_column(String(200))
    class_name: Mapped[Optional[str]] = mapped_column(String(50))
    roll_number: Mapped[Optional[str]] = mapped_column(String(50))

    user: Mapped["User"] = relationship("User", back_populates="student_profile")  # noqa: F821
