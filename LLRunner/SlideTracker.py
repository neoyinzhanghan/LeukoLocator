from LLRunner.SlideMetadata import SlideMetadata
from LLRunner.SST import AccessionNumberNotFoundError
from LLRunner.SR import SlideNotFoundError
from tqdm import tqdm


class SlidePoolMetadataTracker:
    """Class to keep track of slide metadata.
    === Class Attributes ===
    -- slide_metadata: a list of SlideMetadata objects
    -- inaccessable_slides: a list of SlideMetadata objects that could not be accessed
    """

    def __init__(self, slide_paths) -> None:
        self.slide_metadata = []
        self.inaccessable_slides = []
        for slide_path in tqdm(slide_paths, desc="Compiling slides pool metadata"):
            try:
                slide_metadata = SlideMetadata(slide_path)
                self.slide_metadata.append(slide_metadata)
            except AccessionNumberNotFoundError as e:
                self.inaccessable_slides.append(slide_path)
                print(f"Accession number not found for slide {slide_path}.")
            except SlideNotFoundError as e:
                self.inaccessable_slides.append(slide_path)
                print(f"Slide not found in the status results for slide {slide_path}.")

    def get_slides_from_dx(self, dx: str) -> list:
        """Get slides with the given diagnosis."""
        return [slide for slide in self.slide_metadata if slide.Dx == dx]

    def get_slides_From_recorded_specimen_type(self, specimen_type: str) -> list:
        """Get slides with the given recorded specimen type."""
        return [
            slide
            for slide in self.slide_metadata
            if slide.recorded_specimen_type == specimen_type
        ]

    def get_slides_from_predicted_specimen_type(self, specimen_type: str) -> list:
        """Get slides with the given predicted specimen type."""
        return [
            slide
            for slide in self.slide_metadata
            if slide.predicted_specimen_type == specimen_type
        ]


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
    bma_slides = slide_pool_metadata_tracker.get_slides_from_predicted_specimen_type(
        "Bone Marrow Aspirate"
    )
    aml_bma_slides = [slide for slide in aml_slides if slide in bma_slides]

    # what are all the slides with the diagnosis "Plasma cell myeloma" AND are predicted to be a bone marrow aspirate?
    pcm_slides = slide_pool_metadata_tracker.get_slides_from_dx("Plasma cell myeloma")
    pcm_bma_slides = [slide for slide in pcm_slides if slide in bma_slides]

    print("Slides with the diagnosis 'AML' and predicted to be a BMA:")
    for slide in aml_bma_slides:
        print(slide.slide_name)

    print(
        "\nSlides with the diagnosis 'Plasma cell myeloma' and predicted to be a BMA:"
    )
    for slide in pcm_bma_slides:
        print(slide.slide_name)

    print("\nSlides that could not be accessed:")
    for slide_name in slide_pool_metadata_tracker.inaccessable_slides:
        print(slide_name)
