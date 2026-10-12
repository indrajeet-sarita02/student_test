"""Shared helpers for the NEET UG (Advanced Level) question bank data.

Each question is a plain ``dict`` so the data modules stay declarative and easy
to review:

    q(topic, difficulty, text, [opt1, opt2, opt3, opt4], correct_index, explanation)

``correct_index`` is 0-based, so ``0`` marks the first option as the answer.
"""

from __future__ import annotations

from typing import List, Sequence


def q(
    topic: str,
    difficulty: str,
    text: str,
    options: Sequence[str],
    correct: int,
    explanation: str,
) -> dict:
    """Build one normalized question record."""
    if len(options) != 4:
        raise ValueError(f"question must have exactly 4 options: {text!r}")
    if not 0 <= correct <= 3:
        raise ValueError(f"correct index out of range for: {text!r}")
    if difficulty not in {"EASY", "MEDIUM", "HARD"}:
        raise ValueError(f"bad difficulty {difficulty!r} for: {text!r}")
    return {
        "topic": topic,
        "difficulty": difficulty,
        "text": text.strip(),
        "options": [o.strip() for o in options],
        "correct": correct,
        "explanation": explanation.strip(),
    }


def validate(questions: List[dict], subject: str) -> None:
    """Fail fast on malformed data before it reaches the database."""
    seen: set = set()
    for i, item in enumerate(questions, start=1):
        if item["text"] in seen:
            raise ValueError(f"{subject}: duplicate question text at #{i}")
        seen.add(item["text"])
        if len(item["options"]) != 4:
            raise ValueError(f"{subject}: question #{i} does not have 4 options")
        if not 0 <= item["correct"] <= 3:
            raise ValueError(f"{subject}: question #{i} has an invalid answer")
