from LL.resources.PBassumptions import exception_list, dump_dir
from LL.PBCounter import PBCounter
import os
import sys

os.makedirs(dump_dir, exist_ok=True)

# wsi_dir = "/media/hdd2/neo/PB" # this one is for bear
wsi_dir = "/media/hdd3/neo/PB_slides"

for slide_name_stem in exception_list:
    slide_name = slide_name_stem + ".ndpi"
    print(slide_name)
    slide_path = os.path.join(wsi_dir, slide_name)

    pbc = PBCounter(slide_path, hoarding=True)
    pbc.tally_differential()

    sys.exit()
