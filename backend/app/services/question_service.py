"""Question-bank service: CRUD, publish and bulk import.

Every mutation owns its transaction: changes are flushed to obtain primary
keys, an audit entry is appended in the same transaction via
:func:`app.services.audit_service.record_audit`, and ``commit`` only runs when
everything succeeded.

Option rules enforced before persisting anything:

* ``SINGLE_CHOICE`` / ``TRUE_FALSE`` -> at least two options with exactly one
  correct option.
* ``MULTIPLE_CHOICE`` -> at least two options with at least one correct option.
* ``NUMERICAL`` / ``SUBJECTIVE`` -> no options allowed.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Tuple

from fastapi import Request
from sqlalchemy.orm import Session

from app.core.exceptions import (
    AppError,
    BadRequestError,
    NotFoundError,
)
from app.models.question import Question, QuestionOption
from app.repositories import exam_repository
from app.repositories import question_repository as repository
from app.schemas.question import (
    QuestionCreate,
    QuestionImportRequest,
    QuestionImportResponse,
    QuestionUpdate,
)
from app.services.audit_service import record_audit
from app.utils.enums import QuestionStatus, QuestionType
from app.utils.pagination import PaginationParams, paginate

CHOICE_TYPES = {QuestionType.SINGLE_CHOICE.value, QuestionType.TRUE_FALSE.value}
MULTI_TYPE = QuestionType.MULTIPLE_CHOICE.value
NO_OPTION_TYPES = {QuestionType.NUMERICAL.value, QuestionType.SUBJECTIVE.value}


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
    """Append one ``question`` audit row for a successful (pending) mutation."""
    record_audit(
        db,
        user_id=user_id,
        module="question",
        action=action,
        entity_type="question",
        entity_id=entity_id,
        old_data=old_data,
        new_data=new_data,
        request=request,
    )


def _snapshot(question: Question) -> Dict[str, Any]:
    """Plain-data snapshot of a question (options included) for audit rows."""
    return {
        "subject_id": question.subject_id,
        "topic_id": question.topic_id,
        "question_type": question.question_type,
        "question_text": question.question_text,
        "explanation": question.explanation,
        "difficulty": question.difficulty,
        "marks": question.marks,
        "negative_marks": question.negative_marks,
        "status": question.status,
        "source": question.source,
        "is_active": question.is_active,
        "options": [
            {
                "option_text": option.option_text,
                "option_order": option.option_order,
                "is_correct": option.is_correct,
            }
            for option in question.options
        ],
    }


def _as_value(value: Any) -> Any:
    """Unwrap ``StrEnum`` instances to their plain string value."""
    return value.value if isinstance(value, Enum) else value


def _apply_updates(target: Any, data: Dict[str, Any]) -> List[str]:
    """Copy provided non-``None`` values onto ``target``; return changed names."""
    changed: List[str] = []
    for field, value in data.items():
        if value is None:
            continue
        value = _as_value(value)
        if getattr(target, field) != value:
            setattr(target, field, value)
            changed.append(field)
    return changed


def _validate_options(question_type: str, options: Sequence[Any]) -> None:
    """Enforce the per-type option rules (raises ``INVALID_OPTIONS``)."""
    qtype = _as_value(question_type)
    option_count = len(options)
    correct_count = sum(1 for option in options if getattr(option, "is_correct", False))

    if qtype in NO_OPTION_TYPES:
        if option_count:
            raise BadRequestError(
                f"{qtype} questions must not define options.",
                code="INVALID_OPTIONS",
                details={"field": "options"},
            )
        return

    if option_count < 2:
        raise BadRequestError(
            "Choice questions require at least two options.",
            code="INVALID_OPTIONS",
            details={"field": "options"},
        )
    if qtype in CHOICE_TYPES and correct_count != 1:
        raise BadRequestError(
            "Single-choice / true-false questions require exactly one correct option.",
            code="INVALID_OPTIONS",
            details={"field": "options"},
        )
    if qtype == MULTI_TYPE and correct_count < 1:
        raise BadRequestError(
            "Multiple-choice questions require at least one correct option.",
            code="INVALID_OPTIONS",
            details={"field": "options"},
        )


def _normalise_options(options: Sequence[Any]) -> List[Tuple[int, Any]]:
    """Return ``(option_order, option)`` pairs.

    Explicit unique ``option_order`` values are honoured; when they collide
    (the schema default is ``1`` for every option) the list position is used so
    the unique ``(question_id, option_order)`` constraint is never violated.
    """
    orders = [option.option_order for option in options]
    if len(set(orders)) != len(orders):
        return [(index, option) for index, option in enumerate(options, start=1)]
    return [(option.option_order, option) for option in options]


def _build_options(options: Sequence[Any]) -> List[QuestionOption]:
    """Create option rows with a normalised, unique ``option_order``."""
    return [
        QuestionOption(
            option_text=option.option_text,
            option_order=order,
            is_correct=bool(getattr(option, "is_correct", False)),
        )
        for order, option in _normalise_options(options)
    ]


def _validate_topic(db: Session, subject_id: int, topic_id: Optional[int]) -> None:
    """A supplied topic must exist and belong to the selected subject."""
    if topic_id is None:
        return
    topic = exam_repository.get_topic(db, topic_id)
    if topic is None:
        raise NotFoundError("Topic was not found.", code="TOPIC_NOT_FOUND")
    if topic.subject_id != subject_id:
        raise BadRequestError(
            "Topic does not belong to the selected subject.",
            code="INVALID_TOPIC",
            details={"field": "topic_id"},
        )


def _assert_subject_and_topic(
    db: Session, subject_id: int, topic_id: Optional[int]
) -> None:
    """Subject must exist (``SUBJECT_NOT_FOUND``) and topic must match it."""
    if exam_repository.get_subject(db, subject_id) is None:
        raise NotFoundError("Subject was not found.", code="SUBJECT_NOT_FOUND")
    _validate_topic(db, subject_id, topic_id)


def _instantiate(payload: Any, *, user_id: int, status: str) -> Question:
    """Build (but do not persist) a ``Question`` from a create/import payload."""
    return Question(
        subject_id=payload.subject_id,
        topic_id=payload.topic_id,
        question_type=_as_value(payload.question_type),
        question_text=payload.question_text,
        explanation=payload.explanation,
        difficulty=_as_value(payload.difficulty),
        marks=payload.marks,
        negative_marks=payload.negative_marks,
        status=status,
        source=getattr(payload, "source", None),
        created_by=user_id,
        updated_by=user_id,
        options=_build_options(payload.options),
    )


# ---------------------------------------------------------------------------
# Reads
# ---------------------------------------------------------------------------


def list_questions(
    db: Session,
    params: PaginationParams,
    *,
    subject_id: Optional[int] = None,
    topic_id: Optional[int] = None,
    question_type: Optional[str] = None,
    difficulty: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> Any:
    """Return the paginated, filtered question bank listing."""
    stmt = repository.build_question_list_stmt(
        params,
        subject_id=subject_id,
        topic_id=topic_id,
        question_type=question_type,
        difficulty=difficulty,
        is_active=is_active,
    )
    return paginate(db, stmt, params)


def get_question(db: Session, question_id: int) -> Question:
    """Return one question or raise ``NotFoundError`` (``QUESTION_NOT_FOUND``)."""
    question = repository.get_question(db, question_id)
    if question is None:
        raise NotFoundError("Question was not found.", code="QUESTION_NOT_FOUND")
    return question


# ---------------------------------------------------------------------------
# Writes
# ---------------------------------------------------------------------------


def create_question(
    db: Session,
    payload: QuestionCreate,
    *,
    user_id: int,
    request: Optional[Request] = None,
) -> Question:
    """Create a question plus its options in one transaction."""
    _assert_subject_and_topic(db, payload.subject_id, payload.topic_id)
    _validate_options(payload.question_type, payload.options)

    question = _instantiate(payload, user_id=user_id, status=payload.status.value)
    db.add(question)
    try:
        db.flush()
        _audit(
            db,
            user_id=user_id,
            action="create",
            entity_id=question.id,
            new_data=_snapshot(question),
            request=request,
        )
        _commit(db)
    except Exception:
        db.rollback()
        raise
    return question


def update_question(
    db: Session,
    question_id: int,
    payload: QuestionUpdate,
    *,
    user_id: int,
    request: Optional[Request] = None,
) -> Question:
    """Apply the provided fields; a supplied ``options`` list replaces the set."""
    question = get_question(db, question_id)
    old_data = _snapshot(question)

    options_provided = (
        "options" in payload.model_fields_set and payload.options is not None
    )
    scalar_data = payload.model_dump(exclude_unset=True, exclude={"options"})
    effective_type = _as_value(scalar_data.get("question_type") or question.question_type)

    if options_provided:
        _validate_options(effective_type, payload.options or [])
    elif "question_type" in scalar_data:
        _validate_options(effective_type, question.options)

    if "topic_id" in scalar_data and scalar_data["topic_id"] is not None:
        _validate_topic(db, question.subject_id, scalar_data["topic_id"])

    changed = _apply_updates(question, scalar_data)
    if options_provided:
        # Replace the option set in two phases.  Assigning a brand-new list in
        # one go makes SQLAlchemy INSERT the replacements before DELETEing the
        # old rows, which trips the unique ``(question_id, option_order)``
        # constraint (both sets use orders 1..n).  Detach and flush the old
        # rows first so the order values are free before the inserts run.
        question.options.clear()
        db.flush()
        question.options = _build_options(payload.options or [])
        changed.append("options")

    if changed:
        question.updated_by = user_id
        try:
            db.flush()
            _audit(
                db,
                user_id=user_id,
                action="update",
                entity_id=question.id,
                old_data=old_data,
                new_data=_snapshot(question),
                request=request,
            )
            _commit(db)
        except Exception:
            db.rollback()
            raise
    else:
        _commit(db)
    return question


def delete_question(
    db: Session,
    question_id: int,
    *,
    user_id: int,
    request: Optional[Request] = None,
) -> None:
    """Hard-delete a question (and, by cascade, its options)."""
    question = get_question(db, question_id)
    old_data = _snapshot(question)

    db.delete(question)
    action = "delete"
    new_data: Optional[Dict[str, Any]] = None

    try:
        _audit(
            db,
            user_id=user_id,
            action=action,
            entity_id=question_id,
            old_data=old_data,
            new_data=new_data,
            request=request,
        )
        _commit(db)
    except Exception:
        db.rollback()
        raise


def publish_question(
    db: Session,
    question_id: int,
    *,
    user_id: int,
    request: Optional[Request] = None,
) -> Question:
    """Validate choice-type options and set ``status=PUBLISHED``."""
    question = get_question(db, question_id)
    if question.question_type not in NO_OPTION_TYPES:
        _validate_options(question.question_type, question.options)

    old_data = _snapshot(question)
    question.status = QuestionStatus.PUBLISHED.value
    question.updated_by = user_id
    try:
        db.flush()
        _audit(
            db,
            user_id=user_id,
            action="publish",
            entity_id=question.id,
            old_data=old_data,
            new_data=_snapshot(question),
            request=request,
        )
        _commit(db)
    except Exception:
        db.rollback()
        raise
    return question


def import_questions(
    db: Session,
    payload: QuestionImportRequest,
    *,
    user_id: int,
    request: Optional[Request] = None,
) -> QuestionImportResponse:
    """Bulk-create questions in one transaction, collecting per-item errors.

    Each item runs inside a savepoint so a malformed row never poisons the
    surrounding transaction; valid rows are committed together at the end.
    """
    imported = 0
    failed = 0
    errors: List[str] = []

    for index, item in enumerate(payload.questions):
        try:
            with db.begin_nested():
                _assert_subject_and_topic(db, item.subject_id, item.topic_id)
                _validate_options(item.question_type, item.options)
                question = _instantiate(
                    item, user_id=user_id, status=QuestionStatus.DRAFT.value
                )
                db.add(question)
                db.flush()
            imported += 1
        except AppError as exc:
            failed += 1
            errors.append(f"question[{index}]: {exc.message}")
        except Exception as exc:  # defensive: never abort the whole batch
            failed += 1
            errors.append(f"question[{index}]: {exc}")

    _audit(
        db,
        user_id=user_id,
        action="import",
        entity_id=None,
        new_data={
            "imported": imported,
            "failed": failed,
            "errors": errors,
        },
        request=request,
    )
    _commit(db)
    return QuestionImportResponse(imported=imported, failed=failed, errors=errors)
