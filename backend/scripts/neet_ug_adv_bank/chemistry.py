"""NEET UG (Advanced Level) - Chemistry master bank.

``CORE`` is the curated 45-question Set 01 paper.  The rest is generated from
templates whose numeric answers are computed in Python, so the answer key is
correct by construction.
"""

from __future__ import annotations

import math

from scripts.neet_ug_advanced_set01.chemistry import QUESTIONS as _CORE

from .common import merge, nq, q

CORE = list(_CORE)
GEN = []


def _n(x):
    if isinstance(x, str):
        return x
    if isinstance(x, float) and x.is_integer():
        x = int(x)
    if isinstance(x, int):
        return str(x)
    return f"{x:.4g}"


def _num(topic, diff, text, value, distractors, expl, unit=""):
    GEN.append(
        nq(
            topic,
            diff,
            text,
            f"{_n(value)}{unit}",
            [f"{_n(d)}{unit}" for d in distractors],
            expl,
        )
    )


NA = 6.022e23

# ---------------------------------------------------------------------------
# Some Basic Concepts of Chemistry - mole concept
# ---------------------------------------------------------------------------
for mass, M, name in [(18, 18, "water"), (44, 44, "carbon dioxide"),
                      (58.5, 58.5, "sodium chloride"), (98, 98, "sulphuric acid"),
                      (40, 40, "sodium hydroxide"), (180, 180, "glucose"),
                      (56, 56, "potassium hydroxide"), (80, 80, "ammonium nitrate")]:
    n = mass / M
    _num("Some Basic Concepts of Chemistry", "EASY",
         f"The number of moles present in {mass} g of {name} (molar mass = {M} g/mol) is",
         round(n, 3), [round(n * 2, 3), round(n / 2, 3), round(mass * M, 3)],
         f"n = mass / molar mass = {mass}/{M} mol.", " mol")

for mass, M in [(18, 18), (44, 44), (2, 2), (32, 32), (28, 28)]:
    N = mass / M * NA
    _num("Some Basic Concepts of Chemistry", "MEDIUM",
         f"The number of molecules in {mass} g of a substance of molar mass {M} g/mol "
         f"is (N_A = 6.022 x 10^23 mol^-1)",
         f"{N:.3g}", [f"{N / 2:.3g}", f"{mass * M * NA:.3g}", f"{M / mass:.3g}"],
         f"N = (mass/M) x N_A = ({mass}/{M}) x 6.022e23.")

for M in [18, 44, 32, 28, 64]:
    m = M / NA
    _num("Some Basic Concepts of Chemistry", "MEDIUM",
         f"The mass of a single molecule of a gas of molar mass {M} g/mol is "
         f"(N_A = 6.022 x 10^23 mol^-1), approximately",
         f"{m:.3g} g", [f"{m / 2:.3g} g", f"{M * NA:.3g} g", f"{m * 6:.3g} g"],
         f"Mass of one molecule = M/N_A = {M}/6.022e23 g.")

for mol, vol in [(0.5, 0.5), (1, 2), (2, 0.5), (0.1, 0.1), (0.25, 0.25)]:
    conc = mol / vol
    _num("Some Basic Concepts of Chemistry", "MEDIUM",
         f"The molarity of a solution containing {mol} mol of solute in {vol} L of "
         f"solution is",
         round(conc, 3), [round(mol * vol, 3), round(mol / (vol * 1000), 3), round(conc * 2, 3)],
         f"Molarity = moles of solute / volume of solution (L) = {mol}/{vol}.", " M")

for solute_mass, M, solvent_kg in [(4, 40, 1), (5.85, 58.5, 0.5), (18, 180, 0.5)]:
    mol = solute_mass / M
    molality = mol / solvent_kg
    _num("Solutions", "HARD",
         f"The molality of a solution containing {solute_mass} g of a solute "
         f"(molar mass {M} g/mol) in {solvent_kg} kg of solvent is",
         round(molality, 3), [round(solute_mass / solvent_kg, 3), round(molality / 2, 3),
                              round(molality * 2, 3)],
         f"Molality = moles of solute / kg of solvent = ({solute_mass}/{M})/{solvent_kg}.", " m")

# ---------------------------------------------------------------------------
# States of Matter - gas laws
# ---------------------------------------------------------------------------
for n, T, V in [(1, 273, 22.4), (2, 273, 22.4), (0.5, 300, 10)]:
    P = n * 0.0821 * T / V
    _num("States of Matter", "MEDIUM",
         f"{n} mol of an ideal gas occupies {V} L at {T} K (R = 0.0821 L atm/mol/K). "
         f"Its pressure is",
         round(P, 3), [round(n * 0.0821 * T, 3), round(V / (n * 0.0821 * T), 3), round(P * 2, 3)],
         f"P = nRT/V = {n} x 0.0821 x {T} / {V}.", " atm")

for M, T, P in [(44, 273, 1), (28, 273, 1), (32, 300, 2)]:
    d = P * M / (0.0821 * T)
    _num("States of Matter", "HARD",
         f"The density of a gas of molar mass {M} g/mol at {T} K and {P} atm "
         f"(R = 0.0821 L atm/mol/K) is",
         round(d, 3), [round(0.0821 * T / (P * M), 3), round(P * M * 0.0821 * T, 3), round(d / 2, 3)],
         f"d = PM/RT = {P} x {M} / (0.0821 x {T}).", " g/L")

# ---------------------------------------------------------------------------
# Ionic Equilibrium - pH
# ---------------------------------------------------------------------------
for conc in [0.01, 0.001, 0.0001, 1e-6]:
    pH = -math.log10(conc)
    _num("Ionic Equilibrium", "MEDIUM",
         f"The pH of a solution with hydrogen ion concentration {conc:g} M is",
         round(pH, 2), [round(14 - pH, 2), round(pH / 2, 2), round(pH + 1, 2)],
         f"pH = -log[H+] = -log({conc:g}) = {round(pH, 2)}.")

for pOH in [3, 5, 6.5]:
    pH = 14 - pOH
    _num("Ionic Equilibrium", "EASY",
         f"If the pOH of a solution at 298 K is {pOH}, its pH is",
         round(pH, 1), [round(pOH, 1), round(14 + pOH, 1), round(pH / 2, 1)],
         f"pH + pOH = 14, so pH = 14 - {pOH} = {round(pH, 1)}.")

# ---------------------------------------------------------------------------
# Chemical Kinetics
# ---------------------------------------------------------------------------
for k in [0.693, 0.0693, 0.00693, 2.0]:
    th = 0.693 / k
    _num("Chemical Kinetics", "HARD",
         f"For a first-order reaction with rate constant k = {k} s^-1, the half-life is",
         round(th, 2), [round(1 / k, 2), round(0.693 * k, 5), round(th / 2, 2)],
         f"t(1/2) = 0.693/k = 0.693/{k}.", " s")

for rate, conc in [(0.02, 0.1), (0.04, 0.2), (0.1, 0.5)]:
    order1 = rate / conc
    _num("Chemical Kinetics", "MEDIUM",
         f"For a first-order reaction the rate is {rate} mol/L/s when the concentration "
         f"is {conc} mol/L. The rate constant is",
         round(order1, 3), [round(rate * conc, 3), round(rate, 3), round(order1 * 2, 3)],
         f"Rate = k[A], so k = rate/[A] = {rate}/{conc}.", " s^-1")

# ---------------------------------------------------------------------------
# Thermodynamics (chemistry)
# ---------------------------------------------------------------------------
for dH, T, dS in [(-100, 300, -0.1), (-200, 400, -0.2), (50, 300, 0.2), (-92, 298, -0.198)]:
    dG = dH - T * dS
    _num("Thermodynamics", "HARD",
         f"For a reaction, dH = {dH} kJ/mol, dS = {dS} kJ/mol/K and T = {T} K. The "
         f"standard Gibbs energy change is",
         round(dG, 2), [round(dH + T * dS, 2), round(-dG, 2), round(dH * T * dS, 2)],
         f"dG = dH - T dS = {dH} - ({T})({dS}).", " kJ/mol")

# ---------------------------------------------------------------------------
# Electrochemistry
# ---------------------------------------------------------------------------
FARADAY = 96500
for I, t in [(2, 965), (1, 1930), (5, 193), (0.5, 3860)]:
    eqv = I * t / FARADAY  # equivalents = charge / Faraday
    _num("Electrochemistry", "HARD",
         f"The number of equivalents of a substance deposited when a current of {I} A "
         f"flows for {t} s is (F = 96500 C/mol)",
         round(eqv, 4), [round(eqv * 2, 4), round(eqv / 2, 4), round(I * t, 4)],
         f"Equivalents = I t / F = {I} x {t} / 96500.")

for E0, n, conc in [(1.1, 2, 0.1), (0.34, 2, 0.01), (0.76, 2, 0.05)]:
    _num("Electrochemistry", "HARD",
         f"For a cell with standard emf {E0} V, n = {n} and reaction quotient Q = {conc}, "
         f"the cell emf at 298 K is (Nernst equation, 2.303RT/F = 0.059 V)",
         round(E0 - 0.059 / n * math.log10(conc), 4),
         [round(E0 + 0.059 / n * math.log10(conc), 4), round(E0 / n, 4), round(E0, 4)],
         "E = E0 - (0.059/n) log Q at 298 K.")

# ---------------------------------------------------------------------------
# Solutions - colligative properties
# ---------------------------------------------------------------------------
for Kf, m in [(1.86, 1), (1.86, 0.5), (5.12, 0.1), (1.86, 2)]:
    dT = Kf * m
    _num("Solutions", "HARD",
         f"The depression in freezing point of a solution of molality {m} mol/kg in water "
         f"(Kf = {Kf} K kg/mol) is",
         round(dT, 3), [round(dT / 2, 3), round(dT * 2, 3), round(-dT, 3)],
         f"dTf = Kf x m = {Kf} x {m}.", " K")

# ---------------------------------------------------------------------------
# Structure of Atom - Bohr / quantum numbers (curated)
# ---------------------------------------------------------------------------
for n in [1, 2, 3]:
    _num("Structure of Atom", "MEDIUM",
         f"The maximum number of electrons that can be accommodated in the shell with "
         f"principal quantum number n = {n} is",
         2 * n * n, [2 * n * n + 2, 2 * n * n - 2, n * n], f"Maximum electrons = 2n^2 = 2 x {n}^2.")

for l, label in [(0, "s"), (1, "p"), (2, "d")]:
    _num("Structure of Atom", "EASY",
         f"The number of orbitals in the subshell with azimuthal quantum number l = {l} "
         f"({label}-subshell) is",
         2 * l + 1, [2 * l + 2, 2 * l + 3, 2 * l + 4], f"Number of orbitals = 2l + 1 = 2({l}) + 1.")

# ---------------------------------------------------------------------------
# Chemical Bonding - bond order / hybridization (curated)
# ---------------------------------------------------------------------------
for species, order in [("O2", 2), ("N2", 3), ("O2^-", 1.5), ("O2^+", 2.5),
                       ("B2", 1), ("C2", 2), ("NO", 2.5)]:
    _num("Chemical Bonding", "HARD",
         f"According to molecular orbital theory, the bond order of {species} is",
         order, [order + 0.5, order - 0.5, order + 1],
         f"Bond order = (Nb - Na)/2; for {species} this gives {order}.")

for mol, hyb in [("CH4", "sp3"), ("BF3", "sp2"), ("BeCl2", "sp"), ("NH3", "sp3"),
                 ("H2O", "sp3"), ("PCl5", "sp3d"), ("SF6", "sp3d2"), ("C2H4", "sp2"),
                 ("C2H2", "sp"), ("XeF4", "sp3d2")]:
    _wrong = [h for h in ["sp", "sp2", "sp3", "sp3d", "sp3d2"] if h != hyb][:3]
    GEN.append(q("Chemical Bonding", "MEDIUM",
                 f"The hybridization of the central atom in {mol} is",
                 [hyb] + _wrong, 0,
                 f"The steric number (bond pairs + lone pairs) around the central atom "
                 f"in {mol} gives {hyb} hybridization."))
for mol, shape in [("CH4", "tetrahedral"), ("NH3", "trigonal pyramidal"),
                   ("H2O", "bent"), ("BF3", "trigonal planar"),
                   ("PCl5", "trigonal bipyramidal"), ("SF6", "octahedral"),
                   ("C2H4", "trigonal planar"), ("BeCl2", "linear")]:
    _wrong = [s for s in ["tetrahedral", "trigonal pyramidal", "bent", "trigonal planar",
                          "trigonal bipyramidal", "octahedral", "linear", "square planar"]
              if s != shape][:3]
    GEN.append(q("Chemical Bonding", "MEDIUM",
                 f"According to VSEPR theory, the shape of {mol} is",
                 [shape] + _wrong, 0,
                 f"The arrangement of electron pairs about the central atom in {mol} "
                 f"gives a {shape} geometry."))

# ---------------------------------------------------------------------------
# Redox reactions - oxidation number (curated)
# ---------------------------------------------------------------------------
for species, elem, ox in [("KMnO4", "Mn", 7), ("K2Cr2O7", "Cr", 6),
                          ("H2SO4", "S", 6), ("HNO3", "N", 5), ("H2O2", "O", -1),
                          ("Na2S2O3", "S", 2), ("KClO4", "Cl", 7), ("H2S", "S", -2)]:
    _num("Redox Reactions", "MEDIUM",
         f"The oxidation number of {elem} in {species} is",
         ox, [ox + 2, ox - 2, ox + 1] if ox >= 0 else [ox - 1, ox + 1, ox + 2],
         f"Applying the electronegativity/charge rules to {species} gives the "
         f"oxidation number of {elem} as {ox}.")

# ---------------------------------------------------------------------------
# Periodic properties (curated)
# ---------------------------------------------------------------------------
for elem, ie in [("Na", "496"), ("Mg", "738"), ("Al", "577"), ("Si", "786")]:
    _num("Classification of Elements and Periodicity", "MEDIUM",
         f"The first ionization enthalpy of {elem} (in kJ/mol) is closest to",
         ie, [str(int(ie) + 200), str(max(int(ie) - 300, 100)), str(int(ie) + 500)],
         f"Across a period the first ionization enthalpy generally rises, placing "
         f"{elem} near {ie} kJ/mol.")

# ---------------------------------------------------------------------------
# p-Block / d-Block / Coordination (curated)
# ---------------------------------------------------------------------------
for complex_, cn in [("[Co(NH3)6]3+", 6), ("[Ni(CN)4]2-", 4), ("[Fe(CN)6]4-", 6),
                     ("[Cu(NH3)4]2+", 4), ("[PtCl4]2-", 4), ("[Cr(H2O)6]3+", 6)]:
    _num("Coordination Compounds", "MEDIUM",
         f"The coordination number of the central metal ion in {complex_} is",
         cn, [cn - 2, cn + 2, cn - 4 if cn > 4 else cn + 4],
         f"Counting the ligands directly bonded to the central ion in {complex_} "
         f"gives a coordination number of {cn}.")

# ---------------------------------------------------------------------------
# Organic chemistry - functional groups / reagents (curated)
# ---------------------------------------------------------------------------
for name, group in [("ethanol", "-OH"), ("ethanal", "-CHO"), ("propanone", "-CO-"),
                    ("ethanoic acid", "-COOH"), ("methylamine", "-NH2"),
                    ("nitroethane", "-NO2"), ("chloroethane", "-Cl")]:
    _wrong = [g for g in ["-OH", "-CHO", "-CO-", "-COOH", "-NH2", "-NO2", "-Cl"] if g != group][:3]
    GEN.append(q("Organic Chemistry", "EASY",
                 f"The functional group present in {name} is",
                 [group] + _wrong, 0,
                 f"{name} contains the {group} functional group."))

GEN.append(q("Organic Chemistry", "MEDIUM",
             "Which of the following is the correct IUPAC name of CH3-CH2-CH2-CHO?",
             ["Butanal", "Butan-1-ol", "Butanone", "Butanoic acid"], 0,
             "A four-carbon chain ending in an aldehyde (-CHO) is butanal."))
GEN.append(q("Organic Chemistry", "MEDIUM",
             "Which of the following compounds gives a positive Tollens' test?",
             ["Acetaldehyde", "Acetone", "Benzene", "Diethyl ether"], 0,
             "Tollens' reagent oxidises aldehydes such as acetaldehyde, giving a silver mirror."))
GEN.append(q("Organic Chemistry", "HARD",
             "Which of the following is the correct order of basic strength in aqueous "
             "solution?",
             ["(CH3)2NH > CH3NH2 > NH3", "NH3 > CH3NH2 > (CH3)2NH",
              "CH3NH2 > (CH3)2NH > NH3", "NH3 > (CH3)2NH > CH3NH2"], 0,
             "In aqueous solution the +I effect of methyl groups makes (CH3)2NH the "
             "strongest base in this series, followed by CH3NH2 and then NH3."))
GEN.append(q("Organic Chemistry", "HARD",
             "Which of the following compounds will undergo an SN1 reaction most readily?",
             ["tert-Butyl chloride", "n-Butyl chloride", "1-Chlorobutane",
              "Chloromethane"], 0,
             "SN1 reactions are favoured by tertiary alkyl halides because the "
             "intermediate tertiary carbocation is the most stable."))
GEN.append(q("Biomolecules", "MEDIUM", "Which of the following is a reducing sugar?",
             ["Glucose", "Sucrose", "Starch", "Cellulose"], 0,
             "Glucose has a free aldehyde (hemiacetal) group and therefore reduces "
             "Tollens'/Fehling's reagent; sucrose is non-reducing."))
GEN.append(q("Polymers", "EASY", "Nylon-6,6 is a",
             ["polyamide", "polyester", "polyolefin", "polycarbonate"], 0,
             "Nylon-6,6 is formed by the condensation of hexamethylenediamine and "
             "adipic acid, giving amide (-CO-NH-) linkages."))


QUESTIONS = merge(CORE, GEN)
