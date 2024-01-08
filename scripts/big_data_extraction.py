import os
import pandas as pd
from tqdm import tqdm
from LL.PBCounter import PBCounter
from LL.TopView import extract_top_view
from LL.brain.SpecimenClf import *
from pathlib import Path
from openslide.lowlevel import OpenSlideError

specimen_type_fpath = "/media/ssd2/clinical_text_data/tissueType/status_results.csv"
specimen_df = pd.read_csv(specimen_type_fpath)
wsi_read_only_dir = "/pesgisipth/NDPI"
PB_dir = "/media/hdd2/PBs"
BMA_dir = "/media/hdd1/BMAs"
MPBorIBMA_dir = "/media/hdd3/neo/MPBorIBMAs"
log_path = "/home/greg/Documents/neo/tmp/log.txt"

error_dir = "/media/hdd3/neo/open_slide_errors"

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

    # Assuming specimen_df is your DataFrame and wsi_fname is the filename you're searching for.

    # First, ensure that the index (if it's a column used as an index) is of type string
    specimen_df.index = specimen_df.index.astype(str)

    # Then, perform the operation to match the lowercased and stripped index with the wsi_fname
    # Also ensure wsi_fname is a string, strip it, and convert it to lowercase
    wsi_fname_cleaned = str(wsi_fname).strip()

    # Use .loc to locate the row
    specimen_type_box = specimen_df.loc[
        specimen_df.index.str.strip() == wsi_fname_cleaned,
        "Part Description",
    ]

    # If you expect only one match and want to get the single value as a string
    specimen_type_str = (
        specimen_type_box.iloc[0] if not specimen_type_box.empty else None
    )

    print("Recorded Specimen Type String:", specimen_type_str)

    # if the lower case of the specimen type string contains "bone marrow aspirate"

    # first check that the specimen_type_str is not nan (float)
    if not isinstance(specimen_type_str, str):
        specimen_type = "Others"
    elif "bone marrow aspirate" in specimen_type_str.lower():
        specimen_type = "BMA"
    elif "peripheral blood" in specimen_type_str.lower():
        specimen_type = "PB"
        # first make a carbon copy of the slide in the PB_dir
        print(f"Copying {wsi_fname} to {PB_dir}")
        os.system(f'cp "{os.path.join(wsi_read_only_dir, wsi_fname)}" {PB_dir}')
    else:
        specimen_type = "Others"

    print("Recorded Specimen Type:", specimen_type)

    if specimen_type == "BMA":
        # carbon copy the slide to the BMA_dir
        print(f"Copying {wsi_fname} to {BMA_dir}")
        os.system(f'cp "{os.path.join(wsi_read_only_dir, wsi_fname)}" {BMA_dir}')

        try:
            # extract the topview image
            topview = extract_top_view(
                wsi_path=os.path.join(BMA_dir, wsi_fname),
                save_dir=os.path.join(topview_saving_dir, "BMA"),
            )

        except OpenSlideError:
            # move the slide to the error_dir
            print(f"Moving {wsi_fname} to {error_dir}")
            os.system(f'mv "{os.path.join(BMA_dir, wsi_fname)}" {error_dir}')
            update_log(wsi_fname)
            continue

    elif specimen_type == "PB":
        # carbon copy the slide to the PB_dir
        print(f"Copying {wsi_fname} to {PB_dir}")
        os.system(f'cp "{os.path.join(wsi_read_only_dir, wsi_fname)}" {PB_dir}')

        try:
            # extract the topview image
            topview = extract_top_view(
                wsi_path=os.path.join(PB_dir, wsi_fname),
                save_dir=os.path.join(topview_saving_dir, "PB"),
            )

        except OpenSlideError:
            # move the slide to the error_dir
            print(f"Moving {wsi_fname} to {error_dir}")
            os.system(f'mv "{os.path.join(PB_dir, wsi_fname)}" {error_dir}')
            update_log(wsi_fname)
            continue

        pbc = PBCounter(
            wsi_path=os.path.join(PB_dir, wsi_fname),
            hoarding=True,
            continue_on_error=True,
        )
        pbc.tally_differential()

    else:
        # carbon copy the slide to the MPBorIBMA_dir
        print(f"Copying {wsi_fname} to {MPBorIBMA_dir}")
        os.system(f'cp "{os.path.join(wsi_read_only_dir, wsi_fname)}" {MPBorIBMA_dir}')

        try:
            # extract the topview image
            topview = extract_top_view(
                wsi_path=os.path.join(MPBorIBMA_dir, wsi_fname),
            )

            predicted_specimen_type = get_region_type(topview)

            print("Predicted Specimen Type:", predicted_specimen_type)

            if predicted_specimen_type == "Bone Marrow Aspirate":
                # move the slide from the MPBorIBMA_dir to the BMA_dir
                print(f"Moving {wsi_fname} from {MPBorIBMA_dir} to {BMA_dir}")
                os.system(f'mv "{os.path.join(MPBorIBMA_dir, wsi_fname)}" {BMA_dir}')

                # save the topview image to the BMA_dir
                topview.save(
                    os.path.join(
                        topview_saving_dir, "BMA", Path(wsi_fname).stem + ".jpg"
                    )
                )

            elif predicted_specimen_type == "Peripheral Blood":
                # move the slide from the MPBorIBMA_dir to the PB_dir
                print(f"Moving {wsi_fname} from {MPBorIBMA_dir} to {PB_dir}")
                os.system(f'mv "{os.path.join(MPBorIBMA_dir, wsi_fname)}" {PB_dir}')

                # save the topview image to the PB_dir
                topview.save(
                    os.path.join(
                        topview_saving_dir, "PB", Path(wsi_fname).stem + ".jpg"
                    )
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
                os.system(f'rm "{os.path.join(MPBorIBMA_dir, wsi_fname)}"')

        except OpenSlideError:
            # move the slide to the error_dir
            print(f"Moving {wsi_fname} to {error_dir}")
            os.system(f'mv "{os.path.join(MPBorIBMA_dir, wsi_fname)}" {error_dir}')

    update_log(wsi_fname)
