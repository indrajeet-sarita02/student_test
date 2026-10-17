"""Query helpers for the question-bank module.

The repository only *reads*: it builds ``SELECT`` statements for the list
endpoint and answers the existence / cardinality questions the service layer
needs to enforce business rules (question referenced by tests or attempts).

Sort columns are whitelisted; an unknown ``sort_by`` query value never reaches
SQL - it falls back to ``created_at DESC``.
"""

from typing import FrozenSet, Optional, Tuple

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models.attempt import Attempt
from app.models.question import Question, QuestionOption
from app.models.test import TestQuestion
from app.utils.pagination import PaginationParams

#: Columns clients may pass as ``?sort_by=`` on the question listing.
QUESTION_SORTABLE_COLUMNS: FrozenSet[str] = frozenset(
    {"id", "created_at", "updated_at", "marks", "difficulty", "status"}
)


def _apply_sort(
    stmt: Select,
    model: type,
    params: PaginationParams,
    sortable: FrozenSet[str],
) -> Select:
    """Order ``stmt`` by an allowed column; unknown values fall back to
    ``created_at DESC`` (with ``id`` as a stable tie-breaker)."""
    if params.sort_by in sortable and hasattr(model, params.sort_by):
        column = getattr(model, params.sort_by)
        descending = params.sort_order != "asc"
    else:
        column = model.created_at
        descending = True
    return stmt.order_by(
        column.desc() if descending else column.asc(),
        model.id.desc() if descending else model.id.asc(),
    )


def build_question_list_stmt(
    params: PaginationParams,
    *,
    subject_id: Optional[int] = None,
    topic_id: Optional[int] = None,
    question_type: Optional[str] = None,
    difficulty: Optional[str] = None,
    tag: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> Select[Tuple[Question]]:
    """Build the paginated question listing.

    ``params.search`` matches ``question_text`` (case-insensitive);
    ``params.status`` matches the uppercase status. Extra keyword arguments
    cover the ``subject_id`` / ``topic_id`` / ``question_type`` / ``difficulty``
    / ``tag`` / ``is_active`` filters.
    """
    stmt = select(Question)
    if subject_id is not None:
        stmt = stmt.where(Question.subject_id == subject_id)
    if topic_id is not None:
        stmt = stmt.where(Question.topic_id == topic_id)
    if params.status:
        stmt = stmt.where(Question.status == params.status)
    if question_type:
        stmt = stmt.where(Question.question_type == question_type)
    if difficulty:
        stmt = stmt.where(Question.difficulty == difficulty)
    if tag:
        # ``tags`` is a JSONB array; containment checks membership exactly.
        stmt = stmt.where(Question.tags.contains([tag]))
    if is_active is not None:
        stmt = stmt.where(Question.is_active == is_active)
    if params.search:
        pattern = f"%{params.search}%"
        stmt = stmt.where(Question.question_text.ilike(pattern))
    return _apply_sort(stmt, Question, params, QUESTION_SORTABLE_COLUMNS)


def get_question(db: Session, question_id: int) -> Optional[Question]:
    """Return the question with ``question_id`` or ``None``."""
    return db.get(Question, question_id)


def get_question_option(db: Session, option_id: int) -> Optional[QuestionOption]:
    """Return the option with ``option_id`` or ``None``."""
    return db.get(QuestionOption, option_id)


def question_is_referenced(db: Session, question_id: int) -> bool:
    """True when any ``test_questions`` row references the question."""
    stmt = (
        select(TestQuestion.id)
        .where(TestQuestion.question_id == question_id)
        .limit(1)
    )
    return db.scalar(stmt) is not None


def question_referenced_by_attempted_test(db: Session, question_id: int) -> bool:
    """True when the question belongs to a test that already has attempts."""
    stmt = (
        select(TestQuestion.id)
        .join(Attempt, Attempt.test_id == TestQuestion.test_id)
        .where(TestQuestion.question_id == question_id)
        .limit(1)
    )
    return db.scalar(stmt) is not None


def count_question_references(db: Session, question_id: int) -> int:
    """Number of ``test_questions`` rows referencing the question."""
    stmt = (
        select(func.count())
        .select_from(TestQuestion)
        .where(TestQuestion.question_id == question_id)
    )
    return int(db.scalar(stmt) or 0)
