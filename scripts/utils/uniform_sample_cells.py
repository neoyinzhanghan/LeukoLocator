import os
import random
import shutil
import pandas as pd
from tqdm import tqdm

PB_dir = "/media/hdd3/neo/resultsv5"
BMA_dir = "/media/hdd3/neo/results_bma_all_v2_rerun"

save_dir = "/media/hdd3/neo/200K_cells"

os.makedirs(save_dir, exist_ok=True)

# get all the subdirectories in the PB_dir that does not start with ERROR
PB_folders = [
    f
    for f in os.listdir(PB_dir)
    if not f.startswith("ERROR") and os.path.isdir(os.path.join(PB_dir, f))
]

# get all the subdirectories in the BMA_dir that does not start with ERROR
BMA_folders = [
    f
    for f in os.listdir(BMA_dir)
    if not f.startswith("ERROR") and os.path.isdir(os.path.join(BMA_dir, f))
]

# check if any of the folders do not contain a cells subfolder
num_bad = 0
bad = []
for folder in tqdm(PB_folders, desc="Sanity checking PB folders"):
    if not os.path.exists(os.path.join(PB_dir, folder, "cells")):
        num_bad += 1
        bad.append(folder)

for folder in tqdm(BMA_folders, desc="Sanity checking BMA folders"):
    if not os.path.exists(os.path.join(BMA_dir, folder, "cells")):
        num_bad += 1
        bad.append(folder)

print(f"Found {num_bad} bad folders: {bad}")
print(bad)
if len(bad) > 0:
    raise ValueError("Found bad folders")


metadata = {
    "idx": [],
    "original_path": [],
    "cell_type": [],
    "slide_folder": [],
}

current_index = 0
num_cells = 200000

for i in tqdm(
    range(num_cells),
    desc="Sampling cells",
    total=num_cells,
    unit="cell",
    unit_scale=True,
    unit_divisor=int(1e3),
):
    # first decide PB or BMA, randomly with 50% chance each
    # then randomly choose a folder from the chosen type
    if random.random() < 0.5:
        folder = random.choice(PB_folders)
        folder_path = os.path.join(PB_dir, folder)
    else:
        folder = random.choice(BMA_folders)
        folder_path = os.path.join(BMA_dir, folder)

    # in folder/cells, randomly select a subfolder (make sure to skip non-directories)
    cells_folder = os.path.join(folder_path, "cells")
    cell_types = [
        f
        for f in os.listdir(cells_folder)
        if os.path.isdir(os.path.join(cells_folder, f))
    ]
    cell_type = random.choice(cell_types)

    # randomly select an image from the chosen subfolder
    cell_type_folder = os.path.join(cells_folder, cell_type)

    images = [f for f in os.listdir(cell_type_folder) if f.endswith(".jpg")]

    while len(images) == 0:
        cell_type = random.choice(cell_types)
        cell_type_folder = os.path.join(cells_folder, cell_type)
        images = [f for f in os.listdir(cell_type_folder) if f.endswith(".jpg")]

    image = random.choice(images)

    # copy the image to the save_dir, the new image name should be the current index dot jpg
    image_path = os.path.join(cell_type_folder, image)
    shutil.copy(image_path, os.path.join(save_dir, f"{current_index}.jpg"))

    # update the metadata
    metadata["idx"].append(current_index)
    metadata["original_path"].append(image_path)
    metadata["cell_type"].append(cell_type)
    metadata["slide_folder"].append(folder)

    current_index += 1

# save the metadata as a csv file
metadata_df = pd.DataFrame(metadata)
metadata_df.to_csv(os.path.join(save_dir, "metadata.csv"), index=False)
