"""Master question bank for the NEET UG (Advanced Level) 20-set series.

The bank combines:

* the curated 180-question Set 01 paper (``neet_ug_advanced_set01``), reused as
  the conceptual core, and
* a large set of *generated* questions produced deterministically from
  templates (``physics``, ``chemistry``, ``botany``, ``zoology``) so that the
  20 assembled papers share far less content than the raw curated core.

Every record is a plain ``dict`` built with :func:`common.q` /
:func:`common.nq`: ``topic``, ``difficulty``, ``text``, four ``options``, the
0-based ``correct`` index and an ``explanation``.

The bank is a *pool* - individual papers are assembled from it by
``scripts.seed_neet_adv_20sets`` (deterministic selection + option shuffling).
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
