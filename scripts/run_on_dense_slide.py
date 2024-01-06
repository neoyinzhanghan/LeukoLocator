from LL.resources.assumptions import exception_list, dump_dir
from LL.PBCounter import PBCounter
import os
import sys

os.makedirs(dump_dir, exist_ok=True)

# wsi_dir = "/media/hdd2/neo/PB" # this one is for bear
wsi_path = "/media/hdd3/neo/PB_slides/H21-8636;S10;MSK0 - 2023-05-19 16.17.26.ndpi"

pbc = PBCounter(wsi_path, hoarding=True)
pbc.tally_differential()

sys.exit()
