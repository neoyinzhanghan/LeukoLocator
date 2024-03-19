#################
### Logistics ###
#################

# dump_dir = "/media/hdd2/neo/LLResults/debug" # this one is for alpaca
dump_dir = "/media/hdd3/neo/results_pb_chosen"

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
min_cell_VoL = 0

min_WMP = 0.5  # it use to be
max_WMP = 0.7  # it use to be 0.9, but I think we can start reducing this a bit as there are too many regions from the periphery of the smear

focus_region_outlier_tolerance = 3

########################
### Quantity Control ###
########################

min_top_view_mask_prop = 0.3
min_num_regions_within_foci_sd = 500
min_num_regions_after_VoL_filter = 400
min_num_regions_after_WMP_min_filter = 275
min_num_regions_after_WMP_max_filter = 150
min_num_regions_after_region_clf = 100
max_num_regions_after_region_clf = 1000
max_num_cells = 3000


###########################
### Parallel Processing ###
###########################

num_gpus = 3
num_cpus = 12
num_croppers = 32
num_YOLOManagers = 3
max_num_wbc_per_manager = max_num_cells // num_YOLOManagers
num_labellers = 3
num_region_clf_managers = 3
num_focus_region_makers = 32
num_gpus_per_manager = 1
num_cpus_per_manager = num_cpus // (num_gpus // num_gpus_per_manager)
num_cpus_per_cropper = num_cpus // num_croppers
allowed_reading_time = 60  # in seconds

region_clf_batch_size = 256
cell_clf_batch_size = 256
YOLO_batch_size = 32

#############################
### Models Configurations ###
#############################

region_clf_ckpt_path = "/home/greg/Documents/neo/LLCKPTS/LLRegionClf/V1/checkpoints/epoch=99-step=10300.ckpt"
# region_clf_ckpt_path = "/media/ssd1/neo/LLCKPTS/epoch=99-step=10300.ckpt" # This one is for alpaca
# region_clf_ckpt_path = "/media/hdd2/neo/LLCKPTS/epoch=99-step=10300.ckpt" # This one is for bear
region_clf_conf_thres = (
    0.8  # TODO need to do a rigorous calibration still, but for now we are skipping it
)

YOLO_ckpt_path = (
    "/home/greg/Documents/neo/LLCKPTS/YOLOv8/V1/detect/train/weights/best.pt"
)
# YOLO_ckpt_path = "/media/ssd1/neo/LLCKPTS/best.pt" # this one is for alpaca
# YOLO_ckpt_path = "/media/hdd2/neo/LLCKPTS/best.pt" # this one is for bear
YOLO_conf_thres = 0.8  # The calibration says 0.89 to do a 3% FNR control with pvalue less than 0.05 but we can afford to be more aggressive

# HemeLabel_ckpt_path = "/media/ssd1/neo/LLCKPTS/HemeLabel_weights.ckpt" # this one is for alpaca
# HemeLabel_ckpt_path = "/media/hdd2/neo/LLCKPTS/HemeLabel_weights.ckpt" # this one is for alpaca
HemeLabel_ckpt_path = "/media/hdd3/neo/resources/HemeLabel_weights.ckpt"

specimen_clf_checkpoint_path = "/home/greg/Documents/neo/LLCKPTS/SClf.ckpt"

feature_extractor_ckpt_dict = {
    "resnet50": "/media/hdd3/neo/resources/HemeLabel_weights.ckpt"
}
supported_feature_extraction_archs = feature_extractor_ckpt_dict.keys()

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


# These are the slides that we are going to ignore for the differential count

exception_list = [
    "H23-894;S17;MSK7 - 2023-06-15 19.18.03",
    "H22-5721;S12;MSKV - 2023-04-14 16.13.00",
    "H22-10246;S15;MSK6 - 2023-06-15 12.37.37",
    "H22-7118;S11;MSKW - 2023-06-15 17.23.30",
    "H22-10935;S16;MSKB - 2023-06-15 10.44.43",
    "H22-6251;S15;MSKX - 2023-06-15 12.44.35",
    "H21-8723;S14;MSK1 - 2023-05-19 16.23.18",
    "H21-7705;S13;MSK9 - 2023-05-31 15.31.31",
    "H21-8526;S10;MSK8 - 2023-05-19 18.10.06",
    "H21-9688;S11;MSK9 - 2023-04-19 16.55.24",
    "H21-1589;S11;MSK1 - 2023-05-22 08.07.13",
    "H20-8172;S11;MSK5 - 2023-06-15 19.59.48",
    "H20-152;S12;MSKW - 2023-06-27 22.43.39",
    "H19-8719;S13;MSKB - 2023-06-20 10.03.13",
    "H19-3488;S11;MSK8 - 2023-06-27 23.12.56",
    "H19-8904;S10;MSKO - 2023-06-20 10.26.07",
    "H18-9809;S11;MSKJ - 2023-04-25 09.52.53",
    "H18-9196;S11;MSK9 - 2023-06-21 21.36.14",
    "H18-7360;S10;MSKI - 2023-04-25 17.27.10",
    "H18-7697;S11;MSKC - 2023-06-26 20.39.06",
    "H18-6717;S12;MSK6 - 2023-06-26 13.28.54",
    "H18-6286;S2;MSK6 - 2023-04-19 16.08.29",
]
