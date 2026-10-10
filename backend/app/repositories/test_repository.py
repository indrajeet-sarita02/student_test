"""Query helpers for the tests, test-assembly and assignment modules.

The repository only *reads*: it builds ``SELECT`` statements for the list
endpoints and answers the existence / cardinality questions the service layer
needs to enforce business rules (unique codes, publish preconditions, question
membership and the assigned/attempted guards).

Sort columns are whitelisted; an unknown ``sort_by`` query value never reaches
SQL - it falls back to ``created_at DESC``.
"""

from typing import Any, Dict, FrozenSet, List, Optional, Sequence, Set, Tuple

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.assignment import TestAssignment
from app.models.attempt import Attempt
from app.models.question import Question
from app.models.role import Role
from app.models.test import Test, TestQuestion
from app.models.user import User, UserRole
from app.utils.pagination import PaginationParams

#: Columns clients may pass as ``?sort_by=`` for each entity.
TEST_SORTABLE_COLUMNS: FrozenSet[str] = frozenset(
    {"id", "name", "code", "status", "created_at", "updated_at"}
)
ASSIGNMENT_SORTABLE_COLUMNS: FrozenSet[str] = frozenset(
    {"id", "status", "created_at", "updated_at"}
)

#: Role code a user must hold to receive a test assignment.
STUDENT_ROLE_CODE = "STUDENT"


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


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def build_test_list_stmt(
    params: PaginationParams,
    *,
    exam_id: Optional[int] = None,
) -> Select[Tuple[Test]]:
    """Build the paginated test listing.

    ``params.search`` matches name/code (case-insensitive) and ``params.status``
    matches the uppercase status.
    """
    stmt = select(Test)
    if exam_id is not None:
        stmt = stmt.where(Test.exam_id == exam_id)
    if params.status:
        stmt = stmt.where(Test.status == params.status)
    if params.search:
        pattern = f"%{params.search}%"
        stmt = stmt.where(or_(Test.name.ilike(pattern), Test.code.ilike(pattern)))
    return _apply_sort(stmt, Test, params, TEST_SORTABLE_COLUMNS)


def get_test(db: Session, test_id: int) -> Optional[Test]:
    """Return the test with ``test_id`` or ``None``."""
    return db.get(Test, test_id)


def test_code_exists(
    db: Session, code: str, exclude_test_id: Optional[int] = None
) -> bool:
    """True when a test already uses the globally unique ``code``."""
    stmt = select(Test.id).where(func.lower(Test.code) == code.strip().lower())
    if exclude_test_id is not None:
        stmt = stmt.where(Test.id != exclude_test_id)
    return db.scalar(stmt.limit(1)) is not None


def count_test_questions(db: Session, test_id: int) -> int:
    """Number of questions attached to the test."""
    stmt = (
        select(func.count())
        .select_from(TestQuestion)
        .where(TestQuestion.test_id == test_id)
    )
    return int(db.scalar(stmt) or 0)


def count_test_assignments(db: Session, test_id: int) -> int:
    """Number of student assignments for the test."""
    stmt = (
        select(func.count())
        .select_from(TestAssignment)
        .where(TestAssignment.test_id == test_id)
    )
    return int(db.scalar(stmt) or 0)


def count_test_attempts(db: Session, test_id: int) -> int:
    """Number of attempts recorded against the test."""
    stmt = select(func.count()).select_from(Attempt).where(Attempt.test_id == test_id)
    return int(db.scalar(stmt) or 0)


def max_question_order(db: Session, test_id: int) -> int:
    """Highest ``question_order`` currently used by the test (0 when empty)."""
    stmt = select(func.max(TestQuestion.question_order)).where(
        TestQuestion.test_id == test_id
    )
    return int(db.scalar(stmt) or 0)


def get_test_question(
    db: Session, test_id: int, question_id: int
) -> Optional[TestQuestion]:
    """Return the membership row linking question to test, or ``None``."""
    stmt = (
        select(TestQuestion)
        .where(
            TestQuestion.test_id == test_id,
            TestQuestion.question_id == question_id,
        )
        .limit(1)
    )
    return db.scalar(stmt)


def get_test_questions(db: Session, test_id: int) -> List[TestQuestion]:
    """All membership rows of the test ordered by ``question_order``."""
    stmt = (
        select(TestQuestion)
        .where(TestQuestion.test_id == test_id)
        .order_by(TestQuestion.question_order.asc(), TestQuestion.id.asc())
    )
    return list(db.scalars(stmt).all())


def list_test_question_ids(db: Session, test_id: int) -> Set[int]:
    """Set of question ids already attached to the test."""
    stmt = select(TestQuestion.question_id).where(TestQuestion.test_id == test_id)
    return set(db.scalars(stmt).all())


def get_questions_by_ids(
    db: Session, question_ids: Sequence[int]
) -> Dict[int, Question]:
    """Fetch questions by id, keyed by id (missing ids are simply absent)."""
    unique_ids = list(dict.fromkeys(question_ids))
    if not unique_ids:
        return {}
    rows = db.scalars(select(Question).where(Question.id.in_(unique_ids))).all()
    return {question.id: question for question in rows}


def compute_total_marks(db: Session, test_id: int) -> float:
    """Sum of ``marks_override`` (when set) or the question's own marks."""
    stmt = (
        select(
            func.coalesce(
                func.sum(func.coalesce(TestQuestion.marks_override, Question.marks)),
                0,
            )
        )
        .select_from(TestQuestion)
        .join(Question, Question.id == TestQuestion.question_id)
        .where(TestQuestion.test_id == test_id)
    )
    return float(db.scalar(stmt) or 0)


# ---------------------------------------------------------------------------
# Assignments
# ---------------------------------------------------------------------------


def build_assignment_list_stmt(
    params: PaginationParams,
    *,
    test_id: Optional[int] = None,
    student_id: Optional[int] = None,
) -> Select[Tuple[TestAssignment]]:
    """Build the paginated assignment listing filtered by test/student/status."""
    stmt = select(TestAssignment).options(selectinload(TestAssignment.test))
    if test_id is not None:
        stmt = stmt.where(TestAssignment.test_id == test_id)
    if student_id is not None:
        stmt = stmt.where(TestAssignment.student_id == student_id)
    if params.status:
        stmt = stmt.where(TestAssignment.status == params.status)
    return _apply_sort(stmt, TestAssignment, params, ASSIGNMENT_SORTABLE_COLUMNS)


def get_assignment(db: Session, assignment_id: int) -> Optional[TestAssignment]:
    """Return the assignment with ``assignment_id`` or ``None``."""
    return db.get(TestAssignment, assignment_id)


def assignment_exists(db: Session, test_id: int, student_id: int) -> bool:
    """True when the ``(test_id, student_id)`` assignment already exists."""
    stmt = (
        select(TestAssignment.id)
        .where(
            TestAssignment.test_id == test_id,
            TestAssignment.student_id == student_id,
        )
        .limit(1)
    )
    return db.scalar(stmt) is not None


def existing_assignment_student_ids(
    db: Session, test_id: int, student_ids: Sequence[int]
) -> Set[int]:
    """Subset of ``student_ids`` already assigned to the test."""
    unique_ids = list(dict.fromkeys(student_ids))
    if not unique_ids:
        return set()
    stmt = select(TestAssignment.student_id).where(
        TestAssignment.test_id == test_id,
        TestAssignment.student_id.in_(unique_ids),
    )
    return set(db.scalars(stmt).all())


def student_role_user_ids(db: Session, user_ids: Sequence[int]) -> Set[int]:
    """Subset of ``user_ids`` that exist and hold the ``STUDENT`` role."""
    unique_ids = list(dict.fromkeys(user_ids))
    if not unique_ids:
        return set()
    stmt = (
        select(User.id)
        .join(UserRole, UserRole.user_id == User.id)
        .join(Role, Role.id == UserRole.role_id)
        .where(User.id.in_(unique_ids), func.upper(Role.code) == STUDENT_ROLE_CODE)
    )
    return set(db.scalars(stmt).all())


def count_assignment_attempts(db: Session, test_id: int, student_id: int) -> int:
    """Number of attempts by ``student_id`` on ``test_id``."""
    stmt = (
        select(func.count())
        .select_from(Attempt)
        .where(Attempt.test_id == test_id, Attempt.student_id == student_id)
    )
    return int(db.scalar(stmt) or 0)


def decorate_assignment(assignment: TestAssignment) -> TestAssignment:
    """Attach the denormalised ``test_name`` / ``student_name`` fields.

    These are not mapped columns; they are transient attributes consumed by
    ``AssignmentResponse`` (``from_attributes``) so the list/detail endpoints
    avoid an extra serialisation layer.
    """
    test = assignment.test
    student = assignment.student
    assignment.test_name = test.name if test is not None else None
    assignment.student_name = student.full_name if student is not None else None
    assignment.student_email = student.email if student is not None else None
    return assignment
