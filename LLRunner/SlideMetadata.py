from LL.front_end.heme_analyze import *
from pathlib import Path
from LLRunner.SR import sr
from LLRunner.SST import sst


class SlideMetadata:
    """A class that keeps track of the slide metadata.
    === Class Attributes ===
    -- slide_path: the path to the slide
    -- slide_name: the name of the slide
    -- slide_ext = the extension of the slide
    -- accession_number: the accession number of the slide
    -- recorded_specimen_type: the type of specimen
    -- predicted_specimen_type: the predicted type of specimen
    -- bma_confidence: the confidence of the prediction for BMA by the specimen type model
    -- pb_confidence: the confidence of the prediction for PB by the specimen type model
    -- mpboribma_confidence: the confidence of the prediction for MPB by the specimen type model
    -- other_confidence the confidence of the prediction for other by the specimen type model
    -- Dx: the diagnosis of the slide
    -- sub_Dx: the sub-diagnosis of the slide

    """

    def __init__(self, slide_path, run_classifier=False) -> None:
        self.slide_path = slide_path
        self.slide_stem = Path(slide_path).stem
        self.slide_name = Path(slide_path).name
        self.slide_ext = Path(slide_path).suffix
        self.accession_number = self.slide_stem.split(";")[0]
        print(self.accession_number)
        self.recorded_specimen_type = sr.get_recorded_specimen_type(self.slide_name)

        if not run_classifier:
            self.predicted_specimen_type = None # classify_specimen_type(self.slide_path)
            self.conf_dct = None # get_specimen_conf_dict(self.slide_path)
            self.bma_confidence = None # conf_dct["Bone Marrow Aspirate"]
            self.pb_confidence =  None # conf_dct["Peripheral Blood"]
            self.mpboribma_confidence = None #conf_dct["Manual Peripheral Blood or Inadequate Bone Marrow Aspirate"]
            self.other_confidence = None # conf_dct["Others"]
        else:
            self.predicted_specimen_type = classify_specimen_type(self.slide_path)
            self.conf_dct = get_specimen_conf_dict(self.slide_path)
            self.bma_confidence = self.conf_dct["Bone Marrow Aspirate"]
            self.pb_confidence = self.conf_dct["Peripheral Blood"]
            self.mpboribma_confidence = self.conf_dct["Manual Peripheral Blood or Inadequate Bone Marrow Aspirate"]
            self.other_confidence = self.conf_dct["Others"]
        self.Dx, self.sub_Dx = sst.get_dx(self.accession_number)
