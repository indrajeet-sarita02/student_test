"""NEET UG (Advanced Level) - Botany master bank.

``CORE`` is the curated 45-question Set 01 paper.  The generated half is built
from curated ``(term, definition)`` tables (via ``common_bio.describe``) plus a
few quantitative genetics / ecology templates, so every stem is unique and the
answer key is certain.
"""

from __future__ import annotations

from scripts.neet_ug_advanced_set01.botany import QUESTIONS as _CORE

from .common import merge
from .common_bio import describe, numeric_biology

CORE = list(_CORE)
GEN = []

# --- Cell organelles and functions -----------------------------------------
GEN += describe("Cell: The Unit of Life", "MEDIUM", [
    ("the ribosome", "the site of protein synthesis"),
    ("the lysosome", "an organelle containing hydrolytic enzymes for intracellular digestion"),
    ("the Golgi apparatus", "the packaging and secretion of proteins and lipids"),
    ("the mitochondrion", "the site of aerobic respiration and ATP synthesis"),
    ("the chloroplast", "the site of photosynthesis in plant cells"),
    ("the nucleolus", "the site of ribosomal RNA synthesis"),
    ("the peroxisome", "an organelle involved in photorespiration and fatty-acid breakdown"),
    ("the tonoplast", "the membrane surrounding the plant cell vacuole"),
    ("the plasmodesma", "a cytoplasmic channel connecting adjacent plant cells"),
    ("the centriole", "a structure that organises the spindle during cell division"),
])

# --- Plant hormones ---------------------------------------------------------
GEN += describe("Plant Growth and Development", "MEDIUM", [
    ("auxin", "promoting apical dominance and cell elongation"),
    ("gibberellin", "promoting stem elongation, bolting and seed germination"),
    ("cytokinin", "promoting cell division and delaying senescence"),
    ("ethylene", "a gaseous hormone that promotes fruit ripening"),
    ("abscisic acid", "closing stomata and inducing seed dormancy"),
])

# --- Plant kingdom: pigments and stored food --------------------------------
GEN += describe("Plant Kingdom", "MEDIUM", [
    ("fucoxanthin", "the brown pigment characteristic of Phaeophyceae"),
    ("phycoerythrin", "the red pigment characteristic of Rhodophyceae"),
    ("floridean starch", "the stored food of red algae"),
    ("laminarin and mannitol", "the stored food of brown algae"),
    ("chlorenchyma", "photosynthetic parenchyma of green algae"),
    ("the protonema", "the first filamentous stage of a moss"),
    ("the prothallus", "the free-living gametophyte of a fern"),
])

# --- Photosynthesis components ---------------------------------------------
GEN += describe("Photosynthesis", "HARD", [
    ("photosystem II", "the pigment system that splits water and absorbs light at 680 nm"),
    ("photosystem I", "the pigment system that absorbs light at 700 nm"),
    ("RuBisCO", "the enzyme that fixes carbon dioxide in the Calvin cycle"),
    ("the Calvin cycle", "carbon fixation that occurs in the stroma of the chloroplast"),
    ("Kranz anatomy", "the wreath-like arrangement of bundle-sheath cells in C4 plants"),
    ("the light reaction", "the conversion of light energy into ATP and NADPH"),
    ("photorespiration", "the wasteful oxygenation of RuBP that produces no sugar or ATP"),
])

# --- Respiration in plants --------------------------------------------------
GEN += describe("Respiration in Plants", "MEDIUM", [
    ("glycolysis", "the breakdown of glucose to pyruvate in the cytoplasm"),
    ("the Krebs cycle", "the oxidation of acetyl-CoA in the mitochondrial matrix"),
    ("the electron transport system", "the transfer of electrons to oxygen on the inner mitochondrial membrane"),
    ("oxidative phosphorylation", "ATP synthesis driven by the proton gradient"),
    ("fermentation", "anaerobic breakdown of pyruvate giving ethanol or lactic acid"),
])

# --- Cell cycle and cell division ------------------------------------------
GEN += describe("Cell Cycle and Cell Division", "MEDIUM", [
    ("the S phase", "the phase in which DNA is replicated"),
    ("zygotene", "the meiotic stage in which homologous chromosomes pair up (synapsis)"),
    ("pachytene", "the meiotic stage in which crossing over occurs"),
    ("diplotene", "the meiotic stage in which chiasmata become visible"),
    ("anaphase I", "the meiotic stage in which homologous chromosomes separate"),
    ("anaphase of mitosis", "the mitotic stage in which sister chromatids separate"),
    ("metaphase", "the mitotic stage in which chromosomes align at the cell equator"),
])

# --- Anatomy of flowering plants -------------------------------------------
GEN += describe("Anatomy of Flowering Plants", "MEDIUM", [
    ("collenchyma", "living tissue providing mechanical support to young stems"),
    ("sclerenchyma", "dead tissue with thick lignified walls providing hardness"),
    ("parenchyma", "living tissue specialised for storage and photosynthesis"),
    ("xylem", "the tissue that conducts water and minerals upwards"),
    ("phloem", "the tissue that conducts food in both directions"),
    ("the endodermis", "the innermost layer of the cortex bearing Casparian strips"),
    ("the bundle sheath", "the layer of cells surrounding a vascular bundle"),
])

# --- Morphology of flowering plants ----------------------------------------
GEN += describe("Morphology of Flowering Plants", "MEDIUM", [
    ("a pneumatophore", "a respiratory root of mangrove plants"),
    ("a prop root", "a supporting root that arises from the branches of a banyan tree"),
    ("a stilt root", "a supporting root that arises from the lower nodes of maize"),
    ("a tap root", "the primary root modified for storage in carrot and turnip"),
    ("a capitulum", "the head-like inflorescence of sunflower"),
    ("a drupe", "a fruit such as coconut with a fleshy pericarp and hard endocarp"),
    ("the thalamus", "the swollen floral axis on which the flower parts are borne"),
])

# --- Transport in plants ----------------------------------------------------
GEN += describe("Transport in Plants", "MEDIUM", [
    ("osmosis", "the movement of water across a semipermeable membrane"),
    ("plasmolysis", "the shrinkage of protoplasm when a cell loses water in a hypertonic solution"),
    ("guttation", "the loss of water as liquid droplets from leaf margins"),
    ("transpiration", "the loss of water as vapour mainly through stomata"),
    ("the cohesion-tension theory", "the explanation of the ascent of sap in xylem"),
    ("the pressure-flow hypothesis", "the explanation of translocation in the phloem"),
])

# --- Mineral nutrition ------------------------------------------------------
GEN += describe("Mineral Nutrition", "MEDIUM", [
    ("nitrogen", "the element required for the synthesis of proteins and nucleic acids"),
    ("magnesium", "the central metal of the chlorophyll molecule"),
    ("nitrogen fixation", "the conversion of atmospheric nitrogen into ammonia"),
    ("Rhizobium", "the bacterium that fixes nitrogen in the root nodules of legumes"),
    ("mycorrhiza", "a symbiotic association between a fungus and plant roots"),
    ("leghaemoglobin", "the pink pigment that protects nitrogenase in root nodules"),
])

# --- Scientists and landmarks ----------------------------------------------
GEN += describe("Principles of Inheritance and Variation", "EASY", [
    ("Gregor Mendel", "the scientist who formulated the laws of inheritance using pea plants"),
    ("the law of segregation", "the principle that alleles separate during gamete formation"),
    ("the law of independent assortment", "the principle that genes assort independently when unlinked"),
    ("a test cross", "a cross of an individual with a recessive parent"),
    ("a dihybrid cross", "a cross involving two pairs of contrasting characters"),
])

# --- Quantitative genetics / ecology ---------------------------------------
GEN += numeric_biology()

QUESTIONS = merge(CORE, GEN)
