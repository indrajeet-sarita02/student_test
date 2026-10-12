"""Shared helpers for the NEET UG (Advanced Level) master question bank.

Each question is a plain ``dict`` so the data and generators stay declarative:

    q(topic, difficulty, text, [opt1, opt2, opt3, opt4], correct_index, explanation)

``correct_index`` is 0-based.  ``nq`` is a convenience for numeric questions: it
computes the correct option, places it among three distractors at a stable
pseudo-random position (so answers are spread across A-D) and fills the
explanation.
"""

from __future__ import annotations

import hashlib

_DIFFICULTIES = {"EASY", "MEDIUM", "HARD"}


def q(topic, difficulty, text, options, correct, explanation):
    """Build one normalized question record with an explicit answer index."""
    options = [str(o) for o in options]
    if len(options) != 4:
        raise ValueError(f"question must have exactly 4 options: {text!r}")
    if len(set(options)) != 4:
        raise ValueError(f"duplicate options: {text!r}")
    if not 0 <= correct <= 3:
        raise ValueError(f"correct index out of range for: {text!r}")
    if difficulty not in _DIFFICULTIES:
        raise ValueError(f"bad difficulty {difficulty!r} for: {text!r}")
    return {
        "topic": topic,
        "difficulty": difficulty,
        "text": text,
        "options": options,
        "correct": correct,
        "explanation": explanation,
    }


def nq(topic, difficulty, text, correct, distractors, explanation):
    """Numeric question: spread the correct option across A-D deterministically."""
    opts = [str(d) for d in distractors]
    if len(opts) != 3:
        raise ValueError(f"a numeric question needs exactly 3 distractors: {text!r}")
    if not 0 <= 0:  # pragma: no cover - documentation guard
        raise ValueError
    pos = int(hashlib.md5(text.encode("utf-8")).hexdigest(), 16) % 4
    options = list(opts)
    options.insert(pos, str(correct))
    return q(topic, difficulty, text, options, pos, explanation)


def validate(questions, subject):
    """Raise on malformed records or duplicate question text."""
    seen = set()
    for item in questions:
        if len(item["options"]) != 4:
            raise ValueError(f"[{subject}] question must have 4 options: {item['text']!r}")
        if not 0 <= item["correct"] <= 3:
            raise ValueError(f"[{subject}] bad correct index: {item['text']!r}")
        if item["difficulty"] not in _DIFFICULTIES:
            raise ValueError(f"[{subject}] bad difficulty: {item['text']!r}")
        if item["text"] in seen:
            raise ValueError(f"[{subject}] duplicate question text: {item['text']!r}")
        seen.add(item["text"])


def merge(core, generated):
    """Concatenate two banks, dropping later records whose text repeats.

    Generated templates can occasionally reproduce a curated statement; the
    curated (first) copy wins so the final bank stays duplicate-free.
    """
    seen = set()
    out = []
    for item in list(core) + list(generated):
        if item["text"] in seen:
            continue
        seen.add(item["text"])
        out.append(item)
    return out
