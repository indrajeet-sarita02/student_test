"""NEET UG (Advanced Level) - Zoology master bank.

``CORE`` is the curated 45-question Set 01 paper.  The generated half uses the
same :func:`common_bio.describe` helper (curated ``(term, definition)`` tables)
plus a few quantitative physiology templates with computed answers.
"""

from __future__ import annotations

from scripts.neet_ug_advanced_set01.zoology import QUESTIONS as _CORE

from .common import merge, nq
from .common_bio import describe

CORE = list(_CORE)
GEN = []

# --- Animal kingdom ---------------------------------------------------------
GEN += describe("Animal Kingdom", "MEDIUM", [
    ("Porifera", "sponges with a water-canal system and spongin fibres"),
    ("Cnidaria", "radially symmetrical animals bearing stinging cells (cnidoblasts)"),
    ("Platyhelminthes", "flattened worms with flame cells for excretion"),
    ("Aschelminthes", "roundworms possessing a pseudocoelom"),
    ("Annelida", "worms with true metameric segmentation and a closed circulatory system"),
    ("Arthropoda", "the largest phylum, with jointed appendages and chitinous exoskeleton"),
    ("Mollusca", "soft-bodied animals usually with a calcareous shell and a mantle"),
    ("Echinodermata", "spiny-skinned animals with a water-vascular system"),
    ("Hemichordata", "a phylum of worm-like animals with a stomochord"),
    ("Chordata", "animals having a notochord, dorsal nerve cord and pharyngeal gill slits"),
])

# --- Digestion and absorption ----------------------------------------------
GEN += describe("Digestion and Absorption", "MEDIUM", [
    ("pepsin", "a protease that digests proteins to peptones in the acidic stomach"),
    ("trypsin", "a protease secreted by the pancreas that acts in the alkaline small intestine"),
    ("salivary amylase", "an enzyme that digests starch to maltose in the mouth"),
    ("lipase", "an enzyme that splits fats into glycerol and fatty acids"),
    ("bile", "a secretion that emulsifies fats but contains no digestive enzyme"),
    ("villi", "finger-like projections that increase the surface area for absorption"),
])

# --- Body fluids and circulation -------------------------------------------
GEN += describe("Body Fluids and Circulation", "MEDIUM", [
    ("an erythrocyte", "a red blood cell that transports oxygen using haemoglobin"),
    ("a neutrophil", "the most abundant leucocyte, which carries out phagocytosis"),
    ("a basophil", "a granulocyte that secretes histamine and heparin"),
    ("a thrombocyte", "a blood cell fragment that helps in blood clotting"),
    ("blood plasma", "the liquid matrix that transports nutrients, hormones and wastes"),
    ("a lymphocyte", "a white blood cell that mediates immune responses"),
    ("the SA node", "the pacemaker of the human heart"),
])

# --- Breathing and exchange of gases ---------------------------------------
GEN += describe("Breathing and Exchange of Gases", "MEDIUM", [
    ("inspiration", "an active process caused by contraction of the diaphragm and external intercostals"),
    ("tidal volume", "the volume of air inhaled or exhaled during normal breathing, about 500 mL"),
    ("vital capacity", "the maximum volume of air a person can exhale after a maximum inspiration"),
    ("the Bohr effect", "the shift of the oxygen-haemoglobin curve caused by a rise in CO2"),
    ("carbonic anhydrase", "the enzyme that speeds up the conversion of CO2 to bicarbonate in red blood cells"),
])

# --- Excretory products and their elimination -------------------------------
GEN += describe("Excretory Products and their Elimination", "MEDIUM", [
    ("glomerular filtration", "the process in which blood is filtered in the renal corpuscle"),
    ("the loop of Henle", "the nephron region that establishes the medullary concentration gradient"),
    ("ADH", "the hormone that promotes water reabsorption in the collecting duct"),
    ("the juxtaglomerular apparatus", "the structure that releases renin in response to low blood pressure"),
    ("the ureter", "the tube that carries urine from the kidney to the urinary bladder"),
])

# --- Neural control and coordination ---------------------------------------
GEN += describe("Neural Control and Coordination", "MEDIUM", [
    ("the myelin sheath", "an insulating cover that enables saltatory conduction"),
    ("a synapse", "the junction across which a nerve impulse passes from one neuron to another"),
    ("the cerebrum", "the brain region concerned with intelligence, memory and voluntary action"),
    ("the cerebellum", "the brain region that maintains balance and coordinates movement"),
    ("the medulla oblongata", "the brain region that controls respiration and cardiovascular reflexes"),
    ("a neurotransmitter", "a chemical released at a synapse to transmit a nerve impulse"),
])

# --- Chemical coordination and integration ----------------------------------
GEN += describe("Chemical Coordination and Integration", "MEDIUM", [
    ("insulin", "a hormone that lowers blood glucose by promoting cellular uptake"),
    ("glucagon", "a hormone that raises blood glucose by promoting glycogen breakdown"),
    ("thyroxine", "the thyroid hormone that regulates the basal metabolic rate"),
    ("adrenaline", "the hormone that prepares the body for a fight-or-flight response"),
    ("parathormone", "a hormone that raises the blood calcium level"),
    ("oxytocin", "the hormone that stimulates contraction of the uterus during childbirth"),
    ("oxytocin", "the hormone that promotes milk ejection during nursing"),
])

# --- Locomotion and movement -----------------------------------------------
GEN += describe("Locomotion and Movement", "MEDIUM", [
    ("a sarcomere", "the functional unit of contraction between two successive Z-lines"),
    ("actin", "the thin filament protein of the muscle sarcomere"),
    ("myosin", "the thick filament protein that forms cross-bridges"),
    ("the sliding filament theory", "the explanation of muscle contraction by filament sliding"),
    ("calcium ions", "the ions whose release triggers muscle contraction"),
    ("red muscle fibres", "slow, aerobic fibres rich in myoglobin and mitochondria"),
])

# --- Human reproduction -----------------------------------------------------
GEN += describe("Human Reproduction", "MEDIUM", [
    ("spermatogenesis", "the formation of sperm in the seminiferous tubules of the testis"),
    ("ovulation", "the release of a secondary oocyte from the ovary, usually mid-cycle"),
    ("the corpus luteum", "the structure that secretes progesterone after ovulation"),
    ("fertilisation", "the fusion of sperm and ovum usually at the ampullary-isthmic junction"),
    ("implantation", "the embedding of the blastocyst in the endometrium"),
    ("the acrosome", "the structure at the sperm head containing hydrolytic enzymes"),
])

# --- Human health and disease ----------------------------------------------
GEN += describe("Human Health and Disease", "MEDIUM", [
    ("malaria", "a disease caused by Plasmodium and transmitted by female Anopheles"),
    ("typhoid", "a disease caused by Salmonella typhi and confirmed by the Widal test"),
    ("AIDS", "an immunodeficiency disease caused by the human immunodeficiency virus"),
    ("cancer", "a disease characterised by uncontrolled division of body cells"),
    ("immunisation", "the process of inducing protective immunity using a vaccine"),
    ("filariasis", "a disease caused by Wuchereria species and spread by mosquitoes"),
])

# --- Biotechnology and its applications -------------------------------------
GEN += describe("Biotechnology and its Applications", "MEDIUM", [
    ("a restriction endonuclease", "an enzyme that cuts DNA at specific recognition sites"),
    ("a plasmid", "a circular extrachromosomal DNA used as a cloning vector"),
    ("PCR", "a technique that amplifies a specific DNA segment in vitro"),
    ("Bt cotton", "a genetically modified crop carrying a bacterial insecticidal gene"),
    ("RNA interference", "a technique that silences a specific gene using dsRNA"),
    ("a transgenic organism", "an organism that carries and expresses a foreign gene"),
])

# --- Evolution --------------------------------------------------------------
GEN += describe("Evolution", "MEDIUM", [
    ("natural selection", "the differential survival and reproduction of the fittest variants"),
    ("the Hardy-Weinberg principle", "the constancy of allele frequencies in a large, randomly mating population"),
    ("homologous organs", "organs with the same fundamental structure but different functions"),
    ("adaptive radiation", "the diversification of a species into many forms in different habitats"),
    ("analogous organs", "organs with different structure but similar function"),
])

# --- Quantitative physiology (unique stems, computed answers) ----------------
for hr, sv in [(72, 70), (80, 80), (60, 100)]:
    co = hr * sv / 1000.0
    GEN.append(nq(
        "Body Fluids and Circulation", "HARD",
        f"If the heart rate is {hr} beats per minute and the stroke volume is {sv} mL, "
        f"the cardiac output per minute is",
        f"{co:g} L/min", [f"{co / 2:g} L/min", f"{co * 2:g} L/min", f"{co * 1.5:g} L/min"],
        f"Cardiac output = heart rate x stroke volume = {hr} x {sv} mL = {co:g} L/min.",
    ))

for tv, irv, erv in [(500, 2500, 1000), (500, 3000, 1100), (600, 2400, 1000)]:
    vc = tv + irv + erv
    GEN.append(nq(
        "Breathing and Exchange of Gases", "HARD",
        f"For a person with tidal volume {tv} mL, inspiratory reserve volume {irv} mL and "
        f"expiratory reserve volume {erv} mL, the vital capacity is",
        f"{vc} mL", [f"{tv + irv} mL", f"{irv + erv} mL", f"{vc + 1000} mL"],
        f"Vital capacity = TV + IRV + ERV = {tv} + {irv} + {erv} = {vc} mL.",
    ))

for gfr, minutes in [(125, 60), (125, 30), (110, 60)]:
    volume = gfr * minutes / 1000.0
    GEN.append(nq(
        "Excretory Products and their Elimination", "HARD",
        f"If the glomerular filtration rate is {gfr} mL/min, the volume of filtrate formed "
        f"in {minutes} minutes is",
        f"{volume:g} L", [f"{volume / 2:g} L", f"{volume * 2:g} L", f"{gfr:g} L"],
        f"Filtrate volume = GFR x time = {gfr} x {minutes} mL = {volume:g} L.",
    ))

QUESTIONS = merge(CORE, GEN)
