import random
import os
import tqdm
from LL.BMACounter import BMACounter
from LL.resources.BMAassumptions import *


def already_processed(fname, dump_dirs):
    for dump_dir in dump_dirs:
        if dump_dir in fname:
            return True

    return False


# get a list of all directories in the dump_dir
dump_dirs = [
    dname
    for dname in os.listdir(dump_dir)
    if os.path.isdir(os.path.join(dump_dir, dname))
]

source_dir = "/media/hdd1/BMAs"

"""Run the pipeline for 100 slides."""

# get a big list of all the slides in the source directory
slides = os.listdir(source_dir)

slides = slides[:100]

# make sure to only keep things with ndpi extension
slides = [slide for slide in slides if slide.endswith(".ndpi")]

print(slides)

import sys

sys.exit()

# randomly shuffle the slides and select 100
random.shuffle(slides)

for bma_fname in tqdm(slides, desc="Processing BMA slides"):

    if already_processed(bma_fname, dump_dirs):
        print("Already processed", bma_fname)
        continue

    print("Processing", bma_fname)

    # try:
    bma_slide_path = os.path.join(source_dir, bma_fname)
    bma_counter = BMACounter(
        bma_slide_path,
        hoarding=True,
        continue_on_error=True,
        do_extract_features=False,
    )
    bma_counter.tally_differential()

    print("Saving to", bma_counter.save_dir)
