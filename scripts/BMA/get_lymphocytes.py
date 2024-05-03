import os
import shutil
import pandas as pd
from tqdm import tqdm


data_dir = "/media/hdd3/neo/results_bma_all_v2_rerun"
save_dir = "/media/hdd3/neo/lymphocytes_bma_all_v2_rerun"

# Create directories if they don't exist
os.makedirs(save_dir, exist_ok=True)

# get all the folders in data_dir that do not start with 'ERROR_'
subfolders = [
    f.path
    for f in os.scandir(data_dir)
    if f.is_dir() and not f.name.startswith("ERROR_")
]

# folder/cells/L2 is the path to the lymphocytes images
num_per_slide = 10

# randomly take num_per_slide lymphocytes from each slide and save them in a the save_dir, the file name should be 1.jpg, 2.jpg, 3.jpg, ...
# use a metadata file to keep track of the path to the original image, the slide name, and the cell name

# Create directories if they don't exist
os.makedirs(save_dir, exist_ok=True)

metadata = {
    "original_image_path": [],
    "slide_name": [],
    "idx": [],
}

current_index = 0

for subfolder in tqdm(subfolders, desc="Reading Data"):
    # get all the jpg files in the L2 folder
    lymphocytes = [
        f.path
        for f in os.scandir(os.path.join(subfolder, "cells/L2"))
        if f.name.endswith(".jpg")
    ]

    # randomly take num_per_slide lymphocytes from each slide, if there are less than num_per_slide lymphocytes, take all of them
    lymphocytes = lymphocytes[:num_per_slide]

    for lymphocyte in lymphocytes:
        # save the lymphocyte in the save_dir
        save_path = os.path.join(save_dir, f"{current_index}.jpg")
        shutil.copy(lymphocyte, save_path)

        # save the metadata
        metadata["original_image_path"].append(lymphocyte)
        metadata["slide_name"].append(subfolder)
        metadata["idx"].append(current_index)

        current_index += 1

metadata_df = pd.DataFrame(metadata)
metadata_df.to_csv(os.path.join(save_dir, "metadata.csv"), index=False)
