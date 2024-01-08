import os
import pandas as pd
from tqdm import tqdm
from LL.PBCounter import PBCounter
from LL.TopView import extract_top_view
from LL.brain.SpecimenClf import *
from pathlib import Path

specimen_type_fpath = "/media/ssd2/clinical_text_data/tissueType/status_results.csv"
specimen_df = pd.read_csv(specimen_type_fpath)
wsi_read_only_dir = "/pesgisipth/NDPI"
PB_dir = "/media/hdd1/BMAs"
BMA_dir = "/media/hdd2/PBs"
MPBorIBMA_dir = "/media/hdd3/neo/MPBorIBMAs"
log_path = "/home/greg/Documents/neo/tmp/log.txt"

topview_saving_dir = "/media/hdd3/neo/topviews_full"
# this folder has four subfolders: "BMA", "PB", "MPBorIMBA", "Others"

# get the list of all slides which are all ndpi files in the wsi_read_only_dir that start with "H" or "S" and end with ".ndpi"
wsi_fnames = [
    fname
    for fname in os.listdir(wsi_read_only_dir)
    if fname.startswith(("H", "S")) and fname.endswith(".ndpi")
]

# the column "Slide" is the file root name of the slide with .ndpi extension
# the column "Tissue Type Code" is the specimen type


def update_log(wsi_fname, log_path=log_path):
    with open(log_path, "a") as f:
        f.write(wsi_fname + "\n")


def get_list_wsi_fnames_from_log(log_path=log_path):
    with open(log_path, "r") as f:
        return f.read().splitlines()


lst_processed = get_list_wsi_fnames_from_log()

print("Picking up where we left off ... ")
wsi_fnames = [fname for fname in wsi_fnames if fname not in lst_processed]


for wsi_fname in tqdm(wsi_fnames, "Data Extraction In Progress: "):
    print(f"Processing {wsi_fname}...")
    wsi_path = os.path.join(wsi_read_only_dir, wsi_fname)
    
    # First, ensure that the "Slide" column is treated as a string
    specimen_df['Slide'] = specimen_df['Slide'].astype(str)

    # Then perform the operations
    specimen_type_box = specimen_df[
        specimen_df["Slide"].str.lower().str.strip() == wsi_fname.lower().strip()
    ]["Tissue Type Code"]

    print(specimen_type_box)
    specimen_type_str = specimen_type_box.values[0]

    # if the lower case of the specimen type string contains "bone marrow aspirate"
    if "bone marrow aspirate" in specimen_type_str.lower():
        specimen_type = "BMA"
    elif "peripheral blood" in specimen_type_str.lower():
        specimen_type = "PB"
        # first make a carbon copy of the slide in the PB_dir
        print(f"Copying {wsi_fname} to {PB_dir}")
        os.system(f"cp {os.path.join(wsi_read_only_dir, wsi_fname)} {PB_dir}")
    else:
        specimen_type = "Others"

    if specimen_type == "BMA":
        # carbon copy the slide to the BMA_dir
        print(f"Copying {wsi_fname} to {BMA_dir}")
        os.system(f"cp {os.path.join(wsi_read_only_dir, wsi_fname)} {BMA_dir}")

        # extract the topview image
        topview = extract_top_view(
            wsi_path=os.path.join(BMA_dir, wsi_fname),
            save_dir=os.path.join(topview_saving_dir, "BMA"),
        )

    elif specimen_type == "PB":
        # carbon copy the slide to the PB_dir
        print(f"Copying {wsi_fname} to {PB_dir}")
        os.system(f"cp {os.path.join(wsi_read_only_dir, wsi_fname)} {PB_dir}")

        # extract the topview image
        topview = extract_top_view(
            wsi_path=os.path.join(PB_dir, wsi_fname),
            save_dir=os.path.join(topview_saving_dir, "PB"),
        )

        pbc = PBCounter(
            wsi_path=os.path.join(PB_dir, wsi_fname),
            hoarding=True,
            continue_on_error=True,
        )
        pbc.tally_differential()

    else:
        # carbon copy the slide to the MPBorIBMA_dir
        print(f"Copying {wsi_fname} to {MPBorIBMA_dir}")
        os.system(f"cp {os.path.join(wsi_read_only_dir, wsi_fname)} {MPBorIBMA_dir}")

        # extract the topview image
        topview = extract_top_view(
            wsi_path=os.path.join(MPBorIBMA_dir, wsi_fname),
        )

        predicted_specimen_type = get_region_type(topview)

        if predicted_specimen_type == "Bone Marrow Aspirate":
            # move the slide from the MPBorIBMA_dir to the BMA_dir
            print(f"Moving {wsi_fname} from {MPBorIBMA_dir} to {BMA_dir}")
            os.system(f"mv {os.path.join(MPBorIBMA_dir, wsi_fname)} {BMA_dir}")

            # save the topview image to the BMA_dir
            topview.save(
                os.path.join(topview_saving_dir, "BMA", Path(wsi_fname).stem + ".jpg")
            )

        elif predicted_specimen_type == "Peripheral Blood":
            # move the slide from the MPBorIBMA_dir to the PB_dir
            print(f"Moving {wsi_fname} from {MPBorIBMA_dir} to {PB_dir}")
            os.system(f"mv {os.path.join(MPBorIBMA_dir, wsi_fname)} {PB_dir}")

            # save the topview image to the PB_dir
            topview.save(
                os.path.join(topview_saving_dir, "PB", Path(wsi_fname).stem + ".jpg")
            )

            pbc = PBCounter(
                wsi_path=os.path.join(PB_dir, wsi_fname),
                hoarding=True,
                continue_on_error=True,
            )
            pbc.tally_differential()

        elif (
            predicted_specimen_type
            == "Manual Peripheral Blood or Inadequate Bone Marrow Aspirate"
        ):
            # save the topview image to the MPBorIBMA_dir
            topview.save(
                os.path.join(
                    topview_saving_dir, "MPBorIBMA", Path(wsi_fname).stem + ".jpg"
                )
            )

        else:
            # save the topview image to the Others_dir
            topview.save(
                os.path.join(
                    topview_saving_dir, "Others", Path(wsi_fname).stem + ".jpg"
                )
            )

            # delete the slide from the MPBorIBMA_dir
            print(f"Deleting {wsi_fname} from {MPBorIBMA_dir}")
            os.system(f"rm {os.path.join(MPBorIBMA_dir, wsi_fname)}")

    update_log(wsi_fname)
