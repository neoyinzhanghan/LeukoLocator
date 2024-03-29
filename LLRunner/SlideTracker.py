from LLRunner.SlideMetadata import SlideMetadata
from LLRunner.SST import AccessionNumberNotFoundError
from LLRunner.SR import SlideNotFoundError
from tqdm import tqdm


class SlidePoolMetadataTracker:
    """Class to keep track of slide metadata.
    === Class Attributes ===
    -- slide_metadata: a list of SlideMetadata objects
    -- no_recorded_specimen_type: a list of slide paths that do not have a recorded specimen type
    -- no_recorded_dx: a list of slide paths that do not have a recorded diagnosis
    """

    def __init__(self, slide_paths) -> None:
        self.slide_metadata = []
        self.no_recorded_specimen_type = []
        self.no_recorded_dx = []
        for slide_path in tqdm(slide_paths, desc="Compiling slides pool metadata"):
            try:
                slide_metadata = SlideMetadata(slide_path)
                self.slide_metadata.append(slide_metadata)
            except AccessionNumberNotFoundError as e:
                self.no_recorded_dx.append(slide_path)
                print(f"Accession number not found for slide {slide_path}.")
            except SlideNotFoundError as e:
                self.no_recorded_specimen_type.append(slide_path)
                print(f"Slide not found in the status results for slide {slide_path}.")

    def get_slides_from_dx(self, dx: str) -> list:
        """Get slides with the given diagnosis."""
        with_records = [
            slide
            for slide in self.slide_metadata
            if slide.recorded_specimen_type != None
        ]

        return [
            slide
            for slide in with_records
            if slide.Dx.strip().lower() == dx.strip().lower()
        ]

    def get_slides_From_recorded_specimen_type(self, specimen_type: str) -> list:
        """Get slides with the given recorded specimen type."""

        with_records = [
            slide
            for slide in self.slide_metadata
            if slide.recorded_specimen_type != None
        ]

        return [
            slide
            for slide in with_records
            if slide.recorded_specimen_type.strip().lower()
            == specimen_type.strip().lower()
        ]

    def get_slides_from_predicted_specimen_type(self, specimen_type: str) -> list:
        """Get slides with the given predicted specimen type."""
        with_records = [
            slide
            for slide in self.slide_metadata
            if slide.predicted_specimen_type != None
        ]

        return [
            slide
            for slide in with_records
            if slide.predicted_specimen_type.strip().lower()
            == specimen_type.strip().lower()
        ]

    def print_all_dx(self) -> None:
        """Print all the diagnoses."""
        for slide in self.slide_metadata:
            print(slide.Dx)


if __name__ == "__main__":

    import os

    slides_folder = "/media/hdd1/BMAs"

    # first get the paths to all the ndpi files in the slides_folder
    slide_paths = [
        os.path.join(slides_folder, fname)
        for fname in os.listdir(slides_folder)
        if fname.endswith(".ndpi")
    ]

    # get the all the slide metadata
    slide_pool_metadata_tracker = SlidePoolMetadataTracker(slide_paths)

    # what are all the slides with the diagnosis "AML" AND are predicted to be a bone marrow aspirate?
    aml_slides = slide_pool_metadata_tracker.get_slides_from_dx("AML")
    # what are all the slides with the diagnosis "Plasma cell myeloma" AND are predicted to be a bone marrow aspirate?
    pcm_slides = slide_pool_metadata_tracker.get_slides_from_dx("Plasma cell myeloma")

    import pandas as pd

    assert len(aml_slides) > 0
    assert len(pcm_slides) > 0

    slide_info = []
    for slide in aml_slides:
        slide_info.append((slide.slide_path, "AML_BMA"))
    for slide in pcm_slides:
        slide_info.append((slide.slide_path, "PCM_BMA"))
    for slide in slide_pool_metadata_tracker.no_recorded_specimen_type:
        slide_info.append((slide, "No Recorded Specimen Type"))
    for slide in slide_pool_metadata_tracker.no_recorded_dx:
        slide_info.append((slide, "No Recorded Dx"))

    df = pd.DataFrame(slide_info, columns=["Slide Path", "Slide Type"])

    # save the dataframe in /media/hdd3/neo
    df.to_csv("/media/hdd3/neo/selected_slide_info.csv", index=False)
