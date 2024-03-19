import os
import pandas as pd
import random
from tqdm import tqdm
from LL.BMAFocusRegionTracker import NotEnoughFocusRegionsError
from LL.BMACounter import BMACounter
from LL.vision.processing import SlideError
from LL.resources.BMAassumptions import *
from pathlib import Path

bma_slides_dir = "/media/hdd3/neo/BMAs_chosen"

# traverse through all the ndpi files in the bma_slides_dir
bma_fnames = [fname for fname in os.listdir(bma_slides_dir) if fname.endswith(".ndpi")]

# # get the list of all folder in dump_dir
# processeds = [
#     fname for fname in os.listdir(dump_dir) if os.path.isdir(os.path.join(dump_dir, fname))
# ]

# # for each folder in dumb_dir, if the name of the folder starts with ERROR, remove the named ERROR_ from the folder name
# for processed in processeds:
#     if processed.startswith("ERROR"):
#         new_name = processed.replace("ERROR_", "")
#         # remove new_name fomr bma_fnames
#         bma_fnames.remove(new_name)
#     else:
#         bma_fnames.remove(processed)

for bma_fname in tqdm(bma_fnames, desc="Processing BMA slides"):

    print("Processing", bma_fname)

    # try:
    bma_slide_path = os.path.join(bma_slides_dir, bma_fname)
    bma_counter = BMACounter(
        bma_slide_path, hoarding=True, continue_on_error=True, do_extract_features=False
    )
    bma_counter.tally_differential()

    print("Saving to", bma_counter.save_dir)

    # except NotEnoughFocusRegionsError:
    #     print("Not enough focus regions")
    #     bad_slides[bma_fname] = "Not enough focus regions"

    #     # rename the folder to ERROR_ + folder name

    #     old_file_path = bma_counter.save_dir
    #     old_file_name = Path(old_file_path).name
    #     old_file_folder = Path(old_file_path).parent
    #     new_file_name = "ERROR_" + old_file_name
    #     new_file_path = os.path.join(old_file_folder, new_file_name)
    #     os.rename(
    #         bma_counter.save_dir,
    #         new_file_path,
    #     )

    #     continue

    # except SlideError:
    #     print("Slide reading took too long")
    #     bad_slides[bma_fname] = "Slide reading took too long"

    #     # rename the folder to ERROR_ + folder name

    #     old_file_path = bma_counter.save_dir
    #     old_file_name = Path(old_file_path).name
    #     old_file_folder = Path(old_file_path).parent
    #     new_file_name = "ERROR_" + old_file_name
    #     new_file_path = os.path.join(old_file_folder, new_file_name)
    #     os.rename(
    #         bma_counter.save_dir,
    #         new_file_path,
    #     )

    #     continue
