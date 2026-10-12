"""NEET UG (Advanced Level) - Botany: 45 questions."""

from __future__ import annotations

from .common import q

QUESTIONS = [
    # --- Diversity in the Living World ------------------------------------
    q("The Living World", "EASY",
      "In the taxonomic hierarchy, the correct sequence from lower to higher "
      "category is",
      ["species -> genus -> family -> order",
       "species -> family -> genus -> order",
       "genus -> species -> order -> family",
       "order -> family -> genus -> species"], 0,
      "The ascending hierarchy is species, genus, family, order, class, phylum "
      "(division), kingdom."),
    q("Biological Classification", "MEDIUM",
      "The five-kingdom classification was proposed by",
      ["R. H. Whittaker", "Carl Linnaeus", "Aristotle", "Carl Woese"], 0,
      "Whittaker (1969) proposed the kingdoms Monera, Protista, Fungi, Plantae "
      "and Animalia."),
    q("Biological Classification", "HARD",
      "Viruses that infect bacteria are called",
      ["bacteriophages", "viroids", "prions", "lichens"], 0,
      "Bacteriophages are viruses that specifically infect bacteria, e.g. the "
      "T4 phage."),
    q("Biological Classification", "MEDIUM",
      "Viroids differ from viruses in that viroids",
      ["lack a protein coat", "contain DNA", "are larger than viruses",
       "infect only animals"], 0,
      "Viroids are free, low-molecular-weight infectious RNA molecules without a "
      "protein capsid."),

    # --- Plant Kingdom -----------------------------------------------------
    q("Plant Kingdom", "EASY",
      "The pigment responsible for the brown colour of brown algae "
      "(Phaeophyceae) is",
      ["fucoxanthin", "chlorophyll b", "phycoerythrin", "phycocyanin"], 0,
      "Fucoxanthin is the characteristic brown accessory pigment of brown "
      "algae."),
    q("Plant Kingdom", "HARD",
      "Heterospory and the beginning of the seed habit are best illustrated by",
      ["Selaginella and Salvinia", "Chlamydomonas", "Funaria", "Nostoc"], 0,
      "Selaginella and Salvinia are heterosporous pteridophytes that retain the "
      "megaspore, an important step towards the seed habit."),
    q("Plant Kingdom", "MEDIUM",
      "Double fertilisation is a characteristic feature of",
      ["angiosperms", "gymnosperms", "pteridophytes", "bryophytes"], 0,
      "In angiosperms one male gamete fuses with the egg (syngamy) and the other "
      "with the two polar nuclei (triple fusion)."),

    # --- Morphology and Anatomy of Flowering Plants -----------------------
    q("Morphology of Flowering Plants", "MEDIUM",
      "In pea, the type of placentation is",
      ["marginal", "axile", "parietal", "free central"], 0,
      "Pea has a single marginal placenta along the ventral suture of the "
      "unicarpellary ovary."),
    q("Morphology of Flowering Plants", "HARD",
      "Which of the following is a modified stem?",
      ["Potato tuber", "Sweet potato", "Carrot", "Radish"], 0,
      "The potato tuber is a modified underground stem with nodes (eyes); sweet "
      "potato, carrot and radish are storage roots."),
    q("Anatomy of Flowering Plants", "EASY",
      "Which tissue consists of dead cells at maturity and conducts water in "
      "plants?",
      ["Xylem", "Phloem", "Collenchyma", "Parenchyma"], 0,
      "Xylem tracheary elements (tracheids and vessels) are dead at maturity "
      "and conduct water and minerals."),
    q("Anatomy of Flowering Plants", "HARD",
      "The Casparian strip is found in the",
      ["endodermal cells of roots", "epidermal cells of leaves",
       "cork cambium", "pith of stems"], 0,
      "The Casparian strip is a suberised band in the radial and transverse "
      "walls of root endodermal cells that blocks the apoplastic pathway."),

    # --- Cell: The Unit of Life and Biomolecules --------------------------
    q("Cell: The Unit of Life", "EASY",
      "The ribosomes of a prokaryotic cell are of the type",
      ["70S", "80S", "60S", "40S"], 0,
      "Prokaryotic ribosomes are 70S, made of a 50S and a 30S subunit."),
    q("Cell: The Unit of Life", "HARD",
      "Which of the following is a single-membrane-bound cell organelle?",
      ["Lysosome", "Mitochondrion", "Chloroplast", "Nucleus"], 0,
      "Lysosomes are bounded by a single membrane, whereas mitochondria, "
      "chloroplasts and the nucleus have double membranes."),
    q("Cell: The Unit of Life", "EASY",
      "Aerobic respiration in a eukaryotic cell is carried out mainly in the",
      ["mitochondria", "nucleus", "Golgi apparatus", "lysosomes"], 0,
      "Mitochondria are the site of aerobic respiration: the Krebs cycle occurs "
      "in the matrix and the electron transport chain on the inner membrane."),
    q("Biomolecules", "MEDIUM",
      "Enzymes increase the rate of a biochemical reaction by",
      ["lowering the activation energy", "raising the activation energy",
       "increasing the temperature", "changing the equilibrium constant"], 0,
      "Enzymes provide an alternative pathway of lower activation energy; they "
      "do not change the equilibrium position."),
    q("Biomolecules", "HARD",
      "The primary structure of a protein refers to",
      ["the sequence of amino acids joined by peptide bonds",
       "the folding of the polypeptide into a helix", "the 3-D structure",
       "the association of many polypeptide chains"], 0,
      "Primary structure is the linear sequence of amino acids linked by "
      "peptide bonds."),

    # --- Cell Cycle and Cell Division -------------------------------------
    q("Cell Cycle and Cell Division", "EASY",
      "In the eukaryotic cell cycle, DNA replication occurs during the",
      ["S phase", "G1 phase", "G2 phase", "M phase"], 0,
      "DNA synthesis occurs in the S (synthesis) phase of interphase."),
    q("Cell Cycle and Cell Division", "HARD",
      "Crossing over between homologous chromosomes occurs during which "
      "sub-stage of prophase I?",
      ["Pachytene", "Leptotene", "Zygotene", "Diplotene"], 0,
      "Crossing over occurs at the pachytene stage, when recombination nodules "
      "appear on the tetrads."),

    # --- Plant Physiology --------------------------------------------------
    q("Transport in Plants", "MEDIUM",
      "The ascent of sap in tall trees is best explained by the",
      ["cohesion-tension (transpiration pull) theory", "root pressure alone",
       "capillarity alone", "active pumping by xylem"], 0,
      "According to the cohesion-tension theory, transpiration pull, cohesion "
      "of water and adhesion to xylem wall together lift water."),
    q("Transport in Plants", "HARD",
      "When a plant cell is placed in a hypertonic solution it undergoes",
      ["plasmolysis", "imbibition", "turgidity", "deplasmolysis"], 0,
      "Water leaves the cell by exosmosis, and the protoplast shrinks away from "
      "the cell wall (plasmolysis)."),
    q("Mineral Nutrition", "EASY",
      "Which of the following is a macronutrient for plants?",
      ["Nitrogen", "Zinc", "Copper", "Boron"], 0,
      "Nitrogen (like C, H, O, P, K, Ca, Mg, S) is required in large amounts; "
      "Zn, Cu and B are micronutrients."),
    q("Photosynthesis in Higher Plants", "MEDIUM",
      "The light reactions of photosynthesis take place in the",
      ["thylakoid membranes of the chloroplast",
       "stroma of the chloroplast", "cytoplasm",
       "mitochondrial matrix"], 0,
      "Light reactions occur on the thylakoid membranes; the Calvin cycle takes "
      "place in the stroma."),
    q("Photosynthesis in Higher Plants", "HARD",
      "In C4 plants, the primary acceptor of CO2 in the mesophyll cells is",
      ["phosphoenolpyruvate (PEP)", "ribulose-1,5-bisphosphate (RuBP)",
       "oxaloacetate", "3-phosphoglycerate"], 0,
      "PEP carboxylase fixes CO2 onto PEP to form oxaloacetate in the mesophyll "
      "cells of C4 plants."),
    q("Photosynthesis in Higher Plants", "MEDIUM",
      "Photorespiration occurs because RuBisCO",
      ["can bind O2 in place of CO2", "cannot bind CO2",
       "is inactive in light", "is present only in mitochondria"], 0,
      "RuBisCO has affinity for both CO2 and O2; when O2 is high relative to "
      "CO2, it fixes O2 and photorespiration begins."),
    q("Respiration in Plants", "EASY",
      "Glycolysis takes place in the",
      ["cytoplasm", "mitochondrial matrix", "inner mitochondrial membrane",
       "nucleus"], 0,
      "Glycolysis (the EMP pathway) is a cytoplasmic process."),
    q("Respiration in Plants", "HARD",
      "The net number of ATP molecules formed by the complete aerobic oxidation "
      "of one glucose molecule (classical calculation) is",
      ["38", "2", "30", "12"], 0,
      "The classical/NCERT calculation gives a net yield of 38 ATP per glucose "
      "under aerobic conditions."),
    q("Plant Growth and Development", "EASY",
      "Apical dominance in plants is caused by",
      ["auxin produced by the apical bud", "gibberellin",
       "cytokinin produced by roots", "abscisic acid"], 0,
      "Auxin from the apical bud suppresses the growth of lateral buds, causing "
      "apical dominance."),
    q("Plant Growth and Development", "HARD",
      "The plant hormone responsible for bolting (rapid internode elongation) "
      "in rosette plants is",
      ["gibberellin", "auxin", "cytokinin", "ethylene"], 0,
      "Gibberellins promote rapid internode elongation, causing bolting of "
      "rosette plants."),

    # --- Reproduction in Plants -------------------------------------------
    q("Sexual Reproduction in Flowering Plants", "MEDIUM",
      "The mature female gametophyte (embryo sac) of a typical angiosperm "
      "contains",
      ["7 cells and 8 nuclei", "8 cells and 8 nuclei", "7 cells and 7 nuclei",
       "6 cells and 8 nuclei"], 0,
      "The Polygonum-type embryo sac has 7 cells (egg, 2 synergids, 3 "
      "antipodals, 1 central cell) and 8 nuclei because the central cell has "
      "two polar nuclei."),
    q("Sexual Reproduction in Flowering Plants", "HARD",
      "The production of seeds without fertilisation is called",
      ["apomixis", "parthenocarpy", "polyembryony", "syngamy"], 0,
      "Apomixis is the production of seeds without fertilisation; "
      "parthenocarpy refers to fruit development without fertilisation."),

    # --- Genetics and Molecular Biology -----------------------------------
    q("Principles of Inheritance and Variation", "MEDIUM",
      "Mendel's law of segregation is based on the separation of",
      ["the two alleles of a gene during gamete formation",
       "linked genes during meiosis", "chromosomes during mitosis",
       "sister chromatids during anaphase I"], 0,
      "The two alleles of a gene separate from each other during gamete "
      "formation, each gamete receiving one allele."),
    q("Principles of Inheritance and Variation", "HARD",
      "In snapdragon, a cross between red-flowered and white-flowered plants "
      "gives pink-flowered progeny. This is an example of",
      ["incomplete dominance", "codominance", "complete dominance",
       "epistasis"], 0,
      "The heterozygote shows an intermediate phenotype, which is incomplete "
      "dominance."),
    q("Molecular Basis of Inheritance", "MEDIUM",
      "According to Chargaff's rules, in double-stranded DNA",
      ["the amount of adenine equals that of thymine",
       "the amount of adenine equals that of guanine",
       "A + T always equals G + C",
       "purines are present in half the amount of pyrimidines"], 0,
      "A pairs with T and G with C, so A = T and G = C."),
    q("Molecular Basis of Inheritance", "HARD",
      "In eukaryotic cells, the enzyme primarily responsible for the "
      "transcription of mRNA is",
      ["RNA polymerase II", "RNA polymerase I", "RNA polymerase III",
       "DNA polymerase I"], 0,
      "RNA polymerase I transcribes rRNA, RNA polymerase III small RNAs, and "
      "RNA polymerase II mRNA."),
    q("Molecular Basis of Inheritance", "HARD",
      "In the lac operon, the structural gene z codes for",
      ["beta-galactosidase", "permease", "transacetylase",
       "the repressor protein"], 0,
      "In the lac operon z codes for beta-galactosidase, y for permease and a "
      "for transacetylase."),

    # --- Biotechnology -----------------------------------------------------
    q("Biotechnology: Principles and Processes", "EASY",
      "Restriction endonucleases cut DNA at",
      ["specific palindromic recognition sequences", "random sites",
       "single-stranded regions only", "the 5' end of the strand"], 0,
      "They recognise specific palindromic sequences and cut both strands, "
      "often producing sticky ends."),
    q("Biotechnology: Principles and Processes", "HARD",
      "The enzyme used for the polymerase chain reaction (PCR) is",
      ["Taq polymerase", "DNA ligase", "restriction endonuclease",
       "reverse transcriptase"], 0,
      "Thermostable Taq DNA polymerase from Thermus aquaticus is used for the "
      "repeated cycles of PCR."),
    q("Biotechnology and its Applications", "EASY",
      "Bt cotton is resistant to bollworm because it carries a gene from",
      ["Bacillus thuringiensis", "Agrobacterium tumefaciens", "E. coli",
       "Rhizobium"], 0,
      "Cry genes from the soil bacterium Bacillus thuringiensis make the plant "
      "resistant to insect pests such as bollworm."),
    q("Biotechnology and its Applications", "HARD",
      "RNA interference (RNAi) is used to",
      ["silence a specific gene using complementary double-stranded RNA",
       "increase the expression of a target gene",
       "repair mutated DNA", "amplify a target DNA sequence"], 0,
      "Introducing a complementary dsRNA leads to degradation of the target "
      "mRNA, silencing the gene."),

    # --- Ecology -----------------------------------------------------------
    q("Organisms and Populations", "MEDIUM",
      "The logistic growth model is considered realistic because it includes",
      ["environmental resistance due to limited resources",
       "unlimited resources", "exponential growth only",
       "no carrying capacity"], 0,
      "The logistic model includes a carrying capacity K, so growth slows as "
      "resources become limiting."),
    q("Organisms and Populations", "HARD",
      "An age pyramid with a very broad base indicates",
      ["an expanding (growing) population", "a declining population",
       "a stable population", "zero population growth"], 0,
      "A broad base means a large number of young individuals, indicating a "
      "growing population."),
    q("Ecosystem", "EASY",
      "If the producers in an ecosystem contain 10,000 J of energy, the energy "
      "available at the third trophic level, following the 10 per cent law, is",
      ["100 J", "1000 J", "10 J", "1 J"], 0,
      "Energy transfer is 10% per level: producers 10,000 J, herbivores 1000 J "
      "and the third trophic level 100 J."),
    q("Ecosystem", "MEDIUM",
      "An inverted pyramid of numbers/energy is characteristic of",
      ["a small pond or ocean ecosystem", "a grassland ecosystem",
       "a forest ecosystem", "a desert ecosystem"], 0,
      "In aquatic ecosystems the tiny phytoplankton producers are far fewer in "
      "biomass than the consumers, giving an inverted pyramid."),
    q("Biodiversity and Conservation", "EASY",
      "The species-area relationship is described by the equation",
      ["log S = log C + Z log A", "log S = Z log C + log A",
       "log S = log C - Z log A", "S = C/A"], 0,
      "The species-area relationship is log S = log C + Z log A, where Z is the "
      "slope of the line."),
    q("Environmental Issues", "MEDIUM",
      "The accumulation of non-biodegradable pesticides along a food chain is "
      "called",
      ["biomagnification", "eutrophication", "bioremediation", "biodiversity"],
      0,
      "Non-biodegradable pollutants like DDT increase in concentration at "
      "successive trophic levels, a phenomenon called biomagnification."),
]
