"""Shared generators for the Biology (Botany + Zoology) master bank.

Biology has fewer "compute the number" questions than Physics/Chemistry, so the
main workhorse is :func:`describe`, which turns a table of ``(term,
definition)`` pairs into "Which of the following correctly describes <term>?"
questions.  Because the stem names the term, every question has a unique,
self-contained stem.  :func:`numeric_biology` adds genuinely quantitative
genetics / ecology items whose answers are computed in Python.
"""

from __future__ import annotations

from .common import nq, q


def describe(topic, difficulty, pairs, positions=0):
    """One question per ``(term, definition)`` pair in ``pairs``.

    The correct option is the definition of the named term; the three
    distractors are definitions of other terms (deterministically chosen).
    ``positions`` may be 0 (default); option order is reshuffled during paper
    assembly anyway.
    """
    out = []
    definitions = [d for _, d in pairs]
    for index, (term, definition) in enumerate(pairs):
        distractors = []
        for offset in range(1, len(pairs)):
            candidate = definitions[(index + offset) % len(pairs)]
            if candidate != definition and candidate not in distractors:
                distractors.append(candidate)
            if len(distractors) == 3:
                break
        out.append(
            q(
                topic,
                difficulty,
                f"Which of the following correctly describes {term}?",
                [definition] + distractors,
                positions,
                f"{term} refers to {definition}.",
            )
        )
    return out


def numeric_biology():
    """Quantitative genetics / ecology questions (all with unique stems)."""
    out = []

    # 1. Number of gamete types for n heterozygous loci = 2^n
    for n in [1, 2, 3, 4, 5]:
        out.append(
            nq(
                "Principles of Inheritance and Variation",
                "MEDIUM",
                f"How many types of gametes can be produced by an individual that is "
                f"heterozygous at {n} gene loci ?",
                f"{2 ** n}",
                [f"{2 ** (n + 1)}", f"{2 ** (n + 2)}", f"{2 ** n + 1}"],
                f"An individual heterozygous at n loci produces 2^n = 2^{n} = {2 ** n} "
                f"types of gametes.",
            )
        )

    # F2 genotypes in a polyhybrid cross = 3^n
    for n in [1, 2, 3]:
        out.append(
            nq(
                "Principles of Inheritance and Variation",
                "HARD",
                f"In a cross involving {n} independently assorting gene pair(s), the number "
                f"of genotypes expected in the F2 generation is",
                f"{3 ** n}",
                [f"{2 ** n}", f"{4 ** n}", f"{3 ** n + 3}"],
                f"The number of F2 genotypes = 3^n = 3^{n} = {3 ** n}.",
            )
        )

    # energy flow - 10% law
    for start, level in [(10000, 3), (50000, 4), (20000, 2)]:
        energy = start * (0.1 ** (level - 1))
        out.append(
            nq(
                "Ecosystem",
                "MEDIUM",
                f"If the producers in a food chain trap {start} kJ of energy, the energy "
                f"available to organisms at trophic level {level} (following the 10% law) is",
                f"{energy:g} kJ",
                [f"{energy / 10:g} kJ", f"{energy * 2:g} kJ", f"{energy * 3:g} kJ"],
                f"Only 10% of energy is transferred at each step, so energy at level "
                f"{level} = {start} x (0.1)^{level - 1} = {energy:g} kJ.",
            )
        )

    # length of a DNA molecule - 0.34 nm per base pair
    for bp in [1000, 2000, 5000]:
        length = bp * 0.34
        out.append(
            nq(
                "Molecular Basis of Inheritance",
                "HARD",
                f"The length of a B-DNA molecule containing {bp} base pairs "
                f"(0.34 nm per base pair) is",
                f"{length:g} nm",
                [f"{bp * 3.4:g} nm", f"{length / 2:g} nm", f"{bp * 0.034:g} nm"],
                f"Length = number of base pairs x 0.34 nm = {bp} x 0.34 = {length:g} nm.",
            )
        )

    # nucleotides needed to code for a polypeptide
    for aa in [50, 100, 200]:
        nts = aa * 3
        out.append(
            nq(
                "Molecular Basis of Inheritance",
                "MEDIUM",
                f"The minimum number of nucleotides in the coding region of an mRNA "
                f"required to specify a polypeptide of {aa} amino acids is",
                f"{nts}",
                [f"{aa}", f"{aa * 2}", f"{aa * 4}"],
                f"Each amino acid is specified by a codon of three nucleotides, so "
                f"{aa} amino acids need {nts} nucleotides.",
            )
        )

    return out
