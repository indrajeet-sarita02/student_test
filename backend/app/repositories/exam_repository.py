"""Query helpers for the exam / subject / topic module.

The repository only *reads*: it builds ``SELECT`` statements for the list
endpoints and answers the existence / cardinality questions the service layer
needs to enforce business rules (unique codes, publish preconditions, and the
soft-delete vs. hard-delete decision).

Sort columns are whitelisted per entity; an unknown ``sort_by`` query value
never reaches SQL - it falls back to ``created_at DESC``.
"""

from typing import FrozenSet, Optional, Tuple

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.models.exam import Exam
from app.models.question import Question
from app.models.subject import Subject
from app.models.topic import Topic
from app.utils.pagination import PaginationParams

#: Columns clients may pass as ``?sort_by=`` for each entity.
EXAM_SORTABLE_COLUMNS: FrozenSet[str] = frozenset(
    {"id", "name", "code", "created_at", "status"}
)
SUBJECT_SORTABLE_COLUMNS: FrozenSet[str] = frozenset(
    {"id", "name", "code", "created_at"}
)
TOPIC_SORTABLE_COLUMNS: FrozenSet[str] = frozenset({"id", "name", "created_at"})


def _apply_sort(
    stmt: Select,
    model: type,
    params: PaginationParams,
    sortable: FrozenSet[str],
) -> Select:
    """Order ``stmt`` by an allowed column; unknown columns fall back to
    ``created_at DESC``."""
    if params.sort_by in sortable:
        column = getattr(model, params.sort_by)
        descending = params.sort_order != "asc"
    else:
        column = getattr(model, "created_at")
        descending = True
    return stmt.order_by(column.desc() if descending else column.asc())


def _count(db: Session, model: type, *criteria) -> int:
    """``SELECT COUNT(*)`` over ``model`` filtered by ``criteria``."""
    stmt = select(func.count()).select_from(model)
    if criteria:
        stmt = stmt.where(*criteria)
    return int(db.scalar(stmt) or 0)


# ---------------------------------------------------------------------------
# Exams
# ---------------------------------------------------------------------------


def build_exam_list_stmt(
    params: PaginationParams,
    *,
    exam_type: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> Select[Tuple[Exam]]:
    """Build the paginated exam listing.

    ``params.search`` matches name/code/description (case-insensitive),
    ``params.status`` matches the uppercase status, and the keyword arguments
    cover the extra ``exam_type`` / ``is_active`` query filters.
    """
    stmt = select(Exam)
    if params.search:
        pattern = f"%{params.search}%"
        stmt = stmt.where(
            or_(
                Exam.name.ilike(pattern),
                Exam.code.ilike(pattern),
                Exam.description.ilike(pattern),
            )
        )
    if params.status:
        stmt = stmt.where(Exam.status == params.status)
    if exam_type is not None:
        stmt = stmt.where(Exam.exam_type == exam_type)
    if is_active is not None:
        stmt = stmt.where(Exam.is_active == is_active)
    return _apply_sort(stmt, Exam, params, EXAM_SORTABLE_COLUMNS)


def get_exam(db: Session, exam_id: int) -> Optional[Exam]:
    """Return the exam with ``exam_id`` or ``None``."""
    return db.get(Exam, exam_id)


def exam_code_exists(db: Session, code: str) -> bool:
    """True when an exam already uses the globally unique ``code``."""
    return (
        db.scalar(select(Exam.id).where(Exam.code == code).limit(1)) is not None
    )


def count_exam_subjects(db: Session, exam_id: int) -> int:
    """Number of subjects (any activation state) owned by the exam."""
    return _count(db, Subject, Subject.exam_id == exam_id)


# ---------------------------------------------------------------------------
# Subjects
# ---------------------------------------------------------------------------


def build_subject_list_stmt(
    params: PaginationParams,
    *,
    exam_id: Optional[int] = None,
    is_active: Optional[bool] = None,
) -> Select[Tuple[Subject]]:
    """Build the paginated subject listing filtered by exam, search and flag."""
    stmt = select(Subject)
    if exam_id is not None:
        stmt = stmt.where(Subject.exam_id == exam_id)
    if params.search:
        pattern = f"%{params.search}%"
        stmt = stmt.where(or_(Subject.name.ilike(pattern), Subject.code.ilike(pattern)))
    if is_active is not None:
        stmt = stmt.where(Subject.is_active == is_active)
    return _apply_sort(stmt, Subject, params, SUBJECT_SORTABLE_COLUMNS)


def get_subject(db: Session, subject_id: int) -> Optional[Subject]:
    """Return the subject with ``subject_id`` or ``None``."""
    return db.get(Subject, subject_id)


def subject_code_exists(db: Session, exam_id: int, code: str) -> bool:
    """True when the ``(exam_id, code)`` pair is already taken."""
    return (
        db.scalar(
            select(Subject.id)
            .where(Subject.exam_id == exam_id, Subject.code == code)
            .limit(1)
        )
        is not None
    )


def count_subject_topics(db: Session, subject_id: int) -> int:
    """Number of topics (any activation state) under the subject."""
    return _count(db, Topic, Topic.subject_id == subject_id)


def count_subject_questions(db: Session, subject_id: int) -> int:
    """Number of question-bank rows referencing the subject."""
    return _count(db, Question, Question.subject_id == subject_id)


# ---------------------------------------------------------------------------
# Topics
# ---------------------------------------------------------------------------


def build_topic_list_stmt(
    params: PaginationParams,
    *,
    subject_id: Optional[int] = None,
    parent_topic_id: Optional[int] = None,
    is_active: Optional[bool] = None,
) -> Select[Tuple[Topic]]:
    """Build the paginated topic listing filtered by hierarchy and search."""
    stmt = select(Topic)
    if subject_id is not None:
        stmt = stmt.where(Topic.subject_id == subject_id)
    if parent_topic_id is not None:
        stmt = stmt.where(Topic.parent_topic_id == parent_topic_id)
    if params.search:
        pattern = f"%{params.search}%"
        stmt = stmt.where(
            or_(Topic.name.ilike(pattern), Topic.description.ilike(pattern))
        )
    if is_active is not None:
        stmt = stmt.where(Topic.is_active == is_active)
    return _apply_sort(stmt, Topic, params, TOPIC_SORTABLE_COLUMNS)


def get_topic(db: Session, topic_id: int) -> Optional[Topic]:
    """Return the topic with ``topic_id`` or ``None``."""
    return db.get(Topic, topic_id)


def count_topic_children(db: Session, topic_id: int) -> int:
    """Number of child topics hanging below the topic."""
    return _count(db, Topic, Topic.parent_topic_id == topic_id)


def count_topic_questions(db: Session, topic_id: int) -> int:
    """Number of question-bank rows referencing the topic."""
    return _count(db, Question, Question.topic_id == topic_id)
