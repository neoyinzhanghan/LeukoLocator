import os
import pandas as pd
from pathlib import Path
from tqdm import tqdm

save_path = (
    "/media/ssd2/dh_labelled_data/DeepHeme1/MSK_repo_normal/mskcc_bma_normal.csv"
)

cartridge_paths = [
    "/media/ssd2/dh_labelled_data/DeepHeme1/MSK_repo_normal",
]

# each cartridge path contains a number of subfolders, each subfolder is a label
# but we only look at the subfolders whose name is length less than 5
# within each subfolder, there are a number of .jpg images that are labelled with that label

# We want to create a dataframe with columns fpath, institution, abnormal, specimen_type, scanner, split, label, sample_method

# the fpath is the path to the .jpg image
# the institution is MSKCC across the board
# the abnormal is 1 across the board
# the specimen_type is PB across the board
# the scanner is Aperio
# the sample_method is "random" across the board
# the split is NA across the board
# the label is the name of the subfolder

fpaths = []

for cartridge_path in cartridge_paths:
    for subfolder in os.listdir(cartridge_path):
        if len(subfolder) < 5:
            for f in os.listdir(os.path.join(cartridge_path, subfolder)):
                # check if the file is a .png file
                if f.endswith(".png"):
                    fpaths.append(os.path.join(cartridge_path, subfolder, f))

df = pd.DataFrame(fpaths, columns=["fpath"])

df["institution"] = "MSKCC"
df["abnormal"] = 0
df["specimen_type"] = "BMA"
df["scanner"] = "Aperio"
df["sample_method"] = "manual"
df["split"] = "NA"
df["label"] = df["fpath"].apply(lambda x: Path(x).parent.name)

df.to_csv(save_path, index=False)
