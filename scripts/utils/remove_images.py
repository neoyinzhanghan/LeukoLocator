import os
import shutil
from tqdm import tqdm

data_dir = "/media/hdd3/neo/results_bma_normal_v2"

folders_to_remove = [
    "too_high_WMP",
    "too_low_WMP",
    "too_low_VoL",
    "resnet_conf_too_low",
    "passed",
    "inadequate",
    "adequate",
]

# get all the subdirectories in the data_dir that does not start
result_folders = [f for f in os.listdir(data_dir)]

for result_folder in tqdm(result_folders, desc="Parital Removing Results Folders:"):
    for folder_to_remove in folders_to_remove:
        # if result_folder/focus_regions/folder_to_remove exists, remove it
        folder_path = os.path.join(
            data_dir, result_folder, "focus_regions", folder_to_remove
        )

        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
