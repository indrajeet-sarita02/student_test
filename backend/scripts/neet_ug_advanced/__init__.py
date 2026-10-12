"""NEET UG (Advanced Level) full-length question bank data.

Four subjects, 45 questions each (180 total), following the NEET UG blueprint:

    Physics   45
    Chemistry 45
    Botany    45
    Zoology   45
    ------------------
    Total    180  (720 marks at 4 marks per question, -1 for wrong answers)

Each ``QUESTIONS`` list contains normalized records produced by
``common.q``: topic, difficulty, text, four options, the 0-based index of the
correct option and an explanation.
"""

from __future__ import annotations

from .botany import QUESTIONS as BOTANY
from .chemistry import QUESTIONS as CHEMISTRY
from .common import validate
from .physics import QUESTIONS as PHYSICS
from .zoology import QUESTIONS as ZOOLOGY

SUBJECTS = {
    "Physics": PHYSICS,
    "Chemistry": CHEMISTRY,
    "Botany": BOTANY,
    "Zoology": ZOOLOGY,
}

for _subject, _questions in SUBJECTS.items():
    validate(_questions, _subject)

ALL_QUESTIONS = PHYSICS + CHEMISTRY + BOTANY + ZOOLOGY

__all__ = ["SUBJECTS", "PHYSICS", "CHEMISTRY", "BOTANY", "ZOOLOGY", "ALL_QUESTIONS"]
