"""NEET UG (Advanced Level) - Set 01 - Botany: 45 questions."""

from __future__ import annotations

from .common import q

QUESTIONS = [
    # --- Cell: Structure and Function --------------------------------------
    q("Cell: Structure and Function", "EASY",
      "Which organelle is called the 'powerhouse' of the cell?",
      ["Ribosome", "Mitochondrion", "Golgi body", "Lysosome"], 1,
      "Mitochondria carry out oxidative phosphorylation and release most of "
      "the cell's energy as ATP, so they are called the powerhouse of the "
      "cell."),
    q("Cell: Structure and Function", "MEDIUM",
      "The fluid mosaic model of the plasma membrane was proposed by",
      ["Singer and Nicolson", "Robert Hooke", "Watson and Crick",
       "Schleiden and Schwann"], 0,
      "Singer and Nicolson (1972) proposed the fluid mosaic model of the "
      "plasma membrane."),
    q("Cell: Structure and Function", "HARD",
      "Which of the following is a single-membrane-bound organelle?",
      ["Mitochondrion", "Chloroplast", "Lysosome", "Nucleus"], 2,
      "Lysosomes are bounded by a single membrane, whereas mitochondria and "
      "chloroplasts are double-membrane bound and the nucleus has a double "
      "nuclear envelope."),

    # --- Cell Cycle and Cell Division --------------------------------------
    q("Cell Cycle and Cell Division", "EASY",
      "DNA replication occurs during which phase of the cell cycle?",
      ["G1 phase", "S phase", "G2 phase", "M phase"], 1,
      "DNA is synthesised (replicated) during the S (synthesis) phase of "
      "interphase."),
    q("Cell Cycle and Cell Division", "MEDIUM",
      "Crossing over between homologous chromosomes occurs during which stage "
      "of meiosis?",
      ["Leptotene", "Zygotene", "Pachytene", "Diplotene"], 2,
      "Crossing over takes place during the pachytene stage of prophase I of "
      "meiosis."),
    q("Cell Cycle and Cell Division", "HARD",
      "The number of chromatids present in a human cell at metaphase of "
      "mitosis is",
      ["23", "46", "69", "92"], 3,
      "A human cell has 46 chromosomes; at metaphase each has two sister "
      "chromatids, so there are 46 x 2 = 92 chromatids."),

    # --- Plant Kingdom -----------------------------------------------------
    q("Plant Kingdom", "EASY",
      "Which group of plants is called the 'amphibians of the plant kingdom'?",
      ["Bryophytes", "Pteridophytes", "Gymnosperms", "Angiosperms"], 0,
      "Bryophytes need water for the movement of male gametes to the egg, so "
      "they are called amphibians of the plant kingdom."),
    q("Plant Kingdom", "MEDIUM",
      "Double fertilisation is a characteristic feature of",
      ["Gymnosperms", "Bryophytes", "Pteridophytes", "Angiosperms"], 3,
      "Double fertilisation (syngamy and triple fusion) is found only in "
      "angiosperms."),
    q("Plant Kingdom", "HARD",
      "The dominant phase in the life cycle of a fern is the",
      ["Gametophyte (haploid)", "Gametophyte (diploid)",
       "Sporophyte (diploid)", "Sporophyte (haploid)"], 2,
      "In pteridophytes such as ferns, the conspicuous and long-lived phase is "
      "the diploid sporophyte; the gametophyte is small and short-lived."),

    # --- Morphology of Flowering Plants ------------------------------------
    q("Morphology of Flowering Plants", "EASY",
      "The fleshy edible part of a mango fruit is the",
      ["Epicarp", "Mesocarp", "Endocarp", "Seed"], 1,
      "The mango is a drupe whose fleshy edible portion is the mesocarp."),
    q("Morphology of Flowering Plants", "MEDIUM",
      "The fruit of the pea plant is a",
      ["Legume", "Capsule", "Berry", "Drupe"], 0,
      "The pea fruit develops from a superior monocarpellary ovary and splits "
      "along two sutures, so it is a legume (pod)."),
    q("Morphology of Flowering Plants", "HARD",
      "The type of placentation in which ovules are borne on a single "
      "placenta along the ventral suture, as in pea, is",
      ["Axile", "Parietal", "Free central", "Marginal"], 3,
      "In marginal placentation the ovules are arranged in two rows on the "
      "ventral suture, as in pea."),

    # --- Anatomy of Flowering Plants ---------------------------------------
    q("Anatomy of Flowering Plants", "EASY",
      "A vascular bundle in which the cambium is present is called",
      ["Closed", "Radial", "Open", "Conjoint"], 2,
      "The presence of cambium between xylem and phloem makes a bundle open, "
      "allowing secondary growth."),
    q("Anatomy of Flowering Plants", "MEDIUM",
      "Palisade parenchyma is a part of the",
      ["Epidermis", "Mesophyll", "Endodermis", "Pith"], 1,
      "Palisade and spongy parenchyma together form the mesophyll of a leaf."),
    q("Anatomy of Flowering Plants", "HARD",
      "Casparian strips are found in the",
      ["Endodermis", "Epidermis", "Cortex", "Pericycle"], 0,
      "The endodermal cell walls bear casparian strips (suberised bands) that "
      "block the apoplastic pathway in roots."),

    # --- Transport in Plants -----------------------------------------------
    q("Transport in Plants", "EASY",
      "Water and dissolved minerals are transported through the",
      ["Phloem", "Cambium", "Cortex", "Xylem"], 3,
      "Xylem conducts water and minerals upward from the roots in plants."),
    q("Transport in Plants", "MEDIUM",
      "The cohesion-tension theory explains the ascent of sap in the",
      ["Phloem", "Xylem", "Both phloem and xylem", "Neither"], 1,
      "According to the cohesion-tension theory, water rises through the "
      "xylem due to transpiration pull, cohesion and adhesion."),
    q("Transport in Plants", "HARD",
      "The rate of transpiration in a small leafy shoot is measured using a",
      ["Porometer", "Auxanometer", "Potometer", "Clinostat"], 2,
      "A potometer measures the rate of water uptake, which closely reflects "
      "the rate of transpiration."),

    # --- Mineral Nutrition -------------------------------------------------
    q("Mineral Nutrition", "EASY",
      "Which of the following is a micronutrient?",
      ["Zinc", "Nitrogen", "Phosphorus", "Potassium"], 0,
      "Zinc is required in very small amounts and is therefore a "
      "micronutrient, unlike N, P and K."),
    q("Mineral Nutrition", "MEDIUM",
      "Leghemoglobin, which protects the nitrogenase enzyme, is present in",
      ["Leaves of grasses", "Stem of sugarcane", "Fruits of tomato",
       "Root nodules of legumes"], 3,
      "Leghemoglobin occurs in the root nodules of legumes and keeps the "
      "nodule interior anaerobic, protecting nitrogenase."),
    q("Mineral Nutrition", "HARD",
      "The deficiency of magnesium in plants typically causes",
      ["Stunted root growth", "Interveinal chlorosis",
       "Marginal necrosis of leaves", "Premature leaf fall"], 1,
      "Magnesium is a central atom of chlorophyll; its deficiency causes "
      "chlorosis between the veins (interveinal chlorosis)."),

    # --- Photosynthesis ----------------------------------------------------
    q("Photosynthesis", "EASY",
      "The light reaction of photosynthesis takes place in the",
      ["Stroma", "Outer chloroplast membrane", "Thylakoid membrane",
       "Cytoplasm"], 2,
      "The photosystems and electron carriers of the light reaction are "
      "embedded in the thylakoid membrane."),
    q("Photosynthesis", "MEDIUM",
      "The first stable product of the C4 (Hatch-Slack) pathway is",
      ["Oxaloacetic acid (OAA)", "3-phosphoglyceric acid",
       "Ribulose bisphosphate", "Malic acid"], 0,
      "In C4 plants CO2 is first fixed onto phosphoenolpyruvate to give the "
      "4-carbon oxaloacetic acid (OAA)."),
    q("Photosynthesis", "HARD",
      "In the Calvin cycle, the first stable product is",
      ["Oxaloacetic acid", "3-phosphoglyceric acid", "Pyruvic acid",
       "Glucose"], 1,
      "Ribulose bisphosphate carboxylase fixes CO2 onto RuBP, and the first "
      "stable product is 3-phosphoglyceric acid (3-PGA)."),

    # --- Respiration in Plants ---------------------------------------------
    q("Respiration in Plants", "EASY",
      "The final electron acceptor of the electron transport chain in aerobic "
      "respiration is",
      ["NAD+", "FAD", "Carbon dioxide", "Oxygen"], 3,
      "Oxygen accepts the electrons at the end of the mitochondrial electron "
      "transport chain and forms water."),
    q("Respiration in Plants", "MEDIUM",
      "The net gain of ATP molecules by substrate-level phosphorylation during "
      "glycolysis of one glucose molecule is",
      ["1 ATP", "4 ATP", "2 ATP", "38 ATP"], 2,
      "Glycolysis uses 2 ATP and produces 4 ATP, giving a net gain of 2 ATP."),
    q("Respiration in Plants", "HARD",
      "The number of NADH molecules produced per glucose molecule during the "
      "Krebs cycle is",
      ["3 NADH", "6 NADH", "2 NADH", "4 NADH"], 1,
      "Each turn of the Krebs cycle yields 3 NADH; one glucose gives two "
      "turns, so 6 NADH are produced."),

    # --- Plant Growth and Development --------------------------------------
    q("Plant Growth and Development", "EASY",
      "The plant hormone responsible for cell elongation and phototropism is",
      ["Auxin", "Cytokinin", "Gibberellin", "Ethylene"], 0,
      "Auxin (IAA) promotes cell elongation and mediates phototropism by "
      "unequal distribution on the shaded side."),
    q("Plant Growth and Development", "MEDIUM",
      "The plant hormone that promotes cell division (cytokinesis) is",
      ["Auxin", "Gibberellin", "Cytokinin", "Abscisic acid"], 2,
      "Cytokinins promote cell division and are synthesised in regions of "
      "rapid division such as root tips."),
    q("Plant Growth and Development", "HARD",
      "Apical dominance in plants is caused mainly by",
      ["Cytokinin", "Gibberellin", "Ethylene", "Auxin"], 3,
      "Auxin produced by the apical bud suppresses the growth of lateral "
      "buds, causing apical dominance."),

    # --- Principles of Inheritance and Variation ---------------------------
    q("Principles of Inheritance and Variation", "EASY",
      "The 'father of genetics' is",
      ["Gregor Mendel", "Charles Darwin", "Hugo de Vries", "T.H. Morgan"], 0,
      "Gregor Mendel is regarded as the father of genetics for his work on "
      "the laws of inheritance."),
    q("Principles of Inheritance and Variation", "MEDIUM",
      "The phenotypic ratio obtained in the F2 generation of a dihybrid cross "
      "is",
      ["3:1", "9:3:3:1", "1:2:1", "1:1:1:1"], 1,
      "Mendel's dihybrid cross gives the F2 phenotypic ratio 9:3:3:1."),
    q("Principles of Inheritance and Variation", "HARD",
      "The genotypic ratio obtained in the F2 generation of a monohybrid cross "
      "is",
      ["3:1", "9:3:3:1", "1:2:1", "1:1"], 2,
      "A monohybrid cross gives the genotypic ratio 1 (homozygous dominant) : "
      "2 (heterozygous) : 1 (homozygous recessive)."),

    # --- Molecular Basis of Inheritance ------------------------------------
    q("Molecular Basis of Inheritance", "EASY",
      "The genetic material in most organisms is",
      ["Protein", "RNA", "Lipid", "DNA"], 3,
      "DNA is the genetic material in the vast majority of organisms, "
      "although some viruses use RNA."),
    q("Molecular Basis of Inheritance", "MEDIUM",
      "The double-helix model of DNA was proposed by",
      ["Watson and Crick", "Mendel and Morgan", "Griffith and Avery",
       "Nirenberg and Khorana"], 0,
      "James Watson and Francis Crick proposed the double-helix model of DNA "
      "in 1953."),
    q("Molecular Basis of Inheritance", "HARD",
      "In a DNA double helix, adenine pairs with",
      ["Guanine", "Thymine", "Uracil", "Cytosine"], 1,
      "A pairs with T through two hydrogen bonds and G pairs with C through "
      "three hydrogen bonds."),
    q("Molecular Basis of Inheritance", "EASY",
      "The process by which mRNA is synthesised from a DNA template is called",
      ["Translation", "Replication", "Transcription", "Mutation"], 2,
      "Transcription is the synthesis of RNA from a DNA template."),
    q("Molecular Basis of Inheritance", "MEDIUM",
      "The enzyme that unwinds the DNA double helix during replication is",
      ["DNA polymerase", "Ligase", "Primase", "Helicase"], 3,
      "Helicase unwinds the DNA double helix at the replication fork."),

    # --- Ecology: Organisms and Populations --------------------------------
    q("Organisms and Populations", "EASY",
      "The association between an alga and a fungus in a lichen is an example "
      "of",
      ["Parasitism", "Mutualism", "Commensalism", "Predation"], 1,
      "In a lichen the alga photosynthesises and the fungus provides shelter "
      "and minerals, so both benefit (mutualism)."),
    q("Organisms and Populations", "MEDIUM",
      "The logistic growth equation for a population is",
      ["dN/dt = rN", "dN/dt = rN(K - N)/K", "dN/dt = rK", "dN/dt = rN/N"], 1,
      "Logistic growth is described by dN/dt = rN(K - N)/K, where K is the "
      "carrying capacity."),

    # --- Ecosystem ---------------------------------------------------------
    q("Ecosystem", "EASY",
      "The producers of an ecosystem are",
      ["Herbivores", "Consumers", "Green plants (autotrophs)", "Decomposers"], 2,
      "Green plants (autotrophs) trap solar energy and form the base of every "
      "food chain."),
    q("Ecosystem", "MEDIUM",
      "In a parasitic food chain, the pyramid of numbers is",
      ["Always upright", "Inverted", "Always spindle-shaped", "Not defined"], 1,
      "A single host can support a large number of parasites, so the pyramid "
      "of numbers in a parasitic food chain is inverted."),
    q("Ecosystem", "HARD",
      "According to the ten per cent law, the energy transferred from one "
      "trophic level to the next is about",
      ["10%", "50%", "90%", "1%"], 0,
      "Lindeman's ten percent law states that only about 10% of the energy at "
      "one trophic level is transferred to the next."),

    # --- Biodiversity and Conservation -------------------------------------
    q("Biodiversity and Conservation", "EASY",
      "The variety of living organisms present in a region is called",
      ["Ecology", "Biodiversity", "Succession", "Homeostasis"], 1,
      "Biodiversity refers to the variety and variability of living organisms "
      "and the ecosystems they form."),
    q("Environmental Issues", "MEDIUM",
      "The greenhouse gas that contributes most to global warming is",
      ["Oxygen", "Methane", "Carbon dioxide", "Nitrogen"], 2,
      "Carbon dioxide is the principal greenhouse gas responsible for global "
      "warming, although methane is more potent per molecule."),
]
