import pandas as pd
from LLRunner.assumptions import *


class SR:
    """Class for the status resulst of the slide.

    === Class Attributes ===

    -- csv_path: the path to the csv file
    -- df: the dataframe of the csv file
    """

    def __init__(self) -> None:
        self.csv_path = status_results_path
        self.df = pd.read_csv(self.csv_path)

    def get_recorded_specimen_type(self, slide_name) -> str:
        """Get the specimen type of the slide."""

        # Use .loc to locate the row
        specimen_type_box = self.df.loc[
            self.df.index.str.strip() == slide_name,
            "Part Description",
        ]

        # If the slide name is not found, raise SlideNotFoundError
        if specimen_type_box.empty:
            raise SlideNotFoundError(
                f"Slide name '{slide_name}' not found in the dataset."
            )

        # If you expect only one match and want to get the single value as a string
        specimen_type_str = str(specimen_type_box.iloc[0]).strip()

        # check if the specimen_type_str is a string
        assert isinstance(
            specimen_type_str, str
        ), f"The specimen type is not a string. {specimen_type_str} is of type {type(specimen_type_str)}."

        # No need to check if specimen_type_str is None here as we already checked if the box is empty

        # Determine the specimen type based on the description
        if "bone marrow aspirate" in specimen_type_str.lower():
            specimen_type = "BMA"
        elif "peripheral blood" in specimen_type_str.lower():
            specimen_type = "PB"
        else:
            specimen_type = "Others"

        return specimen_type


sr = SR()


class SlideNotFoundError(Exception):
    """Raised when the slide is not found in the status results."""

    def __init__(self, slide_name: str) -> None:
        self.slide_name = slide_name
        super().__init__(f"Slide {slide_name} not found in the status results.")
