"""Question-bank endpoints - CRUD, publish and bulk import.

Mounted by ``app.api.v1.router`` at ``/api/v1/questions``; every path below is
relative to that prefix. Every route is guarded by the ``question.*`` RBAC
permission codes.
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Path, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.permissions import require_permission
from app.db.session import get_db
from app.models.question import Question
from app.models.user import User
from app.schemas.common import ErrorResponse
from app.schemas.question import (
    QuestionCreate,
    QuestionImportRequest,
    QuestionImportResponse,
    QuestionResponse,
    QuestionUpdate,
)
from app.services import question_service
from app.utils.enums import Difficulty, QuestionType
from app.utils.pagination import Page, PaginationParams

router = APIRouter()

_UNAUTHORIZED: Dict[int, Dict[str, Any]] = {
    401: {
        "description": "Missing, expired or invalid access token.",
        "model": ErrorResponse,
    }
}
_FORBIDDEN: Dict[int, Dict[str, Any]] = {
    403: {
        "description": "Authenticated user lacks the required permission.",
        "model": ErrorResponse,
    }
}
_NOT_FOUND: Dict[int, Dict[str, Any]] = {
    404: {
        "description": "Question, subject or topic not found "
        "(QUESTION_NOT_FOUND / SUBJECT_NOT_FOUND / TOPIC_NOT_FOUND).",
        "model": ErrorResponse,
    }
}
_BAD_REQUEST: Dict[int, Dict[str, Any]] = {
    400: {
        "description": "Invalid option configuration (INVALID_OPTIONS) or a "
        "topic that does not belong to the subject (INVALID_TOPIC).",
        "model": ErrorResponse,
    }
}
_CONFLICT: Dict[int, Dict[str, Any]] = {
    409: {
        "description": "Question is referenced by a test that has attempts "
        "(QUESTION_IN_USE).",
        "model": ErrorResponse,
    }
}


@router.get(
    "/",
    response_model=Page[QuestionResponse],
    summary="List questions",
    description=(
        "Return a paginated, sortable question bank. Supports the "
        "`subject_id`, `topic_id`, `status`, `question_type`, `difficulty`, "
        "`tag` and `is_active` filters plus free-text `search` over the "
        "question text. "
        "Sortable by id, created_at, updated_at, marks, difficulty and status "
        "(unknown columns fall back to created_at desc). Requires the "
        "`question.view` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND},
    dependencies=[Depends(require_permission("question.view"))],
)
def list_questions(
    db: Session = Depends(get_db),
    params: PaginationParams = Depends(),
    subject_id: Optional[int] = Query(
        None, ge=1, description="Filter by subject id."
    ),
    topic_id: Optional[int] = Query(None, ge=1, description="Filter by topic id."),
    question_type: Optional[QuestionType] = Query(
        None, description="Filter by question type."
    ),
    difficulty: Optional[Difficulty] = Query(
        None, description="Filter by difficulty (EASY, MEDIUM, HARD)."
    ),
    tag: Optional[str] = Query(
        None, max_length=50, description="Filter by a single tag (exact match)."
    ),
    is_active: Optional[bool] = Query(
        None, description="Filter by the active flag."
    ),
) -> Any:
    """List questions with pagination and subject/topic/type/tag filters."""
    return question_service.list_questions(
        db,
        params,
        subject_id=subject_id,
        topic_id=topic_id,
        question_type=question_type.value if question_type else None,
        difficulty=difficulty.value if difficulty else None,
        tag=tag,
        is_active=is_active,
    )


@router.post(
    "/",
    response_model=QuestionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create question",
    description=(
        "Create a question plus its options in one transaction. The subject "
        "must exist (404 `SUBJECT_NOT_FOUND`) and a supplied topic must belong "
        "to it. Option rules: SINGLE_CHOICE / TRUE_FALSE need at least two "
        "options with exactly one correct; MULTIPLE_CHOICE needs at least two "
        "options with at least one correct; NUMERICAL / SUBJECTIVE accept no "
        "options (400 `INVALID_OPTIONS`). Writes a `question.create` audit "
        "entry. Requires the `question.create` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND, **_BAD_REQUEST},
    dependencies=[Depends(require_permission("question.create"))],
)
def create_question(
    payload: QuestionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Question:
    """Create a question and its options in a single transaction."""
    return question_service.create_question(
        db, payload, user_id=current_user.id, request=request
    )


@router.post(
    "/import",
    response_model=QuestionImportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Import questions",
    description=(
        "Bulk-create up to 500 questions in one transaction. Each row is "
        "validated inside its own savepoint; invalid rows are collected under "
        "`errors` while valid rows are committed. Returns the `imported` / "
        "`failed` counts. Writes one audit entry with the counts. Requires the "
        "`question.create` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND},
    dependencies=[Depends(require_permission("question.create"))],
)
def import_questions(
    payload: QuestionImportRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> QuestionImportResponse:
    """Import many questions, reporting per-row errors."""
    return question_service.import_questions(
        db, payload, user_id=current_user.id, request=request
    )


@router.get(
    "/{question_id}",
    response_model=QuestionResponse,
    summary="Get question",
    description=(
        "Return one question with its options (including the answer key). "
        "Unknown ids return 404 `QUESTION_NOT_FOUND`. Requires the "
        "`question.view` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND},
    dependencies=[Depends(require_permission("question.view"))],
)
def get_question(
    question_id: int = Path(..., ge=1, description="Unique question ID."),
    db: Session = Depends(get_db),
) -> Question:
    """Fetch one question by ID."""
    return question_service.get_question(db, question_id)


@router.put(
    "/{question_id}",
    response_model=QuestionResponse,
    summary="Update question",
    description=(
        "Apply the provided (non-null) fields to the question. Supplying "
        "`options` replaces the whole option set and re-validates it with the "
        "same per-type rules. Writes an audit entry with the old and new "
        "values. Requires the `question.update` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND, **_BAD_REQUEST},
    dependencies=[Depends(require_permission("question.update"))],
)
def update_question(
    payload: QuestionUpdate,
    request: Request,
    question_id: int = Path(..., ge=1, description="Unique question ID."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Question:
    """Update a question, optionally replacing its option set."""
    return question_service.update_question(
        db, question_id, payload, user_id=current_user.id, request=request
    )


@router.delete(
    "/{question_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete question",
    description=(
        "Remove a question. When it is referenced by a test that already has "
        "attempts it is refused with 409 `QUESTION_IN_USE`; when referenced by "
        "tests without attempts it is soft-deactivated (`is_active=false`); "
        "otherwise it is hard-deleted. Both paths are audited. Requires the "
        "`question.delete` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND, **_CONFLICT},
    dependencies=[Depends(require_permission("question.delete"))],
)
def delete_question(
    request: Request,
    question_id: int = Path(..., ge=1, description="Unique question ID."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete, soft-deactivate or refuse deletion of a question."""
    question_service.delete_question(
        db, question_id, user_id=current_user.id, request=request
    )


@router.post(
    "/{question_id}/publish",
    response_model=QuestionResponse,
    summary="Publish question",
    description=(
        "Validate the question's options and move it to `PUBLISHED`. "
        "Choice-type questions without a valid option set are rejected with "
        "400 `INVALID_OPTIONS`. Writes an audit entry. Requires the "
        "`question.publish` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND, **_BAD_REQUEST},
    dependencies=[Depends(require_permission("question.publish"))],
)
def publish_question(
    request: Request,
    question_id: int = Path(..., ge=1, description="Unique question ID."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Question:
    """Publish a question after re-validating its options."""
    return question_service.publish_question(
        db, question_id, user_id=current_user.id, request=request
    )
