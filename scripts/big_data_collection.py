from WCW.resources.assumptions import *
from WCW.communication.saving import save_wbc_candidates_sorted, save_focus_regions_annotated
from WCW.vision.processing import SlideError
from WCW.PBCounter import PBCounter
import pandas as pd
import os

PB_annotations_path = "/media/hdd3/neo/results/PB_annotations_filtered.csv"
wsi_dir = "/media/hdd3/neo/PB_slides"
save_dir = dump_dir
num_to_run = 10
num_ran = 0

PB_annotations_df = pd.read_csv(PB_annotations_path)

# for each class in PB_final_classes, create a column in PB_annotations_df with the name of the class and with all values set to 0
for class_name in PB_final_classes:
    PB_annotations_df[class_name] = [0] * len(PB_annotations_df)

num_wsis = len(PB_annotations_df)

# traverse through the rows of the dataframe of the column 'wsi_fname', which is the filename of the WSI
for i in range(num_wsis):

    # get the wsi_fname
    wsi_fname = PB_annotations_df['wsi_fname'][i]

    # get the wsi_path
    wsi_path = os.path.join(wsi_dir, wsi_fname)

    print(f"Processing {wsi_fname} with {num_ran} slides processed so far.")

    # create a subdirectory in save_dir with the name of the wsi_fname without the extension .ndpi
    sub_dir = os.path.join(save_dir, wsi_fname[:-5])
    if not os.path.exists(sub_dir):
        os.mkdir(sub_dir)

    try:
        if i + 1 > num_to_run:

            print(f"Skipping {wsi_fname}")
            tally_string = "Skipped"

            continue

        else:
            pbc = PBCounter(wsi_path)
            pbc.tally_differential()

            tally_dict = pbc.differential.compute_PB_differential()

            save_focus_regions_annotated(pbc, save_dir=sub_dir)
            save_wbc_candidates_sorted(
                pbc, image_type='snap_shot', save_dir=sub_dir)

            for class_name in PB_final_classes:
                PB_annotations_df.loc[i, class_name] = tally_dict[class_name]


    except SlideError:

        print(f"SlideError: {wsi_fname}")
        tally_string = "SlideError"

        # add the tally_string to the dataframe
        PB_annotations_df.loc[i, class_name] = tally_dict[class_name]

