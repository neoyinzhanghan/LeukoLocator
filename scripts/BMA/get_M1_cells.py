import pandas as pd
import os
import shutil
from tqdm import tqdm
from LLRunner.BMAassumptions import cellnames

results_dir = "/media/hdd3/neo/results_bma_normal_v2"
save_dir = "/media/hdd3/neo/normal_bma_blasts_v2"

# Create directories if they don't exist
os.makedirs(save_dir, exist_ok=True)

# Get all the subfolders that do not start with 'ERROR_' in the results directory
subfolders = [
    f.path
    for f in os.scandir(results_dir)
    if f.is_dir() and not f.name.startswith("ERROR_")
]

second_class_count = {}

for cellname in cellnames:
    second_class_count[cellname] = 0

total_M1_count = 0

for subfolder in tqdm(subfolders, desc="Reading Data"):
    cells_df = pd.read_csv(os.path.join(subfolder, "cells/cells_info.csv"))

    # Compute 'first' and 'second' columns before filtering
    cells_df["first"] = cells_df[cellnames].idxmax(axis=1)
    cells_df["second"] = cells_df[cellnames].apply(
        lambda row: row.nlargest(2).index[-1], axis=1
    )

    # Filter cells based on 'first' and 'second' classes
    M1_cells = cells_df[(cells_df["first"] == "M1")]
    # Copy files from source to destination
    for index, row in M1_cells.iterrows():
        cell_name = row["name"]
        cell_path = os.path.join(
            subfolder, "cells", cell_name.split("-")[0], cell_name
        )  # Corrected path
        save_path = os.path.join(save_dir, cell_name.split(".")[0] + subfolder + ".jpg")
        shutil.copy(cell_path, save_path)

    # Count the number of cells whose second class is cellname for cellname in cellnames
    for cellname in cellnames:
        second_class_count[cellname] += len(
            cells_df[(cells_df["first"] == "M1") & (cells_df["second"] == cellname)]
        )

    total_M1_count += len(M1_cells)

# make a bar plot of the second class count, and include the total M1 count as the title of the plot, save the plot in the results directory as M1_second_class_count.png

import matplotlib.pyplot as plt

plt.bar(second_class_count.keys(), second_class_count.values())
plt.title(f"Total M1 Cells: {total_M1_count}")
plt.savefig(os.path.join(save_dir, "M1_second_class_count.png"))
