from LL.resources.assumptions import exception_list, dump_dir
from LL.PBCounter import PBCounter
import os
import sys

os.makedirs(dump_dir, exist_ok=True)

wsi_dir = "/media/hdd1/neo/PB"

for slide_name_stem in exception_list:
    slide_name = slide_name_stem + ".ndpi"
    print(slide_name)
    slide_path = os.path.join(wsi_dir, slide_name)

    pbc = PBCounter(slide_path, hoarding=True)
    pbc.tally_differential()

    sys.exit()
