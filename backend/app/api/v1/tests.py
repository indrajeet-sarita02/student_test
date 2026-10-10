"""Test-assembly endpoints - CRUD, lifecycle actions and question management.

Mounted by ``app.api.v1.router`` at ``/api/v1/tests``; every path below is
relative to that prefix. Every route is guarded by the ``test.*`` RBAC
permission codes.
"""

from typing import Any, Dict, List, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Path,
    Query,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.permissions import require_all_permissions, require_permission
from app.db.session import get_db
from app.models.test import Test, TestQuestion
from app.models.user import User
from app.repositories import test_repository
from app.schemas.common import ErrorResponse
from app.schemas.test import (
    TestCreate,
    TestImportResponse,
    TestQuestionAdd,
    TestQuestionResponse,
    TestQuestionsBulkAdd,
    TestResponse,
    TestUpdate,
)
from app.services import test_import_service, test_service
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
        "description": "Test or question not found "
        "(TEST_NOT_FOUND / QUESTION_NOT_FOUND / QUESTION_NOT_IN_TEST).",
        "model": ErrorResponse,
    }
}
_BAD_REQUEST: Dict[int, Dict[str, Any]] = {
    400: {
        "description": "A test cannot be published without questions "
        "(TEST_HAS_NO_QUESTIONS).",
        "model": ErrorResponse,
    }
}
_CONFLICT: Dict[int, Dict[str, Any]] = {
    409: {
        "description": "State conflict (TEST_CODE_EXISTS / TEST_NOT_DRAFT / "
        "TEST_NOT_PUBLISHED / TEST_HAS_ATTEMPTS / QUESTION_NOT_PUBLISHED / "
        "QUESTION_ALREADY_ADDED).",
        "model": ErrorResponse,
    }
}
_UNPROCESSABLE: Dict[int, Dict[str, Any]] = {
    422: {
        "description": "The workbook could not be imported "
        "(TEST_IMPORT_INVALID) or the request is malformed.",
        "model": ErrorResponse,
    }
}


def _question_row(link: TestQuestion) -> Dict[str, Any]:
    """Build the ``TestQuestionResponse`` payload for one membership row."""
    question = link.question
    return {
        "id": link.id,
        "test_id": link.test_id,
        "question_id": link.question_id,
        "question_order": link.question_order,
        "marks_override": link.marks_override,
        "negative_marks_override": link.negative_marks_override,
        "question_text": question.question_text if question else None,
        "question_type": question.question_type if question else None,
        "subject_id": question.subject_id if question else None,
        "difficulty": question.difficulty if question else None,
    }


@router.get(
    "/",
    response_model=Page[TestResponse],
    summary="List tests",
    description=(
        "Return a paginated, sortable list of tests with their question and "
        "assignment counts. Supports the `exam_id` filter plus the shared "
        "`status` and free-text `search` (name/code). Sortable by id, name, "
        "code, status, created_at and updated_at (unknown columns fall back to "
        "created_at desc). Requires the `test.view` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND},
    dependencies=[Depends(require_permission("test.view"))],
)
def list_tests(
    db: Session = Depends(get_db),
    params: PaginationParams = Depends(),
    exam_id: Optional[int] = Query(None, ge=1, description="Filter by exam id."),
) -> Any:
    """List tests with pagination, exam/status/search filters and counts."""
    return test_service.list_tests(db, params, exam_id=exam_id)


@router.post(
    "/",
    response_model=TestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create test",
    description=(
        "Create a test in `DRAFT` status. The exam must exist (404 "
        "`EXAM_NOT_FOUND`) and the `code` must be globally unique (409 "
        "`TEST_CODE_EXISTS`). Writes a `test.create` audit entry. Requires the "
        "`test.create` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND, **_CONFLICT},
    dependencies=[Depends(require_permission("test.create"))],
)
def create_test(
    payload: TestCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Test:
    """Create a new DRAFT test under an existing exam."""
    return test_service.create_test(
        db, payload, user_id=current_user.id, request=request
    )


@router.get(
    "/import/template",
    summary="Download test import template",
    description=(
        "Return the sample `.xlsx` workbook used by `POST /tests/import`. It "
        "contains an `Instructions` sheet, a `Test` sheet (Field/Value rows) and "
        "a `Questions` sheet with example rows of every question type. Requires "
        "the `test.create` and `question.create` permissions."
    ),
    responses={
        **_UNAUTHORIZED,
        **_FORBIDDEN,
        200: {
            "content": {
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {}
            },
            "description": "Excel template attachment.",
        },
    },
    dependencies=[Depends(require_all_permissions("test.create", "question.create"))],
)
def download_test_import_template() -> Response:
    """Generate and return the XLSX import template."""
    return Response(
        content=test_import_service.build_test_import_template(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": 'attachment; filename="test_import_template.xlsx"'
        },
    )


@router.post(
    "/import",
    response_model=TestImportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Import test from XLSX",
    description=(
        "Create a new `DRAFT` test and its questions from an uploaded `.xlsx` "
        "workbook. The `Test` sheet supplies the settings (Field/Value rows) and "
        "the `Questions` sheet supplies one question per row; subjects and topics "
        "referenced by code/name are created on demand inside the selected exam. "
        "Imported questions are `DRAFT` and `total_marks` is recomputed. The "
        "workbook is validated in full before anything is written - invalid rows "
        "are returned as 422 `TEST_IMPORT_INVALID` with `details.errors`, and a "
        "duplicate `code` is refused with 409 `TEST_CODE_EXISTS`. Writes a "
        "`test.import` audit entry. Requires the `test.create` and "
        "`question.create` permissions."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND, **_CONFLICT, **_UNPROCESSABLE},
    dependencies=[Depends(require_all_permissions("test.create", "question.create"))],
)
def import_test(
    request: Request,
    file: UploadFile = File(..., description="The .xlsx workbook to import."),
    exam_id: int = Form(..., ge=1, description="Exam the test is created under."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TestImportResponse:
    """Import a DRAFT test and its questions from an XLSX upload."""
    data = file.file.read()
    try:
        file.file.close()
    except Exception:
        pass
    return test_import_service.import_test_from_xlsx(
        db,
        data=data,
        exam_id=exam_id,
        user_id=current_user.id,
        filename=file.filename,
        request=request,
    )


@router.get(
    "/{test_id}",
    response_model=TestResponse,
    summary="Get test",
    description=(
        "Return one test with its question and assignment counts. Unknown ids "
        "return 404 `TEST_NOT_FOUND`. Requires the `test.view` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND},
    dependencies=[Depends(require_permission("test.view"))],
)
def get_test(
    test_id: int = Path(..., ge=1, description="Unique test ID."),
    db: Session = Depends(get_db),
) -> Test:
    """Fetch one test by ID, including its aggregate counts."""
    return test_service.get_test_detail(db, test_id)


@router.put(
    "/{test_id}",
    response_model=TestResponse,
    summary="Update test",
    description=(
        "Apply the provided (non-null) fields to the test. `code` and `status` "
        "are managed through the dedicated actions. Writes an audit entry with "
        "the old and new values. Requires the `test.update` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND},
    dependencies=[Depends(require_permission("test.update"))],
)
def update_test(
    payload: TestUpdate,
    request: Request,
    test_id: int = Path(..., ge=1, description="Unique test ID."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Test:
    """Update the mutable fields of an existing test."""
    return test_service.update_test(
        db, test_id, payload, user_id=current_user.id, request=request
    )


@router.delete(
    "/{test_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete test",
    description=(
        "Delete a test and cascade its questions/assignments. Refused with 409 "
        "`TEST_HAS_ATTEMPTS` when the test already has attempts so historical "
        "data is preserved. Writes an audit entry. Requires the `test.delete` "
        "permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND, **_CONFLICT},
    dependencies=[Depends(require_permission("test.delete"))],
)
def delete_test(
    request: Request,
    test_id: int = Path(..., ge=1, description="Unique test ID."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a test unless it has attempts."""
    test_service.delete_test(db, test_id, user_id=current_user.id, request=request)


@router.get(
    "/{test_id}/questions",
    response_model=List[TestQuestionResponse],
    summary="List test questions",
    description=(
        "Return the questions attached to a test, ordered by `question_order`. "
        "Unknown test ids return 404 `TEST_NOT_FOUND`. Requires the "
        "`test.view` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND},
    dependencies=[Depends(require_permission("test.view"))],
)
def list_test_questions(
    test_id: int = Path(..., ge=1, description="Unique test ID."),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """List the questions attached to a test."""
    test_service.get_test(db, test_id)
    return [_question_row(link) for link in test_repository.get_test_questions(db, test_id)]


@router.post(
    "/{test_id}/questions",
    response_model=TestQuestionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add question to test",
    description=(
        "Attach a published question to a test. The question must exist and be "
        "`PUBLISHED` (409 `QUESTION_NOT_PUBLISHED`); duplicates are refused "
        "with 409 `QUESTION_ALREADY_ADDED`; the order defaults to `max+1`. "
        "Adding is blocked with 409 `TEST_HAS_ATTEMPTS` once the test has "
        "attempts. `total_marks` is recomputed. Writes an audit entry. "
        "Requires the `test.update` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND, **_CONFLICT},
    dependencies=[Depends(require_permission("test.update"))],
)
def add_question(
    payload: TestQuestionAdd,
    request: Request,
    test_id: int = Path(..., ge=1, description="Unique test ID."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TestQuestion:
    """Attach one published question to the test."""
    return test_service.add_question(
        db, test_id, payload, user_id=current_user.id, request=request
    )


@router.post(
    "/{test_id}/questions/bulk",
    response_model=Dict[str, int],
    status_code=status.HTTP_201_CREATED,
    summary="Add questions to test (bulk)",
    description=(
        "Attach several published questions in a single transaction, skipping "
        "duplicates. Every requested question must exist and be `PUBLISHED` "
        "(409 `QUESTION_NOT_PUBLISHED`); adding is blocked with 409 "
        "`TEST_HAS_ATTEMPTS` once the test has attempts. `total_marks` is "
        "recomputed and a single audit entry is written. Returns the `added` / "
        "`skipped` counts. Requires the `test.update` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND, **_CONFLICT},
    dependencies=[Depends(require_permission("test.update"))],
)
def add_questions_bulk(
    payload: TestQuestionsBulkAdd,
    request: Request,
    test_id: int = Path(..., ge=1, description="Unique test ID."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, int]:
    """Attach several published questions to the test in one transaction."""
    return test_service.add_questions_bulk(
        db, test_id, payload, user_id=current_user.id, request=request
    )


@router.delete(
    "/{test_id}/questions/{question_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove question from test",
    description=(
        "Detach a question from a test. 404 `QUESTION_NOT_IN_TEST` when the "
        "question is not part of the test; 409 `TEST_HAS_ATTEMPTS` once the "
        "test has attempts. The remaining questions are renumbered to a "
        "contiguous 1..n and `total_marks` is recomputed. Writes an audit "
        "entry. Requires the `test.update` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND, **_CONFLICT},
    dependencies=[Depends(require_permission("test.update"))],
)
def remove_question(
    request: Request,
    test_id: int = Path(..., ge=1, description="Unique test ID."),
    question_id: int = Path(..., ge=1, description="Unique question ID."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Detach a question, renumber the rest and recompute total marks."""
    test_service.remove_question(
        db, test_id, question_id, user_id=current_user.id, request=request
    )


@router.post(
    "/{test_id}/publish",
    response_model=TestResponse,
    summary="Publish test",
    description=(
        "Publish a `DRAFT` test that owns at least one question. Non-draft "
        "tests are refused with 409 `TEST_NOT_DRAFT`; an empty test with 400 "
        "`TEST_HAS_NO_QUESTIONS`. `total_marks` is recomputed from the attached "
        "questions. Writes an audit entry. Requires the `test.publish` "
        "permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND, **_CONFLICT, **_BAD_REQUEST},
    dependencies=[Depends(require_permission("test.publish"))],
)
def publish_test(
    request: Request,
    test_id: int = Path(..., ge=1, description="Unique test ID."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Test:
    """Publish a draft test and recompute its total marks."""
    return test_service.publish_test(
        db, test_id, user_id=current_user.id, request=request
    )


@router.post(
    "/{test_id}/close",
    response_model=TestResponse,
    summary="Close test",
    description=(
        "Move a `PUBLISHED` test to `CLOSED` so no new attempts can start. "
        "Only published tests can be closed (409 `TEST_NOT_PUBLISHED`). Writes "
        "an audit entry. Requires the `test.publish` permission."
    ),
    responses={**_UNAUTHORIZED, **_FORBIDDEN, **_NOT_FOUND, **_CONFLICT},
    dependencies=[Depends(require_permission("test.publish"))],
)
def close_test(
    request: Request,
    test_id: int = Path(..., ge=1, description="Unique test ID."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Test:
    """Close a published test."""
    return test_service.close_test(
        db, test_id, user_id=current_user.id, request=request
    )
