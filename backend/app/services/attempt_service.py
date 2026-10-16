"""Test-taking engine: start/resume, answer saving, submission and results.

The service owns the transactional lifecycle of an attempt (spec sections 17,
19 and 20):

* :func:`start_attempt` validates eligibility, availability and the attempt
  budget, then either resumes the student's open attempt or creates a new one
  with a server-side ``expires_at``.
* :func:`save_answers` upserts the answer rows, refusing writes after the
  server-side timer has elapsed.
* :func:`submit_attempt` locks the attempt row, evaluates every answer through
  :mod:`app.services.scoring_service`, writes the immutable :class:`Result`
  and moves the attempt to ``EVALUATED``.  A duplicate submission returns the
  already-computed result instead of creating a second one.

Per-answer correctness is deliberately *not* persisted: it is recomputed from
the test configuration at review time so historical results stay reproducible.
"""

import random
from typing import Any, Dict, List, Optional, Sequence, Tuple

from fastapi import Request
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.models.assignment import TestAssignment
from app.models.attempt import Attempt, AttemptAnswer
from app.models.notification import Notification
from app.models.question import Question, QuestionOption
from app.models.result import Result
from app.models.test import Test, TestQuestion
from app.repositories import attempt_repository
from app.schemas.attempt import (
    AnswerItem,
    AttemptResponse,
    SaveAnswersRequest,
    SavedAnswerResponse,
)
from app.schemas.question import OptionPublic, StudentQuestionView
from app.schemas.result import ResultResponse, ReviewAnswer
from app.schemas.student import StudentTestItem
from app.schemas.test import TestBrief
from app.services import scoring_service
from app.services.audit_service import record_audit
from app.utils.datetime import ensure_utc, utcnow
from app.utils.enums import (
    AssignmentStatus,
    AttemptStatus,
    SubmissionType,
    TestStatus,
)
from app.utils.pagination import PaginationParams, paginate

#: Statuses that mean "the attempt is finished and may not be touched again".
TERMINAL_STATUSES = {
    AttemptStatus.SUBMITTED.value,
    AttemptStatus.AUTO_SUBMITTED.value,
    AttemptStatus.EVALUATED.value,
    AttemptStatus.CANCELLED.value,
}

#: Tests a student is allowed to start.
STARTABLE_STATUSES = {TestStatus.PUBLISHED.value}


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------
def _attempt_response(attempt: Attempt) -> AttemptResponse:
    """Build the wire model, attaching the denormalised names."""
    attempt.test_name = attempt.test.name if attempt.test is not None else None
    attempt.student_name = attempt.student.full_name if attempt.student is not None else None
    return AttemptResponse.model_validate(attempt)


def _test_brief(test: Test) -> TestBrief:
    return TestBrief.model_validate(test)


def _effective_marks(test: Test, link: TestQuestion) -> Tuple[float, float]:
    return scoring_service.effective_marks(test, link)


def _question_view(test: Test, link: TestQuestion, *, randomize_options: bool) -> StudentQuestionView:
    """Answer-key-free view of one test question."""
    question = link.question
    marks, negative = _effective_marks(test, link)
    options = list(question.options)
    if randomize_options:
        options = list(options)
        random.shuffle(options)
    return StudentQuestionView(
        id=question.id,
        subject_id=question.subject_id,
        topic_id=question.topic_id,
        question_type=question.question_type,
        question_text=question.question_text,
        difficulty=question.difficulty,
        marks=marks,
        negative_marks=negative,
        options=[OptionPublic.model_validate(option) for option in options],
    )


def _question_views(test: Test, links: Sequence[TestQuestion]) -> List[StudentQuestionView]:
    """Order (and optionally shuffle) the question views of a test."""
    ordered = list(links)
    if test.randomize_questions:
        random.shuffle(ordered)
    return [
        _question_view(test, link, randomize_options=test.randomize_options)
        for link in ordered
    ]


def _remaining_seconds(attempt: Attempt) -> Optional[int]:
    expires_at = ensure_utc(attempt.expires_at)
    if expires_at is None:
        return None
    delta = int((expires_at - utcnow()).total_seconds())
    return max(0, delta)


# ---------------------------------------------------------------------------
# Reads
# ---------------------------------------------------------------------------
def get_attempt(db: Session, attempt_id: int) -> Attempt:
    attempt = attempt_repository.get_attempt(db, attempt_id)
    if attempt is None:
        raise NotFoundError("Attempt was not found.", code="ATTEMPT_NOT_FOUND")
    return attempt


def list_attempts(
    db: Session,
    params: PaginationParams,
    *,
    test_id: Optional[int] = None,
    student_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Admin attempt listing with test/student/status filters."""
    stmt = attempt_repository.build_attempt_list_stmt(
        params, test_id=test_id, student_id=student_id, status=params.status
    )
    return paginate(db, stmt, params)


def get_attempt_detail(db: Session, attempt_id: int) -> Attempt:
    """Attempt with its test/student decorated for the admin response."""
    attempt = get_attempt(db, attempt_id)
    _attempt_response(attempt)
    return attempt


def get_attempt_answers(db: Session, attempt_id: int) -> List[AttemptAnswer]:
    """Every persisted answer of an attempt, with a transient evaluation."""
    attempt = get_attempt(db, attempt_id)
    answers = attempt_repository.get_answers(db, attempt_id)
    test = attempt.test
    links = {link.question_id: link for link in test.test_questions} if test else {}
    answer_map = {answer.question_id: answer for answer in answers}
    score = scoring_service.score_attempt(test, list(links.values()), answer_map) if test else None
    for answer in answers:
        link = links.get(answer.question_id)
        question = link.question if link is not None else answer.question
        status = scoring_service.evaluate_answer(question, answer)
        answer.is_correct = (
            True if status == scoring_service.CORRECT
            else False if status == scoring_service.INCORRECT
            else None
        )
        marks, _ = _effective_marks(test, link) if (test is not None and link is not None) else (0.0, 0.0)
        answer.marks_awarded = scoring_service.awarded_marks(status, marks, 0.0) if question is not None else None
        marks, _ = _effective_marks(test, link) if (test is not None and link is not None) else (0.0, 0.0)
        answer.marks_awarded = scoring_service.awarded_marks(status, marks, 0.0) if question is not None else None
        answer.question_text = getattr(question, "question_text", None)
        labels = _option_label_map(question)
        if answer.selected_option_ids:
            answer.selected_option_text = ", ".join(
                labels.get(int(value), str(value)) for value in answer.selected_option_ids
            )
        elif answer.selected_option_id is not None:
            answer.selected_option_text = labels.get(
                int(answer.selected_option_id), str(answer.selected_option_id)
            )
        else:
            answer.selected_option_text = None
    return answers


# ---------------------------------------------------------------------------
# Starting / resuming
# ---------------------------------------------------------------------------
def _assert_student_eligibility(db: Session, test: Test, student_id: int) -> Optional[TestAssignment]:
    """Return the student's assignment, or ``None`` for an open test."""
    assigned_count = attempt_repository.count_assignments(db, test.id)
    assignment = attempt_repository.get_assignment(db, test.id, student_id)
    if assigned_count > 0 and assignment is None:
        raise ForbiddenError(
            "Test is not assigned to this student.",
            code="NOT_ASSIGNED",
        )
    return assignment


def _assert_availability(test: Test, assignment: Optional[TestAssignment]) -> None:
    now = utcnow()
    if test.scheduled_start_at is not None and ensure_utc(test.scheduled_start_at) > now:
        raise ConflictError(
            "Test has not started yet.",
            code="TEST_WINDOW_CLOSED",
            details={"scheduled_start_at": test.scheduled_start_at.isoformat()},
        )
    if test.scheduled_end_at is not None and ensure_utc(test.scheduled_end_at) < now:
        raise ConflictError(
            "Test window has closed.",
            code="TEST_WINDOW_CLOSED",
            details={"scheduled_end_at": test.scheduled_end_at.isoformat()},
        )
    if assignment is not None:
        if assignment.available_from is not None and ensure_utc(assignment.available_from) > now:
            raise ConflictError(
                "Test is not available to you yet.",
                code="TEST_WINDOW_CLOSED",
                details={"available_from": assignment.available_from.isoformat()},
            )
        if assignment.available_until is not None and ensure_utc(assignment.available_until) < now:
            raise ConflictError(
                "Your availability window for this test has closed.",
                code="TEST_WINDOW_CLOSED",
                details={"available_until": assignment.available_until.isoformat()},
            )


def _max_attempts(test: Test, assignment: Optional[TestAssignment]) -> int:
    if assignment is not None and assignment.max_attempts is not None:
        return int(assignment.max_attempts)
    return int(test.max_attempts or 1)


def start_attempt(
    db: Session,
    test_id: int,
    *,
    student_id: int,
    request: Optional[Request] = None,
) -> Dict[str, Any]:
    """Resume the open attempt or create a new one and return the questions."""
    test = attempt_repository.get_test_with_questions(db, test_id)
    if test is None:
        raise NotFoundError("Test was not found.", code="TEST_NOT_FOUND")
    if test.status not in STARTABLE_STATUSES:
        raise ConflictError(
            "Test is not published.",
            code="TEST_NOT_PUBLISHED",
            details={"status": test.status},
        )
    if not test.test_questions:
        raise BadRequestError("Test has no questions.", code="TEST_HAS_NO_QUESTIONS")

    assignment = _assert_student_eligibility(db, test, student_id)
    _assert_availability(test, assignment)

    # Resume an existing open attempt rather than burning another one.
    open_attempts = attempt_repository.get_started_attempts(db, test_id, student_id)
    if open_attempts:
        attempt = sorted(open_attempts, key=lambda row: row.id)[0]
        if attempt.is_expired:
            submit_attempt(
                db,
                attempt.id,
                student_id=student_id,
                request=request,
                submit_type=SubmissionType.EXPIRED,
            )
        else:
            return {
                "attempt": _attempt_response(attempt),
                "test": _test_brief(test),
                "questions": _question_views(test, test.test_questions),
                "remaining_seconds": _remaining_seconds(attempt),
            }

    max_attempts = _max_attempts(test, assignment)
    used = attempt_repository.count_student_attempts(db, test_id, student_id)
    if used >= max_attempts:
        raise ConflictError(
            "Maximum number of attempts reached.",
            code="MAX_ATTEMPTS_REACHED",
            details={"max_attempts": max_attempts, "attempts_used": used},
        )

    now = utcnow()
    attempt = Attempt(
        test_id=test_id,
        student_id=student_id,
        attempt_number=used + 1,
        started_at=now,
        expires_at=now + _duration(test),
        status=AttemptStatus.STARTED.value,
    )
    db.add(attempt)
    try:
        db.flush()
        record_audit(
            db,
            user_id=student_id,
            module="attempt",
            action="start",
            entity_type="attempt",
            entity_id=attempt.id,
            new_data={"test_id": test_id, "attempt_number": attempt.attempt_number},
            request=request,
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        # A concurrent request created the attempt first - resume it.
        existing = attempt_repository.get_started_attempts(db, test_id, student_id)
        if not existing:
            raise ConflictError("Could not start the attempt.", code="ATTEMPT_CONFLICT")
        attempt = existing[0]
    except Exception:
        db.rollback()
        raise

    return {
        "attempt": _attempt_response(attempt),
        "test": _test_brief(test),
        "questions": _question_views(test, test.test_questions),
        "remaining_seconds": _remaining_seconds(attempt),
    }


def _duration(test: Test):
    from datetime import timedelta

    return timedelta(minutes=int(test.duration_minutes or 0))


def get_active_attempt(db: Session, attempt_id: int, *, student_id: int) -> Dict[str, Any]:
    """Active-attempt payload (questions + answers saved so far)."""
    attempt = get_attempt(db, attempt_id)
    if attempt.student_id != student_id:
        raise NotFoundError("Attempt was not found.", code="ATTEMPT_NOT_FOUND")
    test = attempt_repository.get_test_with_questions(db, attempt.test_id)
    answers = attempt_repository.get_answers(db, attempt_id)
    return {
        "attempt": _attempt_response(attempt),
        "test": _test_brief(test) if test is not None else None,
        "questions": _question_views(test, test.test_questions) if test is not None else [],
        "answers": answers,
        "remaining_seconds": _remaining_seconds(attempt),
    }


# ---------------------------------------------------------------------------
# Saving answers
# ---------------------------------------------------------------------------
def _validate_answer_item(
    db: Session,
    *,
    question: Optional[Question],
    item: AnswerItem,
) -> None:
    if question is None:
        raise BadRequestError(
            "Question does not belong to this test.",
            code="QUESTION_NOT_IN_TEST",
            details={"question_id": item.question_id},
        )
    option_ids = set()
    if item.selected_option_id is not None:
        option_ids.add(int(item.selected_option_id))
    for value in item.selected_option_ids or []:
        option_ids.add(int(value))
    if option_ids:
        valid_ids = {option.id for option in question.options}
        unknown = option_ids - valid_ids
        if unknown:
            raise BadRequestError(
                "Selected option does not belong to the question.",
                code="ANSWER_OPTION_MISMATCH",
                details={"question_id": item.question_id, "option_ids": sorted(unknown)},
            )


def save_answers(
    db: Session,
    attempt_id: int,
    payload: SaveAnswersRequest,
    *,
    student_id: int,
    request: Optional[Request] = None,
) -> Dict[str, Any]:
    """Upsert the provided answers for a still-running attempt."""
    attempt = attempt_repository.get_attempt(db, attempt_id, for_update=True)
    if attempt is None:
        raise NotFoundError("Attempt was not found.", code="ATTEMPT_NOT_FOUND")
    if attempt.student_id != student_id:
        raise NotFoundError("Attempt was not found.", code="ATTEMPT_NOT_FOUND")
    if attempt.status in TERMINAL_STATUSES:
        raise ConflictError(
            "Attempt has already been submitted.",
            code="ATTEMPT_ALREADY_SUBMITTED",
            details={"status": attempt.status},
        )
    if attempt.is_expired:
        raise ConflictError("Attempt time has expired.", code="ATTEMPT_EXPIRED")

    test = attempt_repository.get_test_with_questions(db, attempt.test_id)
    question_map = {link.question_id: link.question for link in test.test_questions} if test else {}
    existing = {answer.question_id: answer for answer in attempt_repository.get_answers(db, attempt_id)}

    now = utcnow()
    saved = 0
    for item in payload.answers:
        _validate_answer_item(db, question=question_map.get(item.question_id), item=item)
        answer = existing.get(item.question_id)
        if answer is None:
            answer = AttemptAnswer(attempt_id=attempt_id, question_id=item.question_id)
            db.add(answer)
            existing[item.question_id] = answer
        answer.selected_option_id = item.selected_option_id
        answer.selected_option_ids = item.selected_option_ids
        answer.answer_text = item.answer_text
        answer.numerical_answer = item.numerical_answer
        answer.is_marked_for_review = bool(item.is_marked_for_review)
        answer.answered_at = now
        saved += 1

    try:
        db.flush()
        record_audit(
            db,
            user_id=student_id,
            module="attempt",
            action="save_answers",
            entity_type="attempt",
            entity_id=attempt_id,
            new_data={"saved": saved},
            request=request,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise

    answered = sum(1 for answer in existing.values() if _is_answered(answer))
    total_questions = len(question_map)
    return {
        "attempt_id": attempt_id,
        "saved": saved,
        "answered_count": answered,
        "remaining_count": max(0, total_questions - answered),
        "expires_at": attempt.expires_at,
    }


def _is_answered(answer: AttemptAnswer) -> bool:
    if answer.selected_option_id is not None:
        return True
    if answer.selected_option_ids:
        return True
    if answer.answer_text and answer.answer_text.strip():
        return True
    if answer.numerical_answer and str(answer.numerical_answer).strip():
        return True
    return False


# ---------------------------------------------------------------------------
# Submission
# ---------------------------------------------------------------------------
def submit_attempt(
    db: Session,
    attempt_id: int,
    *,
    student_id: int,
    request: Optional[Request] = None,
    submit_type: SubmissionType = SubmissionType.MANUAL,
) -> Result:
    """Evaluate an attempt exactly once and persist its result."""
    attempt = attempt_repository.get_attempt(db, attempt_id, for_update=True)
    if attempt is None:
        raise NotFoundError("Attempt was not found.", code="ATTEMPT_NOT_FOUND")
    if attempt.student_id != student_id:
        raise NotFoundError("Attempt was not found.", code="ATTEMPT_NOT_FOUND")

    if attempt.status in TERMINAL_STATUSES or (
        attempt_repository.get_result_by_attempt(db, attempt_id) is not None
    ):
        raise ConflictError(
            "Attempt has already been submitted.",
            code="ATTEMPT_ALREADY_SUBMITTED",
            details={"status": attempt.status},
        )

    test = attempt_repository.get_test_with_questions(db, attempt.test_id)
    if test is None:
        raise NotFoundError("Test was not found.", code="TEST_NOT_FOUND")

    answers = attempt_repository.get_answers(db, attempt_id)
    score = scoring_service.score_attempt(test, test.test_questions, answers)
    passed = scoring_service.is_pass(test, score.score, score.percentage)

    now = utcnow()
    attempt.submitted_at = now
    attempt.score = score.score
    attempt.max_score = score.max_score
    attempt.percentage = score.percentage
    attempt.status = AttemptStatus.EVALUATED.value
    attempt.submission_type = submit_type.value

    result = Result(
        attempt_id=attempt_id,
        student_id=student_id,
        test_id=attempt.test_id,
        score=score.score,
        max_score=score.max_score,
        percentage=score.percentage,
        correct_count=score.correct_count,
        incorrect_count=score.incorrect_count,
        unanswered_count=score.unanswered_count,
        pass_status=passed,
    )
    db.add(result)
    db.flush()

    # Close the student's assignment once they have finished a scored attempt.
    assignment = attempt_repository.get_assignment(db, attempt.test_id, student_id)
    if assignment is not None and assignment.status == AssignmentStatus.ASSIGNED.value:
        assignment.status = AssignmentStatus.COMPLETED.value

    recompute_ranks(db, attempt.test_id)
    record_audit(
        db,
        user_id=student_id,
        module="attempt",
        action="submit",
        entity_type="attempt",
        entity_id=attempt_id,
        new_data={
            "result_id": result.id,
            "score": score.score,
            "max_score": score.max_score,
            "percentage": score.percentage,
            "submission_type": attempt.submission_type,
        },
        request=request,
    )
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return result


def recompute_ranks(db: Session, test_id: int) -> None:
    """Recompute ``rank``/``percentile`` for every result of a test.

    Ranks are competition style (ties share the best rank).  The percentile is
    the share of results scored at or below the row, expressed 0-100.
    """
    results = list(
        db.scalars(
            select(Result)
            .where(Result.test_id == test_id)
            .order_by(Result.score.desc(), Result.id.asc())
        ).all()
    )
    total = len(results)
    if not total:
        return
    previous_score: Optional[float] = None
    current_rank = 0
    for index, result in enumerate(results, start=1):
        score = float(result.score or 0)
        if previous_score is None or score != previous_score:
            current_rank = index
        result.rank = current_rank
        previous_score = score
    for result in results:
        percentage = float(result.percentage or 0)
        at_or_below = sum(1 for other in results if float(other.percentage or 0) <= percentage)
        result.percentile = round(at_or_below / total * 100, 2)


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------
def _result_response(result: Result) -> ResultResponse:
    result.test_name = result.test.name if result.test is not None else None
    result.student_name = result.student.full_name if result.student is not None else None
    result.attempt_number = result.attempt.attempt_number if result.attempt is not None else None
    return ResultResponse.model_validate(result)


def result_payload(result: Result) -> ResultResponse:
    """Public serialiser for a result (used by the results/attempts routers)."""
    return _result_response(result)


def get_result(db: Session, result_id: int) -> Result:
    result = attempt_repository.get_result(db, result_id)
    if result is None:
        raise NotFoundError("Result was not found.", code="RESULT_NOT_FOUND")
    return result


def list_results(
    db: Session,
    params: PaginationParams,
    *,
    test_id: Optional[int] = None,
    student_id: Optional[int] = None,
    published: Optional[bool] = None,
) -> Dict[str, Any]:
    stmt = attempt_repository.build_result_list_stmt(
        params, test_id=test_id, student_id=student_id, published=published
    )
    page = paginate(db, stmt, params)
    for result in page["items"]:
        _result_response(result)
    return page


def list_student_results(
    db: Session,
    params: PaginationParams,
    *,
    student_id: int,
    test_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Paginated own-results listing, newest first (``created_at`` DESC)."""
    stmt = attempt_repository.build_student_result_stmt(
        params, student_id=student_id, test_id=test_id
    )
    page = paginate(db, stmt, params)
    for result in page["items"]:
        _result_response(result)
    return page


def list_student_attempts(
    db: Session,
    params: PaginationParams,
    *,
    student_id: int,
) -> Dict[str, Any]:
    stmt = attempt_repository.build_attempt_list_stmt(params, student_id=student_id)
    return paginate(db, stmt, params)


def publish_result(
    db: Session,
    result_id: int,
    *,
    user_id: int,
    request: Optional[Request] = None,
) -> Result:
    """Publish a result and notify the student (idempotent)."""
    result = get_result(db, result_id)
    if result.published_at is not None:
        raise ConflictError(
            "Result has already been published.", code="RESULT_ALREADY_PUBLISHED"
        )
    result.published_at = utcnow()
    db.add(
        Notification(
            user_id=result.student_id,
            title="Your result is available",
            message=(
                f"Result for '{result.test.name if result.test else 'test'}' "
                f"has been published. Score: {float(result.score or 0):g}."
            ),
            type="RESULT_PUBLISHED",
            is_read=False,
        )
    )
    record_audit(
        db,
        user_id=user_id,
        module="result",
        action="publish",
        entity_type="result",
        entity_id=result.id,
        new_data={"published_at": result.published_at.isoformat()},
        request=request,
    )
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return result


def review_result(db: Session, result_id: int, *, student_id: Optional[int] = None) -> Dict[str, Any]:
    """Result plus the per-question answer key (optionally owner-restricted)."""
    result = get_result(db, result_id)
    if student_id is not None and result.student_id != student_id:
        raise NotFoundError("Result was not found.", code="RESULT_NOT_FOUND")

    attempt = attempt_repository.get_attempt(db, result.attempt_id)
    test = attempt_repository.get_test_with_questions(db, result.test_id) if attempt else None
    answers = attempt_repository.get_answers(db, result.attempt_id)
    answer_map = {answer.question_id: answer for answer in answers}

    reviews: List[ReviewAnswer] = []
    if test is not None:
        ordered = sorted(test.test_questions, key=lambda link: link.question_order)
        for link in ordered:
            question = link.question
            answer = answer_map.get(question.id)
            status = scoring_service.evaluate_answer(question, answer)
            marks, _ = _effective_marks(test, link)
            reviews.append(
                ReviewAnswer(
                    question_id=question.id,
                    question_text=question.question_text,
                    question_type=question.question_type,
                    your_answer=_answer_display(answer, question),
                    correct_answer=_correct_display(question),
                    is_correct=(
                        True if status == scoring_service.CORRECT
                        else False if status == scoring_service.INCORRECT
                        else None
                    ),
                    marks_awarded=scoring_service.awarded_marks(status, marks, 0.0),
                    marks_possible=marks,
                    explanation=question.explanation,
                    options=[
                        {
                            "id": option.id,
                            "option_text": option.option_text,
                            "option_order": option.option_order,
                            "is_correct": option.is_correct,
                        }
                        for option in question.options
                    ],
                )
            )
    return {"result": _result_response(result), "answers": reviews}


def _option_label_map(question: Optional[Question]) -> dict:
    """Map each option id to a ``"A. option text"`` style label."""
    labels: dict = {}
    if question is None:
        return labels
    for option in question.options:
        order = option.option_order or 0
        letter = chr(ord("A") + order - 1) if 1 <= order <= 26 else str(order)
        labels[option.id] = f"{letter}. {option.option_text}"
    return labels


def _answer_display(
    answer: Optional[AttemptAnswer], question: Optional[Question] = None
) -> Optional[str]:
    if answer is None:
        return None
    labels = _option_label_map(question)
    if answer.selected_option_ids:
        return ", ".join(
            labels.get(int(value), str(value)) for value in answer.selected_option_ids
        )
    if answer.selected_option_id is not None:
        return labels.get(int(answer.selected_option_id), str(answer.selected_option_id))
    if answer.numerical_answer:
        return answer.numerical_answer
    if answer.answer_text:
        return answer.answer_text
    return None


def _correct_display(question: Optional[Question]) -> Optional[str]:
    if question is None:
        return None
    correct = sorted(
        (option for option in question.options if option.is_correct),
        key=lambda option: option.option_order or 0,
    )
    if not correct:
        return None
    labels = _option_label_map(question)
    return ", ".join(labels.get(option.id, str(option.id)) for option in correct)


def export_results(
    db: Session,
    *,
    test_id: Optional[int] = None,
    student_id: Optional[int] = None,
    published: Optional[bool] = None,
) -> List[Result]:
    """All matching results (no pagination) for CSV export."""
    params = PaginationParams(
        page=1,
        page_size=100,
        search=None,
        status=None,
        sort_by=None,
        sort_order="desc",
    )
    stmt = attempt_repository.build_result_list_stmt(
        params, test_id=test_id, student_id=student_id, published=published
    )
    return list(db.scalars(stmt).all())


# ---------------------------------------------------------------------------
# Student dashboard helpers
# ---------------------------------------------------------------------------
def _attempt_brief(attempt: Optional[Attempt]) -> Tuple[Optional[int], Optional[str]]:
    if attempt is None:
        return None, None
    return attempt.id, attempt.status


def list_student_tests(
    db: Session,
    *,
    student_id: int,
    search: Optional[str] = None,
) -> List[StudentTestItem]:
    """Visible tests for a student, decorated with assignment/attempt state."""
    now = utcnow()
    stmt = attempt_repository.build_student_test_stmt(
        student_id=student_id, now=now, search=search
    )
    rows = db.execute(stmt).all()
    if not rows:
        return []
    test_ids = [test.id for test, _ in rows]

    attempt_counts = attempt_repository.bulk_attempt_counts(db, test_ids, student_id)
    active_attempts = attempt_repository.bulk_active_attempts(db, test_ids, student_id)

    # Latest attempt and best result per test for the current student.
    attempts = list(
        db.scalars(
            select(Attempt)
            .where(Attempt.student_id == student_id, Attempt.test_id.in_(test_ids))
            .order_by(Attempt.created_at.desc(), Attempt.id.desc())
        ).all()
    )
    last_attempt: Dict[int, Attempt] = {}
    for attempt in attempts:
        last_attempt.setdefault(attempt.test_id, attempt)
    best_percentage = {
        int(test_id): float(value)
        for test_id, value in db.execute(
            select(Result.test_id, func.max(Result.percentage))
            .where(Result.student_id == student_id, Result.test_id.in_(test_ids))
            .group_by(Result.test_id)
        ).all()
    }

    items: List[StudentTestItem] = []
    for test, assignment in rows:
        used = attempt_counts.get(test.id, 0)
        max_attempts = (
            assignment.max_attempts
            if assignment is not None and assignment.max_attempts is not None
            else test.max_attempts
        )
        remaining = max(0, int(max_attempts or 0) - used)
        active = active_attempts.get(test.id)
        last = last_attempt.get(test.id)
        reason: Optional[str] = None
        if test.status != TestStatus.PUBLISHED.value:
            reason = "Test is not open for attempts."
        elif remaining <= 0:
            reason = "No attempts remaining."
        items.append(
            StudentTestItem(
                test=TestBrief.model_validate(test),
                assignment_id=assignment.id if assignment is not None else 0,
                assignment_status=assignment.status if assignment is not None else "OPEN",
                available_from=assignment.available_from if assignment is not None else None,
                available_until=assignment.available_until if assignment is not None else None,
                max_attempts=int(max_attempts) if max_attempts is not None else None,
                attempts_used=used,
                attempts_remaining=remaining,
                can_attempt=reason is None,
                last_attempt_id=last.id if last is not None else None,
                last_attempt_status=last.status if last is not None else None,
                best_percentage=best_percentage.get(test.id),
                unavailable_reason=reason if active is None else None,
            )
        )
    return items


def get_student_test(db: Session, test_id: int, *, student_id: int) -> StudentTestItem:
    """The dashboard row for one visible test (404/403 on invisibility)."""
    items = list_student_tests(db, student_id=student_id)
    for item in items:
        if item.test.id == test_id:
            return item
    raise NotFoundError(
        "Test was not found or is not available to you.",
        code="TEST_NOT_FOUND",
        details={"test_id": test_id},
    )
