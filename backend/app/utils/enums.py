"""Shared enumerations used across models, schemas, services and API layers."""

from enum import Enum


class StrEnum(str, Enum):
    """A string enum that serialises to its value."""

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


class UserStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
    PENDING = "PENDING"


class Gender(StrEnum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class ExamType(StrEnum):
    NEET = "NEET"
    JEE = "JEE"
    UPSC = "UPSC"
    SSC = "SSC"
    CUSTOM = "CUSTOM"


class ExamStatus(StrEnum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class QuestionType(StrEnum):
    SINGLE_CHOICE = "SINGLE_CHOICE"
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    TRUE_FALSE = "TRUE_FALSE"
    NUMERICAL = "NUMERICAL"
    SUBJECTIVE = "SUBJECTIVE"


class QuestionStatus(StrEnum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class Difficulty(StrEnum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"


class NotificationType(StrEnum):
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
