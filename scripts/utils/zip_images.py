import os
import shutil
from tqdm import tqdm

data_dir = "/media/hdd3/neo/results_bma_aml_v2"

folders_to_zip = [
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

for result_folder in tqdm(result_folders, desc="Parital Zipping Results Folders:"):
    for folder_to_zip in folders_to_zip:
        # if result_folder/focus_regions/folder_to_zip exists, zip it and make sure to remove the original folder
        folder_path = os.path.join(
            data_dir, result_folder, "focus_regions", folder_to_zip
        )

        if os.path.exists(folder_path):
            # remove the folder
            shutil.rmtree(folder_path)
