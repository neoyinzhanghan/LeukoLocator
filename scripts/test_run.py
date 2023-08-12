from WCW.resources.assumptions import *
from WCW.communication.saving import save_wbc_candidates, save_focus_regions, save_wbc_candidates_sorted
from WCW.PBCounter import PBCounter
import time

if __name__ == "__main__":

    # test_example_path = "/pesgisipth/NDPI/H23-376;S16;MSK1 - 2023-06-12 14.10.18.ndpi"

    # test_example_path = "/media/hdd3/neo/H20-4473;S11;MSK5 - 2023-04-25 20.58.14.ndpi"

    test_example_path = "/media/hdd3/neo/H23-376;S16;MSK1 - 2023-06-12 14.10.18.ndpi"

    start_time = time.time()
    pbc = PBCounter(test_example_path)
    pbc.tally_differential()
    total_time = time.time() - start_time

    print(f"{len(pbc.differential)} cells are extracted and classified in {total_time} seconds.")

    # save_focus_regions(pbc)
    save_wbc_candidates_sorted(pbc, image_type='padded_YOLO_bbox_image')

    print ("No Removed Classes")
    tally = pbc.differential.tally_dict(omitted_classes=[], removed_classes=[])

    print ("Removed Classes: ER5, ER6")
    tally = pbc.differential.tally_dict(omitted_classes=[], removed_classes=['ER5', 'ER6'])

    print ("Removed Classes: ER5, ER6, PL2, PL3")
    tally = pbc.differential.tally_dict(omitted_classes=[], removed_classes=['ER5', 'ER6', 'PL2', 'PL3'])