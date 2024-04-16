import pandas as pd
from pathlib import Path
from LLRunner.assumptions import cellnames


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
            self.cell_info = pd.read_csv(result_dir / "cell_info.csv")

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
