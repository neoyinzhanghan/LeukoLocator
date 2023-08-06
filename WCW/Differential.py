####################################################################################################
# Imports ##########################################################################################
####################################################################################################

# Outside imports ##################################################################################`
import pandas as pd

# Within package imports ###########################################################################
from assumptions import *


class Differential:
    """ A class representing the differential of a PBCounter object.
    
    === Class Attributes ===
    - wbc_candidate_df : a pandas dataframe containing the information of the WBC candidates
        its columns are: coords, confidence, VoL, cellnames[0], ..., cellnames[num_classes - 1]
    """

    def __init__(self, wbc_candidates):
        """ Initialize a Differential object. The input is a list of WBCCandidate objects. """

        # initialize the dataframe
        df = pd.DataFrame(columns=['coords', 'confidence', 'VoL'] + [cellnames[i] for i in range(num_classes)])

        # traverse through the list of WBCCandidate objects and add them to the dataframe
        for wbc_candidate in wbc_candidates:
            # use concat to avoid deprecation
            new_df = pd.DataFrame([[wbc_candidate.snap_shot_bbox, wbc_candidate.confidence, wbc_candidate.VoL] + wbc_candidate.softmax_vector], columns=['coords', 'confidence', 'VoL'] + [cellnames[i] for i in range(num_classes)])
            df = pd.concat([df, new_df], ignore_index=True)
        
        self.wbc_candidate_df = df