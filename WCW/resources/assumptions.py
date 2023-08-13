focus_regions_size = 2048
snap_shot_size = 96
search_view_level = 3
search_view_crop_size = (1536, 768)
num_classes = 23
top_view_patch_size = 64
min_specimen_prop = 0.25
foci_sds = 6
min_VoL = 10 # 10
min_WMP = 0.55 # 0.55
max_WMP = 0.9 # 0.9
focus_region_outlier_tolerance = 1
num_gpus = 3
num_cpus = 18
num_gpus_per_manager = 1
num_cpus_per_manager = num_cpus // (num_gpus // num_gpus_per_manager)
allowed_time = 20 # in seconds

min_cell_VoL = 10

do_zero_pad = False

YOLO_ckpt_path = "/home/greg/Documents/neo/WhiteCellWizard/WCW/resources/YOLO_checkpoint.pt"
YOLO_conf_thres = 0.27
HemeLabel_ckpt_path = "/home/greg/Documents/neo/WhiteCellWizard/WCW/resources/HemeLabel_weights.ckpt"
dump_dir = "/media/hdd3/neo/dump"

cellnames = ['B1', 'B2', 'E1', 'E4', 'ER1', 'ER2', 'ER3', 'ER4', 'ER5', 'ER6',
             'L2', 'L4', 'M1', 'M2', 'M3', 'M4', 'M5', 'M6',
             'MO2', 'PL2', 'PL3', 'U1', 'U4'] # the last element would never be indexed

ignored_cellnames = ['ER5', 'ER6']
what_to_ignore = 'class' # 'class' or 'instance' if ignore class, then the softmax probability of ignored classes will be set to -np.inf, if ignore instance, then instances of ignored classes will be removed

cellnames_dict = {
    'M1': 'Blast',
    'M2': 'Promyelocyte',
    'M3': 'Myelocyte',
    'M4': 'Metamyelocyte',
    'M5': 'Band neutrophil',
    'M6': 'Segmented netrophil',
    'E0': 'Immature Eosinophil',
    'E1': 'Eosinophil myelocyte',
    'E2': 'Eosinophil metamyelocyte',
    'E3': 'Eosinophil band',
    'E4': 'Eosinophil seg',
    'B1': 'Mast Cell',
    'B2': 'Basophil',
    'MO1': 'Monoblast',
    'MO2': 'Monocyte',
    'L0': 'Lymphoblast',
    'L1': 'Hematogone',
    'L2': 'Small Mature Lymphocyte',
    'L3': 'Reactive lymphocyte/LGL',
    'L4': 'Plasma Cell',
    'ER1': 'Pronormoblast',
    'ER2': 'Basophilic Normoblast',
    'ER3': 'Polychromatophilic Normoblast',
    'ER4': 'Orthochromic Normoblast',
    'ER5': 'Polychromatophilic Erythrocyte',
    'ER6': 'Mature Erythrocyte',
    'U1': 'Artifact',
    'U2': 'Unknown',
    'U3': 'Other',
    'U4': 'Mitotic Body',
    'U5': 'Karyorrhexis',
    'UL': 'Unlabelled',
    'PL1': 'Immature Megakaryocyte',
    'PL2': 'Mature Megakaryocyte',
    'PL3': 'Platelet Clump',
    'PL4': 'Giant Platelet',
    'R': 'Removed Due to Class Ignoring'
}

supported_extensions = ['.svs', '.ndpi']
test_example_path = "/media/hdd1/neo/PB2/666 - 2023-05-31 22.53.12.ndpi"