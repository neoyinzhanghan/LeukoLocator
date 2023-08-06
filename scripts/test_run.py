from WCW.resources.assumptions import *
from WCW.PBCounter import PBCounter

if __name__ == "__main__":
    pbc = PBCounter(test_example_path)
    pbc.tally_differential()
    print(pbc.differential.wbc_candidate_df)