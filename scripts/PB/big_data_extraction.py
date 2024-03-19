import os
from tqdm import tqdm
from LL.PBCounter import PBCounter
from LL.vision.processing import SlideError
from LL.resources.PBassumptions import *

pb_slides_dir = "/media/hdd3/neo/PB_slides"

# traverse through all the ndpi files in the bma_slides_dir
pb_fnames = [fname for fname in os.listdir(pb_slides_dir) if fname.endswith(".ndpi")]

# get a list of all directories in the dump_dir
dump_dirs = [
    dname
    for dname in os.listdir(dump_dir)
    if os.path.isdir(os.path.join(dump_dir, dname))
]


def already_processed(fname, dump_dirs):
    for dump_dir in dump_dirs:
        if dump_dir in fname:
            return True

    return False


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

for pb_fname in tqdm(pb_fnames, desc="Processing BMA slides"):

    if already_processed(pb_fname, dump_dirs):
        print("Already processed", pb_fname)
        continue

    print("Processing", pb_fname)

    # try:
    pb_slide_path = os.path.join(pb_slides_dir, pb_fname)
    pb_counter = PBCounter(pb_slide_path, hoarding=True, continue_on_error=True)
    pb_counter.tally_differential()

    print("Saving to", pb_counter.save_dir)
