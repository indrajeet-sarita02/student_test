"""NEET UG (Advanced Level) - Chemistry: 45 questions."""

from __future__ import annotations

from .common import q

QUESTIONS = [
    # --- Some Basic Concepts of Chemistry ---------------------------------
    q("Some Basic Concepts of Chemistry", "EASY",
      "The number of moles of carbon dioxide in 22 g of the gas (molar mass "
      "44 g/mol) is",
      ["0.5", "1", "2", "0.25"], 0,
      "Moles = mass/molar mass = 22/44 = 0.5 mol."),
    q("Some Basic Concepts of Chemistry", "MEDIUM",
      "The empirical formula of a compound is CH2O and its molecular mass is "
      "180. Its molecular formula is",
      ["C6H12O6", "C3H6O3", "C2H4O2", "C5H10O5"], 0,
      "n = 180/30 = 6, so the molecular formula is (CH2O)6 = C6H12O6."),

    # --- Structure of Atom -------------------------------------------------
    q("Structure of Atom", "EASY",
      "The total number of orbitals in the shell for which the principal "
      "quantum number n = 3 is",
      ["9", "3", "5", "18"], 0,
      "For n = 3 there are one 3s, three 3p and five 3d orbitals, giving 9 "
      "orbitals (18 electrons)."),
    q("Structure of Atom", "MEDIUM",
      "The maximum number of electrons that can occupy the subshell with n = 4 "
      "and l = 2 is",
      ["10", "6", "2", "14"], 0,
      "For l = 2 (d subshell) there are five orbitals, and each holds two "
      "electrons, giving 10."),
    q("Structure of Atom", "HARD",
      "According to the Heisenberg uncertainty principle, the product of the "
      "uncertainties in position and momentum (dx * dp) is",
      ["greater than or equal to h/4pi", "equal to zero",
       "less than h/4pi", "exactly h/2pi"], 0,
      "Heisenberg's relation is dx * dp >= h/4pi."),
    q("Structure of Atom", "MEDIUM",
      "Which of the following sets of quantum numbers is not permitted?",
      ["n = 2, l = 2, m = 0", "n = 2, l = 1, m = 0",
       "n = 3, l = 2, m = -2", "n = 1, l = 0, m = 0"], 0,
      "The azimuthal quantum number l can range from 0 to n - 1; for n = 2, l "
      "cannot be 2."),

    # --- Classification of Elements and Periodicity -----------------------
    q("Classification of Elements and Periodicity", "MEDIUM",
      "The first ionisation enthalpy of nitrogen is greater than that of oxygen "
      "because",
      ["nitrogen has a stable half-filled 2p configuration",
       "nitrogen is smaller in size than oxygen",
       "oxygen has a higher nuclear charge",
       "nitrogen has a completely filled 2p subshell"], 0,
      "The half-filled 2p^3 configuration of nitrogen is extra stable, so "
      "removing an electron from nitrogen is harder."),
    q("Classification of Elements and Periodicity", "HARD",
      "The magnitude of the electron gain enthalpy of chlorine is greater than "
      "that of fluorine because",
      ["the compact 2p subshell of fluorine experiences strong electron-electron "
       "repulsion",
       "chlorine is more electronegative than fluorine",
       "fluorine has a larger atomic radius",
       "chlorine has a lower nuclear charge"], 0,
      "Fluorine's very small 2p subshell causes strong inter-electronic "
      "repulsion, so the incoming electron is less strongly bound than in "
      "chlorine."),

    # --- Chemical Bonding --------------------------------------------------
    q("Chemical Bonding and Molecular Structure", "EASY",
      "The hybridisation of carbon in ethyne (C2H2) is",
      ["sp", "sp2", "sp3", "sp3d"], 0,
      "Each carbon forms two sigma and two pi bonds (steric number 2), so the "
      "hybridisation is sp and the molecule is linear."),
    q("Chemical Bonding and Molecular Structure", "HARD",
      "The bond order of the peroxide ion (O2^2-) is",
      ["1", "2", "1.5", "2.5"], 0,
      "O2^2- has 18 electrons; its molecular orbital configuration gives "
      "bond order = (Nb - Na)/2 = (10 - 8)/2 = 1."),
    q("Chemical Bonding and Molecular Structure", "EASY",
      "According to VSEPR theory, the shape of the water molecule is",
      ["bent (V-shaped)", "linear", "trigonal planar", "tetrahedral"], 0,
      "Oxygen has two bond pairs and two lone pairs; the electron-pair geometry "
      "is tetrahedral and the molecular shape is bent."),
    q("Chemical Bonding and Molecular Structure", "EASY",
      "The dipole moment of carbon dioxide is zero because",
      ["the molecule is linear and the two bond dipoles cancel",
       "the C=O bonds are non-polar",
       "the molecule has a bent structure",
       "oxygen is less electronegative than carbon"], 0,
      "CO2 is linear (O=C=O); the two equal and opposite bond dipoles cancel, "
      "giving zero resultant dipole moment."),

    # --- Thermodynamics ----------------------------------------------------
    q("Thermodynamics", "MEDIUM",
      "For a chemical reaction, the relation between the enthalpy change and "
      "the internal energy change is",
      ["dH = dU + dng*R*T", "dH = dU - dng*R*T", "dH = dU",
       "dU = dH + dng*R*T"], 0,
      "dH = dU + dng*R*T, where dng is the change in the number of moles of gas."),
    q("Thermodynamics", "MEDIUM",
      "For a spontaneous process at constant temperature and pressure",
      ["dG is negative", "dG is positive", "dG is zero",
       "dH is always negative"], 0,
      "Spontaneity at constant T and P requires dG = dH - T*dS < 0."),
    q("Thermodynamics", "EASY",
      "Hess's law of constant heat summation is a consequence of the",
      ["first law of thermodynamics", "second law of thermodynamics",
       "third law of thermodynamics", "law of mass action"], 0,
      "Because enthalpy is a state function (first law), the total enthalpy "
      "change is independent of the path."),

    # --- Equilibrium -------------------------------------------------------
    q("Equilibrium", "EASY",
      "For an exothermic reversible reaction, increasing the temperature",
      ["shifts the equilibrium in the backward direction",
       "shifts the equilibrium in the forward direction",
       "does not change the position of equilibrium",
       "increases the value of Kc"], 0,
      "By Le Chatelier's principle the added heat is absorbed by the "
      "endothermic reverse reaction, shifting equilibrium backwards."),
    q("Equilibrium", "HARD",
      "For the reaction N2(g) + 3H2(g) <-> 2NH3(g), the relation between Kp and "
      "Kc is",
      ["Kp = Kc (RT)^-2", "Kp = Kc (RT)^2", "Kp = Kc (RT)^-4", "Kp = Kc"], 0,
      "dn = 2 - 4 = -2, and Kp = Kc (RT)^dn = Kc (RT)^-2."),

    # --- Ionic Equilibrium -------------------------------------------------
    q("Ionic Equilibrium", "EASY",
      "The pH of a 0.001 M hydrochloric acid solution is",
      ["3", "1", "11", "2"], 0,
      "[H+] = 10^-3 M, so pH = -log(10^-3) = 3."),
    q("Ionic Equilibrium", "HARD",
      "The pH of an acidic buffer made from acetic acid and sodium acetate is "
      "given by",
      ["pH = pKa + log([salt]/[acid])", "pH = pKa - log([salt]/[acid])",
       "pH = pKb + log([salt]/[acid])", "pH = 14 - pKa"], 0,
      "The Henderson-Hasselbalch equation for an acidic buffer is "
      "pH = pKa + log([salt]/[acid])."),

    # --- Redox Reactions ---------------------------------------------------
    q("Redox Reactions", "EASY",
      "The oxidation number of chromium in K2Cr2O7 is",
      ["+6", "+7", "+3", "+2"], 0,
      "2(+1) + 2x + 7(-2) = 0, giving 2x = 12 and x = +6."),
    q("Redox Reactions", "EASY",
      "The oxidation number of manganese in KMnO4 is",
      ["+7", "+6", "+4", "+2"], 0,
      "+1 + x + 4(-2) = 0, giving x = +7."),

    # --- Solutions ---------------------------------------------------------
    q("Solutions", "EASY",
      "The depression in the freezing point of a dilute solution is given by",
      ["dTf = Kf * m", "dTf = Kb * m", "dTf = Kf/m", "dTf = Kf * M"], 0,
      "dTf = i*Kf*m, where m is molality and Kf the molal depression constant."),
    q("Solutions", "MEDIUM",
      "The van't Hoff factor i for an aqueous solution of NaCl that is "
      "completely dissociated is",
      ["2", "1", "3", "0.5"], 0,
      "NaCl -> Na+ + Cl-, giving two particles per formula unit, so i = 2."),
    q("Solutions", "HARD",
      "Which of the following is true for an ideal solution?",
      ["It obeys Raoult's law over the entire range of composition",
       "It shows a positive deviation from Raoult's law",
       "It shows a negative deviation from Raoult's law",
       "Its enthalpy of mixing is large and positive"], 0,
      "An ideal solution obeys Raoult's law at all concentrations and has "
      "dH_mix = 0 and dV_mix = 0."),

    # --- Electrochemistry --------------------------------------------------
    q("Electrochemistry", "EASY",
      "The standard electrode potential of the standard hydrogen electrode is "
      "taken as",
      ["0.00 V", "1.00 V", "-0.76 V", "+0.34 V"], 0,
      "The standard hydrogen electrode is the reference electrode and is "
      "assigned a potential of exactly 0.00 V at 298 K."),
    q("Electrochemistry", "MEDIUM",
      "The quantity of electricity required to deposit one gram-equivalent of a "
      "substance during electrolysis is",
      ["96500 C", "48250 C", "193000 C", "1 C"], 0,
      "One Faraday, about 96500 C, liberates one gram-equivalent."),
    q("Electrochemistry", "HARD",
      "For the half-cell Mn+ + n e- -> M at 298 K, the Nernst equation is",
      ["E = E0 - (0.0591/n) log(1/[Mn+])",
       "E = E0 + (0.0591/n) log(1/[Mn+])",
       "E = E0 - (0.0591*n) log[Mn+]",
       "E = E0 - (0.0591/n) log[Mn+]"], 0,
      "E = E0 - (0.0591/n) log([M]/[Mn+]) with [M] = 1, i.e. "
      "E = E0 - (0.0591/n) log(1/[Mn+])."),

    # --- Chemical Kinetics -------------------------------------------------
    q("Chemical Kinetics", "MEDIUM",
      "For a first-order reaction, the half-life",
      ["is independent of the initial concentration of the reactant",
       "is directly proportional to the initial concentration",
       "is inversely proportional to the initial concentration",
       "doubles as the reaction proceeds"], 0,
      "For a first-order reaction t1/2 = 0.693/k, independent of the initial "
      "concentration."),
    q("Chemical Kinetics", "EASY",
      "The unit of the rate constant for a first-order reaction is",
      ["s^-1", "mol L^-1 s^-1", "L mol^-1 s^-1", "mol^2 L^-2 s^-1"], 0,
      "For a first-order reaction rate = k[A], so k has units of s^-1."),
    q("Chemical Kinetics", "HARD",
      "According to the Arrhenius equation, a rise in temperature increases the "
      "rate of a reaction mainly because",
      ["the fraction of molecules with energy greater than the activation "
       "energy increases",
       "the activation energy decreases",
       "the collision frequency decreases",
       "the order of the reaction changes"], 0,
      "k = A exp(-Ea/RT); a small rise in T sharply increases the fraction of "
      "molecules possessing energy >= Ea."),

    # --- p-Block Elements --------------------------------------------------
    q("The p-Block Elements", "MEDIUM",
      "The decreasing stability of the +5 oxidation state down group 15 "
      "(relative to +3) is attributed to the",
      ["inert pair effect", "lanthanoid contraction", "diagonal relationship",
       "resonance effect"], 0,
      "The ns^2 electron pair becomes increasingly reluctant to take part in "
      "bonding down the group (inert pair effect), stabilising +3."),
    q("The p-Block Elements", "HARD",
      "Complete hydrolysis of XeF6 gives",
      ["XeO3", "XeOF4", "XeO2F2", "Xe"], 0,
      "Complete hydrolysis of xenon hexafluoride yields xenon trioxide, XeO3 "
      "(partial hydrolysis can give XeOF4)."),
    q("The p-Block Elements", "MEDIUM",
      "The ozone (O3) molecule is",
      ["bent with a bond angle of about 117 degrees", "linear",
       "trigonal planar", "tetrahedral"], 0,
      "Ozone has a bent structure because of the lone pair on the central "
      "oxygen, with an O-O-O angle near 117 degrees."),

    # --- d-Block and Coordination Compounds --------------------------------
    q("The d- and f-Block Elements", "EASY",
      "Transition elements exhibit variable oxidation states because",
      ["the energies of the (n-1)d and ns orbitals are very close",
       "they possess completely filled d orbitals",
       "they have very high ionisation energies",
       "they have only a filled ns orbital"], 0,
      "The small energy gap between (n-1)d and ns electrons lets them "
      "participate in bonding to different extents, giving variable oxidation "
      "states."),
    q("The d- and f-Block Elements", "HARD",
      "Lanthanoid contraction is mainly caused by",
      ["poor shielding of the 4f electrons",
       "poor shielding of the 5d electrons",
       "the unusually small size of the 6s orbital",
       "a constant nuclear charge across the series"], 0,
      "The 4f electrons shield the increasing nuclear charge poorly, so the "
      "effective nuclear charge rises across the series and the size "
      "contracts."),
    q("Coordination Compounds", "EASY",
      "The coordination number of the central metal ion in [Cu(NH3)4]2+ is",
      ["4", "6", "2", "3"], 0,
      "Four ammonia ligands are directly bonded to Cu2+, so the coordination "
      "number is 4."),
    q("Coordination Compounds", "HARD",
      "The spin-only magnetic moment of the low-spin complex [Fe(CN)6]3- is "
      "approximately",
      ["1.73 BM", "5.92 BM", "3.87 BM", "0 BM"], 0,
      "Fe3+ (d5) in the strong field of CN- is low spin: t2g^5 with one "
      "unpaired electron, so mu = sqrt(1(1+2)) = 1.73 BM."),
    q("Coordination Compounds", "MEDIUM",
      "The IUPAC name of [Co(NH3)5Cl]Cl2 is",
      ["pentaamminechloridocobalt(III) chloride",
       "pentaamminechloridocobalt(II) chloride",
       "pentaamminechloridocobaltate(III) chloride",
       "pentachloroamminecobalt(III) chloride"], 0,
      "Five NH3 and one Cl- surround Co(III); the complex cation is "
      "pentaamminechloridocobalt(III), balanced by two chloride ions."),

    # --- Organic Chemistry -------------------------------------------------
    q("Haloalkanes and Haloarenes", "HARD",
      "When propene reacts with HCl, the major product is",
      ["2-chloropropane", "1-chloropropane", "1,2-dichloropropane", "propane"],
      0,
      "Markovnikov's rule: H adds to the carbon bearing more hydrogens, giving "
      "the more stable secondary carbocation and hence 2-chloropropane."),
    q("Alcohols, Phenols and Ethers", "MEDIUM",
      "Phenol is more acidic than ethanol because",
      ["the phenoxide ion is stabilised by resonance",
       "the phenoxide ion is destabilised by resonance",
       "phenol has a higher molecular mass than ethanol",
       "ethanol forms hydrogen bonds"], 0,
      "The negative charge of the phenoxide ion is delocalised over the ring by "
      "resonance, stabilising it and increasing acidity."),
    q("Aldehydes, Ketones and Carboxylic Acids", "MEDIUM",
      "Tollens' reagent gives a silver mirror with",
      ["aldehydes", "ketones only", "tertiary alcohols", "ethers"], 0,
      "Aldehydes are oxidised by the ammoniacal silver nitrate of Tollens' "
      "reagent, producing a silver mirror; ketones do not respond."),
    q("Aldehydes, Ketones and Carboxylic Acids", "MEDIUM",
      "The strongest acid among the following is",
      ["CF3COOH", "CH3COOH", "CH2ClCOOH", "CHCl2COOH"], 0,
      "Three electron-withdrawing fluorine atoms strongly stabilise the "
      "carboxylate ion, making CF3COOH the strongest acid."),
    q("Amines", "MEDIUM",
      "In aqueous solution, the correct order of basic strength of the ethyl "
      "derivatives of ammonia is",
      ["(C2H5)2NH > C2H5NH2 > (C2H5)3N > NH3",
       "(C2H5)3N > (C2H5)2NH > C2H5NH2 > NH3",
       "NH3 > C2H5NH2 > (C2H5)2NH > (C2H5)3N",
       "(C2H5)2NH > (C2H5)3N > C2H5NH2 > NH3"], 3,
      "In water the basicity order for the ethylamines is "
      "(C2H5)2NH > (C2H5)3N > C2H5NH2 > NH3, owing to a balance of inductive, "
      "steric and solvation effects."),

    # --- Biomolecules and Polymers ----------------------------------------
    q("Biomolecules", "EASY",
      "Which of the following is a reducing sugar?",
      ["Glucose", "Sucrose", "Starch", "Cellulose"], 0,
      "Glucose has a free aldehydic (hemiacetal) group and reduces Tollens' and "
      "Fehling's reagents; sucrose does not."),
    q("Polymers", "EASY",
      "Nylon-6,6 is a condensation polymer of",
      ["adipic acid and hexamethylenediamine", "caprolactam",
       "ethylene glycol and terephthalic acid", "styrene and butadiene"], 0,
      "Nylon-6,6 is formed by the condensation of hexamethylenediamine with "
      "adipic acid."),
]
