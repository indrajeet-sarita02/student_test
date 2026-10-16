"""Test-assembly service: CRUD, publish/close and question management.

Business rules enforced here:

* publish requires a ``DRAFT`` test with at least one question and recomputes
  ``total_marks`` from the effective marks of each attached question;
* close is only allowed from ``PUBLISHED``;
* once a test has attempts, questions can no longer be added or removed and the
  test itself cannot be deleted.

Every mutation owns its transaction (``flush`` for ids, one ``commit`` on
success) and writes an audit entry in the same transaction.
"""

from enum import Enum
from typing import Any, Dict, Optional

from fastapi import Request
from sqlalchemy import delete as sa_delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    BadRequestError,
    ConflictError,
    NotFoundError,
)
from app.models.question import Question
from app.models.test import Test, TestQuestion
from app.repositories import exam_repository
from app.repositories import question_repository
from app.repositories import test_repository as repository
from app.schemas.test import TestCreate, TestQuestionAdd, TestQuestionsBulkAdd, TestUpdate
from app.services.audit_service import record_audit
from app.utils.enums import QuestionStatus, TestStatus
from app.utils.pagination import PaginationParams, paginate


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _commit(db: Session) -> None:
    """Commit the current transaction, rolling back before re-raising."""
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def _audit(
    db: Session,
    *,
    user_id: int,
    action: str,
    entity_id: Optional[int],
    old_data: Optional[Dict[str, Any]] = None,
    new_data: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None,
) -> None:
    """Append one ``test`` audit row for a successful (pending) mutation."""
    record_audit(
        db,
        user_id=user_id,
        module="test",
        action=action,
        entity_type="test",
        entity_id=entity_id,
        old_data=old_data,
        new_data=new_data,
        request=request,
    )


def _snapshot(test: Test) -> Dict[str, Any]:
    """Plain-data snapshot of a test for audit ``old_data``/``new_data``."""
    return {
        "exam_id": test.exam_id,
        "name": test.name,
        "code": test.code,
        "description": test.description,
        "instructions": test.instructions,
        "duration_minutes": test.duration_minutes,
        "total_marks": test.total_marks,
        "passing_marks": test.passing_marks,
        "negative_marking_enabled": test.negative_marking_enabled,
        "negative_marks": test.negative_marks,
        "randomize_questions": test.randomize_questions,
        "randomize_options": test.randomize_options,
        "max_attempts": test.max_attempts,
        "status": test.status,
        "scheduled_start_at": test.scheduled_start_at,
        "scheduled_end_at": test.scheduled_end_at,
    }


def _apply_updates(target: Any, data: Dict[str, Any]) -> bool:
    """Copy provided non-``None`` values onto ``target``; report any change."""
    changed = False
    for field, value in data.items():
        if value is None:
            continue
        if isinstance(value, Enum):
            value = value.value
        if getattr(target, field) != value:
            setattr(target, field, value)
            changed = True
    return changed


def with_counts(db: Session, test: Test) -> Test:
    """Attach the denormalised ``question_count`` / ``assigned_count`` fields."""
    test.question_count = repository.count_test_questions(db, test.id)
    test.assigned_count = repository.count_test_assignments(db, test.id)
    return test


def _set_total_marks(db: Session, test: Test) -> None:
    """Recompute ``total_marks`` from the attached questions."""
    test.total_marks = repository.compute_total_marks(db, test.id)


def _decorate_question_link(link: TestQuestion, question: Question) -> TestQuestion:
    """Attach the denormalised question fields consumed by ``TestQuestionResponse``."""
    link.question_text = question.question_text
    link.question_type = question.question_type
    link.subject_id = question.subject_id
    link.difficulty = question.difficulty
    return link


# ---------------------------------------------------------------------------
# Reads
# ---------------------------------------------------------------------------


def get_test(db: Session, test_id: int) -> Test:
    """Return one test or raise ``NotFoundError`` (``TEST_NOT_FOUND``)."""
    test = repository.get_test(db, test_id)
    if test is None:
        raise NotFoundError("Test was not found.", code="TEST_NOT_FOUND")
    return test


def get_test_detail(db: Session, test_id: int) -> Test:
    """Return one test enriched with its question/assignment counts."""
    return with_counts(db, get_test(db, test_id))


def list_tests(
    db: Session,
    params: PaginationParams,
    *,
    exam_id: Optional[int] = None,
) -> Any:
    """Return the paginated test listing with question/assignment counts."""
    stmt = repository.build_test_list_stmt(params, exam_id=exam_id)
    page = paginate(db, stmt, params)
    for item in page["items"]:
        with_counts(db, item)
    return page


# ---------------------------------------------------------------------------
# Writes
# ---------------------------------------------------------------------------


def create_test(
    db: Session,
    payload: TestCreate,
    *,
    user_id: int,
    request: Optional[Request] = None,
) -> Test:
    """Create a ``DRAFT`` test under an existing exam with a unique code."""
    if exam_repository.get_exam(db, payload.exam_id) is None:
        raise NotFoundError("Exam was not found.", code="EXAM_NOT_FOUND")
    if repository.test_code_exists(db, payload.code):
        raise ConflictError(
            "A test with this code already exists.", code="TEST_CODE_EXISTS"
        )

    test = Test(
        exam_id=payload.exam_id,
        name=payload.name,
        code=payload.code,
        description=payload.description,
        instructions=payload.instructions,
        duration_minutes=payload.duration_minutes,
        total_marks=payload.total_marks,
        passing_marks=payload.passing_marks,
        negative_marking_enabled=payload.negative_marking_enabled,
        negative_marks=payload.negative_marks,
        randomize_questions=payload.randomize_questions,
        randomize_options=payload.randomize_options,
        max_attempts=payload.max_attempts,
        status=TestStatus.DRAFT.value,
        scheduled_start_at=payload.scheduled_start_at,
        scheduled_end_at=payload.scheduled_end_at,
        created_by=user_id,
        updated_by=user_id,
    )
    db.add(test)
    try:
        db.flush()
        _audit(
            db,
            user_id=user_id,
            action="create",
            entity_id=test.id,
            new_data=_snapshot(test),
            request=request,
        )
        _commit(db)
    except IntegrityError as exc:  # concurrent insert beat the pre-check
        db.rollback()
        raise ConflictError(
            "A test with this code already exists.", code="TEST_CODE_EXISTS"
        ) from exc
    except Exception:
        db.rollback()
        raise
    return test


def update_test(
    db: Session,
    test_id: int,
    payload: TestUpdate,
    *,
    user_id: int,
    request: Optional[Request] = None,
) -> Test:
    """Apply the provided non-``None`` fields to the test."""
    test = get_test(db, test_id)
    old_data = _snapshot(test)
    changed = _apply_updates(test, payload.model_dump(exclude_unset=True))
    if changed:
        test.updated_by = user_id
        try:
            db.flush()
            _audit(
                db,
                user_id=user_id,
                action="update",
                entity_id=test.id,
                old_data=old_data,
                new_data=_snapshot(test),
                request=request,
            )
            _commit(db)
        except Exception:
            db.rollback()
            raise
    else:
        _commit(db)
    return test


def delete_test(
    db: Session,
    test_id: int,
    *,
    user_id: int,
    request: Optional[Request] = None,
) -> None:
    """Delete a test (cascading its questions/assignments) unless it has attempts.

    Raises ``409 TEST_HAS_ATTEMPTS`` when attempts exist so historical data is
    preserved. A Core ``DELETE`` is used so the database ``ON DELETE CASCADE``
    handles the child rows (``Test.assignments`` is lazy="raise").
    """
    test = get_test(db, test_id)
    if repository.count_test_attempts(db, test_id) > 0:
        raise ConflictError(
            "Test has attempts and cannot be deleted.", code="TEST_HAS_ATTEMPTS"
        )
    old_data = _snapshot(test)
    try:
        db.execute(
            sa_delete(Test)
            .where(Test.id == test_id)
            .execution_options(synchronize_session=False)
        )
        _audit(
            db,
            user_id=user_id,
            action="delete",
            entity_id=test_id,
            old_data=old_data,
            new_data=None,
            request=request,
        )
        _commit(db)
    except Exception:
        db.rollback()
        raise


def publish_test(
    db: Session,
    test_id: int,
    *,
    user_id: int,
    request: Optional[Request] = None,
) -> Test:
    """Publish a ``DRAFT`` test that owns at least one question."""
    test = get_test(db, test_id)
    if test.status != TestStatus.DRAFT.value:
        raise ConflictError(
            "Only a DRAFT test can be published.", code="TEST_NOT_DRAFT"
        )
    if repository.count_test_questions(db, test_id) == 0:
        raise BadRequestError(
            "Test has no questions to publish.", code="TEST_HAS_NO_QUESTIONS"
        )
    old_data = _snapshot(test)
    _set_total_marks(db, test)
    test.status = TestStatus.PUBLISHED.value
    test.updated_by = user_id
    try:
        db.flush()
        _audit(
            db,
            user_id=user_id,
            action="publish",
            entity_id=test.id,
            old_data=old_data,
            new_data=_snapshot(test),
            request=request,
        )
        _commit(db)
    except Exception:
        db.rollback()
        raise
    return with_counts(db, test)


def close_test(
    db: Session,
    test_id: int,
    *,
    user_id: int,
    request: Optional[Request] = None,
) -> Test:
    """Move a ``PUBLISHED`` test to ``CLOSED``."""
    test = get_test(db, test_id)
    if test.status != TestStatus.PUBLISHED.value:
        raise ConflictError(
            "Only a PUBLISHED test can be closed.", code="TEST_NOT_PUBLISHED"
        )
    old_data = _snapshot(test)
    test.status = TestStatus.CLOSED.value
    test.updated_by = user_id
    try:
        db.flush()
        _audit(
            db,
            user_id=user_id,
            action="close",
            entity_id=test.id,
            old_data=old_data,
            new_data=_snapshot(test),
            request=request,
        )
        _commit(db)
    except Exception:
        db.rollback()
        raise
    return test


def add_question(
    db: Session,
    test_id: int,
    payload: TestQuestionAdd,
    *,
    user_id: int,
    request: Optional[Request] = None,
) -> TestQuestion:
    """Attach a published question to a test that has no attempts yet.

    Returns the membership row decorated with the denormalised question fields
    consumed by ``TestQuestionResponse``.
    """
    test = get_test(db, test_id)
    if repository.count_test_attempts(db, test_id) > 0:
        raise ConflictError(
            "Questions cannot be added once the test has attempts.",
            code="TEST_HAS_ATTEMPTS",
        )

    question = question_repository.get_question(db, payload.question_id)
    if question is None or question.status != QuestionStatus.PUBLISHED.value:
        raise ConflictError(
            "Question must exist and be published.",
            code="QUESTION_NOT_PUBLISHED",
        )
    if repository.get_test_question(db, test_id, payload.question_id) is not None:
        raise ConflictError(
            "Question is already part of the test.",
            code="QUESTION_ALREADY_ADDED",
        )

    order = (
        payload.question_order
        if payload.question_order is not None
        else repository.max_question_order(db, test_id) + 1
    )
    link = TestQuestion(
        test_id=test_id,
        question_id=payload.question_id,
        question_order=order,
        marks_override=payload.marks_override,
        negative_marks_override=payload.negative_marks_override,
    )
    db.add(link)
    try:
        db.flush()
        _set_total_marks(db, test)
        test.updated_by = user_id
        db.flush()
        _audit(
            db,
            user_id=user_id,
            action="add_question",
            entity_id=test.id,
            new_data={
                "question_id": payload.question_id,
                "question_order": order,
                "total_marks": float(test.total_marks or 0),
            },
            request=request,
        )
        _commit(db)
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(
            "Question is already part of the test.", code="QUESTION_ALREADY_ADDED"
        ) from exc
    except Exception:
        db.rollback()
        raise
    _decorate_question_link(link, question)
    return link


def add_questions_bulk(
    db: Session,
    test_id: int,
    payload: TestQuestionsBulkAdd,
    *,
    user_id: int,
    request: Optional[Request] = None,
) -> Dict[str, int]:
    """Attach several published questions in one transaction, skipping duplicates."""
    test = get_test(db, test_id)
    if repository.count_test_attempts(db, test_id) > 0:
        raise ConflictError(
            "Questions cannot be added once the test has attempts.",
            code="TEST_HAS_ATTEMPTS",
        )

    unique_ids = list(dict.fromkeys(payload.question_ids))
    questions = repository.get_questions_by_ids(db, unique_ids)
    for question_id in unique_ids:
        question = questions.get(question_id)
        if question is None or question.status != QuestionStatus.PUBLISHED.value:
            raise ConflictError(
                f"Question {question_id} must exist and be published.",
                code="QUESTION_NOT_PUBLISHED",
                details={"question_id": question_id},
            )

    existing = repository.list_test_question_ids(db, test_id)
    order = max(repository.max_question_order(db, test_id) + 1, payload.start_order)
    added = 0
    for question_id in unique_ids:
        if question_id in existing:
            continue
        db.add(
            TestQuestion(
                test_id=test_id,
                question_id=question_id,
                question_order=order,
            )
        )
        order += 1
        added += 1

    try:
        db.flush()
        _set_total_marks(db, test)
        test.updated_by = user_id
        db.flush()
        _audit(
            db,
            user_id=user_id,
            action="bulk_add",
            entity_id=test.id,
            new_data={"added": added, "requested": len(unique_ids)},
            request=request,
        )
        _commit(db)
    except Exception:
        db.rollback()
        raise
    return {"added": added, "skipped": len(payload.question_ids) - added}


def remove_question(
    db: Session,
    test_id: int,
    question_id: int,
    *,
    user_id: int,
    request: Optional[Request] = None,
) -> None:
    """Detach a question, renumber the remaining ones and recompute marks."""
    test = get_test(db, test_id)
    link = repository.get_test_question(db, test_id, question_id)
    if link is None:
        raise NotFoundError(
            "Question is not part of this test.", code="QUESTION_NOT_IN_TEST"
        )
    if repository.count_test_attempts(db, test_id) > 0:
        raise ConflictError(
            "Questions cannot be removed once the test has attempts.",
            code="TEST_HAS_ATTEMPTS",
        )

    old_data = {"question_id": question_id, "question_order": link.question_order}
    db.delete(link)
    try:
        db.flush()
        remaining = repository.get_test_questions(db, test_id)
        # Two-pass renumbering avoids transient unique-order collisions.
        for index, row in enumerate(remaining):
            row.question_order = -(index + 1)
        db.flush()
        for index, row in enumerate(remaining):
            row.question_order = index + 1
        _set_total_marks(db, test)
        test.updated_by = user_id
        db.flush()
        _audit(
            db,
            user_id=user_id,
            action="remove_question",
            entity_id=test.id,
            old_data=old_data,
            new_data={"question_id": question_id},
            request=request,
        )
        _commit(db)
    except Exception:
        db.rollback()
        raise
