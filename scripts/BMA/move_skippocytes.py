import os
import shutil
import pandas as pd
from LL.brain.BMASkippocyteDetection import load_model, predict_image
from tqdm import tqdm
from PIL import Image

model_path = "/media/hdd3/neo/MODELS/2024-05-13 blast-skippocyte balanced/1/version_0/checkpoints/epoch=499-step=36500.ckpt"
data_dir = "/media/hdd3/neo/results_bma_normal_v2"

# find all subfolders in data_dir that do not start with 'ERROR_'
subfolders = [
    f.path
    for f in os.scandir(data_dir)
    if f.is_dir() and not f.name.startswith("ERROR_")
]

# remove the skippocytes folder in each of the subfolders if it exists
for subfolder in tqdm(subfolders, desc="Removing Old Skippocytes"):
    skippocytes_folder = os.path.join(subfolder, "skippocytes")
    if os.path.exists(skippocytes_folder):
        shutil.rmtree(skippocytes_folder)

# create the skippocytes folder in each of the subfolders
for subfolder in tqdm(subfolders, desc="Creating Skippocytes Folder"):
    os.makedirs(os.path.join(subfolder, "skippocytes"), exist_ok=True)

# for each subfolder, open the subfolder/cells/cells_info.csv file using pandas
# cellnames contain a list of columns that are cell names
# the cellname.split('-')[0] is the cellclass
# the cell image is saved at subfolder/cells/{cellclass}/{cellname}

# compute the probability of each cell being a skippocyte using the model at model_path
# add the probability as a column to the cells_info.csv file called skippocyte_score
# if the skippocyte_score is greater than 0.5, the cell is a skippocyte and we save it at subfolder/skippocytes/{cellname}}

model = load_model(model_path)

for subfolder in tqdm(subfolders, desc="Finding Skippocytes"):
    cells_info = pd.read_csv(os.path.join(subfolder, "cells", "cells_info.csv"))

    for index, row in tqdm(cells_info.iterrows(), desc="Computing Skippocyte Scores"):
        cellname = row["name"]

        cellclass = cellname.split("-")[0]

        cell_path = os.path.join(subfolder, "cells", cellname.split("-")[0], cellname)

        if cellclass == "M1":
            image = Image.open(cell_path)
            skippocyte_score = predict_image(model, image)
            cells_info.loc[index, "skippocyte_score"] = skippocyte_score
        else:
            cells_info.loc[index, "skippocyte_score"] = 0

    for index, row in tqdm(cells_info.iterrows(), desc="Saving Skippocytes"):

        cellname = row["name"]
        cell_path = os.path.join(subfolder, "cells", cellname.split("-")[0], cellname)
        save_path = os.path.join(subfolder, "skippocytes", cellname)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        shutil.copy(cell_path, save_path)

    # save the cells_info.csv file with the skippocyte_score column included

    cells_info.to_csv(
        os.path.join(subfolder, "skippocytes", "cells_info.csv"), index=False
    )
