import os
import pandas as pd
from pathlib import Path
from tqdm import tqdm

df_path = "/Users/neo/Documents/Research/DeepHeme/LLResults/LLCKPTS/tmp/data_info.csv"

save_path = (
    "/Users/neo/Documents/Research/DeepHeme/LLResults/LLCKPTS/tmp/ucsf_normal.csv"
)

# We want to create a dataframe with columns fpath, institution, abnormal, specimen_type, scanner, split, label, sample_method

# the data_info.csv file has the following columns fpath, label, split

# We want to add the following columns: institution, abnormal, specimen_type, scanner, sample_method
# the institution is UCSF across the board
# the abnormal is 0 across the board
# the specimen_type is BMA across the board
# the scanner is Aperio
# the sample_method is manual across the board

# the fpath is not correct, we need to change it to the correct path

root = "/media/ssd2/dh_labelled_data/DeepHeme1/UCSF_repo"

# for example, /data/aa-ssun2-cmp/hemepath_dataset_FINAL/UCSF_repo/M5/34687.png needs to be changed to /media/ssd2/dh_labelled_data/DeepHeme1/UCSF_repo/M5/34687.png
# M5 is the label, 34687.png is the stem of the file path

df = pd.read_csv(df_path)

df["institution"] = "UCSF"
df["abnormal"] = 0
df["specimen_type"] = "BMA"
df["scanner"] = "Aperio"
df["sample_method"] = "manual"


def get_new_fpath(row):
    stem = Path(row["fpath"]).stem
    label = row["label"]
    new_fpath = os.path.join(root, label, stem + ".png")

    return new_fpath


for i in tqdm(range(len(df))):
    df.loc[i, "fpath"] = get_new_fpath(df.loc[i])

df.to_csv(save_path, index=False)
