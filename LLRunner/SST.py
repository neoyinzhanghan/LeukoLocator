from dataclasses import dataclass, field
import pandas as pd
from LLRunner.assumptions import *


@dataclass
class SST:
    """
    Class for the slide scanning tracker of the slide.
    """

    xlsx_path: str = slide_scanning_tracker_path
    sheet_name: str = slide_scanning_tracker_sheet_name
    df: pd.DataFrame = None

    def get_dx(self, accession_number: str) -> tuple:
        """
        Get the diagnosis and sub-diagnosis of the slide.
        """

        if self.df is None:
            self.df = pd.read_excel(self.xlsx_path, sheet_name=self.sheet_name)

        rows = self.df.loc[self.df["Accession Number"] == accession_number]
        dx_box = rows["General Dx"]
        subdx_box = rows["Sub Dx"]
        dx_str = dx_box.iloc[0] if not dx_box.empty else None
        subdx_str = subdx_box.iloc[0] if not subdx_box.empty else None
        if not isinstance(dx_str, str):
            dx_str = None
        if not isinstance(subdx_str, str):
            subdx_str = None
        if dx_str is not None:
            dx_str = dx_str.strip()
        if subdx_str is not None:
            subdx_str = subdx_str.strip()
        if dx_str is None and subdx_str is None:
            raise AccessionNumberNotFoundError(accession_number)
        return dx_str, subdx_str


sst = SST()


class AccessionNumberNotFoundError(Exception):
    """
    Raised when the accession number is not found in the slide scanning tracker.
    """

    def __init__(self, accession_number: str) -> None:
        self.accession_number = accession_number
        super().__init__(
            f"Accession Number {accession_number} not found in the slide scanning tracker."
        )
