import pandas as pd
import os
import shutil
from tqdm import tqdm
from LLRunner.BMAassumptions import cellnames

results_dir = "/media/hdd3/neo/results_bma_pcm_v2"
save_dir = "/media/hdd3/neo/cells_bma_pcm_v2"

# Create directories if they don't exist
os.makedirs(save_dir, exist_ok=True)
os.makedirs(os.path.join(save_dir, "M1L2"), exist_ok=True)
os.makedirs(os.path.join(save_dir, "L2M1"), exist_ok=True)

# Get all the subfolders that do not start with 'ERROR_' in the results directory
subfolders = [f.path for f in os.scandir(results_dir) if f.is_dir() and not f.name.startswith("ERROR_")]

for subfolder in tqdm(subfolders, desc="Reading Data"):
    cells_df = pd.read_csv(os.path.join(subfolder, "cells/cells_info.csv"))

    # Compute 'first' and 'second' columns before filtering
    cells_df["first"] = cells_df[cellnames].idxmax(axis=1)
    cells_df["second"] = cells_df[cellnames].apply(lambda row: row.nlargest(2).index[-1], axis=1)

    # Filter cells based on 'first' and 'second' classes
    M1L2_cells = cells_df[(cells_df["first"] == "M1") & (cells_df["second"] == "L2")]
    L2M1_cells = cells_df[(cells_df["first"] == "L2") & (cells_df["second"] == "M1")]

    print(f"M1L2_cells Found: {len(M1L2_cells)}")
    print(f"L2M1_cells Found: {len(L2M1_cells)}")

    num_cells_to_save = 10  # It seems like you meant to save 10, not 1000

    # Sample the rows randomly
    if len(M1L2_cells) >= num_cells_to_save:
        M1L2_cells_sample = M1L2_cells.sample(n=num_cells_to_save)
    else:
        M1L2_cells_sample = M1L2_cells

    if len(L2M1_cells) >= num_cells_to_save:
        L2M1_cells_sample = L2M1_cells.sample(n=num_cells_to_save)
    else:
        L2M1_cells_sample = L2M1_cells

    # Copy files from source to destination
    for index, row in M1L2_cells_sample.iterrows():
        cell_name = row["name"]
        cell_path = os.path.join(subfolder, "cells", cell_name.split("-")[0], cell_name)  # Corrected path
        save_path = os.path.join(save_dir, "M1L2", cell_name)
        shutil.copy(cell_path, save_path)

    for index, row in L2M1_cells_sample.iterrows():
        cell_name = row["name"]
        cell_path = os.path.join(subfolder, "cells", cell_name.split("-")[0], cell_name)  # Corrected path
        save_path = os.path.join(save_dir, "L2M1", cell_name)
        shutil.copy(cell_path, save_path)
