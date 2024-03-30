from dataclasses import dataclass, field
import pandas as pd
from LLRunner.assumptions import *


@dataclass
class SR:
    """
    Class for the status results of the slide.
    """

    csv_path: str = status_results_path
    df: pd.DataFrame = field(init=False)

    def __post_init__(self):
        self.df = pd.read_csv(self.csv_path)

    def get_recorded_specimen_type(self, slide_name: str) -> str:
        """
        Get the specimen type of the slide.
        """
        specimen_type_box = self.df.loc[
            self.df.index.str.strip() == slide_name, "Part Description"
        ]

        if specimen_type_box.empty:
            raise SlideNotFoundError(
                f"Slide name '{slide_name}' not found in the dataset."
            )

        specimen_type_str = str(specimen_type_box.iloc[0]).strip()
        assert isinstance(
            specimen_type_str, str
        ), f"The specimen type is not a string. {specimen_type_str} is of type {type(specimen_type_str)}."

        if "bone marrow aspirate" in specimen_type_str.lower():
            specimen_type = "BMA"
        elif "peripheral blood" in specimen_type_str.lower():
            specimen_type = "PB"
        else:
            specimen_type = "Others"

        return specimen_type


sr = SR()


class SlideNotFoundError(Exception):
    """
    Raised when the slide is not found in the status results.
    """

    def __init__(self, slide_name: str) -> None:
        self.slide_name = slide_name
        super().__init__(f"Slide {slide_name} not found in the status results.")
