"""Seed the NEET UG (Advanced Level) paper - Set 02 - into the database.

Creates (idempotently):

* the ``NEET-ADV`` exam (reused if it already exists),
* four subjects - Physics, Chemistry, Botany, Zoology,
* all topics referenced by the questions,
* 180 published questions (45 per subject) with four options and an
  explanation each, stored in the shared question bank, and
* two published tests assigned to the demo students:

  - ``NEET-UG-ADV-SET-02``  - the full paper (180 questions, 720 marks,
    180 minutes, -1 for a wrong answer);
  - ``NEET-UG-ADV-SAMPLE-02`` - a short 20-question sample (5 per subject,
    80 marks, 30 minutes) that reuses the same question bank.

Usage (from the ``backend/`` directory):

    .venv/bin/python scripts/seed_neet_adv_set02.py
    .venv/bin/python scripts/seed_neet_adv_set02.py --replace
    .venv/bin/python scripts/seed_neet_adv_set02.py --dry-run
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = sys.path and __import__("pathlib").Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db.session import SessionLocal  # noqa: E402
from scripts.advanced_paper import TestSpec, seed_paper  # noqa: E402
from scripts.neet_ug_advanced_set02 import SET_CODE, SUBJECTS  # noqa: E402

# ---------------------------------------------------------------------------
# Paper definition
# ---------------------------------------------------------------------------
EXAM_CODE = "NEET-ADV"
EXAM_NAME = "NEET UG (Advanced Level) - Full Length Mock"
EXAM_DESCRIPTION = (
    "Advanced-level NEET UG practice examination covering Physics, Chemistry, "
    "Botany and Zoology."
)

SET_PREFIX = "NEET-UG-ADV-SET-02"

FULL_TEST = TestSpec(
    code="NEET-UG-ADV-SET-02",
    name="NEET UG Advanced - Full Syllabus Mock (Set 02)",
    description=(
        "Full-length advanced NEET UG mock paper: 180 single-correct questions "
        "(Physics 45, Chemistry 45, Botany 45, Zoology 45), 720 marks."
    ),
    selection=None,
    duration_minutes=180,
    marks_per_question=4.0,
    negative_marks=1.0,
    passing_percent=40.0,
    max_attempts=2,
)

SAMPLE_TEST = TestSpec(
    code="NEET-UG-ADV-SAMPLE-02",
    name="NEET UG Advanced - Sample Test (Set 02)",
    description=(
        "Short advanced NEET UG sample test: 20 single-correct questions "
        "(5 per subject) drawn from the Set 02 question bank, 80 marks."
    ),
    instructions=(
        "1. The sample test has 20 single-correct questions carrying 4 marks "
        "each.\n"
        "2. One mark is deducted for every wrong answer.\n"
        "3. The duration of the test is 30 minutes.\n"
        "4. Section distribution: Physics 5, Chemistry 5, Botany 5, Zoology 5."
    ),
    selection={"Physics": 5, "Chemistry": 5, "Botany": 5, "Zoology": 5},
    duration_minutes=30,
    marks_per_question=4.0,
    negative_marks=1.0,
    passing_percent=40.0,
    max_attempts=2,
)

TESTS = [FULL_TEST, SAMPLE_TEST]


def run(session, dry_run: bool, replace: bool) -> None:
    from scripts.advanced_paper import seed_paper

    print("=" * 68)
    print("NEET UG (Advanced Level) - Set 01 seed")
    print("=" * 68)

    if dry_run:
        for name in ("Physics", "Chemistry", "Botany", "Zoology"):
            print(f"  {name:<10} {len(SUBJECTS[name]):>3} questions")
        total = sum(len(SUBJECTS[n]) for n in ("Physics", "Chemistry", "Botany", "Zoology"))
        print(f"  {'TOTAL':<10} {total:>3} questions, {total * 4:.0f} marks")
        print(f"  full test   : {FULL_TEST.code} ({total} questions)")
        print(f"  sample test : {SAMPLE_TEST.code} "
              f"(sum(selection.values()) questions)")
        print("  dry run - nothing written")
        return

    result = seed_paper(
        session,
        question_bank=SUBJECTS,
        set_prefix=SET_PREFIX,
        tests=TESTS,
        exam_code=EXAM_CODE,
        exam_name=EXAM_NAME,
        exam_description=EXAM_DESCRIPTION,
        replace=replace,
    )

    if result.exam is not None:
        print(f"  exam: {result.exam.code} (id={result.exam.id})")
    print(f"  questions created: {result.questions_created}, "
          f"already present: {result.questions_reused}")
    for code, test_id, linked in result.tests:
        print(f"  test: {code} (id={test_id}) - {linked} questions linked")
    print(f"  new assignments: {result.assignments}")
    print("=" * 68)
    print("Done.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed the NEET UG (Advanced Level) paper - Set 01."
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
