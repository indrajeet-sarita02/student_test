"""Pure scoring engine for test attempts.

This module is intentionally free of HTTP, ORM sessions and side effects so it
can be unit-tested in isolation with lightweight objects (see the design spec
sections 17 and 18). It implements the scoring rules that are *reproducible
from the test/question configuration applicable at the time*:

* ``marks_override`` on a ``test_questions`` row wins over ``Question.marks``.
* ``negative_marks_override`` wins over ``Test.negative_marks``; when the test
  has ``negative_marking_enabled = False`` the penalty is forced to ``0``.
* Single-choice / true-false questions compare the selected option against the
  correct option.
* Multiple-choice questions compare the *set* of selected option ids against
  the full correct set (exact match only).
* Numerical questions compare ``numerical_answer`` to the correct option's text
  as a float with a ``1e-6`` tolerance.
* Subjective questions cannot be auto-graded and are reported as ``UNGRADED``.

The public helpers work on plain attribute access, so they happily accept
SQLAlchemy models or in-memory namespaces without importing either.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple

#: Answer evaluation statuses.
CORRECT = "CORRECT"
INCORRECT = "INCORRECT"
UNANSWERED = "UNANSWERED"
UNGRADED = "UNGRADED"

#: Float comparison tolerance for numerical questions.
NUMERICAL_TOLERANCE = 1e-6

_OBJECTIVE_TYPES = {
    "SINGLE_CHOICE",
    "TRUE_FALSE",
    "MULTIPLE_CHOICE",
    "NUMERICAL",
}


@dataclass
class ScoreResult:
    """Outcome of scoring one attempt.

    ``breakdown`` maps ``question_id`` to ``{"status": ..., "marks_awarded":
    ...}`` so the API layer can render per-question feedback without recomputing
    the evaluation.
    """

    score: float = 0.0
    max_score: float = 0.0
    percentage: float = 0.0
    correct_count: int = 0
    incorrect_count: int = 0
    unanswered_count: int = 0
    ungraded_count: int = 0
    breakdown: Dict[int, Dict[str, Any]] = field(default_factory=dict)


def _value(value: Any) -> Any:
    """Return the plain value of a possible ``StrEnum`` / enum member."""
    return getattr(value, "value", value)


def _normalise_type(question: Any) -> str:
    """Normalise ``Question.question_type`` to an uppercase string."""
    return str(_value(getattr(question, "question_type", ""))).upper()


def _has_text(value: Any) -> bool:
    """True when ``value`` carries a non-blank textual answer."""
    return value is not None and str(value).strip() != ""


def effective_marks(test: Any, test_question: Any) -> Tuple[float, float]:
    """Return ``(marks, negative)`` for one ``test_questions`` row.

    ``marks_override`` wins over ``Question.marks`` and
    ``negative_marks_override`` wins over ``Test.negative_marks``. Negative
    marking is disabled entirely when the test flag is off.
    """
    question = getattr(test_question, "question", None)
    override_marks = getattr(test_question, "marks_override", None)
    base_marks = getattr(question, "marks", 0.0) if question is not None else 0.0
    marks = override_marks if override_marks is not None else base_marks

    negative = 0.0
    if getattr(test, "negative_marking_enabled", True):
        override_negative = getattr(test_question, "negative_marks_override", None)
        base_negative = getattr(test, "negative_marks", 0.0)
        negative = (
            override_negative if override_negative is not None else base_negative
        )

    try:
        marks_value = float(marks or 0.0)
    except (TypeError, ValueError):  # pragma: no cover - defensive
        marks_value = 0.0
    try:
        negative_value = float(negative or 0.0)
    except (TypeError, ValueError):  # pragma: no cover - defensive
        negative_value = 0.0
    return marks_value, negative_value


def _correct_options(question: Any) -> Iterable[Any]:
    """Iterate the question's options flagged ``is_correct``."""
    for option in getattr(question, "options", []) or []:
        if bool(getattr(option, "is_correct", False)):
            yield option


def _correct_option_text(question: Any) -> Optional[str]:
    """Text of the first correct option (used by numerical questions)."""
    for option in _correct_options(question):
        return getattr(option, "option_text", None)
    return None


def evaluate_answer(question: Any, answer: Any) -> str:
    """Classify one answer as ``CORRECT``/``INCORRECT``/``UNANSWERED``/``UNGRADED``.

    A missing answer, or one with no selected option(s) / no textual content,
    is ``UNANSWERED``. Subjective questions that do carry an answer are
    ``UNGRADED`` because they require manual review.
    """
    qtype = _normalise_type(question)
    if answer is None:
        return UNANSWERED

    if qtype == "SUBJECTIVE":
        return UNGRADED if _has_text(getattr(answer, "answer_text", None)) else UNANSWERED

    if qtype == "NUMERICAL":
        raw = getattr(answer, "numerical_answer", None)
        if not _has_text(raw):
            return UNANSWERED
        correct_text = _correct_option_text(question)
        if not _has_text(correct_text):
            return INCORRECT
        try:
            return (
                CORRECT
                if abs(float(raw) - float(correct_text)) <= NUMERICAL_TOLERANCE
                else INCORRECT
            )
        except (TypeError, ValueError):
            return INCORRECT

    if qtype == "MULTIPLE_CHOICE":
        selected = getattr(answer, "selected_option_ids", None)
        selected_set = {int(value) for value in selected} if selected else set()
        if not selected_set:
            single = getattr(answer, "selected_option_id", None)
            if single is not None:
                selected_set = {int(single)}
        if not selected_set:
            return UNANSWERED
        correct_set = {int(option.id) for option in _correct_options(question)}
        return CORRECT if selected_set == correct_set else INCORRECT

    # SINGLE_CHOICE and TRUE_FALSE share the same comparison logic (and any
    # unknown objective type falls back here so it is never silently ungraded).
    selected = getattr(answer, "selected_option_id", None)
    if selected is None:
        return UNANSWERED
    correct_ids = {int(option.id) for option in _correct_options(question)}
    return CORRECT if int(selected) in correct_ids else INCORRECT


def awarded_marks(status: str, marks: float, negative: float) -> float:
    """Marks contributed by one evaluated question (may be negative)."""
    if status == CORRECT:
        return float(marks or 0.0)
    if status == INCORRECT:
        return -float(negative or 0.0)
    return 0.0


def _answer_map(answers: Any) -> Dict[int, Any]:
    """Coerce the ``answers`` argument into a ``{question_id: answer}`` mapping.

    Accepts either a mapping already keyed by question id or any iterable of
    answer objects exposing ``question_id``.
    """
    if answers is None:
        return {}
    if isinstance(answers, Mapping):
        return {int(key): value for key, value in answers.items()}
    result: Dict[int, Any] = {}
    for answer in answers:
        question_id = getattr(answer, "question_id", None)
        if question_id is not None:
            result[int(question_id)] = answer
    return result


def score_attempt(
    test: Any,
    test_questions: Iterable[Any],
    answers: Any,
) -> ScoreResult:
    """Score an attempt over every ``test_questions`` row.

    ``max_score`` is the sum of the effective marks of the *graded* questions
    (every question except those the automatic engine cannot grade, i.e.
    ``UNGRADED`` subjective answers). The raw ``score`` may be negative; the
    percentage clamps the numerator at zero so it never goes below ``0``.
    """
    answer_map = _answer_map(answers)
    result = ScoreResult()
    raw_score = 0.0
    max_score = 0.0

    for test_question in test_questions or []:
        question = getattr(test_question, "question", None)
        question_id = getattr(question, "id", None)
        if question_id is None:
            question_id = getattr(test_question, "question_id", None)
        marks, negative = effective_marks(test, test_question)
        status = evaluate_answer(question, answer_map.get(int(question_id)) if question_id is not None else None)
        earned = awarded_marks(status, marks, negative)

        raw_score += earned
        if status == CORRECT:
            result.correct_count += 1
        elif status == INCORRECT:
            result.incorrect_count += 1
        elif status == UNANSWERED:
            result.unanswered_count += 1
        else:
            result.ungraded_count += 1

        if status != UNGRADED:
            max_score += marks

        if question_id is not None:
            result.breakdown[int(question_id)] = {
                "status": status,
                "marks_awarded": earned,
            }

    result.score = round(raw_score, 2)
    result.max_score = round(max_score, 2)
    if result.max_score > 0:
        result.percentage = round(max(0.0, result.score) / result.max_score * 100, 2)
    else:
        result.percentage = 0.0
    return result


def is_pass(test: Any, score: float, percentage: float) -> bool:
    """Decide pass/fail for one result.

    When the test defines ``passing_marks`` the raw score must meet or exceed
    it. When it does not, the documented fallback is a ``50.0`` percentage
    threshold.
    """
    passing_marks = getattr(test, "passing_marks", None)
    if passing_marks is not None:
        return float(score) >= float(passing_marks)
    return float(percentage) >= 50.0
