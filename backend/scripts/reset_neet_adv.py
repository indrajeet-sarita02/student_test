"""Clear ALL test data (tests + questions) that belongs to NEET-related exams.

By default every exam whose code or name looks like NEET is cleaned
(``NEET``, ``NEET-ADV``, ...).  A JSON backup of the removed tests/questions is
written to /tmp/opencode first.  Keeps the exams and their subjects/topics;
removes:
  * every test under the NEET exams (+ its test_questions, assignments,
    attempts, results)
  * every question (and options) whose subject belongs to a NEET exam

Usage:  .venv/bin/python scripts/reset_neet_adv.py [--dry-run] [--exam-codes NEET NEET-ADV]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import delete, or_, select  # noqa: E402

from app.db.session import SessionLocal  # noqa: E402
from app.models import (  # noqa: E402
    Attempt,
    AttemptAnswer,
    Exam,
    Question,
    QuestionOption,
    Result,
    Subject,
    Test,
    TestAssignment,
    TestQuestion,
)

BACKUP_PATH = Path("/tmp/opencode/neet_adv_backup.json")


def neet_exams(session, exam_codes=None):
    """Return every NEET-related exam (explicit codes if given)."""
    stmt = select(Exam)
    if exam_codes:
        stmt = stmt.where(Exam.code.in_(exam_codes))
    else:
        stmt = stmt.where(or_(Exam.code.ilike("%NEET%"), Exam.name.ilike("%NEET%")))
    return session.execute(stmt.order_by(Exam.id)).scalars().all()


def backup(session, exam, test_ids, subject_ids) -> None:
    data = {"tests": [], "questions": []}
    for t in session.execute(select(Test).where(Test.id.in_(test_ids))).scalars():
        data["tests"].append(
            {"id": t.id, "code": t.code, "name": t.name, "status": t.status,
             "total_marks": float(t.total_marks), "duration_minutes": t.duration_minutes}
        )
    qs = session.execute(select(Question).where(Question.subject_id.in_(subject_ids))).scalars().all()
    for q in qs:
        data["questions"].append(
            {"source": q.source, "subject_id": q.subject_id, "text": q.question_text,
             "explanation": q.explanation, "difficulty": q.difficulty,
             "options": [{"text": o.option_text, "order": o.option_order,
                          "is_correct": o.is_correct} for o in q.options]}
        )
    BACKUP_PATH.parent.mkdir(parents=True, exist_ok=True)
    suffix = f"_{exam.code.replace('/', '_')}"
    path = BACKUP_PATH.with_name(f"{BACKUP_PATH.stem}{suffix}{BACKUP_PATH.suffix}")
    path.write_text(json.dumps(data, indent=2))
    print(f"  backup written: {path} "
          f"({len(data['tests'])} tests, {len(data['questions'])} questions)")


def clear_exam(session, exam, dry_run: bool) -> tuple[int, int]:
    subject_ids = list(
        session.execute(select(Subject.id).where(Subject.exam_id == exam.id)).scalars()
    )
    test_ids = list(
        session.execute(select(Test.id).where(Test.exam_id == exam.id)).scalars()
    )
    question_ids = list(
        session.execute(
            select(Question.id).where(Question.subject_id.in_(subject_ids))
        ).scalars()
    ) if subject_ids else []
    print(f"exam {exam.code} (id={exam.id})")
    print(f"  subjects: {subject_ids}")
    print(f"  tests to delete: {len(test_ids)}")
    print(f"  questions to delete: {len(question_ids)}")
    if dry_run:
        print("  dry run: nothing deleted")
        return len(test_ids), len(question_ids)

    backup(session, exam, test_ids, subject_ids)

    # Remove attempt/result chains tied to these tests or questions.
    if test_ids:
        attempt_ids = list(
            session.execute(select(Attempt.id).where(Attempt.test_id.in_(test_ids))).scalars()
        )
        if attempt_ids:
            session.execute(delete(AttemptAnswer).where(AttemptAnswer.attempt_id.in_(attempt_ids)))
        session.execute(delete(Result).where(Result.test_id.in_(test_ids)))
        session.execute(delete(Attempt).where(Attempt.test_id.in_(test_ids)))
        session.execute(delete(TestAssignment).where(TestAssignment.test_id.in_(test_ids)))
        session.execute(delete(TestQuestion).where(TestQuestion.test_id.in_(test_ids)))
        session.execute(delete(Test).where(Test.id.in_(test_ids)))

    if question_ids:
        session.execute(delete(AttemptAnswer).where(AttemptAnswer.question_id.in_(question_ids)))
        session.execute(delete(TestQuestion).where(TestQuestion.question_id.in_(question_ids)))
        session.execute(delete(QuestionOption).where(QuestionOption.question_id.in_(question_ids)))
        session.execute(delete(Question).where(Question.id.in_(question_ids)))

    session.commit()
    return len(test_ids), len(question_ids)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--exam-codes",
        nargs="*",
        default=None,
        help="explicit exam codes to clean (default: every NEET-related exam)",
    )
    args = parser.parse_args()

    session = SessionLocal()
    try:
        exams = neet_exams(session, args.exam_codes)
        if not exams:
            print("no NEET-related exams found - nothing to do")
            return

        total_tests = total_questions = 0
        for exam in exams:
            tests, questions = clear_exam(session, exam, args.dry_run)
            total_tests += tests
            total_questions += questions

        print("Done.")
        print(f"deleted tests: {total_tests}, questions: {total_questions}")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
