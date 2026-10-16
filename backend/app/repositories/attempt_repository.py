"""Read/query helpers for the test engine (attempts, answers, results).

The repository only builds ``SELECT`` statements and answers small existence /
cardinality questions for :mod:`app.services.attempt_service` and the routers.
It never commits: all mutations happen in the service layer inside a single
transaction.

Sort columns are whitelisted per entity; an unknown ``?sort_by=`` never reaches
SQL and falls back to the entity's ``created_at DESC``.
"""

from datetime import datetime
from typing import Any, Dict, FrozenSet, List, Optional, Sequence, Tuple

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.orm import Session, aliased, selectinload

from app.models.assignment import TestAssignment
from app.models.attempt import Attempt, AttemptAnswer
from app.models.question import Question
from app.models.result import Result
from app.models.test import Test, TestQuestion
from app.models.user import User
from app.utils.enums import AssignmentStatus, AttemptStatus
from app.utils.pagination import PaginationParams, build_page

ATTEMPT_SORTABLE_COLUMNS: FrozenSet[str] = frozenset(
    {"id", "created_at", "started_at", "submitted_at", "score", "percentage", "status"}
)
RESULT_SORTABLE_COLUMNS: FrozenSet[str] = frozenset(
    {"id", "created_at", "score", "percentage", "rank", "published_at"}
)


def paginate_query(db: Session, stmt: Select, params: PaginationParams) -> Dict[str, Any]:
    """Apply ``LIMIT/OFFSET`` plus ``total``/``total_pages`` to a select.

    This mirrors :func:`app.utils.pagination.paginate`, but is reimplemented
    locally because the shared helper's ``select_count`` references an
    undefined ``select`` name (a pre-existing foundation bug). ``app/utils`` is
    protected and therefore never edited by this module.
    """
    total = int(
        db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    )
    rows = db.scalars(stmt.offset(params.offset).limit(params.limit)).all()
    return build_page(rows, params.page, params.page_size, total)


def _apply_sort(
    stmt: Select,
    model: Any,
    params: PaginationParams,
    sortable: FrozenSet[str],
) -> Select:
    """Order ``stmt`` by a whitelisted column, else ``created_at DESC``."""
    if params.sort_by in sortable:
        column = getattr(model, params.sort_by)
        descending = params.sort_order != "asc"
    else:
        column = getattr(model, "created_at")
        descending = True
    return stmt.order_by(column.desc() if descending else column.asc(), model.id.desc())


# ---------------------------------------------------------------------------
# Tests / assignments / attempts
# ---------------------------------------------------------------------------


def get_test_with_questions(db: Session, test_id: int) -> Optional[Test]:
    """Load a test together with its ordered questions and their options."""
    stmt = (
        select(Test)
        .where(Test.id == test_id)
        .options(
            selectinload(Test.test_questions)
            .selectinload(TestQuestion.question)
            .selectinload(Question.options)
        )
    )
    return db.scalars(stmt).first()


def get_test(db: Session, test_id: int) -> Optional[Test]:
    """Return the test row (without eager question loading) or ``None``."""
    return db.get(Test, test_id)


def get_attempt(db: Session, attempt_id: int, *, for_update: bool = False) -> Optional[Attempt]:
    """Return an attempt, optionally taking a fresh row-level lock.

    ``populate_existing`` guarantees the locked read refreshes any instance
    already present in the session identity map, which is essential for the
    submission state machine under concurrency.
    """
    stmt = select(Attempt).where(Attempt.id == attempt_id)
    if for_update:
        stmt = stmt.execution_options(populate_existing=True).with_for_update()
    return db.scalars(stmt).first()


def get_assignment(db: Session, test_id: int, student_id: int) -> Optional[TestAssignment]:
    """Active (non-cancelled) assignment of one student for one test."""
    return db.scalars(
        select(TestAssignment).where(
            TestAssignment.test_id == test_id,
            TestAssignment.student_id == student_id,
            TestAssignment.status != AssignmentStatus.CANCELLED.value,
        )
    ).first()


def count_assignments(db: Session, test_id: int) -> int:
    """Number of non-cancelled assignments a test has (0 => open test)."""
    return int(
        db.scalar(
            select(func.count())
            .select_from(TestAssignment)
            .where(
                TestAssignment.test_id == test_id,
                TestAssignment.status != AssignmentStatus.CANCELLED.value,
            )
        )
        or 0
    )


def count_student_attempts(db: Session, test_id: int, student_id: int) -> int:
    """Non-cancelled attempts a student has made on a test."""
    return int(
        db.scalar(
            select(func.count())
            .select_from(Attempt)
            .where(
                Attempt.test_id == test_id,
                Attempt.student_id == student_id,
                Attempt.status != AttemptStatus.CANCELLED.value,
            )
        )
        or 0
    )


def get_started_attempts(db: Session, test_id: int, student_id: int) -> List[Attempt]:
    """All ``STARTED`` attempts of a student on a test (normally at most one)."""
    return list(
        db.scalars(
            select(Attempt).where(
                Attempt.test_id == test_id,
                Attempt.student_id == student_id,
                Attempt.status == AttemptStatus.STARTED.value,
            )
        ).all()
    )


def count_test_questions(db: Session, test_id: int) -> int:
    """Number of questions assembled into a test."""
    return int(
        db.scalar(
            select(func.count())
            .select_from(TestQuestion)
            .where(TestQuestion.test_id == test_id)
        )
        or 0
    )


def get_answers(db: Session, attempt_id: int) -> List[AttemptAnswer]:
    """All persisted answers of an attempt."""
    return list(
        db.scalars(
            select(AttemptAnswer).where(AttemptAnswer.attempt_id == attempt_id)
        ).all()
    )


def build_attempt_list_stmt(
    params: PaginationParams,
    *,
    test_id: Optional[int] = None,
    student_id: Optional[int] = None,
    status: Optional[str] = None,
) -> Select:
    """Admin attempt listing with optional test/student/status filters."""
    stmt = select(Attempt)
    if test_id is not None:
        stmt = stmt.where(Attempt.test_id == test_id)
    if student_id is not None:
        stmt = stmt.where(Attempt.student_id == student_id)
    if status:
        stmt = stmt.where(Attempt.status == status)
    if params.search:
        pattern = f"%{params.search}%"
        stmt = (
            stmt.outerjoin(Test, Test.id == Attempt.test_id)
            .outerjoin(User, User.id == Attempt.student_id)
            .where(
                or_(
                    Test.name.ilike(pattern),
                    User.username.ilike(pattern),
                    User.first_name.ilike(pattern),
                    User.last_name.ilike(pattern),
                )
            )
        )
    return _apply_sort(stmt, Attempt, params, ATTEMPT_SORTABLE_COLUMNS)


def build_student_test_stmt(
    *,
    student_id: int,
    now: datetime,
    search: Optional[str] = None,
) -> Select:
    """Visible published tests for a student, with the student's assignment row.

    Visibility rule: the test is assigned to the student **or** the test has no
    non-cancelled assignments at all (an "open" test). The test must be
    currently inside its scheduled window; assigned tests must additionally be
    inside their per-student availability window.
    """
    stmt = select(Test, TestAssignment)
    stmt = stmt.outerjoin(
        TestAssignment,
        and_(
            TestAssignment.test_id == Test.id,
            TestAssignment.student_id == student_id,
            TestAssignment.status != AssignmentStatus.CANCELLED.value,
        ),
    )
    # The outer query already joins ``TestAssignment`` (the current student's
    # assignment).  The EXISTS probe must therefore reference an *alias*: using
    # the same entity twice makes SQLAlchemy auto-correlate the subquery against
    # the outer join and emit a statement with no FROM clause
    # ("returned no FROM clauses due to auto-correlation").
    assigned = aliased(TestAssignment)
    other_assignment = (
        select(assigned.id)
        .where(
            assigned.test_id == Test.id,
            assigned.status != AssignmentStatus.CANCELLED.value,
        )
        .correlate(Test)
        .exists()
    )
    stmt = stmt.where(
        or_(TestAssignment.id.isnot(None), ~other_assignment)
    )
    stmt = stmt.where(
        or_(Test.scheduled_start_at.is_(None), Test.scheduled_start_at <= now),
        or_(Test.scheduled_end_at.is_(None), Test.scheduled_end_at >= now),
        or_(
            TestAssignment.id.is_(None),
            and_(
                or_(
                    TestAssignment.available_from.is_(None),
                    TestAssignment.available_from <= now,
                ),
                or_(
                    TestAssignment.available_until.is_(None),
                    TestAssignment.available_until >= now,
                ),
            ),
        ),
    )
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(or_(Test.name.ilike(pattern), Test.code.ilike(pattern)))
    return stmt.order_by(Test.created_at.desc(), Test.id.desc())


def bulk_attempt_counts(
    db: Session, test_ids: Sequence[int], student_id: int
) -> Dict[int, int]:
    """``{test_id: non-cancelled attempt count}`` for one student."""
    if not test_ids:
        return {}
    rows = db.execute(
        select(Attempt.test_id, func.count())
        .where(
            Attempt.student_id == student_id,
            Attempt.test_id.in_(list(test_ids)),
            Attempt.status != AttemptStatus.CANCELLED.value,
        )
        .group_by(Attempt.test_id)
    ).all()
    return {int(test_id): int(count) for test_id, count in rows}


def bulk_active_attempts(
    db: Session, test_ids: Sequence[int], student_id: int
) -> Dict[int, Attempt]:
    """``{test_id: STARTED attempt}`` for one student."""
    if not test_ids:
        return {}
    rows = db.scalars(
        select(Attempt).where(
            Attempt.student_id == student_id,
            Attempt.test_id.in_(list(test_ids)),
            Attempt.status == AttemptStatus.STARTED.value,
        )
    ).all()
    return {int(attempt.test_id): attempt for attempt in rows}


def bulk_question_counts(db: Session, test_ids: Sequence[int]) -> Dict[int, int]:
    """``{test_id: question count}`` for a batch of tests."""
    if not test_ids:
        return {}
    rows = db.execute(
        select(TestQuestion.test_id, func.count())
        .where(TestQuestion.test_id.in_(list(test_ids)))
        .group_by(TestQuestion.test_id)
    ).all()
    return {int(test_id): int(count) for test_id, count in rows}


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------


def get_result(db: Session, result_id: int) -> Optional[Result]:
    """Return one result row or ``None``."""
    return db.get(Result, result_id)


def get_result_by_attempt(db: Session, attempt_id: int) -> Optional[Result]:
    """Return the result belonging to an attempt, if any."""
    return db.scalars(select(Result).where(Result.attempt_id == attempt_id)).first()


def build_result_list_stmt(
    params: PaginationParams,
    *,
    test_id: Optional[int] = None,
    student_id: Optional[int] = None,
    published: Optional[bool] = None,
) -> Select:
    """Admin result listing with test/student/published filters and search."""
    stmt = select(Result).options(
        selectinload(Result.student),
        selectinload(Result.test),
        selectinload(Result.attempt),
    )
    if test_id is not None:
        stmt = stmt.where(Result.test_id == test_id)
    if student_id is not None:
        stmt = stmt.where(Result.student_id == student_id)
    if published is not None:
        stmt = stmt.where(
            Result.published_at.isnot(None)
            if published
            else Result.published_at.is_(None)
        )
    if params.search:
        pattern = f"%{params.search}%"
        stmt = stmt.join(User, User.id == Result.student_id).where(
            or_(
                User.username.ilike(pattern),
                User.first_name.ilike(pattern),
                User.last_name.ilike(pattern),
            )
        )
    return _apply_sort(stmt, Result, params, RESULT_SORTABLE_COLUMNS)


def build_student_result_stmt(
    params: PaginationParams,
    *,
    student_id: int,
    test_id: Optional[int] = None,
) -> Select:
    """Own results of a student (always includes unpublished results)."""
    stmt = select(Result).where(Result.student_id == student_id).options(
        selectinload(Result.student),
        selectinload(Result.test),
        selectinload(Result.attempt),
    )
    if test_id is not None:
        stmt = stmt.where(Result.test_id == test_id)
    return _apply_sort(stmt, Result, params, RESULT_SORTABLE_COLUMNS)


def count_results(db: Session, test_id: int) -> int:
    """Total results recorded for a test."""
    return int(
        db.scalar(
            select(func.count()).select_from(Result).where(Result.test_id == test_id)
        )
        or 0
    )


def count_higher_scores(db: Session, test_id: int, score: float, exclude_id: int) -> int:
    """Results of the same test that scored strictly higher than ``score``."""
    return int(
        db.scalar(
            select(func.count())
            .select_from(Result)
            .where(
                Result.test_id == test_id,
                Result.score > score,
                Result.id != exclude_id,
            )
        )
        or 0
    )


def count_lower_equal_percentage(db: Session, test_id: int, percentage: float) -> int:
    """Results of the same test whose percentage is <= ``percentage``."""
    return int(
        db.scalar(
            select(func.count())
            .select_from(Result)
            .where(Result.test_id == test_id, Result.percentage <= percentage)
        )
        or 0
    )
