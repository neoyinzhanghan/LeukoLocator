import os
from tqdm import tqdm

results_folder = "/media/hdd3/neo/results_bma_chosen_no_masking"
save_folder = "/media/hdd3/neo/results_bma_chosen_no_masking_LITE"

os.makedirs(save_folder, exist_ok=True)

# make a carbon copy of everything in the results_folder, except the focus_regions subfolder
# delete some unnecessary subfolders in the focus_regions subfolder
# use tqdm to track progress

# first get a list of a folders in the results_folder
folders = os.listdir(results_folder)

# then make a carbon copy of each folder in the save_folder
# then delete focus_regions/YOLO_df, focus_regions/inadequate, focus_regions/adequate
# use cp -r to copy the focus_regions/high_mag_unannotated folder
# and use rm -r to delete the focus_regions/YOLO_df, focus_regions/inadequate, focus_regions/adequate folders

for folder in tqdm(folders, desc="Copying folders"):
    # make a carbon copy of the folder in the save_folder
    folder_path = os.path.join(results_folder, folder)
    save_folder_path = os.path.join(save_folder, folder)
    os.system(f"cp -r \"{folder_path} {save_folder_path}\"")

    # delete focus_regions/YOLO_df, focus_regions/inadequate, focus_regions/adequate
    focus_regions_path = os.path.join(save_folder_path, "focus_regions")
    os.system(f"rm -r \"{os.path.join(focus_regions_path, 'YOLO_df')}\"")
    os.system(f"rm -r \"{os.path.join(focus_regions_path, 'inadequate')}\"")
    os.system(f"rm -r \"{os.path.join(focus_regions_path, 'adequate')}\"")