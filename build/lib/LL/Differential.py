####################################################################################################
# Imports ##########################################################################################
####################################################################################################

# Outside imports ##################################################################################`
import pandas as pd
import numpy as np

# Within package imports ###########################################################################
from LL.resources.assumptions import *


class Differential:
    """ A class representing the differential of a PBCounter object.

    === Class Attributes ===
    - wbc_candidate_df : a pandas dataframe containing the information of the WBC candidates
        its columns are: coords, confidence, VoL, cellnames[0], ..., cellnames[num_classes - 1]
    """

    def __init__(self, wbc_candidates):
        """ Initialize a Differential object. The input is a list of WBCCandidate objects. """

        # initialize the dataframe
        df = pd.DataFrame(columns=['cell_id', 'name', 'coords', 'confidence',
                          'VoL'] + [cellnames[i] for i in range(num_classes)])

        # traverse through the list of WBCCandidate objects and add them to the dataframe
        for ind in range(len(wbc_candidates)):
            # use concat to avoid deprecation
            new_df = wbc_candidates[ind].compute_cell_info(ind)
            df = pd.concat([df, new_df], ignore_index=True)

        self.wbc_candidate_df = df

    def __len__(self):
        """ Return the number of cells in the differential. """

        return len(self.wbc_candidate_df)

    def __getitem__(self, key) -> dict:
        """ Return the key-th row of the dataframe.
        The key is the row index of the dataframe as a dictionary."""

        return self.wbc_candidate_df.iloc[key].to_dict()

    def tally_dict(self, omitted_classes, removed_classes, print_results=True):
        """ Return a dictionary of the tally of the differential. 
        First make a clone of the dataframe. Set all omitted classes to -np.inf. 
        Then add a column which is the label computed as the argmax of the softmax vector.
        Then remove all instances labelled into the removed classes. 
        Then return the tally of the dataframe. 
        Print the tally if print_results is True. """

        # check if omitted_classes are inside cellnames, if not raise a ValueError
        for omitted_class in omitted_classes:
            if omitted_class not in cellnames:
                raise ValueError(
                    f"One of the omitted class ({omitted_class}) is not a element of supported classes {cellnames}.")

        # do the same for removed_classes
        for removed_class in removed_classes:
            if removed_class not in cellnames:
                raise ValueError(
                    f"One of the removed class ({removed_class}) is not a element of supported classes {cellnames}.")

        # clone the dataframe
        df = self.wbc_candidate_df.copy()

        # set all omitted classes to -np.inf
        for omitted_class in omitted_classes:
            df[omitted_class] = -np.inf

        # create a new column which is the label computed as the argmax of the softmax vector
        # the label should be an element of cellnames
        df['label'] = df[cellnames].idxmax(axis=1)

        # remove all instances labelled into the removed classes
        df = df[~df['label'].isin(removed_classes)]

        # tally the dataframe, create a dictionary, key is a cellname, and value is the proportion of that cellname in the dataframe
        tally = df['label'].value_counts(normalize=True).to_dict()

        # print the tally if print_results is True
        if print_results:
            for cellname in tally:
                print(f"{cellnames_dict[cellname]}: {tally[cellname]}")

        return tally

    def tally_string(self, omitted_classes, removed_classes, print_results=True):
        """ First get the tally dictionary, and then convert it to a string as how it would be printed. """

        # get the tally dictionary
        tally = self.tally_dict(
            omitted_classes, removed_classes, print_results)

        # convert the tally dictionary to a string
        tally_string = ""

        for cellname in tally:
            tally_string += f"{cellnames_dict[cellname]}: {tally[cellname]}\n"

        return tally_string

    def compute_PB_differential(self, omitted_classes=omitted_classes, removed_classes=removed_classes, differential_group_dict=differential_group_dict):
        """ Return a dictionary of the tally of the differential for the final PB result.
        Use differential_group_dict to group the cells into the following categories:
        Immature Granulocyte, Neutrophil, Eosinophil, Blast, Monocyte, Lymphocyte, Nucleated RBC, Basophil. """

        # get the tally dictionary
        tally = self.tally_dict(
            omitted_classes, removed_classes, print_results=False)

        # create a new dictionary
        PB_tally = {}

        # traverse through the keys of differential_group_dict
        for key in PB_final_classes:

            # initialize the value of the key to be 0
            PB_tally[key] = 0

            # traverse through the values of the key
            for value in differential_group_dict[key]:
                
                if value not in tally:
                    continue

                # add the value to the key
                PB_tally[key] += tally[value]

        return PB_tally
