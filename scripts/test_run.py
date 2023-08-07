from WCW.resources.assumptions import *
from WCW.PBCounter import PBCounter
import time

if __name__ == "__main__":

    start_time = time.time()
    pbc = PBCounter(test_example_path)
    pbc.tally_differential()
    total_time = time.time() - start_time

    print(f"{len(pbc.differential)} cells are extracted and classified in {total_time} seconds.")

    pbc.differential.tally(omitted_classes=[], removed_classes=['ER5', 'ER6'])