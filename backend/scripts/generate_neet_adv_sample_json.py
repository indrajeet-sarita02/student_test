"""Generate a sample JSON export of the NEET UG (Advanced) paper.

Writes ``samples/neet_ug_adv_set01_sample.json`` - a compact, human-readable
sample in the shape used by ``backend/scripts/import_neet_json.py``.

Usage (from the ``backend/`` directory):

    .venv/bin/python scripts/generate_neet_adv_sample_json.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.neet_ug_advanced_set01 import (  # noqa: E402
    BOTANY,
    CHEMISTRY,
    PHYSICS,
    SET_CODE,
    SET_LABEL,
    ZOOLOGY,
)

OUTPUT = PROJECT_ROOT / "samples" / "neet_ug_adv_set01_sample.json"

SUBJECTS: Dict[str, Tuple[str, Sequence[dict]]] = {
    "Physics": ("PHY", PHYSICS),
    "Chemistry": ("CHEM", CHEMISTRY),
    "Botany": ("BOT", BOTANY),
    "Zoology": ("ZOO", ZOOLOGY),
}

SAMPLES: List[Tuple[str, int]] = [
    ("Physics", 0),
    ("Chemistry", 1),
    ("Botany", 6),
    ("Zoology", 11),
    ("Physics", 1),
]

LETTERS = ("A", "B", "C", "D")


def _json_question(subject_name: str, index: int) -> dict:
    _code, questions = SUBJECTS[subject_name]
    item = questions[index]
    qid = f"{_code}_{index + 1:03d}"
    return {
        "subject": subject_name,
        "q_id": qid,
        "question": item["text"],
        "options": {
            "A": item["options"][0],
            "B": item["options"][1],
            "C": item["options"][2],
            "D": item["options"][3],
        },
        "correct_answer": LETTERS[item["correct"]],
        "explanation": item["explanation"],
        "difficulty": item["difficulty"],
        "topic": item["topic"],
    }


def build_sample() -> dict:
    return {
        "exam": "NEET UG (Advanced Level) - Full Length Mock",
        "set_code": SET_CODE,
        "set_number": 1,
        "set_label": SET_LABEL,
        "difficulty": "Advanced",
        "total_questions": len(SAMPLES),
        "questions": [_json_question(s, i) for s, i in SAMPLES],
    }


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    data = build_sample()
    OUTPUT.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"Wrote {OUTPUT} ({OUTPUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
