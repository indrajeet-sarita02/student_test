"""Create the full-length NEET UG (Advanced Level) sets from the master bank.

The master bank lives in :mod:`scripts.neet_ug_adv_bank` (Physics, Chemistry,
Botany, Zoology pools).  For every requested set this script:

1. deterministically selects 45 questions per subject (a sliding window across
   the whole pool, so different sets draw different content),
2. shuffles the four options of every selected question (so the correct answer
   is spread across A-D) and records the new answer index,
3. inserts the 180 questions + the published test, and assigns it to the demo
   students, using the shared ``advanced_paper.seed_paper`` engine, and
4. writes a JSON paper with the **answer and explanation printed under every
   question** to ``samples/`` for review/printing.

Sets 01-03 already exist and are intentionally left untouched by default; the
script therefore defaults to ``--start 4 --count 7``.

Usage (from the ``backend`` directory)::

    .venv/bin/python scripts/seed_neet_adv_10sets.py                 # sets 04-10
    .venv/bin/python scripts/seed_neet_adv_10sets.py --dry-run       # preview only
    .venv/bin/python scripts/seed_neet_adv_10sets.py --start 1 --count 10 --replace
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
PROJECT_ROOT = HERE.parents[1]  # backend/
SCRIPTS_DIR = HERE.parent  # backend/scripts/
for _path in (str(PROJECT_ROOT), str(SCRIPTS_DIR)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from advanced_paper import TestSpec, seed_paper  # noqa: E402
from neet_ug_adv_bank import SUBJECTS  # noqa: E402

EXAM_CODE = "NEET-ADV"
EXAM_NAME = "NEET UG (Advanced Level) - Full Length Mock"
EXAM_DESCRIPTION = (
    "NEET UG advanced-level full-length mock series (Physics, Chemistry, Botany, "
    "Zoology). 180 questions, 720 marks, 180 minutes, -1 for a wrong answer."
)
PER_SUBJECT = 45
SUBJECT_ORDER = ["Physics", "Chemistry", "Botany", "Zoology"]


def _seed_int(*parts) -> int:
    digest = hashlib.md5("|".join(str(p) for p in parts).encode("utf-8")).hexdigest()
    return int(digest, 16) % (2 ** 31)


def _shuffle_options(item: dict, seed: int) -> dict:
    """Return a copy of ``item`` with its options shuffled deterministically."""
    rng = random.Random(seed)
    options = list(item["options"])
    correct_text = options[item["correct"]]
    rng.shuffle(options)
    return {**item, "options": options, "correct": options.index(correct_text)}


def build_set_bank(set_number: int, total_sets: int) -> dict:
    """Assemble the 45-per-subject question bank for one set."""
    bank = {}
    for name in SUBJECT_ORDER:
        pool = SUBJECTS[name]
        size = len(pool)
        start = ((set_number - 1) * size) // total_sets
        chosen = [pool[(start + k) % size] for k in range(PER_SUBJECT)]
        order_rng = random.Random(_seed_int("order", set_number, name))
        order_rng.shuffle(chosen)
        bank[name] = [
            _shuffle_options(item, _seed_int("opt", set_number, name, item["text"]))
            for item in chosen
        ]
    return bank


def _answer_letter(correct: int) -> str:
    return "ABCD"[correct]


def write_paper_json(bank: dict, set_number: int, out_dir: Path) -> Path:
    """Write one set as a paper with the answer + explanation under each question."""
    out_dir.mkdir(parents=True, exist_ok=True)
    set_code = f"NEET-UG-ADV-SET-{set_number:02d}"
    questions = []
    number = 0
    for name in SUBJECT_ORDER:
        for item in bank[name]:
            number += 1
            questions.append(
                {
                    "number": number,
                    "subject": name,
                    "question": item["text"],
                    "options": {
                        letter: text for letter, text in zip("ABCD", item["options"])
                    },
                    "answer": "ABCD"[item["correct"]],
                    "explanation": item["explanation"],
                    "difficulty": item["difficulty"],
                    "topic": item["topic"],
                }
            )
    payload = {
        "exam": EXAM_NAME,
        "set_code": set_code,
        "set_label": f"Set {set_number:02d}",
        "total_questions": len(questions),
        "questions": questions,
    }
    path = out_dir / f"{set_code}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=4, help="first set number (default 4)")
    parser.add_argument("--count", type=int, default=7, help="number of sets (default 7)")
    parser.add_argument("--total", type=int, default=10, help="series size used to spread selection")
    parser.add_argument("--replace", action="store_true", help="delete and recreate each set")
    parser.add_argument("--dry-run", action="store_true", help="build only, no DB writes")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=PROJECT_ROOT.parent / "samples",
        help="directory for the JSON papers (default <repo>/samples)",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    numbers = list(range(args.start, args.start + args.count))
    print(f"Building sets: {', '.join(f'{n:02d}' for n in numbers)} (of {args.total})")

    session = None
    if not args.dry_run:
        from app.db.session import SessionLocal

        session = SessionLocal()

    try:
        for number in numbers:
            bank = build_set_bank(number, args.total)
            counts = {name: len(bank[name]) for name in SUBJECT_ORDER}
            answer_pos = [0, 0, 0, 0]
            for name in SUBJECT_ORDER:
                for item in bank[name]:
                    answer_pos[item["correct"]] += 1
            print(
                f"\nSet {number:02d}: "
                + ", ".join(f"{k}={v}" for k, v in counts.items())
                + f" | answers A/B/C/D = {answer_pos}"
            )
            json_path = write_paper_json(bank, number, args.out_dir)
            print(f"  wrote {json_path}")

            if args.dry_run:
                continue

            spec = TestSpec(
                code=f"NEET-UG-ADV-SET-{number:02d}",
                name=f"NEET UG (Advanced Level) - Set {number:02d}",
                description=(
                    "Full-length advanced NEET UG paper - "
                    f"Set {number:02d} (180 questions, 720 marks, 180 minutes)."
                ),
                selection=None,
                max_attempts=1,
            )
            result = seed_paper(
                session,
                question_bank=bank,
                set_prefix=spec.code,
                tests=[spec],
                exam_code=EXAM_CODE,
                exam_name=EXAM_NAME,
                exam_description=EXAM_DESCRIPTION,
                replace=args.replace,
            )
            for code, test_id, linked in result.tests:
                print(
                    f"  DB: test {code} (id={test_id}) linked {linked} questions; "
                    f"created {result.questions_created}, reused {result.questions_reused}, "
                    f"assignments {result.assignments}"
                )
        return 0
    finally:
        if session is not None:
            session.close()


if __name__ == "__main__":
    raise SystemExit(main())
