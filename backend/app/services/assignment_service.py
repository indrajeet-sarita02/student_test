"""Assignment service: assign tests to students and revoke assignments.

Business rules:

* a test must be ``PUBLISHED`` before students can be assigned;
* only users holding the ``STUDENT`` role can be assigned (``USER_NOT_A_STUDENT``);
* the ``(test_id, student_id)`` pair is unique (``ALREADY_ASSIGNED``);
* an assignment that already has attempts cannot be deleted
  (``ASSIGNMENT_HAS_ATTEMPTS``);
* creating an assignment also writes a ``TEST_ASSIGNED`` notification row.

Every mutation owns its transaction (``flush`` for ids, one ``commit`` on
success) and writes an audit entry in the same transaction.
"""

from typing import Any, Dict, List, Optional

from fastapi import Request
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.models.assignment import TestAssignment
from app.models.notification import Notification
from app.repositories import test_repository as repository
from app.schemas.assignment import AssignmentCreate, TestAssignmentBulkRequest
from app.services.audit_service import record_audit
from app.utils.datetime import utcnow
from app.utils.enums import AssignmentStatus, NotificationType, TestStatus
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
    """Append one ``assignment`` audit row for a successful mutation."""
    record_audit(
        db,
        user_id=user_id,
        module="assignment",
        action=action,
        entity_type="assignment",
        entity_id=entity_id,
        old_data=old_data,
        new_data=new_data,
        request=request,
    )


def _snapshot(assignment: TestAssignment) -> Dict[str, Any]:
    """Plain-data snapshot of an assignment for audit rows."""
    return {
        "test_id": assignment.test_id,
        "student_id": assignment.student_id,
        "assigned_at": assignment.assigned_at,
        "available_from": assignment.available_from,
        "available_until": assignment.available_until,
        "max_attempts": assignment.max_attempts,
        "status": assignment.status,
    }


def _decorate(assignment: TestAssignment) -> TestAssignment:
    """Attach the denormalised test/student fields for the response schema."""
    return repository.decorate_assignment(assignment)


def _notify(db: Session, student_id: int, test_name: str) -> None:
    """Queue a ``TEST_ASSIGNED`` notification row for a student."""
    db.add(
        Notification(
            user_id=student_id,
            title="New test assigned",
            message=f'You have been assigned the test "{test_name}".',
            type=NotificationType.TEST_ASSIGNED.value,
            is_read=False,
        )
    )


def _require_published_test(db: Session, test_id: int):
    """Return the test or raise ``TEST_NOT_FOUND`` / ``TEST_NOT_PUBLISHED``."""
    test = repository.get_test(db, test_id)
    if test is None:
        raise NotFoundError("Test was not found.", code="TEST_NOT_FOUND")
    if test.status != TestStatus.PUBLISHED.value:
        raise ConflictError(
            "Test must be published before it can be assigned.",
            code="TEST_NOT_PUBLISHED",
        )
    return test


# ---------------------------------------------------------------------------
# Reads
# ---------------------------------------------------------------------------


def list_assignments(
    db: Session,
    params: PaginationParams,
    *,
    test_id: Optional[int] = None,
    student_id: Optional[int] = None,
) -> Any:
    """Return the paginated assignment listing enriched with names."""
    stmt = repository.build_assignment_list_stmt(
        params, test_id=test_id, student_id=student_id
    )
    page = paginate(db, stmt, params)
    for assignment in page["items"]:
        _decorate(assignment)
    return page


def get_assignment(db: Session, assignment_id: int) -> TestAssignment:
    """Return one assignment or raise ``ASSIGNMENT_NOT_FOUND``."""
    assignment = repository.get_assignment(db, assignment_id)
    if assignment is None:
        raise NotFoundError("Assignment was not found.", code="ASSIGNMENT_NOT_FOUND")
    return assignment


# ---------------------------------------------------------------------------
# Writes
# ---------------------------------------------------------------------------


def create_assignment(
    db: Session,
    payload: AssignmentCreate,
    *,
    user_id: int,
    request: Optional[Request] = None,
) -> TestAssignment:
    """Assign a published test to a student and notify them."""
    test = _require_published_test(db, payload.test_id)

    if payload.student_id not in repository.student_role_user_ids(
        db, [payload.student_id]
    ):
        raise BadRequestError(
            "User does not exist or does not hold the STUDENT role.",
            code="USER_NOT_A_STUDENT",
            details={"student_id": payload.student_id},
        )

    if repository.assignment_exists(db, payload.test_id, payload.student_id):
        raise ConflictError(
            "This student is already assigned to the test.",
            code="ALREADY_ASSIGNED",
        )

    assignment = TestAssignment(
        test_id=payload.test_id,
        student_id=payload.student_id,
        assigned_at=utcnow(),
        available_from=payload.available_from,
        available_until=payload.available_until,
        max_attempts=payload.max_attempts,
        status=AssignmentStatus.ASSIGNED.value,
    )
    db.add(assignment)
    db.flush()
    _notify(db, payload.student_id, test.name)
    _audit(
        db,
        user_id=user_id,
        action="assign",
        entity_id=assignment.id,
        new_data=_snapshot(assignment),
        request=request,
    )
    _commit(db)
    return _decorate(assignment)


def bulk_assign(
    db: Session,
    payload: TestAssignmentBulkRequest,
    *,
    user_id: int,
    request: Optional[Request] = None,
) -> Dict[str, Any]:
    """Assign a published test to many students in one transaction.

    Users that do not exist, do not hold the ``STUDENT`` role or are already
    assigned are skipped (counted, never fatal). A single audit entry records
    the resulting counts.
    """
    test = _require_published_test(db, payload.test_id)

    student_ids: List[int] = list(dict.fromkeys(payload.student_ids))
    valid_ids = repository.student_role_user_ids(db, student_ids)
    existing_ids = repository.existing_assignment_student_ids(
        db, payload.test_id, student_ids
    )

    created: List[TestAssignment] = []
    skipped = 0
    for student_id in student_ids:
        if student_id not in valid_ids or student_id in existing_ids:
            skipped += 1
            continue
        assignment = TestAssignment(
            test_id=payload.test_id,
            student_id=student_id,
            assigned_at=utcnow(),
            available_from=payload.available_from,
            available_until=payload.available_until,
            max_attempts=payload.max_attempts,
            status=AssignmentStatus.ASSIGNED.value,
        )
        db.add(assignment)
        created.append(assignment)
    db.flush()
    for assignment in created:
        _notify(db, assignment.student_id, test.name)
    _audit(
        db,
        user_id=user_id,
        action="bulk_assign",
        entity_id=payload.test_id,
        new_data={
            "test_id": payload.test_id,
            "created": len(created),
            "skipped": skipped,
            "requested": len(student_ids),
        },
        request=request,
    )
    _commit(db)
    for assignment in created:
        _decorate(assignment)
    return {"created": len(created), "skipped": skipped, "assignments": created}


def delete_assignment(
    db: Session,
    assignment_id: int,
    *,
    user_id: int,
    request: Optional[Request] = None,
) -> None:
    """Delete an assignment unless the student already has attempts."""
    assignment = get_assignment(db, assignment_id)
    if (
        repository.count_assignment_attempts(
            db, assignment.test_id, assignment.student_id
        )
        > 0
    ):
        raise ConflictError(
            "Assignment has attempts and cannot be deleted.",
            code="ASSIGNMENT_HAS_ATTEMPTS",
        )

    old_data = _snapshot(assignment)
    db.delete(assignment)
    _audit(
        db,
        user_id=user_id,
        action="delete",
        entity_id=assignment_id,
        old_data=old_data,
        new_data=None,
        request=request,
    )
    _commit(db)
