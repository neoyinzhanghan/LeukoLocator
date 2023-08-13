###################################################################################################
# IMPORTS #########################################################################################
###################################################################################################

import os
from WCW.resources.assumptions import *
import pandas as pd
from WCW.PBCounter import PBCounter
from WCW.communication.saving import save_wbc_candidates_sorted
from WCW.vision.processing import SlideError

PB_annotations_path = "/home/greg/Documents/neo/H23_PB_metadata.csv"
wsi_dir = "/pesgisipth/NDPI"
save_dir = dump_dir

# first open the csv file in PB_annotations_path and read it into a pandas dataframe
PB_annotations_df = pd.read_csv(PB_annotations_path)

# we want to add a column named WCW_tally to the dataframe
# first create a list of zeros with the same length as the number of rows in the dataframe
WCW_tally = [0] * len(PB_annotations_df)

# add the list as a column to the dataframe
PB_annotations_df['WCW_tally'] = WCW_tally

# traverse through the rows of the dataframe of the column 'wsi_fname', which is the filename of the WSI
for i in range(len(PB_annotations_df)):

    # get the wsi_fname
    wsi_fname = PB_annotations_df['wsi_fname'][i]

    # get the wsi_path
    wsi_path = os.path.join(wsi_dir, wsi_fname)

    try:
        pbc = PBCounter(wsi_path)
        pbc.tally_differential()

        tally_string = pbc.differential.tally_string(
        omitted_classes=[], removed_classes=['ER5', 'ER6', 'PL2', 'PL3'])

        # save_focus_regions(pbc)
        save_wbc_candidates_sorted(pbc, image_type='snap_shot')

    except SlideError:
        tally_string = "SlideError"


    # add the tally_string to the dataframe
    PB_annotations_df['WCW_tally'][i] = tally_string

# save the dataframe as a csv file
PB_annotations_df.to_csv(os.path.join(save_dir, 'WCW_tally.csv'), index=False)
