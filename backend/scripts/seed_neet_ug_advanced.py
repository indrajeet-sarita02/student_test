"""Seed the NEET UG (Advanced Level) full-length paper into the database.

Creates (idempotently):

* the ``NEET-ADV`` exam,
* four subjects - Physics, Chemistry, Botany, Zoology,
* all topics referenced by the questions,
* 180 published questions (45 per subject) with four options and an
  explanation each, stored in the shared question bank, and
* one published test ``NEET-UG-ADV-SET-A`` (720 marks, 180 minutes, -1 for a
  wrong answer) with all 180 questions attached and assigned to the demo
  students.

Usage (from the ``backend/`` directory):

    .venv/bin/python scripts/seed_neet_ug_advanced.py
    .venv/bin/python scripts/seed_neet_ug_advanced.py --replace
    .venv/bin/python scripts/seed_neet_ug_advanced.py --dry-run

Every question is keyed by its ``source`` tag (``NEET-UG-ADV-SET-A-...``), so
re-running the script is safe and skips rows that already exist.  ``--replace``
deletes this paper (test + its questions) first, then rebuilds it.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import delete, select  # noqa: E402

from app.db.session import SessionLocal  # noqa: E402
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
from scripts.neet_ug_advanced import SUBJECTS as QUESTION_BANK  # noqa: E402

# ---------------------------------------------------------------------------
# Paper definition
# ---------------------------------------------------------------------------
EXAM_CODE = "NEET-ADV"
EXAM_NAME = "NEET UG (Advanced Level) - Full Length Mock"
EXAM_TYPE = "NEET"
EXAM_DESCRIPTION = (
    "Advanced-level NEET UG practice examination covering Physics, Chemistry, "
    "Botany and Zoology."
)

TEST_CODE = "NEET-UG-ADV-SET-A"
TEST_NAME = "NEET UG Advanced - Full Syllabus Mock (Set A)"
TEST_DESCRIPTION = (
    "Full-length advanced NEET UG mock paper: 180 single-correct questions "
    "(Physics 45, Chemistry 45, Botany 45, Zoology 45), 720 marks."
)
TEST_INSTRUCTIONS = (
    "1. The paper has 180 single-correct questions carrying 4 marks each.\n"
    "2. One mark is deducted for every wrong answer; unattempted questions "
    "carry no penalty.\n"
    "3. The duration of the test is 180 minutes.\n"
    "4. Section distribution: Physics 45, Chemistry 45, Botany 45, "
    "Zoology 45."
)

DURATION_MINUTES = 180
MARKS_PER_QUESTION = 4.0
NEGATIVE_MARKS = 1.0
PASSING_PERCENT = 40.0
MAX_ATTEMPTS = 2
ASSIGN_DURATION_DAYS = 30

SET_PREFIX = "NEET-UG-ADV-SET-A"

# subject name -> (subject code, sort order)
SUBJECT_ORDER: List[Tuple[str, str, int]] = [
    ("Physics", "PHY", 1),
    ("Chemistry", "CHEM", 2),
    ("Botany", "BOT", 3),
    ("Zoology", "ZOO", 4),
]
SUBJECT_CODE = {name: code for name, code, _ in SUBJECT_ORDER}

ASSIGN_STUDENT_EMAILS = ("student@example.com", "student2@example.com")


def _source_code(subject_code: str, index: int) -> str:
    return f"{SET_PREFIX}-{subject_code}-{index:03d}"


def get_owner_id(session) -> Optional[int]:
    """Prefer the superadmin, then an admin, then any user."""
    for email in ("superadmin@example.com", "admin@example.com"):
        uid = session.execute(
            select(User.id).where(User.email == email)
        ).scalar_one_or_none()
        if uid:
            return uid
    return session.execute(select(User.id).order_by(User.id).limit(1)).scalar_one_or_none()


def replace_existing(session) -> None:
    """Delete this paper's test and its questions (cascades handled by DB)."""
    session.execute(delete(Test).where(Test.code == TEST_CODE))
    session.execute(
        delete(Question).where(Question.source.like(f"{SET_PREFIX}-%"))
    )
    session.commit()


def upsert_exam(session, owner_id: Optional[int]) -> Exam:
    exam = session.execute(
        select(Exam).where(Exam.code == EXAM_CODE)
    ).scalar_one_or_none()
    if exam is None:
        exam = Exam(
            name=EXAM_NAME,
            code=EXAM_CODE,
            description=EXAM_DESCRIPTION,
            exam_type=EXAM_TYPE,
            status="PUBLISHED",
            duration_minutes=DURATION_MINUTES,
            passing_percentage=PASSING_PERCENT,
            is_active=True,
            created_by=owner_id,
            updated_by=owner_id,
        )
        session.add(exam)
        session.flush()
    return exam


def upsert_subjects(session, exam: Exam) -> Dict[str, Subject]:
    subjects: Dict[str, Subject] = {}
    for name, code, order in SUBJECT_ORDER:
        subject = session.execute(
            select(Subject).where(
                Subject.exam_id == exam.id, Subject.code == code
            )
        ).scalar_one_or_none()
        if subject is None:
            subject = Subject(
                exam_id=exam.id,
                name=name,
                code=code,
                description=f"{name} section of the advanced NEET UG mock.",
                sort_order=order,
                is_active=True,
            )
            session.add(subject)
            session.flush()
        subjects[name] = subject
    return subjects


def upsert_topics(session, subjects: Dict[str, Subject]) -> Dict[Tuple[int, str], int]:
    """Ensure a topic row exists for every (subject, topic-name) pair."""
    topic_ids: Dict[Tuple[int, str], int] = {}
    for name, _code, _order in SUBJECT_ORDER:
        subject = subjects[name]
        seen: List[str] = []
        for item in QUESTION_BANK[name]:
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


def build_existing_map(session) -> Dict[str, Question]:
    rows = session.execute(
        select(Question).where(Question.source.like(f"{SET_PREFIX}-%"))
    ).scalars()
    return {row.source: row for row in rows}


def create_questions(
    session,
    owner_id: Optional[int],
    subjects: Dict[str, Subject],
    topic_ids: Dict[Tuple[int, str], int],
    existing: Dict[str, Question],
) -> Tuple[List[Question], int, int]:
    """Insert questions that are not present yet; return (ordered, created, skipped)."""
    ordered: List[Question] = []
    created = 0
    skipped = 0
    for name, _code, _order in SUBJECT_ORDER:
        subject = subjects[name]
        code = SUBJECT_CODE[name]
        for index, item in enumerate(QUESTION_BANK[name], start=1):
            source = _source_code(code, index)
            question = existing.get(source)
            if question is None:
                question = Question(
                    subject_id=subject.id,
                    topic_id=topic_ids[(subject.id, item["topic"])],
                    question_type="SINGLE_CHOICE",
                    question_text=item["text"],
                    explanation=item["explanation"],
                    difficulty=item["difficulty"],
                    marks=MARKS_PER_QUESTION,
                    negative_marks=NEGATIVE_MARKS,
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
                skipped += 1
            ordered.append(question)
    if created:
        session.flush()
    return ordered, created, skipped


def upsert_test(
    session, exam: Exam, owner_id: Optional[int], questions: List[Question]
) -> Test:
    test = session.execute(
        select(Test).where(Test.code == TEST_CODE)
    ).scalar_one_or_none()
    total_marks = MARKS_PER_QUESTION * len(questions)
    passing_marks = round(total_marks * PASSING_PERCENT / 100.0, 2)
    if test is None:
        test = Test(
            exam_id=exam.id,
            name=TEST_NAME,
            code=TEST_CODE,
            description=TEST_DESCRIPTION,
            instructions=TEST_INSTRUCTIONS,
            duration_minutes=DURATION_MINUTES,
            total_marks=total_marks,
            passing_marks=passing_marks,
            negative_marking_enabled=True,
            negative_marks=NEGATIVE_MARKS,
            randomize_questions=False,
            randomize_options=False,
            max_attempts=MAX_ATTEMPTS,
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

    linked = set(
        session.execute(
            select(TestQuestion.question_id).where(TestQuestion.test_id == test.id)
        ).scalars()
    )
    added = 0
    for order, question in enumerate(questions, start=1):
        if question.id in linked:
            continue
        session.add(
            TestQuestion(
                test_id=test.id,
                question_id=question.id,
                question_order=order,
            )
        )
        added += 1
    session.flush()
    print(f"  test_questions linked: {added} (already linked: {len(linked)})")
    return test


def upsert_assignments(session, test: Test) -> int:
    now = datetime.now(timezone.utc)
    available_from = now - timedelta(days=1)
    available_until = now + timedelta(days=ASSIGN_DURATION_DAYS)
    students = session.execute(
        select(User).where(User.email.in_(ASSIGN_STUDENT_EMAILS))
    ).scalars().all()
    if not students:
        print("  !! no demo students found - skipping assignments")
        return 0
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
                    max_attempts=MAX_ATTEMPTS,
                    status="ASSIGNED",
                )
            )
            created += 1
    session.flush()
    return created


def run(session, dry_run: bool, replace: bool) -> None:
    print("=" * 68)
    print("NEET UG (Advanced Level) - full-length paper seed")
    print("=" * 68)

    if dry_run:
        for name, _code, _order in SUBJECT_ORDER:
            print(f"  {name:<10} {len(QUESTION_BANK[name]):>3} questions")
        total = sum(len(QUESTION_BANK[n]) for n, _c, _o in SUBJECT_ORDER)
        print(f"  {'TOTAL':<10} {total:>3} questions, {total * MARKS_PER_QUESTION:.0f} marks")
        print("  dry run - nothing written")
        return

    if replace:
        print(f"--replace: removing existing '{TEST_CODE}' paper ...")
        replace_existing(session)

    owner_id = get_owner_id(session)
    if owner_id is None:
        print("  !! no users found; created_by will be NULL")

    exam = upsert_exam(session, owner_id)
    subjects = upsert_subjects(session, exam)
    topic_ids = upsert_topics(session, subjects)
    existing = build_existing_map(session)
    questions, created, skipped = create_questions(
        session, owner_id, subjects, topic_ids, existing
    )
    print(f"  exam: {exam.code} (id={exam.id})")
    print(f"  questions created: {created}, already present: {skipped}")
    test = upsert_test(session, exam, owner_id, questions)
    assignments = upsert_assignments(session, test)
    session.commit()
    print(f"  test: {test.code} (id={test.id}) - {len(questions)} questions, "
          f"{test.total_marks} marks, {test.duration_minutes} min")
    print(f"  new assignments: {assignments}")
    print("=" * 68)
    print("Done.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed the NEET UG (Advanced Level) full-length paper."
    )
    parser.add_argument("--replace", action="store_true",
                        help="delete and rebuild this paper first")
    parser.add_argument("--dry-run", action="store_true",
                        help="report the planned inserts without writing")
    args = parser.parse_args()

    session = SessionLocal()
    try:
        run(session, dry_run=args.dry_run, replace=args.replace)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
