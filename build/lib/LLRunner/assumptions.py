############################
### Clinical Data Confid ###
############################

slide_scanning_tracker_path = "/media/ssd2/clinical_text_data/SST/SST.xlsx"
slide_scanning_tracker_sheet_name = "Sheet1"
status_results_path = "/media/ssd2/clinical_text_data/tissueType/status_results.csv"
bma_info_path = (
    "/media/ssd2/clinical_text_data/HemeParser11/hemeParser11_bm_diff_202404032109.csv"
)

######################
### Biology Config ###
######################

cellnames = [
    "B1",
    "B2",
    "E1",
    "E4",
    "ER1",
    "ER2",
    "ER3",
    "ER4",
    "ER5",
    "ER6",
    "L2",
    "L4",
    "M1",
    "M2",
    "M3",
    "M4",
    "M5",
    "M6",
    "MO2",
    "PL2",
    "PL3",
    "U1",
    "U4",
]

what_to_ignore = "class"  # 'class' or 'instance' if ignore class, then the softmax probability of ignored classes will be set to -np.inf, if ignore instance, then instances of ignored classes will be removed

cellnames_dict = {
    "M1": "Blast",  # K
    "M2": "Promyelocyte",  # K, combine with blass
    "M3": "Myelocyte",  # K
    "M4": "Metamyelocyte",  # K, and combine with band and seg
    "M5": "Band neutrophil",  # K, and combine band and seg
    "M6": "Segmented netrophil",  # K, and combine band and seg
    "E0": "Immature Eosinophil",  # K, combine with mature eosinophil
    "E1": "Eosinophil myelocyte",  # K, combine with mature eosinophil
    "E2": "Eosinophil metamyelocyte",  # K, combine with mature eosinophil
    "E3": "Eosinophil band",  # K, and combine band and seg
    "E4": "Eosinophil seg",  # K, and combine band and seg
    "B1": "Mast Cell",  # K, put them with basophils
    "B2": "Basophil",  # K
    "MO1": "Monoblast",  # NA
    "MO2": "Monocyte",  # K
    "L0": "Lymphoblast",  # NA
    "L1": "Hematogone",  # NA
    "L2": "Small Mature Lymphocyte",  # K
    "L3": "Reactive lymphocyte/LGL",  # NA
    "L4": "Plasma Cell",  # K
    "ER1": "Pronormoblast",  # Move to M1
    # K, for the differential create a new class nucleated erythroid
    "ER2": "Basophilic Normoblast",
    # K, for the differential create a new class nucleated erythroid
    "ER3": "Polychromatophilic Normoblast",
    # K, for the differential create a new class nucleated erythroid
    "ER4": "Orthochromic Normoblast",
    "ER5": "Polychromatophilic Erythrocyte",  # M
    "ER6": "Mature Erythrocyte",  # M
    "U1": "Artifact",  # R
    "U2": "Unknown",  # R
    "U3": "Other",  # R
    "U4": "Mitotic Body",  # M
    "U5": "Karyorrhexis",  # R
    "UL": "Unlabelled",  # R
    "PL1": "Immature Megakaryocyte",  # R
    "PL2": "Mature Megakaryocyte",  # R
    "PL3": "Platelet Clump",  # R
    "PL4": "Giant Platelet",  # R
    "R": "Removed",
}

supported_extensions = [".svs", ".ndpi"]

differential_group_dict = {
    "Immature Granulocyte": ["M3"],
    "Neutrophil": ["M4", "M5", "M6"],
    "Eosinophil": ["E1", "E4"],
    "Blast": ["M1", "ER1", "M2"],
    "Monocyte": ["MO2"],
    "Lymphocyte": ["L2", "L4"],
    "Nucleated RBC": ["ER2", "ER3", "ER4"],
    "Basophil": ["B2", "B1"],
}

# differential_group_dict = {
#     'Immature Granulocyte': ['M3'],
#     'Neutrophil': ['M4', 'M5', 'M6'],
#     'Eosinophil': ['E0', 'E1', 'E2', 'E3', 'E4'],
#     'Blast': ['M1', 'ER1', 'M2'],
#     'Monocyte': ['MO2'],
#     'Lymphocyte': ['L2'],
#     'Nucleated RBC': ['ER2', 'ER3', 'ER4'],
#     'Basophil': ['B2', 'B1'],
# }

PB_final_classes = [
    "Immature Granulocyte",
    "Neutrophil",
    "Eosinophil",
    "Blast",
    "Monocyte",
    "Lymphocyte",
    "Nucleated RBC",
    "Basophil",
]

omitted_classes = ["ER5", "ER6", "U4"]
removed_classes = ["U1", "PL2", "PL3"]

# kept_cellnames are the cellnames that are not in omitted_classes and removed_classes
kept_cellnames = [
    cellname
    for cellname in cellnames
    if cellname not in omitted_classes and cellname not in removed_classes
]

translate = {
    "Mono": "Monocyte",
    "mono": "Monocyte",
    "Eos": "Eosinophil",
    "eos": "Eosinophil",
    "Baso": "Basophil",
    "baso": "Basophil",
    "Lymph": "Lymphocyte",
    "lymph": "Lymphocyte",
    "Lymphocyte": "Lymphocyte",
    "Immature Granulocyte": "Immature Granulocyte",
    "Neutrophil": "Neutrophil",
    "Eosinophil": "Eosinophil",
    "Blast": "Blast",
    "Monocyte": "Monocyte",
    "Nucleated RBC": "Nucleated RBC",
    "lymphocyte": "Lymphocyte",
    "immature granulocyte": "Immature Granulocyte",
    "neutrophil": "Neutrophil",
    "eosinophil": "Eosinophil",
    "blast": "Blast",
    "monocyte": "Monocyte",
    "nucleated rbc": "Nucleated RBC",
}
