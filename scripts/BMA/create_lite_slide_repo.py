import os
import numpy as np
import shutil
from pathlib import Path
from tqdm import tqdm

data_dir = "/media/hdd1/neo/BMA_AML"
save_dir = "/media/hdd1/neo/BMA_AML_lite"
results_dir = "/media/hdd3/neo/results_bma_aml_v3"
num_slides = 25

# make the save_dir if it does not exist
os.makedirs(save_dir, exist_ok=True)

# gather the path fo all the .ndpi files in the data_dir
ndpi_files = list(Path(data_dir).rglob("*.ndpi"))

# get the name of all the folders in the results_dir
subfolders = [
    f.name
    for f in os.scandir(results_dir)
    if f.is_dir() and not f.name.startswith("ERROR_")
]

# for each of ndpi file, find the folder in subfolders that contain the file name (without the extension) of the ndpi file

num_found = 0
for ndpi_file in tqdm(ndpi_files, desc="Creating Lite Slide Repo"):

    if num_found >= num_slides:
        break
    ndpi_file_name = ndpi_file.stem

    # find the folder in subfolders that contains the ndpi_file_name
    subfolder = next(
        (subfolder for subfolder in subfolders if ndpi_file_name in subfolder),
        None,
    )

    if subfolder is None:
        continue

    # if the subfolder starts with 'ERROR_', skip it
    if subfolder.startswith("ERROR_"):
        continue

    # copy the ndpi file to the save_dir as a symlink
    os.makedirs(os.path.join(save_dir, subfolder), exist_ok=True)
    os.symlink(ndpi_file, os.path.join(save_dir, subfolder, ndpi_file_name + ".ndpi"))

    num_found += 1
