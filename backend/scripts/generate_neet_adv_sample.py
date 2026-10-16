"""Generate the NEET UG (Advanced) sample XLSX import file.

Writes ``samples/neet_ug_adv_set01_sample.xlsx`` - a ready-to-upload workbook in
the same format the API serves from ``GET /api/v1/tests/import/template`` and
expects at ``POST /api/v1/tests/import``.

The workbook carries five representative questions taken straight from the
``neet_ug_advanced_set01`` question bank (the same data used by
``seed_neet_adv_set01.py``), so the sample can never drift away from the paper:

    Physics    PHY-001, PHY-002
    Chemistry  CHEM-002
    Botany     BOT-007
    Zoology    ZOO-012

Usage (from the ``backend/`` directory):

    .venv/bin/python scripts/generate_neet_adv_sample.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

# Make the project root importable regardless of the invocation directory.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.test_import_service import (  # noqa: E402
    INSTRUCTIONS_SHEET,
    QUESTIONS_SHEET,
    QUESTION_COLUMNS,
    TEST_SHEET,
)
from app.utils.xlsx import read_xlsx, write_xlsx  # noqa: E402
from scripts.neet_ug_advanced_set01 import (  # noqa: E402
    BOTANY,
    CHEMISTRY,
    PHYSICS,
    SET_CODE,
    ZOOLOGY,
)

OUTPUT = PROJECT_ROOT / "samples" / "neet_ug_adv_set01_sample.xlsx"

#: subject code -> (display name, question list)
SUBJECTS: Dict[str, Tuple[str, Sequence[dict]]] = {
    "PHY": ("Physics", PHYSICS),
    "CHEM": ("Chemistry", CHEMISTRY),
    "BOT": ("Botany", BOTANY),
    "ZOO": ("Zoology", ZOOLOGY),
}

#: The representative rows: ``(subject code, 0-based index within that subject)``.
SAMPLES: List[Tuple[str, int]] = [
    ("PHY", 0),   # PHY-001
    ("PHY", 1),   # PHY-002
    ("CHEM", 1),  # CHEM-002
    ("BOT", 6),   # BOT-007
    ("ZOO", 11),  # ZOO-012
]

LETTERS = ("A", "B", "C", "D")


def _question_row(subject_code: str, index: int) -> List[Any]:
    subject_name, questions = SUBJECTS[subject_code]
    item = questions[index]
    source = f"{SET_CODE}-{subject_code}-{index + 1:03d}"
    correct = LETTERS[item["correct"]]
    options = list(item["options"]) + [""] * (6 - len(item["options"]))
    row: List[Any] = [
        subject_code,
        subject_name,
        item["topic"],
        item["text"],
        "SINGLE_CHOICE",
        item["difficulty"],
        4,
        1,
        item["explanation"],
        source,
        *options,
        correct,
    ]
    return row


def _test_sheet() -> List[List[Any]]:
    return [
        ["Field", "Value"],
        ["name", "NEET UG Advanced - Sample (Set 01)"],
        ["code", "NEET-UG-ADV-SET-01-SAMPLE-IMPORT"],
        [
            "description",
            "Sample import workbook: 5 representative questions from the "
            "NEET UG (Advanced) Set 01 paper.",
        ],
        [
            "instructions",
            "Attempt all questions. Each question carries 4 marks; "
            "1 mark is deducted for a wrong answer.",
        ],
        ["duration_minutes", 30],
        ["passing_marks", 8],
        ["negative_marking_enabled", "TRUE"],
        ["negative_marks", 1],
        ["randomize_questions", "FALSE"],
        ["randomize_options", "FALSE"],
        ["max_attempts", 1],
        ["scheduled_start_at", ""],
        ["scheduled_end_at", ""],
    ]


def _instruction_rows() -> List[List[Any]]:
    return [
        ["NEET UG (Advanced) - sample test import"],
        [],
        ["This workbook follows the standard test-import format."],
        ["Fill in or edit the 'Test' and 'Questions' sheets, then upload it"],
        ["from Admin -> Tests -> Import (choose the NEET-ADV exam)."],
        [],
        ["Columns: subject_code, subject_name, topic, question_text,"],
        ["question_type, difficulty, marks, negative_marks, explanation,"],
        ["source, option_1..option_6, correct_options (letters or numbers)."],
        [],
        [f"Sample questions are taken from {SET_CODE}."],
        ["Imported questions and the new test are created in DRAFT status."],
    ]


def _questions_sheet() -> List[List[Any]]:
    rows: List[List[Any]] = [list(QUESTION_COLUMNS)]
    rows.extend(_question_row(code, index) for code, index in SAMPLES)
    return rows


def build_workbook() -> bytes:
    """Return the sample workbook bytes (Test + Questions + Instructions)."""
    return write_xlsx(
        [
            (INSTRUCTIONS_SHEET, _instruction_rows()),
            (TEST_SHEET, _test_sheet()),
            (QUESTIONS_SHEET, _questions_sheet()),
        ]
    )


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    data = build_workbook()
    OUTPUT.write_bytes(data)

    # Sanity check: the sample must round-trip through our own reader.
    sheets = read_xlsx(data)
    question_rows = sheets[QUESTIONS_SHEET]
    assert len(question_rows) == len(SAMPLES) + 1, "unexpected question row count"
    assert all(
        len(row) == len(QUESTION_COLUMNS) for row in question_rows
    ), "question rows do not align with the header columns"
    print(
        f"Wrote {OUTPUT} ({len(data)} bytes, "
        f"{len(SAMPLES)} sample questions)"
    )


if __name__ == "__main__":
    main()
