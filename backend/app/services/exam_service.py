"""Application services for exams, subjects and topics.

Every mutation owns its transaction: changes are flushed to obtain primary
keys, an audit entry is appended to the same transaction via
:func:`app.services.audit_service.record_audit`, and ``commit`` only runs when
everything succeeded - any failure rolls the session back before the error
propagates to the API layer.

Read helpers (:func:`get_exam` / :func:`get_subject` / :func:`get_topic`) raise
``NotFoundError`` with the stable codes ``EXAM_NOT_FOUND`` /
``SUBJECT_NOT_FOUND`` / ``TOPIC_NOT_FOUND``; list queries live in
:mod:`app.repositories.exam_repository` and are paginated by the routers.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Set

from fastapi import Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    BadRequestError,
    ConflictError,
    NotFoundError,
)
from app.models.exam import Exam
from app.models.subject import Subject
from app.models.topic import Topic
from app.repositories import exam_repository as repository
from app.schemas.exam import ExamCreate, ExamUpdate
from app.schemas.subject import SubjectCreate, SubjectUpdate
from app.schemas.topic import TopicCreate, TopicUpdate
from app.services.audit_service import record_audit
from app.utils.enums import ExamStatus


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _apply_updates(target: Any, data: Dict[str, Any]) -> List[str]:
    """Copy every provided, non-``None`` value onto ``target``.

    Enum instances are stored as their plain string values so the ORM never
    persists ``ExamStatus.PUBLISHED`` style representations. Returns the names
    of the fields whose value actually changed.
    """
    changed: List[str] = []
    for field, value in data.items():
        if value is None:
            continue
        if isinstance(value, Enum):
            value = value.value
        if getattr(target, field) != value:
            setattr(target, field, value)
            changed.append(field)
    return changed


def _commit(db: Session) -> None:
    """Commit the current transaction, rolling back before re-raising failures."""
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def _audit(
    db: Session,
    *,
    user_id: int,
    module: str,
    action: str,
    entity_id: int,
    old_data: Optional[Dict[str, Any]] = None,
    new_data: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None,
) -> None:
    """Append one audit row for a successful (pending) mutation."""
    record_audit(
        db,
        user_id=user_id,
        module=module,
        action=action,
        entity_type=module,
        entity_id=entity_id,
        old_data=old_data,
        new_data=new_data,
        request=request,
    )


def _exam_snapshot(exam: Exam) -> Dict[str, Any]:
    """Plain-data snapshot of an exam for audit ``old_data``/``new_data``."""
    return {
        "name": exam.name,
        "code": exam.code,
        "description": exam.description,
        "exam_type": exam.exam_type,
        "status": exam.status,
        "duration_minutes": exam.duration_minutes,
        "passing_percentage": exam.passing_percentage,
        "start_at": exam.start_at,
        "end_at": exam.end_at,
        "is_active": exam.is_active,
    }


def _subject_snapshot(subject: Subject) -> Dict[str, Any]:
    """Plain-data snapshot of a subject for audit entries."""
    return {
        "exam_id": subject.exam_id,
        "name": subject.name,
        "code": subject.code,
        "description": subject.description,
        "sort_order": subject.sort_order,
        "is_active": subject.is_active,
    }


def _topic_snapshot(topic: Topic) -> Dict[str, Any]:
    """Plain-data snapshot of a topic for audit entries."""
    return {
        "subject_id": topic.subject_id,
        "parent_topic_id": topic.parent_topic_id,
        "name": topic.name,
        "description": topic.description,
        "sort_order": topic.sort_order,
        "is_active": topic.is_active,
    }


def _parent_topic_is_valid(
    db: Session,
    *,
    subject_id: int,
    topic_id: Optional[int],
    parent_id: int,
) -> bool:
    """Check a proposed ``parent_topic_id`` for create/update.

    The parent must exist, belong to the same subject, must not be the topic
    itself, and must not introduce a cycle in the (already possibly flawed)
    hierarchy - the upward walk is protected by a visited set.
    """
    if topic_id is not None and parent_id == topic_id:
        return False
    seen: Set[int] = set()
    current: Optional[int] = parent_id
    while current is not None:
        if current in seen:  # pre-existing cycle - refuse to extend it
            return False
        seen.add(current)
        node = repository.get_topic(db, current)
        if node is None or node.subject_id != subject_id:
            return False
        current = node.parent_topic_id
    return True


# ---------------------------------------------------------------------------
# Exams
# ---------------------------------------------------------------------------


def get_exam(db: Session, exam_id: int) -> Exam:
    """Return one exam or raise ``NotFoundError`` (``EXAM_NOT_FOUND``)."""
    exam = repository.get_exam(db, exam_id)
    if exam is None:
        raise NotFoundError("Exam was not found.", code="EXAM_NOT_FOUND")
    return exam


def create_exam(
    db: Session,
    payload: ExamCreate,
    *,
    user_id: int,
    request: Optional[Request] = None,
) -> Exam:
    """Create an exam in ``DRAFT`` status with a unique code (commits)."""
    if repository.exam_code_exists(db, payload.code):
        raise ConflictError(
            "An exam with this code already exists.", code="EXAM_CODE_EXISTS"
        )
    exam = Exam(
        name=payload.name,
        code=payload.code,
        description=payload.description,
        exam_type=payload.exam_type.value,
        status=ExamStatus.DRAFT.value,
        duration_minutes=payload.duration_minutes,
        passing_percentage=payload.passing_percentage,
        start_at=payload.start_at,
        end_at=payload.end_at,
        created_by=user_id,
        updated_by=user_id,
    )
    db.add(exam)
    try:
        db.flush()
        _audit(
            db,
            user_id=user_id,
            module="exam",
            action="create",
            entity_id=exam.id,
            new_data=_exam_snapshot(exam),
            request=request,
        )
        _commit(db)
    except IntegrityError as exc:  # concurrent insert beat the pre-check
        db.rollback()
        raise ConflictError(
            "An exam with this code already exists.", code="EXAM_CODE_EXISTS"
        ) from exc
    except Exception:
        db.rollback()
        raise
    return exam


def update_exam(
    db: Session,
    exam_id: int,
    payload: ExamUpdate,
    *,
    user_id: int,
    request: Optional[Request] = None,
) -> Exam:
    """Apply the non-``None`` fields of ``payload`` (``code`` is immutable)."""
    exam = get_exam(db, exam_id)
    old_data = _exam_snapshot(exam)
    changed = _apply_updates(exam, payload.model_dump(exclude_unset=True))
    if changed:
        exam.updated_by = user_id
        try:
            db.flush()
            _audit(
                db,
                user_id=user_id,
                module="exam",
                action="update",
                entity_id=exam.id,
                old_data=old_data,
                new_data=_exam_snapshot(exam),
                request=request,
            )
            _commit(db)
        except Exception:
            db.rollback()
            raise
    else:
        _commit(db)
    return exam


def delete_exam(
    db: Session,
    exam_id: int,
    *,
    user_id: int,
    request: Optional[Request] = None,
) -> None:
    """Soft-deactivate when subjects/tests exist, otherwise hard-delete."""
    exam = get_exam(db, exam_id)
    entity_id = exam.id
    old_data = _exam_snapshot(exam)
    has_children = (
        repository.count_exam_subjects(db, exam_id) > 0
        or repository.count_exam_tests(db, exam_id) > 0
    )
    if has_children:
        exam.is_active = False
        exam.updated_by = user_id
        action = "deactivate"
        new_data: Optional[Dict[str, Any]] = {"is_active": False}
    else:
        db.delete(exam)
        action = "delete"
        new_data = None
    try:
        _audit(
            db,
            user_id=user_id,
            module="exam",
            action=action,
            entity_id=entity_id,
            old_data=old_data,
            new_data=new_data,
            request=request,
        )
        _commit(db)
    except Exception:
        db.rollback()
        raise


def publish_exam(
    db: Session,
    exam_id: int,
    *,
    user_id: int,
    request: Optional[Request] = None,
) -> Exam:
    """Set ``status=PUBLISHED`` for an active exam owning at least one subject."""
    exam = get_exam(db, exam_id)
    if not exam.is_active:
        raise BadRequestError(
            "Inactive exam cannot be published.", code="EXAM_INACTIVE"
        )
    if repository.count_exam_subjects(db, exam_id) == 0:
        raise BadRequestError(
            "Exam has no subjects to publish.", code="EXAM_HAS_NO_SUBJECTS"
        )
    old_data = _exam_snapshot(exam)
    exam.status = ExamStatus.PUBLISHED.value
    exam.updated_by = user_id
    try:
        db.flush()
        _audit(
            db,
            user_id=user_id,
            module="exam",
            action="publish",
            entity_id=exam.id,
            old_data=old_data,
            new_data=_exam_snapshot(exam),
            request=request,
        )
        _commit(db)
    except Exception:
        db.rollback()
        raise
    return exam


def archive_exam(
    db: Session,
    exam_id: int,
    *,
    user_id: int,
    request: Optional[Request] = None,
) -> Exam:
    """Set ``status=ARCHIVED`` (keeps all historical data untouched)."""
    exam = get_exam(db, exam_id)
    old_data = _exam_snapshot(exam)
    exam.status = ExamStatus.ARCHIVED.value
    exam.updated_by = user_id
    try:
        db.flush()
        _audit(
            db,
            user_id=user_id,
            module="exam",
            action="archive",
            entity_id=exam.id,
            old_data=old_data,
            new_data=_exam_snapshot(exam),
            request=request,
        )
        _commit(db)
    except Exception:
        db.rollback()
        raise
    return exam


# ---------------------------------------------------------------------------
# Subjects
# ---------------------------------------------------------------------------


def get_subject(db: Session, subject_id: int) -> Subject:
    """Return one subject or raise ``NotFoundError`` (``SUBJECT_NOT_FOUND``)."""
    subject = repository.get_subject(db, subject_id)
    if subject is None:
        raise NotFoundError("Subject was not found.", code="SUBJECT_NOT_FOUND")
    return subject


def create_subject(
    db: Session,
    payload: SubjectCreate,
    *,
    user_id: int,
    request: Optional[Request] = None,
) -> Subject:
    """Create a subject under an existing exam with a unique ``(exam, code)``."""
    if repository.get_exam(db, payload.exam_id) is None:
        raise NotFoundError("Exam was not found.", code="EXAM_NOT_FOUND")
    if repository.subject_code_exists(db, payload.exam_id, payload.code):
        raise ConflictError(
            "A subject with this code already exists for the exam.",
            code="SUBJECT_CODE_EXISTS",
        )
    subject = Subject(
        exam_id=payload.exam_id,
        name=payload.name,
        code=payload.code,
        description=payload.description,
        sort_order=payload.sort_order,
    )
    db.add(subject)
    try:
        db.flush()
        _audit(
            db,
            user_id=user_id,
            module="subject",
            action="create",
            entity_id=subject.id,
            new_data=_subject_snapshot(subject),
            request=request,
        )
        _commit(db)
    except IntegrityError as exc:  # concurrent insert beat the pre-check
        db.rollback()
        raise ConflictError(
            "A subject with this code already exists for the exam.",
            code="SUBJECT_CODE_EXISTS",
        ) from exc
    except Exception:
        db.rollback()
        raise
    return subject


def update_subject(
    db: Session,
    subject_id: int,
    payload: SubjectUpdate,
    *,
    user_id: int,
    request: Optional[Request] = None,
) -> Subject:
    """Apply the non-``None`` fields of ``payload`` to the subject."""
    subject = get_subject(db, subject_id)
    old_data = _subject_snapshot(subject)
    changed = _apply_updates(subject, payload.model_dump(exclude_unset=True))
    if changed:
        try:
            db.flush()
            _audit(
                db,
                user_id=user_id,
                module="subject",
                action="update",
                entity_id=subject.id,
                old_data=old_data,
                new_data=_subject_snapshot(subject),
                request=request,
            )
            _commit(db)
        except Exception:
            db.rollback()
            raise
    else:
        _commit(db)
    return subject


def delete_subject(
    db: Session,
    subject_id: int,
    *,
    user_id: int,
    request: Optional[Request] = None,
) -> None:
    """Soft-deactivate when topics/questions exist, otherwise hard-delete."""
    subject = get_subject(db, subject_id)
    entity_id = subject.id
    old_data = _subject_snapshot(subject)
    has_children = (
        repository.count_subject_topics(db, subject_id) > 0
        or repository.count_subject_questions(db, subject_id) > 0
    )
    if has_children:
        subject.is_active = False
        action = "deactivate"
        new_data: Optional[Dict[str, Any]] = {"is_active": False}
    else:
        db.delete(subject)
        action = "delete"
        new_data = None
    try:
        _audit(
            db,
            user_id=user_id,
            module="subject",
            action=action,
            entity_id=entity_id,
            old_data=old_data,
            new_data=new_data,
            request=request,
        )
        _commit(db)
    except Exception:
        db.rollback()
        raise


# ---------------------------------------------------------------------------
# Topics
# ---------------------------------------------------------------------------


def get_topic(db: Session, topic_id: int) -> Topic:
    """Return one topic or raise ``NotFoundError`` (``TOPIC_NOT_FOUND``)."""
    topic = repository.get_topic(db, topic_id)
    if topic is None:
        raise NotFoundError("Topic was not found.", code="TOPIC_NOT_FOUND")
    return topic


def create_topic(
    db: Session,
    payload: TopicCreate,
    *,
    user_id: int,
    request: Optional[Request] = None,
) -> Topic:
    """Create a topic; an optional parent must belong to the same subject."""
    if repository.get_subject(db, payload.subject_id) is None:
        raise NotFoundError("Subject was not found.", code="SUBJECT_NOT_FOUND")
    if payload.parent_topic_id is not None and not _parent_topic_is_valid(
        db,
        subject_id=payload.subject_id,
        topic_id=None,
        parent_id=payload.parent_topic_id,
    ):
        raise BadRequestError(
            "Parent topic must exist and belong to the same subject.",
            code="INVALID_PARENT_TOPIC",
        )
    topic = Topic(
        subject_id=payload.subject_id,
        parent_topic_id=payload.parent_topic_id,
        name=payload.name,
        description=payload.description,
        sort_order=payload.sort_order,
    )
    db.add(topic)
    try:
        db.flush()
        _audit(
            db,
            user_id=user_id,
            module="topic",
            action="create",
            entity_id=topic.id,
            new_data=_topic_snapshot(topic),
            request=request,
        )
        _commit(db)
    except Exception:
        db.rollback()
        raise
    return topic


def update_topic(
    db: Session,
    topic_id: int,
    payload: TopicUpdate,
    *,
    user_id: int,
    request: Optional[Request] = None,
) -> Topic:
    """Apply the non-``None`` fields of ``payload``, re-validating the parent."""
    topic = get_topic(db, topic_id)
    data = payload.model_dump(exclude_unset=True)
    parent_id = data.get("parent_topic_id")
    if parent_id is not None and not _parent_topic_is_valid(
        db,
        subject_id=topic.subject_id,
        topic_id=topic.id,
        parent_id=parent_id,
    ):
        raise BadRequestError(
            "Parent topic must exist and belong to the same subject.",
            code="INVALID_PARENT_TOPIC",
        )
    old_data = _topic_snapshot(topic)
    changed = _apply_updates(topic, data)
    if changed:
        try:
            db.flush()
            _audit(
                db,
                user_id=user_id,
                module="topic",
                action="update",
                entity_id=topic.id,
                old_data=old_data,
                new_data=_topic_snapshot(topic),
                request=request,
            )
            _commit(db)
        except Exception:
            db.rollback()
            raise
    else:
        _commit(db)
    return topic


def delete_topic(
    db: Session,
    topic_id: int,
    *,
    user_id: int,
    request: Optional[Request] = None,
) -> None:
    """Soft-deactivate when children/questions exist, otherwise hard-delete."""
    topic = get_topic(db, topic_id)
    entity_id = topic.id
    old_data = _topic_snapshot(topic)
    has_children = (
        repository.count_topic_children(db, topic_id) > 0
        or repository.count_topic_questions(db, topic_id) > 0
    )
    if has_children:
        topic.is_active = False
        action = "deactivate"
        new_data: Optional[Dict[str, Any]] = {"is_active": False}
    else:
        db.delete(topic)
        action = "delete"
        new_data = None
    try:
        _audit(
            db,
            user_id=user_id,
            module="topic",
            action=action,
            entity_id=entity_id,
            old_data=old_data,
            new_data=new_data,
            request=request,
        )
        _commit(db)
    except Exception:
        db.rollback()
        raise
