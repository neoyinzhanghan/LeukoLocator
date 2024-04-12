import os
import shutil
from tqdm import tqdm

data_dir = "/Users/neo/Documents/Research/MODELS/results/results_bma_normal_v1_LITE"
save_dir = "/Users/neo/Documents/Research/MODELS/results/cell_locations/normal"

# first find all folders in the data_dir that does not start with name ERROR and is a directory
folders = [
    f
    for f in os.listdir(data_dir)
    if not f.startswith("ERROR") and os.path.isdir(os.path.join(data_dir, f))
]

# for each folder, there is a csv file folder/cells/cells_info.csv
# copy that csv file to the save_dir using filename as folder name (with the .csv extension)
for folder in tqdm(folders, desc="Copying CSV files"):
    csv_file = os.path.join(data_dir, folder, "cells", "cells_info.csv")
    shutil.copy(csv_file, os.path.join(save_dir, f"{folder}.csv"))
