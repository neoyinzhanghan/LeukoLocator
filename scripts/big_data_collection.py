from WCW.resources.assumptions import *
from WCW.communication.saving import save_wbc_candidates_sorted, save_focus_regions_annotated
from WCW.vision.processing import SlideError
from WCW.PBCounter import PBCounter, NoCellFoundError, TooManyCandidatesError
import pandas as pd
import os
import time

PB_annotations_path = "/media/hdd3/neo/results/PB_annotations_filtered_processed.csv"
wsi_dir = "/media/hdd3/neo/PB_slides"
save_dir = dump_dir

PB_annotations_df = pd.read_csv(PB_annotations_path)

# # for each class in PB_final_classes, create a column in PB_annotations_df with the name of the class and with all values set to 0
# for class_name in PB_final_classes:
#     PB_annotations_df[class_name] = [0] * len(PB_annotations_df)

# # now add a new column of num of wbcs scanned and num of focus regions scanned
# PB_annotations_df['num_wbcs_scanned'] = [0] * len(PB_annotations_df)
# PB_annotations_df['num_focus_regions_scanned'] = [0] * len(PB_annotations_df)

# # add a new column named processing_time
# PB_annotations_df['processing_time'] = [0] * len(PB_annotations_df)

num_wsis = len(PB_annotations_df)
num_to_run = num_wsis + 1000
num_ran = 0
num_to_skip = 12

# traverse through the rows of the dataframe of the column 'wsi_fname', which is the filename of the WSI
for i in range(num_wsis):

    # get the wsi_fname
    wsi_fname = PB_annotations_df['wsi_fname'][i]

    # get the wsi_path
    wsi_path = os.path.join(wsi_dir, wsi_fname)

    if num_ran + 1 <= num_to_skip:

        print(f"Skipping {wsi_fname}")
        tally_string = "Skipped"

        num_ran += 1

        continue

    print(f"Processing {wsi_fname} with {num_ran} slides processed so far.")

    try:
        if i + 1 > num_to_run:

            print(f"Skipping {wsi_fname}")
            tally_string = "Skipped"

            for class_name in PB_final_classes:
                PB_annotations_df.loc[i, class_name] = tally_string

            PB_annotations_df.loc[i, 'num_wbcs_scanned'] = tally_string
            PB_annotations_df.loc[i,
                                  'num_focus_regions_scanned'] = tally_string

            PB_annotations_df.loc[i, 'processing_time'] = tally_string

            continue

        else:

            start_time = time.time()

            # create a subdirectory in save_dir with the name of the wsi_fname without the extension .ndpi
            sub_dir = os.path.join(save_dir, wsi_fname[:-5])
            if not os.path.exists(sub_dir):
                os.mkdir(sub_dir)
            pbc = PBCounter(wsi_path)
            pbc.tally_differential()

            tally_dict = pbc.differential.compute_PB_differential()

            time_taken = time.time() - start_time

            save_focus_regions_annotated(pbc, save_dir=sub_dir)
            save_wbc_candidates_sorted(
                pbc, image_type='snap_shot', save_dir=sub_dir)

            # save the top view image in the sub_dir
            pbc.top_view.image.save(os.path.join(sub_dir, "top_view.jpg"))

            for class_name in PB_final_classes:
                PB_annotations_df.loc[i, class_name] = tally_dict[class_name]

            PB_annotations_df.loc[i, 'num_wbcs_scanned'] = len(
                pbc.wbc_candidates)
            PB_annotations_df.loc[i, 'num_focus_regions_scanned'] = len(
                pbc.focus_regions)

            PB_annotations_df.loc[i, 'processing_time'] = time_taken

            # save the dataframe as a csv file in the save_dir with file name PB_annotations_filtered_processed.csv
            PB_annotations_df.to_csv(os.path.join(
                save_dir, "PB_annotations_filtered_processed.csv"), index=False)

            i += 1

    except NoCellFoundError:

        print(f"NoCellFoundError: {wsi_fname}")
        tally_string = "NoCellFoundError"

        # add the tally_string to the dataframe
        for class_name in PB_final_classes:
            PB_annotations_df.loc[i, class_name] = tally_string

        PB_annotations_df.loc[i, 'num_wbcs_scanned'] = tally_string
        PB_annotations_df.loc[i, 'num_focus_regions_scanned'] = tally_string

        PB_annotations_df.loc[i, 'processing_time'] = tally_string

        # save the dataframe as a csv file in the save_dir with file name PB_annotations_filtered_processed.csv
        PB_annotations_df.to_csv(os.path.join(
            save_dir, "PB_annotations_filtered_processed.csv"), index=False)

        i += 1

    except SlideError:

        print(f"SlideError: {wsi_fname}")
        tally_string = "SlideError"

        # add the tally_string to the dataframe
        for class_name in PB_final_classes:
            PB_annotations_df.loc[i, class_name] = tally_string

        PB_annotations_df.loc[i, 'num_wbcs_scanned'] = tally_string
        PB_annotations_df.loc[i, 'num_focus_regions_scanned'] = tally_string

        PB_annotations_df.loc[i, 'processing_time'] = tally_string

        # save the dataframe as a csv file in the save_dir with file name PB_annotations_filtered_processed.csv
        PB_annotations_df.to_csv(os.path.join(
            save_dir, "PB_annotations_filtered_processed.csv"), index=False)

        i += 1
    
    except TooManyCandidatesError:

        print(f"TooManyCandidatesError: {wsi_fname}")
        tally_string = "TooManyCandidatesError"

        # add the tally_string to the dataframe
        for class_name in PB_final_classes:
            PB_annotations_df.loc[i, class_name] = tally_string

        PB_annotations_df.loc[i, 'num_wbcs_scanned'] = tally_string
        PB_annotations_df.loc[i, 'num_focus_regions_scanned'] = tally_string

        PB_annotations_df.loc[i, 'processing_time'] = tally_string

        # save the dataframe as a csv file in the save_dir with file name PB_annotations_filtered_processed.csv
        PB_annotations_df.to_csv(os.path.join(
            save_dir, "PB_annotations_filtered_processed.csv"), index=False)

        i += 1
    

# save the dataframe as a csv file in the save_dir with file name PB_annotations_filtered_processed.csv
PB_annotations_df.to_csv(os.path.join(
    save_dir, "PB_annotations_filtered_processed.csv"), index=False)
