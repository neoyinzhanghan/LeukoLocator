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

exception_list = [
    "H23-894;S17;MSK7 - 2023-06-15 19.18.03",
    "H22-5721;S12;MSKV - 2023-04-14 16.13.00",
    "H22-10246;S15;MSK6 - 2023-06-15 12.37.37",
    "H22-7118;S11;MSKW - 2023-06-15 17.23.30",
    "H22-10935;S16;MSKB - 2023-06-15 10.44.43",
    "H22-6251;S15;MSKX - 2023-06-15 12.44.35",
    "H21-8723;S14;MSK1 - 2023-05-19 16.23.18",
    "H21-7705;S13;MSK9 - 2023-05-31 15.31.31",
    "H21-8526;S10;MSK8 - 2023-05-19 18.10.06",
    "H21-9688;S11;MSK9 - 2023-04-19 16.55.24",
    "H21-1589;S11;MSK1 - 2023-05-22 08.07.13",
    "H20-8172;S11;MSK5 - 2023-06-15 19.59.48",
    "H20-152;S12;MSKW - 2023-06-27 22.43.39",
    "H19-8719;S13;MSKB - 2023-06-20 10.03.13",
    "H19-3488;S11;MSK8 - 2023-06-27 23.12.56",
    "H19-8904;S10;MSKO - 2023-06-20 10.26.07",
    "H18-9809;S11;MSKJ - 2023-04-25 09.52.53",
    "H18-9196;S11;MSK9 - 2023-06-21 21.36.14",
    "H18-7360;S10;MSKI - 2023-04-25 17.27.10",
    "H18-7697;S11;MSKC - 2023-06-26 20.39.06",
]

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

        if wsi_fname_stem in exception_list:
            tqdm.write(f"Skipping {wsi_fname_stem} because it is in the exception list")
            continue

        save_dir = os.path.join(dump_dir, Path(wsi_path).stem)

        print(f"Processing {wsi_fname_stem}...")

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
