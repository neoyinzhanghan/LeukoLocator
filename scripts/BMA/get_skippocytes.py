import os
import pandas as pd
import shutil
from tqdm import tqdm
from LLRunner.assumptions import cellnames

data_dir = "/media/hdd3/neo/results_bma_normal_v2"

# find all subfolders in data_dir that do not start with 'ERROR_'
subfolders = [
    f.path
    for f in os.scandir(data_dir)
    if f.is_dir() and not f.name.startswith("ERROR_")
]


# for each subfolder, open the subfolder/cells/cells_info.csv file using pandas
# cellnames contain a list of columns that are cell names
# find the maximum value among all the cell names in the cells_info.csv file for each row separately
# for all the cells with maximum value < 0.6927, get the string at the name column
# the string .split('-')[0] is the cellclass
# the cell image is saved at subfolder/cells/{cellclass}/{cellname}
# copy the image and save it at subfolder/skippocytes/{cellclass}/{cellname}

for subfolder in tqdm(subfolders, desc="Finding Skippocytes"):
    cells_info = pd.read_csv(os.path.join(subfolder, "cells/cells_info.csv"))
    cells_info["max_prob"] = cells_info[cellnames].max(axis=1)
    skippocytes = cells_info[cells_info["max_prob"] < 0.6927]

    # create the skippocytes folder
    os.makedirs(os.path.join(subfolder, "skippocytes"), exist_ok=True)

    for index, row in skippocytes.iterrows():
        cellclass = row["name"].split("-")[0]
        os.makedirs(os.path.join(subfolder, f"skippocytes/{cellclass}"), exist_ok=True)
        cellname = row["name"]
        cell_path = os.path.join(subfolder, f"cells/{cellclass}/{cellname}")
        save_path = os.path.join(subfolder, f"skippocytes/{cellclass}/{cellname}")
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        shutil.copy(cell_path, save_path)
