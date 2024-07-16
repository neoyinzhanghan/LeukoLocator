import os
import shutil
from tqdm import tqdm

data_dir = "/media/hdd1/neo/results_bma_normal_v3_cleaned"

# get the paths of all first level subdirectories in data_dir
subfolders = [f.path for f in os.scandir(data_dir) if f.is_dir()]

# filter out subfolders that start with "ERROR"
subfolders = [f for f in subfolders if not f.split("/")[-1].startswith("ERROR")]

# in each subfolders there is a further subdirectory called "cells", get the further further subdirectories of the cells directory
cell_image_dirs = []

for subfolder in subfolders:
    cells_folder = os.path.join(subfolder, "cells")
    if os.path.isdir(cells_folder):
        cell_types = [f.path for f in os.scandir(cells_folder) if f.is_dir()]
        cell_image_dirs.extend(cell_types)

for cell_image_dir in tqdm(cell_image_dirs, desc="Deleting OG Features"):
    # delete the OG_features folder in each of the cell_image_dirs if it exists
    og_features_folder = os.path.join(cell_image_dir, "OG_features")

    if os.path.exists(og_features_folder):
        shutil.rmtree(og_features_folder)
