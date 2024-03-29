import pandas as pd
from LLRunner.assumptions import *


class SST:
    """Class for the slide scanning tracker of the slide.

    === Class Attributes ===
    -- xlsx_path: the path to the Excel file
    -- sheet_name: the name of the sheet
    -- df: the dataframe of the Excel file

    """

    def __init__(self) -> None:
        self.xlsx_path = slide_scanning_tracker_path
        self.sheet_name = slide_scanning_tracker_sheet_name
        self.df = pd.read_excel(self.xlsx_path, sheet_name=self.sheet_name)

        # print(self.df.head())

        # import sys

        # sys.exit()

        # # print the head of the Accession Number column as a list
        # print(self.df["Accession Number"].head().tolist())

        # import sys
        # sys.exit()

    def get_dx(self, accession_number) -> str:
        """Get the diagnosis and sub-diagnosis of the slide."""

        # find all the rows with the given accession number
        rows = self.df.loc[self.df["Accession Number"] == accession_number]

        print(rows)

        # # if the number of rows is 0, raise AccessionNumberNotFoundError
        # if rows.empty:
        #     print(rows)
        #     raise AccessionNumberNotFoundError(accession_number)
        
        # get the "General Dx" and "Sub Dx" columns
        dx_box = rows["General Dx"]

        subdx_box = rows["Sub Dx"]

        # get the dx and subdx as strings
        dx_str = dx_box.iloc[0] if not dx_box.empty else None
        subdx_str = subdx_box.iloc[0] if not subdx_box.empty else None

        # if they are not string types, convert them to None
        if not isinstance(dx_str, str):
            dx_str = None

        if not isinstance(subdx_str, str):
            subdx_str = None

        return dx_str, subdx_str


sst = SST()


class AccessionNumberNotFoundError(Exception):
    """Raised when the accession number is not found in the slide scanning tracker."""

    def __init__(self, accession_number: str) -> None:
        self.accession_number = accession_number
        super().__init__(
            f"Accession Number {accession_number} not found in the slide scanning tracker."
        )
