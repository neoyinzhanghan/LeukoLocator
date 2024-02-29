import os
import pandas as pd
import random
from tqdm import tqdm
from LL.BMACounter import BMACounter
from LL.resources.BMAassumptions import *

bma_slides_dir = "/media/hdd1/BMAs"

# traverse through all the ndpi files in the bma_slides_dir
bma_fnames = [
    fname
    for fname in os.listdir(bma_slides_dir)
    if fname.endswith(".ndpi")
]

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

num_processed = 0

# shuffle the list of bma_fnames
random.shuffle(bma_fnames)

for bma_fname in tqdm(bma_fnames, desc="Processing BMA slides"):
    print("Processing", bma_fname)

    if num_processed > 5:
        print("Finished processing the set number of slides. Exiting ...")
        import sys
        sys.exit()

    try:    

        bma_slide_path = os.path.join(bma_slides_dir, bma_fname)
        bma_counter = BMACounter(bma_slide_path, hoarding=True, continue_on_error=False)
        bma_counter.tally_differential()

        print("Saving to", bma_counter.save_dir)

        num_processed += 1

    except Exception as e:
        print("Error:", e)

    except KeyboardInterrupt:
        print("Interrupted")
        break