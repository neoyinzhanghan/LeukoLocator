import os
import pandas as pd
from tqdm import tqdm

from_dir = "/pesgisipth/NDPI"
to_dir = "/media/hdd3/neo/PB_slides"
PB_annotations_path = "/media/hdd3/neo/results/PB_annotations_filtered.csv"

# first open the csv file in PB_annotations_path and read it into a pandas dataframe
PB_annotations_df = pd.read_csv(PB_annotations_path)

# traverse through the wsi_fname column in the dataframe, and copy the files from from_dir to to_dir
for wsi_fname in tqdm(PB_annotations_df['wsi_fname']): # do not use shutil 
    os.system(f"cp \'{os.path.join(from_dir, wsi_fname)}\' {to_dir}")