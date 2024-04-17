import pandas as pd
import os
import shutil
from tqdm import tqdm
from LLRunner.BMAassumptions import cellnames

results_dir = "/media/hdd3/neo/results_bma_aml_v2"
save_dir = "/media/hdd3/neo/cells_bma_aml_v2"

os.makedirs(save_dir, exist_ok=True)
os.makedirs(os.path.join(save_dir, "M1L2"), exist_ok=True)
os.makedirs(os.path.join(save_dir, "L2M1"), exist_ok=True)

# get all the subfolders that do not start with ERROR_ in the results directory
subfolders = [
    f.path
    for f in os.scandir(results_dir)
    if f.is_dir() and not f.name.startswith("ERROR_")
]

# get a list of data frames, which are the "cells/cells_info.csv" file in each of the subfolders
cells_dfs = []
for subfolder in tqdm(subfolders, desc="Reading Data"):
    cells_df = pd.read_csv(os.path.join(subfolder, "cells/cells_info.csv"))
    cells_dfs.append(cells_df)


# combine all these into a single data frame
cells_df = pd.concat(cells_dfs, ignore_index=True)

# for each element in cellnames there is a corresponding column in the cells_df which is the cell class probability
# get the top probability class of each cell, and the second highest probability class of each cell
cells_df["first"] = cells_df[cellnames].idxmax(axis=1)
cells_df["second"] = cells_df[cellnames].apply(
    lambda row: row.nlargest(2).index[-1], axis=1
)

# get all the cells that have M1 as the top probability class and L2 as the second highest probability class
M1L2_cells = cells_df[(cells_df["first"] == "M1") & (cells_df["second"] == "L2")]

# conversely, get all the cells that have L2 as the top probability class and M1 as the second highest probability class
L2M1_cells = cells_df[(cells_df["first"] == "L2") & (cells_df["second"] == "M1")]

# print how many cells are in each of these categories
print(f"M1L2_cells Found: {len(M1L2_cells)}")
print(f"L2M1_cells Found: {len(L2M1_cells)}")

num_cells_to_save = 1000

# randomly select 1000 rows from each of these categories
M1L2_cells_sample = M1L2_cells.sample(n=num_cells_to_save)
L2M1_cells_sample = L2M1_cells.sample(n=num_cells_to_save)


# iterate through the rows of the M1L2_cells_sample and L2M1_cells_sample data frames
# and copy the corresponding cell directories to the save_dir
for index, row in tqdm(
    M1L2_cells_sample.iterrows(), desc="M1L2", total=num_cells_to_save
):
    cell_name = row["name"]

    # the cell path is subfolder/cells/cell_name.split("-")[0]/cell_name
    cell_path = os.path.join(results_dir, cell_name.split("-")[0], "cells", cell_name)
    save_path = os.path.join(save_dir, "M1L2", cell_name)

    # cp the cell at cell_path to save_path
    shutil.copytree(cell_path, save_path)

for index, row in tqdm(
    L2M1_cells_sample.iterrows(), desc="L2M1", total=num_cells_to_save
):
    cell_name = row["name"]

    # the cell path is subfolder/cells/cell_name.split("-")[0]/cell_name
    cell_path = os.path.join(results_dir, cell_name.split("-")[0], "cells", cell_name)
    save_path = os.path.join(save_dir, "L2M1", cell_name)

    # cp the cell at cell_path to save_path
    shutil.copytree(cell_path, save_path)
