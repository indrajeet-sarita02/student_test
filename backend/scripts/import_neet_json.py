"""Import NEET question JSON files into the Student Test database.

The JSON files in ``samples/`` use this shape (a single set object, or a list of
set objects such as ``NEET_UG_Advanced_All_20_Sets.json``)::

    {
      "exam": "NEET UG",
      "set_number": 1,
      "difficulty": "Advanced",
      "total_questions": 180,
      "questions": [
        {
          "subject": "Physics",
          "q_id": "PHY_001",
          "question": "...",
          "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
          "correct_answer": "B",
          "explanation": "..."
        }, ...
      ]
    }

The importer maps each subject to the matching subject of the target exam,
creates one published test per set (180 questions, 720 marks, 180 minutes,
-1 for a wrong answer) and assigns it to the demo students.

Usage (from the ``backend/`` directory)::

    .venv/bin/python scripts/import_neet_json.py ../samples/NEET_UG_Advanced_Set_1.json --dry-run
    .venv/bin/python scripts/import_neet_json.py ../samples/NEET_UG_Advanced_Set_1.json
    .venv/bin/python scripts/import_neet_json.py ../samples/NEET_UG_Advanced_All_20_Sets.json --sets 1,2
    .venv/bin/python scripts/import_neet_json.py ../samples/NEET_UG_Advanced_Set_1.json --replace

Idempotency: every question is keyed by a ``source`` tag derived from the file
name, set number and ``q_id``.  Tests are keyed by their generated ``code``.
Re-running skips rows that already exist; ``--replace`` deletes the tests and
questions created from the same file first.  ``--validate-only`` checks the
file without touching the database.
"""

from __future__ import annotations

import argparse
import json
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

# subject name -> (subject code, sort order)
SUBJECT_MAP: Dict[str, Tuple[str, int]] = {
    "Physics": ("PHY", 1),
    "Chemistry": ("CHEM", 2),
    "Botany": ("BOT", 3),
    "Zoology": ("ZOO", 4),
}
OPTION_ORDER = {"A": 1, "B": 2, "C": 3, "D": 4}

DIFFICULTY_MAP = {
    "easy": "EASY",
    "medium": "MEDIUM",
    "hard": "HARD",
    "advanced": "HARD",
}

MARKS_PER_QUESTION = 4.0
NEGATIVE_MARKS = 1.0
DURATION_MINUTES = 180
PASSING_PERCENT = 40.0
MAX_ATTEMPTS = 2
ASSIGN_DURATION_DAYS = 30
ASSIGN_STUDENT_EMAILS = ("student@example.com", "student2@example.com")

DEFAULT_EXAM_CODE = "NEET-ADV"


# ---------------------------------------------------------------------------
# JSON loading / validation
# ---------------------------------------------------------------------------
class ValidationError(Exception):
    pass


def load_sets(path: Path) -> List[dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid JSON: {exc}") from exc
    if isinstance(data, dict):
        sets = [data]
    elif isinstance(data, list):
        sets = data
    else:
        raise ValidationError("top level must be an object or a list of objects")
    for i, s in enumerate(sets, start=1):
        if not isinstance(s, dict) or "questions" not in s:
            raise ValidationError(f"entry #{i} is not a set object with 'questions'")
    return sets


def validate_set(s: dict, label: str) -> List[str]:
    problems: List[str] = []
    questions = s.get("questions")
    if not isinstance(questions, list) or not questions:
        problems.append(f"{label}: no questions")
        return problems
    declared = s.get("total_questions")
    if isinstance(declared, int) and declared != len(questions):
        problems.append(f"{label}: total_questions={declared} but {len(questions)} found")
    for i, q in enumerate(questions, start=1):
        tag = f"{label} q{i}"
        if not isinstance(q, dict):
            problems.append(f"{tag}: not an object")
            continue
        subject = q.get("subject")
        if subject not in SUBJECT_MAP:
            problems.append(f"{tag}: unknown subject {subject!r}")
        if not str(q.get("question", "")).strip():
            problems.append(f"{tag}: empty question text")
        if not str(q.get("q_id", "")).strip():
            problems.append(f"{tag}: missing q_id")
        opts = q.get("options")
        if not isinstance(opts, dict) or set(opts.keys()) != {"A", "B", "C", "D"}:
            problems.append(f"{tag}: options must have exactly A, B, C, D")
        elif any(not str(v).strip() for v in opts.values()):
            problems.append(f"{tag}: empty option text")
        if q.get("correct_answer") not in OPTION_ORDER:
            problems.append(f"{tag}: bad correct_answer {q.get('correct_answer')!r}")
    return problems


def question_difficulty(set_difficulty: Optional[str]) -> str:
    return DIFFICULTY_MAP.get(str(set_difficulty or "medium").lower(), "MEDIUM")


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------
def get_owner_id(session) -> Optional[int]:
    for email in ("superadmin@example.com", "admin@example.com"):
        uid = session.execute(
            select(User.id).where(User.email == email)
        ).scalar_one_or_none()
        if uid:
            return uid
    return session.execute(select(User.id).order_by(User.id).limit(1)).scalar_one_or_none()


def upsert_exam(session, code: str, name: str, owner_id: Optional[int]) -> Exam:
    exam = session.execute(select(Exam).where(Exam.code == code)).scalar_one_or_none()
    if exam is None:
        exam = Exam(
            name=name,
            code=code,
            description="Imported NEET UG question sets (JSON).",
            exam_type="NEET",
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


def upsert_subjects(session, exam: Exam, needed: set) -> Dict[str, Subject]:
    subjects: Dict[str, Subject] = {}
    for name in SUBJECT_MAP:
        if name not in needed:
            continue
        code, order = SUBJECT_MAP[name]
        subject = session.execute(
            select(Subject).where(Subject.exam_id == exam.id, Subject.code == code)
        ).scalar_one_or_none()
        if subject is None:
            subject = Subject(
                exam_id=exam.id,
                name=name,
                code=code,
                sort_order=order,
                is_active=True,
            )
            session.add(subject)
            session.flush()
        subjects[name] = subject
    return subjects


def replace_existing(session, source_prefixes: List[str], test_codes: List[str]) -> None:
    """Delete only the tests/questions produced for the *selected* sets."""
    if test_codes:
        session.execute(delete(Test).where(Test.code.in_(test_codes)))
    for prefix in source_prefixes:
        session.execute(delete(Question).where(Question.source.like(f"{prefix}-%")))
    session.commit()


def upsert_set(
    session,
    exam: Exam,
    subjects: Dict[str, Subject],
    source_tag: str,
    test_code: str,
    test_name: str,
    set_data: dict,
    owner_id: Optional[int],
) -> Tuple[Test, int, int]:
    questions_json = set_data["questions"]
    difficulty = question_difficulty(set_data.get("difficulty"))
    set_number = set_data.get("set_number")

    def source_for(q: dict) -> str:
        qid = str(q["q_id"]).strip()
        if isinstance(set_number, int):
            return f"{source_tag}-S{int(set_number):02d}-{qid}"
        return f"{source_tag}-{qid}"

    wanted_sources = [source_for(q) for q in questions_json]
    existing = {
        row.source: row
        for row in session.execute(
            select(Question).where(Question.source.in_(wanted_sources))
        ).scalars()
    }

    ordered: List[Question] = []
    created = skipped = 0
    for q, source in zip(questions_json, wanted_sources):
        question = existing.get(source)
        if question is None:
            correct = str(q["correct_answer"]).strip().upper()
            question = Question(
                subject_id=subjects[q["subject"]].id,
                topic_id=None,
                question_type="SINGLE_CHOICE",
                question_text=str(q["question"]).strip(),
                explanation=str(q.get("explanation", "")).strip() or None,
                difficulty=difficulty,
                marks=MARKS_PER_QUESTION,
                negative_marks=NEGATIVE_MARKS,
                status="PUBLISHED",
                source=source,
                is_active=True,
                created_by=owner_id,
                updated_by=owner_id,
                options=[
                    QuestionOption(
                        option_text=str(q["options"][letter]).strip(),
                        option_order=order,
                        is_correct=(letter == correct),
                        is_active=True,
                    )
                    for letter, order in OPTION_ORDER.items()
                ],
            )
            session.add(question)
            existing[source] = question
            created += 1
        else:
            skipped += 1
        ordered.append(question)
    session.flush()

    total_marks = MARKS_PER_QUESTION * len(ordered)
    passing_marks = round(total_marks * PASSING_PERCENT / 100.0, 2)
    test = session.execute(
        select(Test).where(Test.code == test_code)
    ).scalar_one_or_none()
    if test is None:
        test = Test(
            exam_id=exam.id,
            name=test_name,
            code=test_code,
            description=f"Imported from JSON (set {set_number}).",
            instructions="180 single-correct questions, 4 marks each, -1 for a "
                         "wrong answer, duration 180 minutes.",
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
        test.total_marks = total_marks
        test.passing_marks = passing_marks

    linked = set(
        session.execute(
            select(TestQuestion.question_id).where(TestQuestion.test_id == test.id)
        ).scalars()
    )
    for order, question in enumerate(ordered, start=1):
        if question.id not in linked:
            session.add(
                TestQuestion(test_id=test.id, question_id=question.id, question_order=order)
            )
    session.flush()

    now = datetime.now(timezone.utc)
    students = session.execute(
        select(User).where(User.email.in_(ASSIGN_STUDENT_EMAILS))
    ).scalars().all()
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
                    available_from=now - timedelta(days=1),
                    available_until=now + timedelta(days=ASSIGN_DURATION_DAYS),
                    max_attempts=MAX_ATTEMPTS,
                    status="ASSIGNED",
                )
            )
    session.flush()
    return test, created, skipped


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Import NEET question JSON into the DB.")
    parser.add_argument("path", help="path to the JSON file")
    parser.add_argument("--exam-code", default=DEFAULT_EXAM_CODE,
                        help=f"exam code to attach to (default {DEFAULT_EXAM_CODE})")
    parser.add_argument("--exam-name", default="NEET UG (Advanced Level) - Full Length Mock")
    parser.add_argument("--source-tag", default=None,
                        help="prefix for question source tags (default: file stem)")
    parser.add_argument("--test-prefix", default=None,
                        help="prefix for test codes (default: file stem)")
    parser.add_argument("--sets", default=None,
                        help="comma-separated set numbers to import (default: all)")
    parser.add_argument("--replace", action="store_true",
                        help="delete this file's tests/questions first")
    parser.add_argument("--dry-run", action="store_true",
                        help="parse and validate, then stop without writing")
    parser.add_argument("--validate-only", action="store_true",
                        help="validate the file and report, without touching the DB")
    parser.add_argument("--skip-validation", action="store_true",
                        help="import even if validation reports problems")
    args = parser.parse_args()

    path = Path(args.path)
    if not path.is_file():
        raise SystemExit(f"file not found: {path}")
    stem = path.stem
    source_tag = (args.source_tag or stem).upper().replace(" ", "_")
    test_prefix = (args.test_prefix or stem).upper().replace(" ", "_")

    sets = load_sets(path)

    wanted: Optional[set] = None
    if args.sets:
        wanted = {int(x) for x in args.sets.split(",") if x.strip()}

    selected = []
    problems: List[str] = []
    for s in sets:
        sn = s.get("set_number")
        if wanted is not None and sn not in wanted:
            continue
        selected.append(s)
        problems.extend(validate_set(s, f"set {sn}"))

    print("=" * 68)
    print(f"file: {path.name}")
    print(f"sets found: {len(sets)}   selected: {len(selected)}")
    total_q = sum(len(s.get("questions", [])) for s in selected)
    print(f"questions selected: {total_q}")
    print(f"exam code: {args.exam_code}   source tag: {source_tag}")
    print(f"validation problems: {len(problems)}")
    for p in problems[:20]:
        print("   -", p)

    if args.validate_only:
        print("validate-only: done (nothing written)")
        return
    if args.dry_run:
        for s in selected:
            sn = s.get("set_number")
            print(f"   would import set {sn}: {len(s['questions'])} questions, "
                  f"test code {test_prefix}-S{int(sn):02d}" if isinstance(sn, int)
                  else f"   would import set {sn}: {len(s['questions'])} questions")
        print("dry run: nothing written")
        return
    if problems and not args.skip_validation:
        raise SystemExit("refusing to import: fix the validation problems above "
                         "(or pass --skip-validation)")

    session = SessionLocal()
    try:
        test_codes = [
            f"{test_prefix}-S{int(s['set_number']):02d}"
            for s in selected if isinstance(s.get("set_number"), int)
        ]
        source_prefixes = [
            f"{source_tag}-S{int(s['set_number']):02d}"
            if isinstance(s.get("set_number"), int) else source_tag
            for s in selected
        ]
        if args.replace:
            print(f"--replace: removing {len(test_codes)} test(s) and questions for "
                  f"{len(source_prefixes)} selected set(s) ...")
            replace_existing(session, source_prefixes, test_codes)

        owner_id = get_owner_id(session)
        exam = upsert_exam(session, args.exam_code, args.exam_name, owner_id)
        needed = {q["subject"] for s in selected for q in s["questions"]}
        subjects = upsert_subjects(session, exam, needed)

        for s in selected:
            sn = s.get("set_number")
            test_code = f"{test_prefix}-S{int(sn):02d}" if isinstance(sn, int) else f"{test_prefix}-S"
            test_name = f"NEET UG Advanced - Imported Set {sn}"
            test, created, skipped = upsert_set(
                session, exam, subjects, source_tag, test_code, test_name,
                s, owner_id,
            )
            session.commit()
            print(f"  set {sn}: test {test.code} (id={test.id}) | "
                  f"created {created}, existing {skipped}, "
                  f"{test.total_marks} marks")
        session.commit()
        print("Done.")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
