from WCW.resources.assumptions import *
from WCW.communication.saving import save_wbc_candidates, save_focus_regions, save_wbc_candidates_sorted
from WCW.PBCounter import PBCounter
import time

if __name__ == "__main__":

    start_time = time.time()
    pbc = PBCounter(test_example_path)
    pbc.tally_differential()
    total_time = time.time() - start_time

    print(f"{len(pbc.differential)} cells are extracted and classified in {total_time} seconds.")

    # save_focus_regions(pbc)
    save_wbc_candidates_sorted(pbc, image_type='padded_YOLO_bbox_image')

    tally = pbc.differential.tally(omitted_classes=[], removed_classes=[])
    tally = pbc.differential.tally(omitted_classes=[], removed_classes=['ER5', 'ER6'])
    tally = pbc.differential.tally(omitted_classes=[], removed_classes=['ER5', 'ER6', 'PL2', 'PL3'])