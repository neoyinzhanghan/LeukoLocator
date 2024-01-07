####################################################################################################
# Imports ##########################################################################################
####################################################################################################

# Outside imports ##################################################################################
import numpy as np
import yaml


# Within package imports ###########################################################################
from LL.resources.assumptions import *


def numpy_to_python(value):
    """Converts numpy objects to Python native objects."""
    if isinstance(value, (np.generic, np.ndarray)):
        return value.item() if np.isscalar(value) else value.tolist()
    else:
        return value


def save_selected_variables_to_yaml(variable_names, yaml_file):
    # Extract specified variables from the current scope
    variables = {name: globals()[name] for name in variable_names if name in globals()}

    # Write to YAML file
    with open(yaml_file, "w") as file:
        yaml.dump(variables, file, default_flow_style=False, sort_keys=False)


# List of variable names to save
selected_variable_names = [
    "dump_dir",
    "focus_regions_size",
    "snap_shot_size",
    "search_view_level",
    "search_view_crop_size",
    "num_classes",
    "top_view_patch_size",
    "min_specimen_prop",
    "do_zero_pad",
    "foci_sds",
    "foci_sd_inc",
    "min_VoL",
    "search_view_downsample_rate",
    "min_cell_VoL",
    "min_WMP",
    "max_WMP",
    "focus_region_outlier_tolerance",
    "min_top_view_mask_prop",
    "max_num_cells",
    "min_num_regions_within_foci_sd",
    "min_num_regions_after_VoL_filter",
    "min_num_regions_after_WMP_min_filter",
    "min_num_regions_after_WMP_max_filter",
    "min_num_regions_after_region_clf",
    "max_num_regions_after_region_clf",
    "num_gpus",
    "num_cpus",
    "num_croppers",
    "num_YOLOManagers",
    "max_num_wbc_per_manager",
    "num_labellers",
    "num_region_clf_managers",
    "num_focus_region_makers",
    "num_gpus_per_manager",
    "num_cpus_per_manager",
    "num_cpus_per_cropper",
    "allowed_reading_time",
    "region_clf_batch_size",
    "cell_clf_batch_size",
    "YOLO_batch_size",
    "region_clf_ckpt_path",
    "region_clf_conf_thres",
    "YOLO_ckpt_path",
    "YOLO_conf_thres",
    "HemeLabel_ckpt_path",
    "omitted_classes",
    "removed_classes",
]
