import os
import shutil
from tqdm import tqdm

result_dir  = "/media/hdd3/neo/results_bma_v1/"
save_dir = "/media/hdd3/neo/results_bma_v1/selected_focus_regions"

# for every folder in the result_dir if the folder contains a subfolder "focus_regions" 
# and if folder/focus_regions contains a further subfolder "high_mag_unannotated"
# copy all the files in "high_mag_unannotated" to save_dir

for folder in tqdm(os.listdir(result_dir), desc="Processing Results"):
    if os.path.isdir(os.path.join(result_dir, folder)):
        if "focus_regions" in os.listdir(os.path.join(result_dir, folder)):
            if "high_mag_unannotated" in os.listdir(os.path.join(result_dir, folder, "focus_regions")):
                high_mag_unannotated_dir = os.path.join(result_dir, folder, "focus_regions", "high_mag_unannotated")
                for file in os.listdir(high_mag_unannotated_dir):
                    shutil.copy(os.path.join(high_mag_unannotated_dir, file), os.path.join(save_dir, file))