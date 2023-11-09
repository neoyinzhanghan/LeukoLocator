#################
### Logistics ###
#################

dump_dir = "/media/hdd3/neo/resultsv3"

############################
### WSI Image Parameters ###
############################

focus_regions_size = 2048
snap_shot_size = 96
search_view_level = 3
search_view_crop_size = (1536, 768)
num_classes = 23
top_view_patch_size = 64
min_specimen_prop = 0.25
do_zero_pad = False


#######################
### Quality Control ###
#######################

foci_sds = 6
foci_sd_inc = 1

min_VoL = 100  # 10
search_view_downsample_rate = 8
min_cell_VoL = 10

min_WMP = 0.5  # it use to be
max_WMP = 0.7  # it use to be 0.9, but I think we can start reducing this a bit as there are too many regions from the periphery of the smear

focus_region_outlier_tolerance = 3

########################
### Quantity Control ###
########################

min_top_view_mask_prop = 0.3
max_num_candidates = 16384
min_num_regions_within_foci_sd = 500
min_num_regions_after_VoL_filter = 400
min_num_regions_after_WMP_min_filter = 275
min_num_regions_after_WMP_max_filter = 150
min_num_regions_after_region_clf = 100
max_num_regions_after_region_clf = 1000

###########################
### Parallel Processing ###
###########################

num_gpus = 3
num_cpus = 16
num_croppers = 8
num_gpus_per_manager = 1
num_cpus_per_manager = num_cpus // (num_gpus // num_gpus_per_manager)
num_cpus_per_cropper = num_cpus // num_croppers
allowed_reading_time = 20  # in seconds

#############################
### Models Configurations ###
#############################

region_clf_ckpt_path = "/home/greg/Documents/neo/LLCKPTS/LLRegionClf/V1/checkpoints/epoch=99-step=10300.ckpt"
region_clf_conf_thres = (
    0.8  # TODO need to do a conformal calibration and adjust this number accordingly
)

YOLO_ckpt_path = "/media/hdd3/neo/resources/YOLO_checkpoint.pt"
YOLO_conf_thres = 0.27

HemeLabel_ckpt_path = "/media/hdd3/neo/resources/HemeLabel_weights.ckpt"

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
]  # the last element would never be indexed

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
test_example_path = "/media/hdd1/neo/PB2/666 - 2023-05-31 22.53.12.ndpi"

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
