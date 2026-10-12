"""NEET UG (Advanced Level) - Zoology: 45 questions."""

from __future__ import annotations

from .common import q

QUESTIONS = [
    # --- Animal Kingdom and Structural Organisation -----------------------
    q("Animal Kingdom", "EASY",
      "Sponges belong to the phylum",
      ["Porifera", "Coelenterata", "Annelida", "Echinodermata"], 0,
      "Sponges have a canal system and were placed in the phylum Porifera "
      "(now Parazoa)."),
    q("Animal Kingdom", "MEDIUM",
      "Animals in which the body cavity is absent are called",
      ["acoelomates", "pseudocoelomates", "coelomates", "diploblastic"], 0,
      "Flatworms (Platyhelminthes) lack a true body cavity and are "
      "acoelomates."),
    q("Animal Kingdom", "HARD",
      "Which of the following is a characteristic feature of chordates?",
      ["A dorsal hollow nerve cord", "A ventral solid nerve cord",
       "An exoskeleton of chitin", "Radial symmetry in the adult"], 0,
      "Chordates have a notochord, a dorsal hollow nerve cord and paired "
      "pharyngeal gill slits at some stage of life."),
    q("Structural Organisation in Animals", "MEDIUM",
      "The tissue that covers body surfaces and lines internal organs, and "
      "also forms glands, is",
      ["epithelial tissue", "muscular tissue", "nervous tissue",
       "skeletal connective tissue"], 0,
      "Epithelial tissue covers and lines surfaces and also forms glands."),

    # --- Digestion and Absorption -----------------------------------------
    q("Digestion and Absorption", "MEDIUM",
      "Bile, which helps in the emulsification of fats, is produced by the",
      ["liver", "pancreas", "gall bladder", "stomach"], 0,
      "Bile is secreted by the liver and stored and concentrated in the gall "
      "bladder."),
    q("Digestion and Absorption", "HARD",
      "The inactive zymogen trypsinogen secreted by the pancreas is activated "
      "by",
      ["enterokinase", "gastric HCl", "pepsin", "bile salts"], 0,
      "Intestinal enterokinase converts trypsinogen into active trypsin."),
    q("Digestion and Absorption", "MEDIUM",
      "The largest gland in the human body is the",
      ["liver", "pancreas", "thyroid", "salivary gland"], 0,
      "The liver is the largest gland and the largest internal organ."),

    # --- Breathing and Exchange of Gases ----------------------------------
    q("Breathing and Exchange of Gases", "MEDIUM",
      "Most of the oxygen in blood is transported as",
      ["oxyhaemoglobin", "dissolved oxygen in plasma",
       "bicarbonate ions", "carbaminohaemoglobin"], 0,
      "About 97% of oxygen is carried bound to haemoglobin as oxyhaemoglobin."),
    q("Breathing and Exchange of Gases", "HARD",
      "The Bohr effect describes the",
      ["shift of the oxygen dissociation curve to the right when CO2/H+ rises",
       "shift of the curve to the left when pH falls",
       "binding of CO2 to haemoglobin in the lungs",
       "effect of oxygen on carbon dioxide transport in tissues"], 0,
      "The Bohr effect: higher CO2/H+ (lower pH) reduces haemoglobin's affinity "
      "for oxygen, shifting the curve right and unloading oxygen in tissues."),
    q("Breathing and Exchange of Gases", "MEDIUM",
      "Most of the carbon dioxide in blood is transported as",
      ["bicarbonate ions", "dissolved CO2", "carbaminohaemoglobin",
       "free carbonic acid"], 0,
      "About 70% of CO2 is transported as bicarbonate ions produced by the "
      "action of carbonic anhydrase in red blood cells."),

    # --- Body Fluids and Circulation --------------------------------------
    q("Body Fluids and Circulation", "MEDIUM",
      "The pacemaker of the human heart is the",
      ["SA node", "AV node", "bundle of His", "Purkinje fibres"], 0,
      "The sino-atrial (SA) node initiates the heartbeat and is called the "
      "pacemaker."),
    q("Body Fluids and Circulation", "HARD",
      "The volume of blood pumped by each ventricle per minute is called the",
      ["cardiac output", "stroke volume", "end-diastolic volume",
       "cardiac index"], 0,
      "Cardiac output = stroke volume x heart rate, the volume pumped per "
      "minute."),

    # --- Excretory Products and their Elimination -------------------------
    q("Excretory Products and their Elimination", "EASY",
      "The structural and functional unit of the kidney is the",
      ["nephron", "neuron", "alveolus", "villus"], 0,
      "Each kidney contains about a million nephrons, the functional units of "
      "the kidney."),
    q("Excretory Products and their Elimination", "HARD",
      "The counter-current mechanism of the kidney is important for",
      ["concentrating urine by maintaining a medullary osmotic gradient",
       "filtration of blood at the glomerulus",
       "secretion of glucose into the filtrate",
       "reabsorption of proteins"], 0,
      "The loop of Henle and vasa recta maintain a medullary concentration "
      "gradient that allows water reabsorption and concentrated urine."),

    # --- Locomotion and Movement ------------------------------------------
    q("Locomotion and Movement", "MEDIUM",
      "The functional unit of a skeletal muscle is the",
      ["sarcomere", "myofibril", "sarcolemma", "motor unit"], 0,
      "The sarcomere, the region between two successive Z-lines, is the "
      "functional contractile unit."),
    q("Locomotion and Movement", "MEDIUM",
      "According to the sliding filament theory, muscle contraction occurs "
      "when",
      ["thin (actin) filaments slide over thick (myosin) filaments",
       "the A-band shortens",
       "the myosin filaments shorten",
       "the sarcomere lengthens"], 0,
      "Actin filaments slide inward over myosin, shortening the sarcomere while "
      "the filament lengths themselves remain unchanged."),

    # --- Neural Control and Coordination ----------------------------------
    q("Neural Control and Coordination", "MEDIUM",
      "The resting membrane potential of a neuron is mainly due to",
      ["the differential permeability to K+ and Na+ ions",
       "movement of chloride ions only",
       "active transport of calcium ions",
       "release of neurotransmitters"], 0,
      "The resting potential (about -70 mV) is set largely by K+ permeability "
      "and the sodium-potassium pump."),
    q("Neural Control and Coordination", "HARD",
      "Transmission of a nerve impulse across a chemical synapse involves",
      ["release of neurotransmitters into the synaptic cleft",
       "direct flow of ions through gap junctions",
       "movement of the axon towards the dendrite",
       "release of hormones into the blood"], 0,
      "At a chemical synapse, an action potential triggers neurotransmitter "
      "release into the cleft, which then acts on the postsynaptic membrane."),

    # --- Chemical Coordination and Integration ----------------------------
    q("Chemical Coordination and Integration", "MEDIUM",
      "Insulin is secreted by the",
      ["beta cells of the islets of Langerhans",
       "alpha cells of the islets of Langerhans",
       "acinar cells of the pancreas",
       "cells of the adrenal medulla"], 0,
      "Beta cells of the islets of Langerhans secrete insulin; alpha cells "
      "secrete glucagon."),
    q("Chemical Coordination and Integration", "HARD",
      "Which of the following hormones acts through the second messenger cyclic "
      "AMP?",
      ["Adrenaline", "Cortisol", "Testosterone", "Aldosterone"], 0,
      "Adrenaline binds a membrane receptor and raises cyclic AMP; cortisol, "
      "testosterone and aldosterone are steroid hormones that act on "
      "intracellular receptors."),
    q("Chemical Coordination and Integration", "MEDIUM",
      "Diabetes insipidus is caused by a deficiency of",
      ["antidiuretic hormone (vasopressin)", "insulin", "thyroxine",
       "glucagon"], 0,
      "A deficiency of ADH reduces water reabsorption, causing the excretion of "
      "large volumes of dilute urine (diabetes insipidus)."),

    # --- Human Reproduction and Reproductive Health -----------------------
    q("Human Reproduction", "MEDIUM",
      "Spermatogenesis in humans is directly stimulated by",
      ["follicle-stimulating hormone (FSH)", "luteinising hormone (LH)",
       "progesterone", "oxytocin"], 0,
      "FSH acts on Sertoli cells to stimulate spermatogenesis; LH stimulates "
      "Leydig cells to secrete androgens."),
    q("Human Reproduction", "HARD",
      "Ovulation in the human menstrual cycle is triggered by",
      ["a surge in luteinising hormone (LH)", "a surge in progesterone",
       "a fall in oestrogen", "a rise in FSH only"], 0,
      "A sharp mid-cycle surge of LH ruptures the mature Graafian follicle and "
      "causes ovulation."),
    q("Human Reproduction", "MEDIUM",
      "In humans, fertilisation normally takes place in the",
      ["ampulla of the fallopian tube", "uterus", "cervix", "ovary"], 0,
      "Fertilisation occurs at the ampullary-isthmic junction of the fallopian "
      "tube."),
    q("Human Reproduction", "MEDIUM",
      "The corpus luteum secretes",
      ["progesterone", "oestrogen only", "LH", "FSH"], 0,
      "The corpus luteum secretes progesterone, which maintains the "
      "endometrium for implantation."),
    q("Human Reproduction", "HARD",
      "The correct sequence of the male reproductive duct system is",
      ["rete testis -> vasa efferentia -> epididymis -> vas deferens -> urethra",
       "epididymis -> rete testis -> ureter -> urethra",
       "rete testis -> vas deferens -> epididymis -> urethra",
       "vasa efferentia -> rete testis -> ureter -> vas deferens"], 0,
      "Sperms pass from the rete testis through the vasa efferentia to the "
      "epididymis, then the vas deferens, ejaculatory duct and urethra."),
    q("Reproductive Health", "MEDIUM",
      "Copper-T acts as a contraceptive mainly by",
      ["releasing copper ions that suppress sperm motility and fertilising "
       "capacity",
       "blocking ovulation",
       "thickening the cervical mucus only",
       "preventing implantation by hormonal action"], 0,
      "The copper ions released suppress sperm motility and the fertilising "
      "capacity of sperms."),

    # --- Human Health and Disease -----------------------------------------
    q("Human Health and Disease", "MEDIUM",
      "Malaria in humans is caused by",
      ["Plasmodium", "Wuchereria", "Ascaris", "Entamoeba"], 0,
      "Malaria is caused by species of Plasmodium, transmitted by the female "
      "Anopheles mosquito."),
    q("Human Health and Disease", "EASY",
      "Which immunoglobulin can cross the placenta and provide passive immunity "
      "to the foetus?",
      ["IgG", "IgM", "IgA", "IgE"], 0,
      "IgG is the only antibody class that can cross the placenta."),
    q("Human Health and Disease", "MEDIUM",
      "Cancer cells that spread to distant parts of the body through the blood "
      "are said to have undergone",
      ["metastasis", "benign growth", "contact inhibition", "apoptosis"], 0,
      "The spread of malignant cells to distant sites is called metastasis."),
    q("Human Health and Disease", "HARD",
      "Which of the following is an autoimmune disease?",
      ["Rheumatoid arthritis", "Malaria", "Tuberculosis", "AIDS"], 0,
      "In rheumatoid arthritis the immune system attacks the body's own "
      "tissues, making it an autoimmune disease."),

    # --- Genetics and Evolution -------------------------------------------
    q("Principles of Inheritance and Variation", "HARD",
      "Haemophilia in humans is an example of",
      ["X-linked recessive inheritance", "Y-linked inheritance",
       "autosomal dominant inheritance", "mitochondrial inheritance"], 0,
      "Haemophilia is an X-linked recessive disorder, so it is far more common "
      "in males."),
    q("Principles of Inheritance and Variation", "HARD",
      "A man of blood group AB marries a woman of blood group O. The possible "
      "blood groups of their children are",
      ["A and B", "AB and O", "AB only", "A, B and O"], 0,
      "AB x OO gives AO (blood group A) or BO (blood group B) children."),
    q("Human Reproduction", "MEDIUM",
      "Down's syndrome in humans is caused by",
      ["trisomy of chromosome 21", "monosomy of chromosome 21",
       "trisomy of chromosome 18", "XXY condition"], 0,
      "Down's syndrome results from an extra copy of chromosome 21 (trisomy "
      "21)."),
    q("Evolution", "MEDIUM",
      "The theory of natural selection was proposed by",
      ["Charles Darwin", "Jean-Baptiste Lamarck", "Hugo de Vries",
       "Gregor Mendel"], 0,
      "Charles Darwin (with Alfred Russel Wallace) proposed natural selection "
      "as the mechanism of evolution."),
    q("Evolution", "HARD",
      "According to the Hardy-Weinberg principle, allele frequencies in a "
      "population remain constant only when",
      ["there is no mutation, migration, selection or genetic drift",
       "mating is non-random",
       "the population is very small",
       "natural selection acts strongly"], 0,
      "The principle holds for a large, randomly mating population with no "
      "mutation, migration, selection or drift."),
    q("Evolution", "MEDIUM",
      "Homologous organs provide evidence for",
      ["divergent evolution", "convergent evolution", "analogous evolution",
       "spontaneous generation"], 0,
      "Homologous structures with a common ancestry but different functions "
      "indicate divergent evolution."),

    # --- Biotechnology and Microbes ---------------------------------------
    q("Biotechnology and its Applications", "MEDIUM",
      "The first recombinant human insulin produced by genetic engineering was "
      "marketed as",
      ["Humulin", "Insulin glargine", "Somatotropin", "Erythropoietin"], 0,
      "Eli Lilly produced human insulin from recombinant DNA technology under "
      "the trade name Humulin."),
    q("Microbes in Human Welfare", "EASY",
      "Curd is formed from milk by the action of",
      ["Lactobacillus", "yeast", "Aspergillus", "Penicillium"], 0,
      "Lactic acid bacteria (Lactobacillus) curdle milk into curd by producing "
      "lactic acid."),
    q("Microbes in Human Welfare", "HARD",
      "Which microorganism is used industrially to produce citric acid?",
      ["Aspergillus niger", "Saccharomyces cerevisiae",
       "Clostridium butylicum", "Penicillium notatum"], 0,
      "Aspergillus niger is used for the commercial production of citric acid."),

    # --- Additional coverage ---------------------------------------------
    q("Digestion and Absorption", "EASY",
      "Maximum absorption of the products of digestion occurs in the",
      ["small intestine", "stomach", "large intestine", "oesophagus"], 0,
      "The small intestine (mainly the jejunum and ileum) is the principal site "
      "of absorption of the products of digestion."),
    q("Human Health and Disease", "EASY",
      "AIDS is caused by",
      ["human immunodeficiency virus (HIV)", "human papilloma virus",
       "herpes simplex virus", "Epstein-Barr virus"], 0,
      "AIDS is caused by HIV, a retrovirus that infects helper T-lymphocytes."),
    q("Human Health and Disease", "MEDIUM",
      "In humans, B-lymphocytes acquire immunocompetence and mature in the",
      ["bone marrow", "thymus", "spleen", "lymph nodes"], 0,
      "B-lymphocytes mature in the bone marrow, whereas T-lymphocytes mature "
      "in the thymus."),
    q("Evolution", "MEDIUM",
      "Analogous organs provide evidence for",
      ["convergent evolution", "divergent evolution", "homologous ancestry",
       "spontaneous generation"], 0,
      "Analogous organs have different structural origins but similar "
      "functions, indicating convergent evolution."),
    q("Human Reproduction", "EASY",
      "The middle piece of a human sperm is packed with",
      ["mitochondria", "lysosomes", "ribosomes", "Golgi bodies"], 0,
      "The middle piece contains numerous mitochondria that supply the energy "
      "for the motility of the sperm."),
]
