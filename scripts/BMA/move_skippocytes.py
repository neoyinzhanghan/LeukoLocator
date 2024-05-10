import os
import pandas as pd
from PIL import Image
from LL.brain.BMASkippocyteDetection import load_model, predict_image
from tqdm import tqdm

data_dir = "/media/hdd3/neo/results_bma_normal_v2"

load_model_path = "/media/hdd3/neo/MODELS/2024-05-08 blast skippocyte v1/1/version_0/checkpoints/epoch=499-step=36500.ckpt"

# first load the model
model = load_model(load_model_path)

# get the list of all subdirectories in the data_dir that does not start with ERROR

result_folders = [
    f
    for f in os.listdir(data_dir)
    if os.path.isdir(os.path.join(data_dir, f)) and not f.startswith("ERROR")
]

# for each result_folder in results_folder, result_folder/cells contain a number of subfolders, each being a class of cells containing jpg images
# for each result_folder in results_folder, result_folder/cells/cells_info.csv

for result_folder in tqdm(result_folders, desc="Processsing Results Folders:"):

    # remove result_folder/skippocytes
    if os.path.exists(os.path.join(data_dir, result_folder, "skippocytes")):
        os.system(f"rm -r \"{os.path.join(data_dir, result_folder, 'skippocytes')}\"")

    # create result_folder/skippocytes
    os.system(f"mkdir \"{os.path.join(data_dir, result_folder, 'skippocytes')}\"")

    # open the cells_info.csv file
    cells_info_path = os.path.join(data_dir, result_folder, "cells", "cells_info.csv")

    # open as a pandas dataframe
    cells_info = pd.read_csv(cells_info_path)

    # add a new column called "skippocyte_score" to cells_info
    cells_info["skippocyte_score"] = None

    # for each row in cells_info, get the label and name column
    for idx, row in cells_info.iterrows():
        image_path = os.path.join(
            data_dir, result_folder, "cells", row["label"], row["name"]
        )

        image = Image.open(image_path)
        prediction = predict_image(image, model)

        cells_info.loc[idx, "skippocyte_score"] = prediction

        if prediction > 0.5:
            # copy the image to result_folder/skippocytes using shutil
            os.system(
                f"cp \"{image_path} {os.path.join(data_dir, result_folder, 'skippocytes')}\""
            )

    # save the updated cells_info to cells_info.csv in skippocytes folder
    cells_info.to_csv(
        os.path.join(data_dir, result_folder, "skippocytes", "cells_info.csv"),
        index=False,
    )
