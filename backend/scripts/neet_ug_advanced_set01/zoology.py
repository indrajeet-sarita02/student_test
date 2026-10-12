"""NEET UG (Advanced Level) - Set 01 - Zoology: 45 questions."""

from __future__ import annotations

from .common import q

QUESTIONS = [
    # --- Animal Kingdom ----------------------------------------------------
    q("Animal Kingdom", "EASY",
      "The phylum characterised by a water vascular system and tube feet is",
      ["Arthropoda", "Echinodermata", "Mollusca", "Annelida"], 1,
      "Echinoderms such as starfish possess a water vascular system with tube "
      "feet used in locomotion and feeding."),
    q("Animal Kingdom", "MEDIUM",
      "The simplest metazoans that show a tissue level of organisation belong "
      "to",
      ["Porifera", "Platyhelminthes", "Aschelminthes", "Cnidaria"], 3,
      "Cnidarians (Coelenterata) show a tissue level of organisation, whereas "
      "sponges have only a cellular level of organisation."),
    q("Animal Kingdom", "HARD",
      "Flame cells (protonephridia), which help in excretion and "
      "osmoregulation, are found in",
      ["Platyhelminthes", "Nematoda", "Annelida", "Arthropoda"], 0,
      "Flame cells are the excretory and osmoregulatory structures of "
      "flatworms (Platyhelminthes)."),

    # --- Structural Organisation in Animals --------------------------------
    q("Structural Organisation in Animals", "EASY",
      "The tissue that connects a muscle to a bone is",
      ["Ligament", "Cartilage", "Tendon", "Areolar tissue"], 2,
      "A tendon is a dense connective tissue that joins skeletal muscle to "
      "bone, whereas a ligament joins bone to bone."),
    q("Structural Organisation in Animals", "MEDIUM",
      "The epithelium that lines the inner surface of the mouth is",
      ["Simple squamous", "Stratified squamous", "Cuboidal",
       "Ciliated columnar"], 1,
      "The mouth is lined by stratified squamous epithelium, which protects "
      "against mechanical abrasion."),

    # --- Digestion and Absorption ------------------------------------------
    q("Digestion and Absorption", "EASY",
      "The hardest substance in the human body is",
      ["Enamel", "Dentine", "Cementum", "Pulp"], 0,
      "Enamel, the outermost covering of a tooth, is the hardest substance in "
      "the human body."),
    q("Digestion and Absorption", "MEDIUM",
      "The enzyme pepsin acts in the",
      ["Mouth", "Duodenum", "Ileum", "Stomach"], 3,
      "Pepsin is a protease that acts in the acidic medium of the stomach, "
      "converting proteins into peptones."),
    q("Digestion and Absorption", "HARD",
      "Bile juice helps mainly in the",
      ["digestion of proteins", "absorption of glucose",
       "emulsification of fats", "absorption of water"], 2,
      "Bile salts emulsify fats, breaking large fat globules into smaller "
      "droplets so that lipases can act on them."),

    # --- Breathing and Exchange of Gases -----------------------------------
    q("Breathing and Exchange of Gases", "EASY",
      "Exchange of respiratory gases in the lungs occurs across the",
      ["Bronchi", "Alveoli", "Trachea", "Larynx"], 1,
      "The thin, highly vascular walls of the alveoli are the actual site of "
      "gaseous exchange between air and blood."),
    q("Breathing and Exchange of Gases", "MEDIUM",
      "The volume of air inspired or expired during normal breathing (tidal "
      "volume) is about",
      ["500 mL", "1500 mL", "2500 mL", "3000 mL"], 0,
      "Tidal volume is about 500 mL in a healthy adult; larger volumes are "
      "used during forced breathing."),
    q("Breathing and Exchange of Gases", "HARD",
      "Most of the carbon dioxide is transported in the blood as",
      ["carbaminohemoglobin", "dissolved CO2 in plasma", "carbonic acid",
       "bicarbonate ions"], 3,
      "About 70% of CO2 is carried as bicarbonate ions, about 20-25% as "
      "carbaminohemoglobin and the rest dissolved in plasma."),

    # --- Body Fluids and Circulation ---------------------------------------
    q("Body Fluids and Circulation", "EASY",
      "The natural pacemaker of the human heart is the",
      ["AV node", "Bundle of His", "SA node", "Purkinje fibres"], 2,
      "The sino-atrial (SA) node generates the impulses that set the rhythm of "
      "the heartbeat, so it acts as the pacemaker."),
    q("Body Fluids and Circulation", "MEDIUM",
      "The blood group regarded as the universal donor is",
      ["O negative", "AB positive", "A positive", "B negative"], 0,
      "O negative red cells carry neither A, B nor Rh D antigens, so they can "
      "be given to almost all recipients (universal donor)."),
    q("Body Fluids and Circulation", "HARD",
      "Erythroblastosis foetalis is likely to occur when",
      ["the mother is Rh-positive and the foetus is Rh-negative",
       "the mother is Rh-negative and the foetus is Rh-positive",
       "only ABO incompatibility exists",
       "both the mother and the foetus are Rh-negative"], 1,
      "An Rh-negative mother sensitised to Rh-positive foetal cells produces "
      "antibodies that destroy the red cells of a subsequent Rh-positive "
      "foetus."),

    # --- Excretory Products and their Elimination --------------------------
    q("Excretory Products and their Elimination", "EASY",
      "The structural and functional unit of the kidney is the",
      ["Neuron", "Alveolus", "Nephridium", "Nephron"], 3,
      "Each kidney contains about a million nephrons, the units that filter "
      "blood and form urine."),
    q("Excretory Products and their Elimination", "MEDIUM",
      "The hormone that increases water reabsorption in the collecting duct is",
      ["Aldosterone", "Renin", "ADH (vasopressin)", "ANF"], 2,
      "Antidiuretic hormone increases the permeability of the collecting duct "
      "to water, concentrating the urine."),
    q("Excretory Products and their Elimination", "HARD",
      "The juxtaglomerular cells of the kidney secrete",
      ["Renin", "Erythropoietin", "ADH", "Aldosterone"], 0,
      "Juxtaglomerular cells release renin, which starts the "
      "renin-angiotensin-aldosterone system that raises blood pressure."),

    # --- Locomotion and Movement -------------------------------------------
    q("Locomotion and Movement", "EASY",
      "The functional unit of contraction in a muscle fibre is the",
      ["Myofibril", "Sarcomere", "Myosin", "Actin"], 1,
      "The sarcomere, the region between two successive Z-lines, is the "
      "functional unit of muscle contraction."),
    q("Locomotion and Movement", "MEDIUM",
      "The number of bones in the adult human body is",
      ["106", "156", "306", "206"], 3,
      "An adult human skeleton has 206 bones."),
    q("Locomotion and Movement", "HARD",
      "The joint between the humerus and the pectoral girdle is a",
      ["Hinge joint", "Pivot joint", "Ball and socket joint",
       "Gliding joint"], 2,
      "The shoulder joint is a ball-and-socket joint, allowing movement in "
      "all planes."),

    # --- Neural Control and Coordination -----------------------------------
    q("Neural Control and Coordination", "EASY",
      "The structural and functional unit of the nervous system is the",
      ["Neuron", "Nephron", "Neuroglia", "Axon"], 0,
      "The neuron is the structural and functional unit of the nervous "
      "system."),
    q("Neural Control and Coordination", "MEDIUM",
      "The gap between two successive myelin sheaths along an axon is called a",
      ["Synapse", "Node of Ranvier", "Dendrite", "Neurotransmitter"], 1,
      "The unmyelinated gaps in a myelinated axon are called nodes of "
      "Ranvier, where saltatory conduction occurs."),
    q("Neural Control and Coordination", "HARD",
      "The resting membrane potential of a neuron is maintained chiefly by the",
      ["Na+ channels only", "K+ channels only", "Ca2+ pump",
       "Na+/K+ ATPase pump"], 3,
      "The Na+/K+ ATPase pump transports 3 Na+ out and 2 K+ in, maintaining "
      "the resting potential across the membrane."),

    # --- Chemical Coordination and Integration -----------------------------
    q("Chemical Coordination and Integration", "EASY",
      "The hormone that lowers blood glucose is",
      ["Glucagon", "Adrenaline", "Insulin", "Cortisol"], 2,
      "Insulin, secreted by the beta cells of the islets of Langerhans, "
      "lowers blood glucose by promoting its uptake and storage."),
    q("Chemical Coordination and Integration", "MEDIUM",
      "The 'master gland' of the human body is the",
      ["Pituitary", "Thyroid", "Adrenal", "Pancreas"], 0,
      "The pituitary is called the master gland because it controls the "
      "secretion of many other endocrine glands."),
    q("Chemical Coordination and Integration", "HARD",
      "The hormone secreted by the corpus luteum is",
      ["Estrogen only", "Progesterone", "FSH", "LH"], 1,
      "The corpus luteum mainly secretes progesterone, which maintains the "
      "uterine lining during the early stages of pregnancy."),

    # --- Human Reproduction -------------------------------------------------
    q("Human Reproduction", "EASY",
      "The male gamete in humans is the",
      ["Ovum", "Zygote", "Spermatozoon", "Oogonium"], 2,
      "The spermatozoon (sperm) is the motile male gamete."),
    q("Human Reproduction", "MEDIUM",
      "Fertilisation in humans normally occurs in the",
      ["Fallopian tube (ampulla)", "Uterus", "Ovary", "Cervix"], 0,
      "Fertilisation normally takes place in the ampullary-isthmic junction "
      "of the fallopian tube."),
    q("Human Reproduction", "HARD",
      "The hormone that triggers ovulation is",
      ["FSH", "LH", "Progesterone", "Estrogen"], 1,
      "A surge of luteinising hormone (LH) around the middle of the cycle "
      "triggers the rupture of the mature follicle (ovulation)."),

    # --- Reproductive Health ------------------------------------------------
    q("Reproductive Health", "EASY",
      "The surgical method of permanent birth control in females is",
      ["Vasectomy", "Condom", "IUD", "Tubectomy"], 3,
      "Tubectomy (tubal ligation) is the surgical sterilisation method used "
      "in females; vasectomy is used in males."),
    q("Reproductive Health", "MEDIUM",
      "Oral contraceptive pills prevent pregnancy mainly by",
      ["preventing ovulation", "killing sperms in the vagina",
       "blocking the fallopian tubes", "preventing implantation only"], 0,
      "Combined oral pills contain hormones that suppress the release of "
      "gonadotropins, thereby preventing ovulation."),

    # --- Human Health and Disease ------------------------------------------
    q("Human Health and Disease", "EASY",
      "Malaria is caused by",
      ["Vibrio cholerae", "Trypanosoma", "Plasmodium", "HIV"], 2,
      "Malaria is caused by the protozoan Plasmodium, transmitted by the "
      "bite of an infected female Anopheles mosquito."),
    q("Human Health and Disease", "MEDIUM",
      "AIDS is caused by",
      ["a DNA virus", "a retrovirus (HIV)", "a bacterium", "a protozoan"], 1,
      "HIV is a retrovirus that infects helper T-lymphocytes and causes "
      "AIDS."),
    q("Human Health and Disease", "HARD",
      "Antibody-mediated immunity is also known as",
      ["Humoral immunity", "Cell-mediated immunity", "Innate immunity",
       "Passive immunity"], 0,
      "Antibody-mediated (B-cell) immunity acts through antibodies in the "
      "body fluids, so it is called humoral immunity."),

    # --- Biotechnology and its Applications --------------------------------
    q("Biotechnology and its Applications", "EASY",
      "The enzyme used to cut DNA at specific recognition sites is",
      ["DNA ligase", "DNA polymerase", "Helicase",
       "Restriction endonuclease"], 3,
      "Restriction endonucleases recognise specific base sequences and cut "
      "DNA at those sites, producing sticky ends."),
    q("Biotechnology and its Applications", "MEDIUM",
      "The polymerase chain reaction (PCR) is used to",
      ["separate proteins", "join DNA fragments", "amplify DNA", "stain DNA"], 2,
      "PCR amplifies (makes many copies of) a specific segment of DNA using "
      "primers, a polymerase and thermal cycling."),
    q("Biotechnology and its Applications", "HARD",
      "Bt cotton is resistant to insect pests because it carries",
      ["a gene from E. coli", "cry genes from Bacillus thuringiensis",
       "a gene from Agrobacterium", "a gene from yeast"], 1,
      "Bt cotton expresses cry genes from Bacillus thuringiensis, whose "
      "protein is toxic to certain insect larvae."),

    # --- Ecology and Environment -------------------------------------------
    q("Organisms and Populations", "EASY",
      "The interaction in which both interacting species benefit is called",
      ["Mutualism", "Parasitism", "Commensalism", "Predation"], 0,
      "In mutualism both partners benefit, giving a (+/+) relationship, as in "
      "lichens and mycorrhizae."),
    q("Ecosystem", "EASY",
      "The non-living components of an ecosystem are called",
      ["Biotic", "Organic", "Abiotic", "Climatic only"], 2,
      "Abiotic components include physical and chemical factors such as "
      "light, temperature, water and minerals."),
    q("Ecosystem", "MEDIUM",
      "The pyramid of energy in an ecosystem is",
      ["Always inverted", "Sometimes inverted", "Variable", "Always upright"], 3,
      "Energy decreases at each successive trophic level, so the pyramid of "
      "energy is always upright."),
    q("Ecosystem", "MEDIUM",
      "The ten percent law of energy transfer was given by",
      ["Odum", "Lindeman", "Tansley", "Darwin"], 1,
      "Lindeman (1942) proposed that only about 10% of the energy at one "
      "trophic level is transferred to the next."),
    q("Environmental Issues", "HARD",
      "The ozone layer protects living organisms from",
      ["Infrared rays", "X-rays", "Ultraviolet radiation", "Microwaves"], 2,
      "Stratospheric ozone absorbs harmful ultraviolet radiation from the "
      "Sun, protecting living organisms."),

    # --- Genetics and Evolution --------------------------------------------
    q("Principles of Inheritance and Variation", "EASY",
      "Alternative forms of the same gene are called",
      ["Alleles", "Genes", "Chromosomes", "Genomes"], 0,
      "Alleles are the alternative forms of a gene that occupy the same locus "
      "on homologous chromosomes."),
    q("Evolution", "MEDIUM",
      "The theory of natural selection was proposed by",
      ["Lamarck", "De Vries", "Mendel", "Darwin"], 3,
      "Charles Darwin proposed the theory of natural selection in his book "
      "'On the Origin of Species'."),
    q("Principles of Inheritance and Variation", "HARD",
      "The ABO blood group system in humans is an example of",
      ["Codominance only", "Multiple alleles", "Incomplete dominance",
       "Pleiotropy"], 1,
      "The ABO system is controlled by three alleles (IA, IB and i) of a "
      "single gene, so it is an example of multiple alleles."),
]
