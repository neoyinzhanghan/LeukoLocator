from LL.resources.assumptions import *
from LL.PBCounter import PBCounter
from tqdm import tqdm
import pandas as pd
import os

PB_annotations_path = "/media/hdd3/neo/results/PB_annotations_filtered_processed.csv"
wsi_dir = "/media/hdd3/neo/PB_slides"

PB_annotations_df = pd.read_csv(PB_annotations_path)

num_wsis = len(PB_annotations_df)

# traverse through the rows of the dataframe of the column 'wsi_fname', which is the filename of the WSI
for i in tqdm(range(num_wsis), desc="Processing WSIs"):
    # get the wsi_fname
    wsi_fname = PB_annotations_df["wsi_fname"][i]

    # get the wsi_path
    wsi_path = os.path.join(wsi_dir, wsi_fname)

    pbc = PBCounter(wsi_path, hoarding=True)

    pbc.find_focus_regions()
