"""Reusable seeder for NEET UG (Advanced Level) full-length papers.

A *paper* is described by:

* a question bank ``{subject_name: [question, ...]}`` (records built with
  ``neet_ug_advanced_set01.common.q``),
* a ``set_prefix`` used as the idempotency key for every question
  (``source = "<set_prefix>-<SUBJECT_CODE>-<NNN>"``), and
* one or more :class:`TestSpec` objects, each of which links a subset of the
  questions into a published test and assigns it to the demo students.

All writes are idempotent: re-running skips rows that already exist.  Pass
``replace=True`` to delete the tests and questions belonging to ``set_prefix``
first.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import delete, select  # noqa: E402

from app.models import (  # noqa: E402
    Exam,
    Question,
    QuestionOption,
    Subject,
    Test,
    TestAssignment,
    TestQuestion,
    Topic,
    User,
)

# (subject name, subject code, sort order)
DEFAULT_SUBJECT_ORDER: List[Tuple[str, str, int]] = [
    ("Physics", "PHY", 1),
    ("Chemistry", "CHEM", 2),
    ("Botany", "BOT", 3),
    ("Zoology", "ZOO", 4),
]

DEFAULT_ASSIGN_EMAILS = ("student@example.com", "student2@example.com")

FULL_TEST_INSTRUCTIONS = (
    "1. The paper has 180 single-correct questions carrying 4 marks each.\n"
    "2. One mark is deducted for every wrong answer; unattempted questions "
    "carry no penalty.\n"
    "3. The duration of the test is 180 minutes.\n"
    "4. Section distribution: Physics 45, Chemistry 45, Botany 45, "
    "Zoology 45."
)


@dataclass
class TestSpec:
    """Description of one test built from the shared question bank."""

    code: str
    name: str
    description: str = ""
    instructions: str = FULL_TEST_INSTRUCTIONS
    # subject -> number of questions to link (first N of that subject).
    # ``None`` links the whole bank.
    selection: Optional[Dict[str, int]] = None
    duration_minutes: int = 180
    marks_per_question: float = 4.0
    negative_marks: float = 1.0
    passing_percent: float = 40.0
    max_attempts: int = 2
    assign_days: int = 30


@dataclass
class SeedResult:
    exam: Optional[Exam] = None
    questions_created: int = 0
    questions_reused: int = 0
    tests: List[Tuple[str, int, int]] = field(default_factory=list)  # (code, id, linked)
    assignments: int = 0


def _source(subject_code: str, index: int, set_prefix: str) -> str:
    return f"{set_prefix}-{subject_code}-{index:03d}"


def get_owner_id(session) -> Optional[int]:
    for email in ("superadmin@example.com", "admin@example.com"):
        uid = session.execute(select(User.id).where(User.email == email)).scalar_one_or_none()
        if uid:
            return uid
    return session.execute(select(User.id).order_by(User.id).limit(1)).scalar_one_or_none()


def upsert_exam(
    session,
    *,
    code: str,
    name: str,
    description: str,
    duration_minutes: int,
    passing_percent: float,
    owner_id: Optional[int],
) -> Exam:
    exam = session.execute(select(Exam).where(Exam.code == code)).scalar_one_or_none()
    if exam is None:
        exam = Exam(
            name=name,
            code=code,
            description=description,
            exam_type="NEET",
            status="PUBLISHED",
            duration_minutes=duration_minutes,
            passing_percentage=passing_percent,
            is_active=True,
            created_by=owner_id,
            updated_by=owner_id,
        )
        session.add(exam)
        session.flush()
    return exam


def upsert_subjects(session, exam: Exam, subject_order) -> Dict[str, Subject]:
    subjects: Dict[str, Subject] = {}
    for name, code, order in subject_order:
        subject = session.execute(
            select(Subject).where(Subject.exam_id == exam.id, Subject.code == code)
        ).scalar_one_or_none()
        if subject is None:
            subject = Subject(
                exam_id=exam.id,
                name=name,
                code=code,
                description=f"{name} section of the advanced NEET UG paper.",
                sort_order=order,
                is_active=True,
            )
            session.add(subject)
            session.flush()
        subjects[name] = subject
    return subjects


def upsert_topics(session, subjects, subject_order, question_bank) -> Dict[Tuple[int, str], int]:
    topic_ids: Dict[Tuple[int, str], int] = {}
    for name, _code, _order in subject_order:
        subject = subjects[name]
        seen: List[str] = []
        for item in question_bank[name]:
            if item["topic"] not in seen:
                seen.append(item["topic"])
        for order, topic_name in enumerate(seen, start=1):
            topic = session.execute(
                select(Topic).where(
                    Topic.subject_id == subject.id, Topic.name == topic_name
                )
            ).scalar_one_or_none()
            if topic is None:
                topic = Topic(
                    subject_id=subject.id,
                    name=topic_name,
                    description=f"{topic_name} ({name})",
                    sort_order=order,
                    is_active=True,
                )
                session.add(topic)
                session.flush()
            topic_ids[(subject.id, topic_name)] = topic.id
    return topic_ids


def replace_paper(session, *, set_prefix: str, test_codes: Sequence[str]) -> None:
    if test_codes:
        session.execute(delete(Test).where(Test.code.in_(list(test_codes))))
    session.execute(delete(Question).where(Question.source.like(f"{set_prefix}-%")))
    session.commit()


def upsert_questions(
    session,
    *,
    subjects,
    subject_order,
    question_bank,
    topic_ids,
    set_prefix: str,
    spec: TestSpec,
    owner_id: Optional[int],
) -> Tuple[Dict[Tuple[int, int], Question], int, int]:
    """Create every question in the bank (idempotently) and index it by
    ``(subject_id, index)`` so tests can link subsets."""
    existing = {
        row.source: row
        for row in session.execute(
            select(Question).where(Question.source.like(f"{set_prefix}-%"))
        ).scalars()
    }
    indexed: Dict[Tuple[int, int], Question] = {}
    created = reused = 0
    for name, code, _order in subject_order:
        subject = subjects[name]
        for index, item in enumerate(question_bank[name], start=1):
            source = _source(code, index, set_prefix)
            question = existing.get(source)
            if question is None:
                question = Question(
                    subject_id=subject.id,
                    topic_id=topic_ids.get((subject.id, item["topic"])),
                    question_type="SINGLE_CHOICE",
                    question_text=item["text"],
                    explanation=item["explanation"],
                    difficulty=item["difficulty"],
                    marks=spec.marks_per_question,
                    negative_marks=spec.negative_marks,
                    status="PUBLISHED",
                    source=source,
                    is_active=True,
                    created_by=owner_id,
                    updated_by=owner_id,
                    options=[
                        QuestionOption(
                            option_text=option,
                            option_order=position,
                            is_correct=((position - 1) == item["correct"]),
                            is_active=True,
                        )
                        for position, option in enumerate(item["options"], start=1)
                    ],
                )
                session.add(question)
                created += 1
            else:
                reused += 1
            indexed[(subject.id, index)] = question
    if created:
        session.flush()
    return indexed, created, reused


def selected_questions(indexed, subjects, subject_order, question_bank, spec: TestSpec):
    """Return the ordered list of questions a given test should link."""
    chosen = []
    for name, _code, _order in subject_order:
        subject = subjects[name]
        count = len(question_bank[name]) if spec.selection is None else spec.selection.get(name, 0)
        for index in range(1, count + 1):
            chosen.append(indexed[(subject.id, index)])
    return chosen


def upsert_test(session, *, exam: Exam, owner_id: Optional[int], spec: TestSpec, questions) -> Test:
    total_marks = spec.marks_per_question * len(questions)
    passing_marks = round(total_marks * spec.passing_percent / 100.0, 2)
    test = session.execute(select(Test).where(Test.code == spec.code)).scalar_one_or_none()
    if test is None:
        test = Test(
            exam_id=exam.id,
            name=spec.name,
            code=spec.code,
            description=spec.description,
            instructions=spec.instructions,
            duration_minutes=spec.duration_minutes,
            total_marks=total_marks,
            passing_marks=passing_marks,
            negative_marking_enabled=True,
            negative_marks=spec.negative_marks,
            randomize_questions=False,
            randomize_options=False,
            max_attempts=spec.max_attempts,
            status="PUBLISHED",
            created_by=owner_id,
            updated_by=owner_id,
        )
        session.add(test)
        session.flush()
    else:
        test.exam_id = exam.id
        test.total_marks = total_marks
        test.passing_marks = passing_marks
        test.duration_minutes = spec.duration_minutes

    linked = set(
        session.execute(
            select(TestQuestion.question_id).where(TestQuestion.test_id == test.id)
        ).scalars()
    )
    # Re-create links in the intended order for a fresh test.
    linked_now = 0
    for order, question in enumerate(questions, start=1):
        if question.id in linked:
            continue
        session.add(
            TestQuestion(test_id=test.id, question_id=question.id, question_order=order)
        )
        linked_now += 1
    session.flush()
    return test


def upsert_assignments(session, *, test: Test, spec: TestSpec, students_email) -> int:
    now = datetime.now(timezone.utc)
    available_from = now - timedelta(days=1)
    available_until = now + timedelta(days=spec.assign_days)
    students = session.execute(
        select(User).where(User.email.in_(list(students_email)))
    ).scalars().all()
    created = 0
    for student in students:
        assignment = session.execute(
            select(TestAssignment).where(
                TestAssignment.test_id == test.id,
                TestAssignment.student_id == student.id,
            )
        ).scalar_one_or_none()
        if assignment is None:
            session.add(
                TestAssignment(
                    test_id=test.id,
                    student_id=student.id,
                    assigned_at=now,
                    available_from=available_from,
                    available_until=available_until,
                    max_attempts=spec.max_attempts,
                    status="ASSIGNED",
                )
            )
            created += 1
    session.flush()
    return created


def seed_paper(
    session,
    *,
    question_bank,
    set_prefix: str,
    tests: Sequence[TestSpec],
    exam_code: str,
    exam_name: str,
    exam_description: str,
    subject_order=DEFAULT_SUBJECT_ORDER,
    assign_emails=DEFAULT_ASSIGN_EMAILS,
    replace: bool = False,
    dry_run: bool = False,
) -> SeedResult:
    subject_order = list(subject_order)
    result = SeedResult()

    if dry_run:
        for name, _code, _order in subject_order:
            print(f"    {name:10} {len(question_bank[name]):3} questions")
        return result

    if replace:
        replace_paper(session, set_prefix=set_prefix, test_codes=[t.code for t in tests])

    # Every test in this paper shares the same 4/ -1 per-question marks, so the
    # first spec's marking scheme defines the question rows.
    marking = tests[0]
    owner_id = get_owner_id(session)
    exam = upsert_exam(
        session,
        code=exam_code,
        name=exam_name,
        description=exam_description,
        duration_minutes=marking.duration_minutes,
        passing_percent=marking.passing_percent,
        owner_id=owner_id,
    )
    subjects = upsert_subjects(session, exam, subject_order)
    topic_ids = upsert_topics(session, subjects, subject_order, question_bank)

    indexed, created, reused = upsert_questions(
        session,
        subjects=subjects,
        subject_order=subject_order,
        question_bank=question_bank,
        topic_ids=topic_ids,
        set_prefix=set_prefix,
        spec=marking,
        owner_id=owner_id,
    )
    result.exam = exam
    result.questions_created = created
    result.questions_reused = reused

    for spec in tests:
        questions = selected_questions(indexed, subjects, subject_order, question_bank, spec)
        test = upsert_test(session, exam=exam, owner_id=owner_id, spec=spec, questions=questions)
        assigned = upsert_assignments(session, test=test, spec=spec, students_email=assign_emails)
        result.assignments += assigned
        result.tests.append((test.code, test.id, len(questions)))

    session.commit()
    return result
