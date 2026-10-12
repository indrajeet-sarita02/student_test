"""NEET UG (Advanced Level) - Set 01 - Chemistry: 45 questions."""

from __future__ import annotations

from .common import q

QUESTIONS = [
    # --- Some Basic Concepts of Chemistry ----------------------------------
    q("Some Basic Concepts of Chemistry", "EASY",
      "The number of moles present in 44 g of carbon dioxide (molar mass 44 g "
      "mol^-1) is",
      ["0.5", "1", "2", "4"], 1,
      "Moles = mass/molar mass = 44/44 = 1 mol."),
    q("Some Basic Concepts of Chemistry", "MEDIUM",
      "The mass of one molecule of water is approximately "
      "(N_A = 6.022 x 10^23 mol^-1)",
      ["1.8 x 10^-23 g", "3.0 x 10^-23 g", "6.0 x 10^-23 g", "9.0 x 10^-23 g"], 1,
      "Mass of one molecule = 18 / (6.022 x 10^23) = 2.99 x 10^-23 g, about "
      "3.0 x 10^-23 g."),
    q("Some Basic Concepts of Chemistry", "HARD",
      "A compound contains 40% carbon, 6.7% hydrogen and 53.3% oxygen by mass. "
      "Its empirical formula is",
      ["C2H4O2", "CHO", "CH4O", "CH2O"], 3,
      "Mole ratio C:H:O = 40/12 : 6.7/1 : 53.3/16 = 3.33 : 6.7 : 3.33, i.e. "
      "1 : 2 : 1, giving the empirical formula CH2O."),

    # --- Structure of Atom -------------------------------------------------
    q("Structure of Atom", "EASY",
      "The number of protons in an atom is equal to its",
      ["number of neutrons", "mass number", "number of nucleons",
       "atomic number"], 3,
      "The atomic number Z equals the number of protons in the nucleus."),
    q("Structure of Atom", "MEDIUM",
      "The maximum number of electrons that can be accommodated in a subshell "
      "for which the azimuthal quantum number l = 2 is",
      ["10", "6", "8", "14"], 0,
      "For l = 2 (d subshell) there are (2l + 1) = 5 orbitals, each holding 2 "
      "electrons, so the maximum is 10."),
    q("Structure of Atom", "HARD",
      "The number of unpaired electrons in an Fe^3+ ion (Z = 26) is",
      ["3", "4", "6", "5"], 3,
      "Fe is [Ar]3d6 4s2; Fe^3+ is [Ar]3d5, and a half-filled d^5 set has 5 "
      "unpaired electrons."),

    # --- Classification of Elements and Periodicity ------------------------
    q("Classification of Elements and Periodicity", "EASY",
      "On moving from left to right across a period, the atomic radius "
      "generally",
      ["increases", "decreases", "remains the same",
       "first increases then decreases"], 1,
      "The increasing nuclear charge pulls the electrons closer, so the atomic "
      "radius decreases across a period."),
    q("Classification of Elements and Periodicity", "MEDIUM",
      "The element with the highest electronegativity is",
      ["oxygen", "chlorine", "fluorine", "nitrogen"], 2,
      "Fluorine has the highest electronegativity (3.98 on the Pauling scale)."),
    q("Classification of Elements and Periodicity", "HARD",
      "The correct order of the first ionisation enthalpy of carbon, nitrogen "
      "and oxygen is",
      ["C > N > O", "N > O > C", "O > N > C", "C > O > N"], 1,
      "Nitrogen has a half-filled 2p^3 configuration, giving it the highest "
      "first ionisation enthalpy: N > O > C."),

    # --- Chemical Bonding --------------------------------------------------
    q("Chemical Bonding", "EASY",
      "The bond formed by the sharing of electrons between two atoms is called "
      "a",
      ["ionic bond", "metallic bond", "hydrogen bond", "covalent bond"], 3,
      "A covalent bond is formed by the mutual sharing of electron pairs "
      "between atoms."),
    q("Chemical Bonding", "MEDIUM",
      "The shape of the methane (CH4) molecule is",
      ["square planar", "trigonal planar", "tetrahedral", "linear"], 2,
      "Four bonding pairs around carbon with no lone pairs give a tetrahedral "
      "shape with bond angles of 109.5 degrees."),
    q("Chemical Bonding", "HARD",
      "The number of sigma and pi bonds in a benzene molecule (C6H6) is",
      ["6 sigma and 3 pi", "6 sigma and 6 pi", "12 sigma and 3 pi",
       "12 sigma and 6 pi"], 2,
      "There are 6 C-H sigma bonds, 6 C-C sigma bonds in the ring and 3 pi "
      "bonds, i.e. 12 sigma and 3 pi bonds."),

    # --- Thermodynamics ----------------------------------------------------
    q("Thermodynamics", "EASY",
      "The SI unit of enthalpy is",
      ["joule", "calorie", "kelvin", "pascal"], 0,
      "Enthalpy is a form of energy, so its SI unit is the joule (J)."),
    q("Thermodynamics", "MEDIUM",
      "For an exothermic reaction at constant pressure, the change in enthalpy "
      "(ΔH) is",
      ["negative", "positive", "zero", "unpredictable"], 0,
      "In an exothermic reaction heat is released, so ΔH is negative."),
    q("Thermodynamics", "HARD",
      "The standard enthalpy of formation of an element in its most stable "
      "standard state is",
      ["always positive", "zero", "always negative", "equal to its atomic mass"], 1,
      "By convention the standard enthalpy of formation of an element in its "
      "standard state is taken as zero."),

    # --- Equilibrium -------------------------------------------------------
    q("Equilibrium", "EASY",
      "According to Le Chatelier's principle, an increase in pressure shifts a "
      "gaseous equilibrium towards",
      ["the side with more moles of gas", "the reactant side always",
       "the side with fewer moles of gas", "no change at all"], 2,
      "Raising the pressure favours the direction that reduces the number of "
      "gas molecules, i.e. the side with fewer moles of gas."),
    q("Equilibrium", "MEDIUM",
      "The pH of a 0.01 M aqueous HCl solution is",
      ["1", "2", "12", "3"], 1,
      "HCl is a strong acid, so [H+] = 0.01 M = 10^-2 M and pH = 2."),
    q("Equilibrium", "HARD",
      "For the sparingly soluble salt Ag2CrO4, the solubility product "
      "expression is",
      ["[Ag+]^2 [CrO4^2-]", "[Ag+] [CrO4^2-]", "[Ag+] [CrO4^2-]^2",
       "[Ag+]^2 [CrO4^2-]^2"], 0,
      "Ag2CrO4 dissolves to give 2 Ag+ and 1 CrO4^2-, so "
      "Ksp = [Ag+]^2 [CrO4^2-]."),

    # --- Redox Reactions ---------------------------------------------------
    q("Redox Reactions", "EASY",
      "Oxidation, in terms of electrons, means",
      ["loss of protons", "gain of electrons", "loss of electrons",
       "gain of neutrons"], 2,
      "Oxidation is the loss of electrons; reduction is the gain of electrons "
      "(OIL RIG)."),
    q("Redox Reactions", "MEDIUM",
      "The oxidation state of chromium in K2Cr2O7 is",
      ["+6", "+3", "+7", "+2"], 0,
      "2(+1) + 2x + 7(-2) = 0 gives x = +6."),

    # --- Solutions ---------------------------------------------------------
    q("Solutions", "EASY",
      "The number of moles of solute dissolved per litre of solution is called",
      ["molality", "molarity", "normality", "mole fraction"], 1,
      "Molarity (M) is the number of moles of solute per litre of solution."),
    q("Solutions", "MEDIUM",
      "Colligative properties of a dilute solution depend on",
      ["the nature of the solute", "the nature of the solvent",
       "the size of the solute particles", "the number of solute particles"], 3,
      "Colligative properties depend only on the number of solute particles, "
      "not on their chemical nature."),
    q("Solutions", "HARD",
      "The van't Hoff factor (i) for K2SO4 in dilute aqueous solution, assuming "
      "complete dissociation, is",
      ["2", "3", "4", "1"], 1,
      "K2SO4 dissociates into 2 K+ and 1 SO4^2-, giving i = 3 for complete "
      "dissociation."),

    # --- Electrochemistry --------------------------------------------------
    q("Electrochemistry", "EASY",
      "In an electrochemical cell, oxidation takes place at the",
      ["cathode", "salt bridge", "anode", "voltmeter"], 2,
      "Oxidation (loss of electrons) always occurs at the anode."),
    q("Electrochemistry", "MEDIUM",
      "The SI unit of molar conductivity is",
      ["S m^-1", "S m^2 mol^-1", "S m mol^-1", "S^-1 m^2 mol^-1"], 1,
      "Molar conductivity = conductivity/concentration, giving the SI unit "
      "S m^2 mol^-1."),
    q("Electrochemistry", "HARD",
      "One faraday of electric charge is equal to",
      ["9650 C", "965 C", "96500 C", "1 C"], 2,
      "One faraday equals the charge on one mole of electrons, about "
      "96500 C mol^-1."),

    # --- Chemical Kinetics -------------------------------------------------
    q("Chemical Kinetics", "EASY",
      "The unit of the rate constant of a first-order reaction is",
      ["mol L^-1 s^-1", "s^-1", "L mol^-1 s^-1", "mol^-1 s^-1"], 1,
      "For a first-order reaction rate = k[A]; matching units gives k in s^-1."),
    q("Chemical Kinetics", "MEDIUM",
      "The half-life of a first-order reaction is",
      ["independent of initial concentration",
       "directly proportional to initial concentration",
       "inversely proportional to initial concentration",
       "proportional to the square of initial concentration"], 0,
      "For a first-order reaction t(1/2) = 0.693/k, which does not contain the "
      "initial concentration."),
    q("Chemical Kinetics", "HARD",
      "For a certain reaction, doubling the concentration of A doubles the "
      "rate. The order of the reaction with respect to A is",
      ["zero", "first", "second", "third"], 1,
      "Rate doubling when [A] doubles means rate ∝ [A]^1, so the order with "
      "respect to A is one."),

    # --- Surface Chemistry -------------------------------------------------
    q("Surface Chemistry", "EASY",
      "Which of the following is a characteristic of physical adsorption?",
      ["It is irreversible", "It is reversible",
       "It is highly specific", "It involves strong chemical bonds"], 1,
      "Physical adsorption arises from weak van der Waals forces, so it is "
      "reversible and not specific."),

    # --- p-Block Elements --------------------------------------------------
    q("p-Block Elements (Group 15)", "EASY",
      "The most electronegative element among the group 15 elements is",
      ["phosphorus", "arsenic", "nitrogen", "bismuth"], 2,
      "Electronegativity decreases down group 15; nitrogen is the most "
      "electronegative of them."),
    q("p-Block Elements (Group 16)", "MEDIUM",
      "The hydride of group 16 with the highest boiling point is",
      ["H2S", "H2O", "H2Se", "H2Te"], 1,
      "Water has extensive hydrogen bonding, giving it a much higher boiling "
      "point than the other group 16 hydrides."),
    q("p-Block Elements (Group 15)", "HARD",
      "The number of P-O-P bridges present in a molecule of P4O10 is",
      ["4", "10", "12", "6"], 3,
      "P4O10 contains 6 P-O-P bridges linking the four phosphorus atoms."),

    # --- d-Block Elements --------------------------------------------------
    q("d-Block Elements", "EASY",
      "Which of the following is a transition element?",
      ["Fe (Z = 26)", "Ca (Z = 20)", "Zn (Z = 30)", "Na (Z = 11)"], 0,
      "A transition element has a partially filled d subshell in a common "
      "oxidation state; Fe qualifies, whereas Ca, Zn and Na do not."),
    q("d-Block Elements", "MEDIUM",
      "The electronic configuration of copper (Z = 29) is",
      ["[Ar]3d9 4s2", "[Ar]3d10 4s2", "[Ar]3d8 4s2", "[Ar]3d10 4s1"], 3,
      "The fully filled 3d10 4s1 arrangement is more stable for copper, so "
      "Cu is [Ar]3d10 4s1."),

    # --- Coordination Compounds --------------------------------------------
    q("Coordination Compounds", "MEDIUM",
      "The IUPAC name of K4[Fe(CN)6] is",
      ["potassium hexacyanidoferrate(III)", "potassium ferrocyanide(III)",
       "potassium hexacyanidoferrate(II)", "potassium hexacyanoiron(II)"], 2,
      "The complex anion [Fe(CN)6]^4- contains Fe in the +2 state, so the name "
      "is potassium hexacyanidoferrate(II)."),
    q("Coordination Compounds", "HARD",
      "The geometry of the complex ion [Ni(CN)4]^2- is",
      ["tetrahedral", "linear", "octahedral", "square planar"], 3,
      "CN^- is a strong-field ligand; Ni^2+ (d8) undergoes dsp2 hybridisation, "
      "giving a square planar geometry."),

    # --- Haloalkanes and Haloarenes ----------------------------------------
    q("Haloalkanes", "EASY",
      "The bond between carbon and chlorine in CH3Cl is best described as",
      ["polar covalent", "ionic", "non-polar covalent", "coordinate"], 0,
      "The electronegativity difference makes the C-Cl bond a polar covalent "
      "bond."),
    q("Haloalkanes", "MEDIUM",
      "The correct order of reactivity towards the SN2 reaction is",
      ["tertiary > secondary > primary > methyl",
       "primary > methyl > secondary > tertiary",
       "methyl > primary > secondary > tertiary",
       "secondary > tertiary > primary > methyl"], 2,
      "SN2 reactivity decreases with increasing steric hindrance, so "
      "methyl > primary > secondary > tertiary."),
    q("Haloalkanes", "HARD",
      "Which of the following undergoes an SN1 reaction most readily?",
      ["CH3Br", "CH3CH2Br", "(CH3)3CBr", "(CH3)2CHBr"], 2,
      "SN1 proceeds through a carbocation; the tertiary carbonium ion from "
      "(CH3)3CBr is the most stable, so it reacts fastest."),

    # --- Alcohols, Phenols and Ethers --------------------------------------
    q("Alcohols and Phenols", "EASY",
      "Ethanol reacts with metallic sodium to give",
      ["sodium ethanoate and water", "sodium ethoxide and hydrogen",
       "ethene and hydrogen", "ethanol and sodium hydroxide"], 1,
      "2 C2H5OH + 2 Na -> 2 C2H5ONa + H2, giving sodium ethoxide and hydrogen."),
    q("Alcohols and Phenols", "MEDIUM",
      "Which of the following is more acidic?",
      ["Ethanol", "Both are equally acidic", "Neither is acidic", "Phenol"], 3,
      "The phenoxide ion is stabilised by resonance, so phenol is more acidic "
      "than ethanol."),

    # --- Aldehydes, Ketones and Carboxylic Acids ---------------------------
    q("Aldehydes and Ketones", "EASY",
      "The IUPAC name of CH3CHO is",
      ["methanal", "propanal", "ethanal", "ethanone"], 2,
      "CH3CHO has two carbon atoms and an aldehyde group, so it is ethanal."),

    # --- Amines ------------------------------------------------------------
    q("Amines", "MEDIUM",
      "The strongest base in aqueous solution among the following is",
      ["NH3", "CH3NH2", "C6H5NH2", "(CH3)2NH"], 3,
      "The +I effect of two methyl groups and hydration make dimethylamine a "
      "stronger base than the others; aniline is weakest due to resonance."),

    # --- Biomolecules ------------------------------------------------------
    q("Biomolecules", "EASY",
      "The building blocks (monomers) of proteins are",
      ["amino acids", "glucose units", "fatty acids", "nucleotides"], 0,
      "Proteins are polymers built from amino acid monomers linked by peptide "
      "bonds."),
]
