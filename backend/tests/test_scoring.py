"""Unit tests for the pure scoring engine (no database required).

The engine works on plain attribute access, so the fixtures below use
``SimpleNamespace`` stand-ins for questions, options, test-questions and tests.
Helper builders are intentionally *not* named ``test_*`` so pytest does not try
to collect them as test cases.
"""

from types import SimpleNamespace

from app.services import scoring_service as scoring


# ---------------------------------------------------------------------------
# Lightweight builders
# ---------------------------------------------------------------------------


def make_option(option_id: int, text: str, correct: bool = False) -> SimpleNamespace:
    return SimpleNamespace(id=option_id, option_text=text, is_correct=correct)


def make_question(
    question_id: int, qtype: str, options, marks: float = 4.0
) -> SimpleNamespace:
    return SimpleNamespace(
        id=question_id, question_type=qtype, options=options, marks=marks
    )


def make_tq(question_obj, marks_override=None, negative_override=None) -> SimpleNamespace:
    return SimpleNamespace(
        question=question_obj,
        question_id=question_obj.id,
        marks_override=marks_override,
        negative_marks_override=negative_override,
    )


def make_test(
    negative_marks: float = 1.0,
    negative_marking_enabled: bool = True,
    passing_marks=None,
) -> SimpleNamespace:
    return SimpleNamespace(
        negative_marks=negative_marks,
        negative_marking_enabled=negative_marking_enabled,
        passing_marks=passing_marks,
    )


def make_answer(**kwargs) -> SimpleNamespace:
    base = dict(
        selected_option_id=None,
        selected_option_ids=None,
        answer_text=None,
        numerical_answer=None,
    )
    base.update(kwargs)
    return SimpleNamespace(**base)


# ---------------------------------------------------------------------------
# Single choice / true-false
# ---------------------------------------------------------------------------


def test_single_choice_correct_incorrect_unanswered():
    q = make_question(
        1, "SINGLE_CHOICE", [make_option(10, "A", True), make_option(11, "B")]
    )
    assert scoring.evaluate_answer(q, make_answer(selected_option_id=10)) == scoring.CORRECT
    assert scoring.evaluate_answer(q, make_answer(selected_option_id=11)) == scoring.INCORRECT
    assert scoring.evaluate_answer(q, None) == scoring.UNANSWERED
    assert scoring.evaluate_answer(q, make_answer()) == scoring.UNANSWERED


def test_true_false_uses_same_logic():
    q = make_question(
        2, "TRUE_FALSE", [make_option(20, "True", True), make_option(21, "False")]
    )
    assert scoring.evaluate_answer(q, make_answer(selected_option_id=20)) == scoring.CORRECT
    assert scoring.evaluate_answer(q, make_answer(selected_option_id=21)) == scoring.INCORRECT


# ---------------------------------------------------------------------------
# Multiple choice
# ---------------------------------------------------------------------------


def test_multiple_choice_requires_exact_set():
    q = make_question(
        3,
        "MULTIPLE_CHOICE",
        [make_option(30, "A", True), make_option(31, "B", True), make_option(32, "C")],
    )
    assert scoring.evaluate_answer(q, make_answer(selected_option_ids=[30, 31])) == scoring.CORRECT
    assert scoring.evaluate_answer(q, make_answer(selected_option_ids=[30])) == scoring.INCORRECT
    assert (
        scoring.evaluate_answer(q, make_answer(selected_option_ids=[30, 31, 32]))
        == scoring.INCORRECT
    )
    assert scoring.evaluate_answer(q, make_answer(selected_option_ids=[])) == scoring.UNANSWERED


# ---------------------------------------------------------------------------
# Numerical / subjective
# ---------------------------------------------------------------------------


def test_numerical_tolerance():
    q = make_question(4, "NUMERICAL", [make_option(40, "3.14159", True)])
    assert scoring.evaluate_answer(q, make_answer(numerical_answer="3.14159")) == scoring.CORRECT
    assert scoring.evaluate_answer(q, make_answer(numerical_answer="3.0")) == scoring.INCORRECT
    assert (
        scoring.evaluate_answer(q, make_answer(numerical_answer="not-a-number"))
        == scoring.INCORRECT
    )
    assert scoring.evaluate_answer(q, make_answer(numerical_answer="  ")) == scoring.UNANSWERED


def test_subjective_is_ungraded_and_blank_is_unanswered():
    q = make_question(5, "SUBJECTIVE", [])
    assert scoring.evaluate_answer(q, make_answer(answer_text="my essay")) == scoring.UNGRADED
    assert scoring.evaluate_answer(q, make_answer(answer_text="   ")) == scoring.UNANSWERED


# ---------------------------------------------------------------------------
# effective_marks / negative marking
# ---------------------------------------------------------------------------


def test_effective_marks_override_and_negative_toggle():
    q = make_question(6, "SINGLE_CHOICE", [make_option(60, "A", True)], marks=4.0)
    tq = make_tq(q, marks_override=5.0, negative_override=2.0)

    assert scoring.effective_marks(make_test(negative_marks=1.0), tq) == (5.0, 2.0)
    # Without overrides the question/test defaults apply.
    assert scoring.effective_marks(make_test(negative_marks=1.5), make_tq(q)) == (4.0, 1.5)
    # Disabling negative marking forces the penalty to zero.
    marks, negative = scoring.effective_marks(
        make_test(negative_marks=1.5, negative_marking_enabled=False), tq
    )
    assert (marks, negative) == (5.0, 0.0)


def test_awarded_marks():
    assert scoring.awarded_marks(scoring.CORRECT, 4.0, 1.0) == 4.0
    assert scoring.awarded_marks(scoring.INCORRECT, 4.0, 1.0) == -1.0
    assert scoring.awarded_marks(scoring.UNANSWERED, 4.0, 1.0) == 0.0
    assert scoring.awarded_marks(scoring.UNGRADED, 4.0, 1.0) == 0.0


# ---------------------------------------------------------------------------
# score_attempt aggregation
# ---------------------------------------------------------------------------


def test_score_attempt_aggregates_and_clamps_percentage():
    q1 = make_question(101, "SINGLE_CHOICE", [make_option(1001, "A", True), make_option(1002, "B")], marks=4.0)
    q2 = make_question(102, "SINGLE_CHOICE", [make_option(1003, "C", True), make_option(1004, "D")], marks=4.0)
    q3 = make_question(103, "SINGLE_CHOICE", [make_option(1005, "E", True), make_option(1006, "F")], marks=4.0)
    tqs = [make_tq(q1), make_tq(q2), make_tq(q3)]

    answers = {
        101: make_answer(selected_option_id=1001),  # correct -> +4
        102: make_answer(selected_option_id=1004),  # incorrect -> -1
        # 103 unanswered -> 0
    }
    result = scoring.score_attempt(make_test(negative_marks=1.0), tqs, answers)

    assert result.score == 3.0
    assert result.max_score == 12.0
    assert result.percentage == 25.0
    assert result.correct_count == 1
    assert result.incorrect_count == 1
    assert result.unanswered_count == 1
    assert result.breakdown[101]["status"] == scoring.CORRECT


def test_score_attempt_negative_total_clamps_percentage_at_zero():
    q1 = make_question(201, "SINGLE_CHOICE", [make_option(2001, "A", True), make_option(2002, "B")], marks=4.0)
    q2 = make_question(202, "SINGLE_CHOICE", [make_option(2003, "C", True), make_option(2004, "D")], marks=4.0)
    answers = {
        201: make_answer(selected_option_id=2002),  # wrong
        202: make_answer(selected_option_id=2004),  # wrong
    }
    result = scoring.score_attempt(make_test(negative_marks=3.0), [make_tq(q1), make_tq(q2)], answers)
    assert result.score == -6.0
    assert result.percentage == 0.0
    assert result.incorrect_count == 2


def test_is_pass_thresholds():
    assert scoring.is_pass(make_test(passing_marks=4.0), 4.0, 40.0) is True
    assert scoring.is_pass(make_test(passing_marks=4.0), 3.9, 99.0) is False
    # No passing marks -> 50% fallback.
    assert scoring.is_pass(make_test(passing_marks=None), 0.0, 50.0) is True
    assert scoring.is_pass(make_test(passing_marks=None), 0.0, 49.9) is False
