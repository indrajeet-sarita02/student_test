"""Aggregation queries backing the report endpoints.

Every function here builds a SQL aggregate query (``func.count`` / ``avg`` /
``sum`` / ``case``) and never loads whole tables into the application. The
question/subject accuracy columns re-apply the scoring rules inside SQL so the
report stays consistent with :mod:`app.services.scoring_service`:

* single-choice / true-false: the selected option is one of the correct options;
* multiple-choice: the selected set equals the correct set (JSONB containment);
* numerical: the numeric answer matches the correct option text within ``1e-6``;
* subjective: cannot be auto-graded and is reported as unattempted.

The app targets PostgreSQL 17, so the JSONB operators used for multiple-choice
containment are rendered for that dialect.
"""

from typing import Any, Dict, List, Optional

from sqlalchemy import Float, and_, case, cast, func, or_, select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.assignment import TestAssignment
from app.models.attempt import Attempt, AttemptAnswer
from app.models.exam import Exam
from app.models.question import Question, QuestionOption
from app.models.result import Result
from app.models.role import Role
from app.models.subject import Subject
from app.models.test import Test, TestQuestion
from app.models.topic import Topic
from app.models.user import User, UserRole
from app.utils.enums import AttemptStatus, QuestionType, TestStatus

# ---------------------------------------------------------------------------
# Shared scoring expressions (SQL mirror of scoring_service)
# ---------------------------------------------------------------------------

_QTYPE = Question.question_type
_SINGLE_TYPES = (QuestionType.SINGLE_CHOICE.value, QuestionType.TRUE_FALSE.value)


def _correct_ids() -> Any:
    """JSONB array of the correct option ids for the correlated question."""
    return func.coalesce(
        func.jsonb_agg(QuestionOption.id),
        func.jsonb_build_array(),
    )


def _correct_ids_subquery() -> Any:
    """Scalar correlated subquery: correct option ids of the current question."""
    return (
        select(_correct_ids())
        .where(
            QuestionOption.question_id == Question.id,
            QuestionOption.is_correct.is_(True),
        )
        .scalar_subquery()
    )


def _selected_ids_array() -> Any:
    """``selected_option_ids`` coerced to a JSONB array.

    The column is JSONB and a Python ``None`` is persisted as the JSON scalar
    ``null`` rather than SQL NULL.  ``jsonb_array_length`` (and the containment
    operators) reject that scalar with ``cannot get array length of a scalar``,
    so normalise on ``jsonb_typeof``: real arrays pass through, while SQL NULL,
    JSON ``null`` and any other scalar become ``[]``.
    """
    column = AttemptAnswer.selected_option_ids
    return case(
        (func.jsonb_typeof(column) == "array", column),
        else_=func.jsonb_build_array(),
    )


def _selected_set() -> Any:
    """The answer's selected option ids as JSONB (multi list or single id)."""
    column = AttemptAnswer.selected_option_ids
    return case(
        (func.jsonb_typeof(column) == "array", column),
        else_=func.jsonb_build_array(AttemptAnswer.selected_option_id),
    )


def _answered_expr() -> Any:
    """True when the answer row carries any student-provided content."""
    return or_(
        AttemptAnswer.selected_option_id.isnot(None),
        func.jsonb_array_length(_selected_ids_array()) > 0,
        func.nullif(func.trim(AttemptAnswer.numerical_answer), "").isnot(None),
        func.nullif(func.trim(AttemptAnswer.answer_text), "").isnot(None),
    )


def _correct_expr() -> Any:
    """True when the answer is objectively correct for its question type."""
    correct_single = and_(
        _QTYPE.in_(_SINGLE_TYPES),
        AttemptAnswer.selected_option_id.isnot(None),
        AttemptAnswer.selected_option_id.in_(
            select(QuestionOption.id).where(
                QuestionOption.question_id == Question.id,
                QuestionOption.is_correct.is_(True),
            )
        ),
    )
    correct_ids = _correct_ids_subquery()
    selected = _selected_set()
    correct_multiple = and_(
        _QTYPE == QuestionType.MULTIPLE_CHOICE.value,
        selected.op("@>")(correct_ids),
        selected.op("<@")(correct_ids),
    )
    correct_text = (
        select(QuestionOption.option_text)
        .where(
            QuestionOption.question_id == Question.id,
            QuestionOption.is_correct.is_(True),
        )
        .limit(1)
        .scalar_subquery()
    )
    correct_numerical = and_(
        _QTYPE == QuestionType.NUMERICAL.value,
        func.abs(
            cast(func.nullif(func.trim(AttemptAnswer.numerical_answer), ""), Float)
            - cast(correct_text, Float)
        )
        <= 1e-6,
    )
    return or_(correct_single, correct_multiple, correct_numerical)


def _group_by_question() -> Any:
    """Grouped correctness aggregates for one question."""
    answered = _answered_expr()
    correct = _correct_expr()
    return {
        "times_used": func.count(AttemptAnswer.id),
        "times_answered": func.coalesce(
            func.sum(case((answered, 1), else_=0)), 0
        ),
        "correct_count": func.coalesce(
            func.sum(case((and_(answered, correct), 1), else_=0)), 0
        ),
        "incorrect_count": func.coalesce(
            func.sum(
                case(
                    (
                        and_(
                            answered,
                            ~correct,
                            _QTYPE != QuestionType.SUBJECTIVE.value,
                        ),
                        1,
                    ),
                    else_=0,
                )
            ),
            0,
        ),
        "unattempted_count": func.coalesce(
            func.sum(case((~answered, 1), else_=0)), 0
        ),
    }


def _accuracy(correct: Any, answered: Any) -> Any:
    """Percentage accuracy, ``None`` when nothing was answered."""
    return case(
        (answered > 0, func.round(correct * 100.0 / func.nullif(answered, 0), 2)),
        else_=None,
    )


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


def dashboard_report(db: Session) -> Dict[str, Any]:
    """Global counts plus average percentage and pass rate."""
    total_users = int(db.scalar(select(func.count()).select_from(User)) or 0)
    total_students = int(
        db.scalar(
            select(func.count(func.distinct(UserRole.user_id)))
            .select_from(UserRole)
            .join(Role, Role.id == UserRole.role_id)
            .where(Role.code == "STUDENT")
        )
        or 0
    )
    total_exams = int(db.scalar(select(func.count()).select_from(Exam)) or 0)
    total_tests = int(db.scalar(select(func.count()).select_from(Test)) or 0)
    total_questions = int(db.scalar(select(func.count()).select_from(Question)) or 0)
    published_tests = int(
        db.scalar(
            select(func.count())
            .select_from(Test)
            .where(Test.status == TestStatus.PUBLISHED.value)
        )
        or 0
    )
    total_attempts = int(db.scalar(select(func.count()).select_from(Attempt)) or 0)
    active_attempts = int(
        db.scalar(
            select(func.count())
            .select_from(Attempt)
            .where(Attempt.status == AttemptStatus.STARTED.value)
        )
        or 0
    )
    total_results = int(db.scalar(select(func.count()).select_from(Result)) or 0)
    average_percentage = db.scalar(select(func.avg(Result.percentage)))
    passed = int(
        db.scalar(
            select(func.count())
            .select_from(Result)
            .where(Result.pass_status.is_(True))
        )
        or 0
    )
    pass_rate = round(passed / total_results * 100, 2) if total_results else 0.0
    return {
        "total_users": total_users,
        "total_students": total_students,
        "total_exams": total_exams,
        "total_tests": total_tests,
        "total_questions": total_questions,
        "published_tests": published_tests,
        "total_attempts": total_attempts,
        "active_attempts": active_attempts,
        "total_results": total_results,
        "average_percentage": round(float(average_percentage or 0.0), 2),
        "pass_rate": pass_rate,
    }


# ---------------------------------------------------------------------------
# Exams
# ---------------------------------------------------------------------------


def exams_report(db: Session) -> List[Dict[str, Any]]:
    """Per-exam subject/question/test/attempt counts and average percentage."""
    subject_counts = (
        select(Subject.exam_id.label("exam_id"), func.count(Subject.id).label("subject_count"))
        .group_by(Subject.exam_id)
        .subquery()
    )
    question_counts = (
        select(Subject.exam_id.label("exam_id"), func.count(Question.id).label("question_count"))
        .select_from(Subject)
        .join(Question, Question.subject_id == Subject.id)
        .group_by(Subject.exam_id)
        .subquery()
    )
    test_counts = (
        select(Test.exam_id.label("exam_id"), func.count(Test.id).label("test_count"))
        .group_by(Test.exam_id)
        .subquery()
    )
    attempt_counts = (
        select(Test.exam_id.label("exam_id"), func.count(Attempt.id).label("attempt_count"))
        .select_from(Test)
        .join(Attempt, Attempt.test_id == Test.id)
        .group_by(Test.exam_id)
        .subquery()
    )
    avg_percentage = (
        select(
            Test.exam_id.label("exam_id"),
            func.avg(Result.percentage).label("average_percentage"),
        )
        .select_from(Test)
        .join(Result, Result.test_id == Test.id)
        .group_by(Test.exam_id)
        .subquery()
    )
    stmt = (
        select(
            Exam.id,
            Exam.name,
            Exam.code,
            Exam.status,
            func.coalesce(subject_counts.c.subject_count, 0),
            func.coalesce(question_counts.c.question_count, 0),
            func.coalesce(test_counts.c.test_count, 0),
            func.coalesce(attempt_counts.c.attempt_count, 0),
            avg_percentage.c.average_percentage,
        )
        .outerjoin(subject_counts, subject_counts.c.exam_id == Exam.id)
        .outerjoin(question_counts, question_counts.c.exam_id == Exam.id)
        .outerjoin(test_counts, test_counts.c.exam_id == Exam.id)
        .outerjoin(attempt_counts, attempt_counts.c.exam_id == Exam.id)
        .outerjoin(avg_percentage, avg_percentage.c.exam_id == Exam.id)
        .order_by(Exam.id.asc())
    )
    return [
        {
            "exam_id": row[0],
            "exam_name": row[1],
            "exam_code": row[2],
            "status": row[3],
            "subject_count": int(row[4] or 0),
            "question_count": int(row[5] or 0),
            "test_count": int(row[6] or 0),
            "attempt_count": int(row[7] or 0),
            "average_percentage": (
                round(float(row[8]), 2) if row[8] is not None else None
            ),
        }
        for row in db.execute(stmt).all()
    ]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def tests_report(
    db: Session,
    *,
    exam_id: Optional[int] = None,
    status: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Per-test assembly/attempt/result statistics."""
    question_counts = (
        select(
            TestQuestion.test_id.label("test_id"),
            func.count(TestQuestion.id).label("question_count"),
        )
        .group_by(TestQuestion.test_id)
        .subquery()
    )
    assigned_counts = (
        select(TestAssignment.test_id.label("test_id"), func.count().label("assigned_count"))
        .group_by(TestAssignment.test_id)
        .subquery()
    )
    attempt_counts = (
        select(Attempt.test_id.label("test_id"), func.count().label("attempt_count"))
        .group_by(Attempt.test_id)
        .subquery()
    )
    result_stats = (
        select(
            Result.test_id.label("test_id"),
            func.count().label("evaluated_count"),
            func.avg(Result.percentage).label("average_percentage"),
            func.max(Result.percentage).label("highest_percentage"),
            func.min(Result.percentage).label("lowest_percentage"),
            func.sum(case((Result.pass_status.is_(True), 1), else_=0)).label("passed_count"),
        )
        .group_by(Result.test_id)
        .subquery()
    )
    stmt = (
        select(
            Test.id,
            Test.name,
            Test.code,
            Test.exam_id,
            Exam.name,
            Test.status,
            func.coalesce(question_counts.c.question_count, 0),
            func.coalesce(assigned_counts.c.assigned_count, 0),
            func.coalesce(attempt_counts.c.attempt_count, 0),
            func.coalesce(result_stats.c.evaluated_count, 0),
            result_stats.c.average_percentage,
            result_stats.c.highest_percentage,
            result_stats.c.lowest_percentage,
            result_stats.c.passed_count,
        )
        .join(Exam, Exam.id == Test.exam_id)
        .outerjoin(question_counts, question_counts.c.test_id == Test.id)
        .outerjoin(assigned_counts, assigned_counts.c.test_id == Test.id)
        .outerjoin(attempt_counts, attempt_counts.c.test_id == Test.id)
        .outerjoin(result_stats, result_stats.c.test_id == Test.id)
    )
    if exam_id is not None:
        stmt = stmt.where(Test.exam_id == exam_id)
    if status:
        stmt = stmt.where(Test.status == status)
    stmt = stmt.order_by(Test.id.asc())

    rows: List[Dict[str, Any]] = []
    for row in db.execute(stmt).all():
        evaluated = int(row[9] or 0)
        passed = int(row[13] or 0)
        rows.append(
            {
                "test_id": row[0],
                "test_name": row[1],
                "test_code": row[2],
                "exam_id": row[3],
                "exam_name": row[4],
                "status": row[5],
                "question_count": int(row[6] or 0),
                "assigned_count": int(row[7] or 0),
                "attempt_count": int(row[8] or 0),
                "evaluated_count": evaluated,
                "average_percentage": (
                    round(float(row[10]), 2) if row[10] is not None else None
                ),
                "highest_percentage": (
                    round(float(row[11]), 2) if row[11] is not None else None
                ),
                "lowest_percentage": (
                    round(float(row[12]), 2) if row[12] is not None else None
                ),
                "pass_rate": (
                    round(passed / evaluated * 100, 2) if evaluated else None
                ),
            }
        )
    return rows


# ---------------------------------------------------------------------------
# Students
# ---------------------------------------------------------------------------


def student_report(db: Session, student_id: int) -> Dict[str, Any]:
    """Per-student activity plus average/best percentages, score and rank."""
    student = db.get(User, student_id)
    if student is None:
        raise NotFoundError("User was not found.", code="USER_NOT_FOUND")

    tests_assigned = int(
        db.scalar(
            select(func.count())
            .select_from(TestAssignment)
            .where(TestAssignment.student_id == student_id)
        )
        or 0
    )
    attempts_taken = int(
        db.scalar(
            select(func.count())
            .select_from(Attempt)
            .where(Attempt.student_id == student_id)
        )
        or 0
    )
    tests_completed = int(
        db.scalar(
            select(func.count())
            .select_from(Result)
            .where(Result.student_id == student_id)
        )
        or 0
    )
    avg_percentage, best_percentage, avg_score = db.execute(
        select(
            func.avg(Result.percentage),
            func.max(Result.percentage),
            func.avg(Result.score),
        ).where(Result.student_id == student_id)
    ).one()

    rank: Optional[int] = None
    if avg_percentage is not None:
        per_student = (
            select(
                Result.student_id.label("student_id"),
                func.avg(Result.percentage).label("avg_percentage"),
            )
            .group_by(Result.student_id)
            .subquery()
        )
        higher = int(
            db.scalar(
                select(func.count())
                .select_from(per_student)
                .where(per_student.c.avg_percentage > avg_percentage)
            )
            or 0
        )
        rank = 1 + higher

    return {
        "student_id": student.id,
        "student_name": student.full_name,
        "username": student.username,
        "tests_assigned": tests_assigned,
        "attempts_taken": attempts_taken,
        "tests_completed": tests_completed,
        "average_percentage": (
            round(float(avg_percentage), 2) if avg_percentage is not None else None
        ),
        "best_percentage": (
            round(float(best_percentage), 2) if best_percentage is not None else None
        ),
        "average_score": (
            round(float(avg_score), 2) if avg_score is not None else None
        ),
        "rank": rank,
    }


# ---------------------------------------------------------------------------
# Questions
# ---------------------------------------------------------------------------


def questions_report(
    db: Session,
    *,
    subject_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Per-question usage and accuracy statistics."""
    aggregates = _group_by_question()
    stmt = (
        select(
            Question.id,
            Question.subject_id,
            Subject.name,
            Question.question_type,
            Question.difficulty,
            Question.status,
            aggregates["times_used"],
            aggregates["times_answered"],
            aggregates["correct_count"],
            aggregates["incorrect_count"],
            aggregates["unattempted_count"],
        )
        .join(Subject, Subject.id == Question.subject_id)
        .outerjoin(AttemptAnswer, AttemptAnswer.question_id == Question.id)
        .group_by(
            Question.id,
            Question.subject_id,
            Subject.name,
            Question.question_type,
            Question.difficulty,
            Question.status,
        )
    )
    if subject_id is not None:
        stmt = stmt.where(Question.subject_id == subject_id)
    stmt = stmt.order_by(Question.id.asc())
    rows: List[Dict[str, Any]] = []
    for row in db.execute(stmt).all():
        times_answered = int(row[7] or 0)
        correct = int(row[8] or 0)
        rows.append(
            {
                "question_id": row[0],
                "subject_id": row[1],
                "subject_name": row[2],
                "question_type": row[3],
                "difficulty": row[4],
                "status": row[5],
                "times_used": int(row[6] or 0),
                "times_answered": times_answered,
                "correct_count": correct,
                "incorrect_count": int(row[9] or 0),
                "unattempted_count": int(row[10] or 0),
                "accuracy": (
                    round(correct / times_answered * 100, 2) if times_answered else None
                ),
            }
        )
    return rows


# ---------------------------------------------------------------------------
# Subjects
# ---------------------------------------------------------------------------


def subjects_report(
    db: Session,
    *,
    exam_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Per-subject counts, attempt count, average percentage and accuracy."""
    question_counts = (
        select(Subject.id.label("subject_id"), func.count(Question.id).label("question_count"))
        .outerjoin(Question, Question.subject_id == Subject.id)
        .group_by(Subject.id)
        .subquery()
    )
    topic_counts = (
        select(Subject.id.label("subject_id"), func.count(Topic.id).label("topic_count"))
        .outerjoin(Topic, Topic.subject_id == Subject.id)
        .group_by(Subject.id)
        .subquery()
    )
    attempt_counts = (
        select(
            Question.subject_id.label("subject_id"),
            func.count(func.distinct(AttemptAnswer.attempt_id)).label("attempt_count"),
        )
        .select_from(AttemptAnswer)
        .join(Question, Question.id == AttemptAnswer.question_id)
        .group_by(Question.subject_id)
        .subquery()
    )
    avg_percentage = (
        select(
            Question.subject_id.label("subject_id"),
            func.avg(Attempt.percentage).label("average_percentage"),
        )
        .select_from(AttemptAnswer)
        .join(Question, Question.id == AttemptAnswer.question_id)
        .join(Attempt, Attempt.id == AttemptAnswer.attempt_id)
        .group_by(Question.subject_id)
        .subquery()
    )
    answered = _answered_expr()
    correct = _correct_expr()
    accuracy_stats = (
        select(
            Question.subject_id.label("subject_id"),
            func.coalesce(func.sum(case((answered, 1), else_=0)), 0).label("answered_count"),
            func.coalesce(
                func.sum(case((and_(answered, correct), 1), else_=0)), 0
            ).label("correct_count"),
        )
        .select_from(AttemptAnswer)
        .join(Question, Question.id == AttemptAnswer.question_id)
        .group_by(Question.subject_id)
        .subquery()
    )
    stmt = (
        select(
            Subject.id,
            Subject.name,
            Subject.exam_id,
            Exam.name,
            func.coalesce(question_counts.c.question_count, 0),
            func.coalesce(topic_counts.c.topic_count, 0),
            func.coalesce(attempt_counts.c.attempt_count, 0),
            avg_percentage.c.average_percentage,
            accuracy_stats.c.answered_count,
            accuracy_stats.c.correct_count,
        )
        .join(Exam, Exam.id == Subject.exam_id)
        .outerjoin(question_counts, question_counts.c.subject_id == Subject.id)
        .outerjoin(topic_counts, topic_counts.c.subject_id == Subject.id)
        .outerjoin(attempt_counts, attempt_counts.c.subject_id == Subject.id)
        .outerjoin(avg_percentage, avg_percentage.c.subject_id == Subject.id)
        .outerjoin(accuracy_stats, accuracy_stats.c.subject_id == Subject.id)
    )
    if exam_id is not None:
        stmt = stmt.where(Subject.exam_id == exam_id)
    stmt = stmt.order_by(Subject.id.asc())
    rows: List[Dict[str, Any]] = []
    for row in db.execute(stmt).all():
        answered_count = int(row[8] or 0)
        correct_count = int(row[9] or 0)
        rows.append(
            {
                "subject_id": row[0],
                "subject_name": row[1],
                "exam_id": row[2],
                "exam_name": row[3],
                "question_count": int(row[4] or 0),
                "topic_count": int(row[5] or 0),
                "attempt_count": int(row[6] or 0),
                "average_percentage": (
                    round(float(row[7]), 2) if row[7] is not None else None
                ),
                "accuracy": (
                    round(correct_count / answered_count * 100, 2)
                    if answered_count
                    else None
                ),
            }
        )
    return rows


__all__ = [
    "dashboard_report",
    "exams_report",
    "questions_report",
    "student_report",
    "subjects_report",
    "tests_report",
]
