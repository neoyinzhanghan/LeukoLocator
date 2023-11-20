from LL.resources.assumptions import *
from LL.PBCounter import PBCounter
from pathlib import Path
from tqdm import tqdm
import pandas as pd
import os

# example_slide_path = "/media/ssd1/neo/PBSlides/LL_test_example.ndpi"
# pbc = PBCounter(example_slide_path, hoarding=True)

# pbc.tally_differential()

PB_annotations_path = "/media/hdd3/neo/results/PB_annotations_filtered_processed.csv"
wsi_dir = "/media/hdd3/neo/PB_slides"

PB_annotations_df = pd.read_csv(PB_annotations_path)

num_wsis = len(PB_annotations_df)

# get the list of folder names in the dump_dir, these are the names of the WSIs that have been processed, the last one may or may not have been fully processed
# because the script may have been interrupted at the last one, so we need to reprocess the last one just in case
# only the folders
processed_wsi_fnames_stem = [
    fname
    for fname in os.listdir(dump_dir)
    if os.path.isdir(os.path.join(dump_dir, fname))
]


# get the length of the list of folder names in the dump_dir, these are the names of the WSIs that have been processed, the last one may or may not have been fully processed
# because the script may have been interrupted at the last one, so we need to reprocess the last one just in case
num_processed_wsi_fnames_stem = len(processed_wsi_fnames_stem)

current_idx = 0

# traverse through the rows of the dataframe of the column 'wsi_fname', which is the filename of the WSI
for i in tqdm(range(num_wsis), desc="Processing WSIs"):
    current_idx += 1
    try:
        if current_idx < num_processed_wsi_fnames_stem:
            # make sure to update the tqdm progress bar
            tqdm.write(
                f"Skipping {PB_annotations_df['wsi_fname'][i]} because it has been processed"
            )
            continue
        # get the wsi_fname
        wsi_fname = PB_annotations_df["wsi_fname"][i]

        # get the wsi_path
        wsi_path = os.path.join(wsi_dir, wsi_fname)

        wsi_fname_stem = Path(wsi_fname).stem

        save_dir = os.path.join(dump_dir, Path(wsi_path).stem)

        pbc = PBCounter(wsi_path, hoarding=True)

        pbc.find_focus_regions()

        pbc.find_wbc_candidates()

        pbc.label_wbc_candidates()

        pbc.tally_differential()

    except Exception as e:
        save_dir = os.path.join(dump_dir, Path(wsi_path).stem)

        # if the save_dir does not exist, create it
        os.makedirs(save_dir, exist_ok=True)

        # save the exception in the save_dir as error.txt

        with open(os.path.join(save_dir, "error.txt"), "w") as f:
            f.write(str(e))

        # rename the save_dir name to "ERROR_" + save_dir
        os.rename(save_dir, os.path.join(dump_dir, "ERROR_" + Path(wsi_path).stem))
