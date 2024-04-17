import pandas as pd
from pathlib import Path
from LLRunner.assumptions import cellnames
from LLRunner.BMAassumptions import *


class BMAResult:
    """
    Class for keeping track of the results of the LLRunner on a BMA slide.

    === Class Attributes ===
    -- result_dir: the directory where the results are stored
    -- error: a boolean indicating if the result directory is an error directory
    -- cell_info: a pandas DataFrame containing the cell information
    """

    def __init__(self, result_dir):
        """Use the result directory to get the results of the LLRunner."""

        # result_dir is a string, make it a Path object
        result_dir = Path(result_dir)

        # first check if the result directory exists
        assert result_dir.exists(), f"Result directory {result_dir} does not exist."

        # second check if the result directory's folder name starts with "ERROR_"
        self.error = result_dir.name.startswith("ERROR_")

        self.result_dir = result_dir

        if not self.error:
            self.cell_info = pd.read_csv(result_dir / "cells" / "cells_info.csv")

    def get_stacked_differential(self):
        """In the cell_info dataframe there are columns corresponding to each cell type in the list cellnames.
        Take the average of the probabilities for each cell type and return a dictionary with the cell type as the key and the average probability as the value.
        """

        # get the columns corresponding to the cell types
        cell_columns = self.cell_info[cellnames]

        # take the average of the probabilities for each cell type
        average_probabilities = cell_columns.mean()

        # return a dictionary with the cell type as the key and the average probability as the value
        return average_probabilities.to_dict()

    def get_one_hot_differential(self):
        """
        In the cell_info dataframe there are columns corresponding to each cell type in the list cellnames.
        The predicted class is the class with the highest probability, return a dictionary with the cell type as the key and the proportion of cells predicted as that type as the value.
        """

        # get the columns corresponding to the cell types
        cell_columns = self.cell_info[cellnames]

        # get the predicted class for each cell
        predicted_classes = cell_columns.idxmax(axis=1)

        # get the proportion of cells predicted as each cell type
        one_hot_differential = predicted_classes.value_counts(normalize=True)

        # return a dictionary with the cell type as the key and the proportion of cells predicted as that type as the value
        return one_hot_differential.to_dict()

    def get_grouped_differential(
        self,
        omitted_classes=omitted_classes,
        removed_classes=removed_classes,
        differential_group_dict=differential_group_dict,
    ):
        """
        First set the probability in the omitted classes to 0.
        Then classify the cells into the cellnames classes and remove all the cells in the removed classes.
        Finally, give the cell a class from the differential_group_dict based on their cellname classes.
        (The differential_group_dict should map a grouped class to the a list of cellname classes that grouped class contains)
        """

        # set the values of columns corresponding to the omitted classes to 0
        self.cell_info[omitted_classes] = 0

        # classify the cells into the cellnames classes
        self.cell_info["cell_class"] = self.cell_info[cellnames].idxmax(axis=1)

        # remove all the cells in the removed classes
        self.cell_info = self.cell_info[
            ~self.cell_info["cell_class"].isin(removed_classes)
        ]

        # give the cell a class from the differential_group_dict based on their cellname classes
        self.cell_info["grouped_class"] = self.cell_info["cell_class"].apply(
            lambda x: next(
                (
                    grouped_class
                    for grouped_class in differential_group_dict
                    if x in differential_group_dict[grouped_class]
                ),
                None,
            )
        )

        # get the proportion of cells in each grouped class
        grouped_differential = self.cell_info["grouped_class"].value_counts(
            normalize=True
        )

        # return a dictionary with the grouped class as the key and the proportion of cells in that class as the value
        return grouped_differential.to_dict()

    def get_grouped_stacked_differential(self):
        """First set the omitted class probabilities to zero, and then remove all rows where the top probability class is in removed_classes.
        Then use the differential_group_dict to group the cells into the grouped classes.
        But you stack the probablities together, for example if "neutrophils/bands": ["M5", "M6"]" then you sum the probabilities of M5 and M6 together to get the probability of neutrophils/bands.
        Then return a dictionary with the grouped class as the key and the average probability as the value.
        """

        # set the values of columns corresponding to the omitted classes to 0
        self.cell_info[omitted_classes] = 0

        # classify the cells into the cellnames classes
        self.cell_info["cell_class"] = self.cell_info[cellnames].idxmax(axis=1)

        # remove all the cells in the removed classes
        self.cell_info = self.cell_info[
            ~self.cell_info["cell_class"].isin(removed_classes)
        ]

        for grouped_class, cellnames_list in differential_group_dict.items():
            self.cell_info[grouped_class + "_grouped_stacked"] = self.cell_info[
                cellnames_list
            ].sum(axis=1)

        # get the average probability of cells in each grouped class
        grouped_stacked_differential = self.cell_info[
            [
                grouped_class + "_grouped_stacked"
                for grouped_class in differential_group_dict
            ]
        ].mean()

        # return a dictionary with the grouped class as the key and the average probability of cells in that class as the value
        return grouped_stacked_differential.to_dict()

    def get_raw_counts(self):
        """
        Return the raw counts of the cells in the cell_info dataframe after classifying the cells into the cellnames classes.
        """

        # classify the cells into the cellnames classes
        self.cell_info["cell_class"] = self.cell_info[cellnames].idxmax(axis=1)

        # get the raw counts of the cells in the cell_info dataframe
        raw_counts = self.cell_info["cell_class"].value_counts()

        # return a dictionary with the cell type as the key and the raw count of cells of that type as the value
        return raw_counts.to_dict()

    def get_grouped_raw_counts(self):
        """
        Return the raw counts of the cells in the cell_info dataframe after classifying the cells into the cellnames classes
        after setting omitted class probabilities to 0 and removing all the cells in the removed classes.
        The counts should be grouped based on the differential_group_dict.
        """

        # set the values of columns corresponding to the omitted classes to 0
        self.cell_info[omitted_classes] = 0

        # classify the cells into the cellnames classes
        self.cell_info["cell_class"] = self.cell_info[cellnames].idxmax(axis=1)

        # remove all the cells in the removed classes
        self.cell_info = self.cell_info[
            ~self.cell_info["cell_class"].isin(removed_classes)
        ]

        # give the cell a class from the differential_group_dict based on their cellname classes
        self.cell_info["grouped_class"] = self.cell_info["cell_class"].apply(
            lambda x: next(
                (
                    grouped_class
                    for grouped_class in differential_group_dict
                    if x in differential_group_dict[grouped_class]
                ),
                None,
            )
        )

        # get the raw counts of the cells in the cell_info dataframe
        grouped_raw_counts = self.cell_info["grouped_class"].value_counts()

        # return a dictionary with the grouped class as the key and the raw count of cells in that class as the value
        return grouped_raw_counts.to_dict()

    def get_M1L2_results(self):
        """Get the differential and count for cells where the top class is M1 and the second class is L2.
        Conversely, get the differential and count for cells where the top class is L2 and the second class is M1.

        Store in a dictionary with keys `M1L2` and `L2M1`, and `M1L2_count`, `L2M1_count` respectively.
        """

        # get all the cells that have M1 as the top probability class and L2 as the second highest probability class
        M1L2_cells = self.cell_info[
            (self.cell_info["first"] == "M1") & (self.cell_info["second"] == "L2")
        ]

        # conversely, get all the cells that have L2 as the top probability class and M1 as the second highest probability class
        L2M1_cells = self.cell_info[
            (self.cell_info["first"] == "L2") & (self.cell_info["second"] == "M1")
        ]

        # print how many cells are in each of these categories
        M1L2_count = len(M1L2_cells)
        L2M1_count = len(L2M1_cells)

        # get the differential for each of these categories
        M1L2_diff = M1L2_count / len(self.cell_info)
        L2M1_diff = L2M1_count / len(self.cell_info)

        return {
            "M1L2": M1L2_diff,
            "L2M1": L2M1_diff,
            "M1L2_count": M1L2_count,
            "L2M1_count": L2M1_count,
        }
