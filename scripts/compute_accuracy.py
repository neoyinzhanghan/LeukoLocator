import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from LL.resources.assumptions import *
from pathlib import Path


cartridges_dir = "/Users/neo/Documents/Research/DeepHeme/LLData/LabelledCartridges"

# cartridges consist of all subdirectories in cartridges_dir, make sure to check that the subdirectories are indeed directories
cartridges = [
    cartridge
    for cartridge in os.listdir(cartridges_dir)
    if os.path.isdir(os.path.join(cartridges_dir, cartridge))
]

total = 0
correct = 0

for cartridge in cartridges:
    for cellname in cellnames:
        # get all the cell images in the subfolder named cellname in the cartridge
        try:
            cell_images = os.listdir(os.path.join(cartridges_dir, cartridge, cellname))
            # make sure to check the cell_images has .jpg extension
            cell_images = [
                cell_image
                for cell_image in cell_images
                if Path(cell_image).suffix == ".jpg"
            ]
        except FileNotFoundError:
            continue

        for cell_image in cell_images:
            path = Path(cell_image)
            stem = path.stem
            if stem.split("-")[0] == cellname:
                correct += 1
            total += 1

print(f"Accuracy: {correct/total}")


# now we are going to compute class specific accuracies
# first we need to get the number of cells in each class

# get the number of cells in each class
num_cells = {}
correct_num_cells = {}
for cellname in cellnames:
    num_cells[cellname] = 0
    correct_num_cells[cellname] = 0
    for cartridge in cartridges:
        try:
            cell_images = os.listdir(os.path.join(cartridges_dir, cartridge, cellname))
            cell_images = [
                cell_image
                for cell_image in cell_images
                if Path(cell_image).suffix == ".jpg"
            ]

            for cell_image in cell_images:
                num_cells[cellname] += 1

                if cell_image.split("-")[0] == cellname:
                    correct_num_cells[cellname] += 1
        except FileNotFoundError:
            continue

accuracies = {}
for cellname in cellnames:
    if num_cells[cellname] == 0:
        accuracies[cellname] = np.nan
    else:
        accuracies[cellname] = correct_num_cells[cellname] / num_cells[cellname]

# Combine the num cells, correct num cells, and accuracies into a dataframe
df = pd.DataFrame(
    [num_cells, correct_num_cells, accuracies],
    index=["num_cells", "correct_num_cells", "accuracy"],
).T

# add a column for the cell names
df["cellname"] = df.index

# save the dataframe as a csv file
df.to_csv(os.path.join(cartridges_dir, "accuracy.csv"))