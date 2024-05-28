import os
import random
import shutil
import pandas as pd
from tqdm import tqdm

PB_dir = "/media/hdd3/neo/resultsv5"
BMA_dir = "/media/hdd3/neo/results_bma_all_v2_rerun"
save_dir = "/media/hdd3/neo/200K_cells"

os.makedirs(save_dir, exist_ok=True)

# Get all subdirectories in PB_dir that do not start with "ERROR"
PB_folders = [
    f
    for f in os.listdir(PB_dir)
    if not f.startswith("ERROR") and os.path.isdir(os.path.join(PB_dir, f))
]

# Get all subdirectories in BMA_dir that do not start with "ERROR"
BMA_folders = [
    f
    for f in os.listdir(BMA_dir)
    if not f.startswith("ERROR") and os.path.isdir(os.path.join(BMA_dir, f))
]

# Check if any folders do not contain a "cells" subfolder
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

if num_bad > 0:
    raise ValueError(f"Found {num_bad} bad folders: {bad}")

metadata = {"idx": [], "cell_type": []}

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
    # Randomly choose either PB or BMA with a 50% chance
    if random.random() < 0.5:
        folder = random.choice(PB_folders)
        folder_path = os.path.join(PB_dir, folder)
    else:
        folder = random.choice(BMA_folders)
        folder_path = os.path.join(BMA_dir, folder)

    # Randomly select a cell type directory within the folder
    cells_folder = os.path.join(folder_path, "cells")
    cell_types = [
        f
        for f in os.listdir(cells_folder)
        if os.path.isdir(os.path.join(cells_folder, f))
    ]
    cell_type = random.choice(cell_types)

    # Randomly select an image from the chosen cell type directory
    cell_type_folder = os.path.join(cells_folder, cell_type)
    images = [f for f in os.listdir(cell_type_folder) if f.endswith(".jpg")]

    # Ensure there is at least one image to choose from
    while len(images) == 0:
        cell_type = random.choice(cell_types)
        cell_type_folder = os.path.join(cells_folder, cell_type)
        images = [f for f in os.listdir(cell_type_folder) if f.endswith(".jpg")]

    image = random.choice(images)

    # Copy the image to save_dir with a new filename based on the current index
    image_path = os.path.join(cell_type_folder, image)
    shutil.copy(image_path, os.path.join(save_dir, f"{current_index}.jpg"))

    # Update metadata (excluding original path and slide folder for deidentification)
    metadata["idx"].append(current_index)
    metadata["cell_type"].append(cell_type)

    current_index += 1

# Save metadata to a CSV file
metadata_df = pd.DataFrame(metadata)
metadata_df.to_csv(os.path.join(save_dir, "metadata.csv"), index=False)
