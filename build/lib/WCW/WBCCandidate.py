####################################################################################################
# Imports ##########################################################################################
####################################################################################################

# Outside imports ##################################################################################
import pandas as pd
import numpy as np

# Within package imports ###########################################################################
from WCW.vision.image_quality import VoL
from WCW.resources.assumptions import *


class WBCCandidate:
    """ A class representing a WBC candidate. 

    === Class Attributes ===

    - snap_shot_bbox : The bounding box of the snap shot of the candidate, in the level_0 view of the PBCounter object containing this candidate.
    - YOLO_bbox : The bounding box of the candidate, in the level_0 view of the PBCounter object containing this candidate, in the format of (TL_x, TL_y, BR_x, BR_y)
    - YOLO_bbox_image : The image of the candidate, in the level_0 view of the PBCounter object containing this candidate.

    - snap_shot : The snap shot of the candidate, in the search_view of the PBCounter object containing this candidate.
    - padded_YOLO_bbox_image : The padded bounding box of the candidate, cropped and zero padded to have square dimension of snap_shot_size

    - confidence : The confidence of the candidate, in the search_view of the PBCounter object containing this candidate.
    - VoL : The variance of laplacian of the snap shot of the candidate, in the level_0 view of the PBCounter object containing this candidate.

    - softmax_vector : the director softmax vector output of the HemeLabel model, should be a vector of length 23
    - name : the name of the candidate, should be the cell_id followed by top 4 classes separated by dashes, with extension .jpg for example: 1-ER4-ER5-ER2-ER1.jpg
    - cell_id : the cell_id of the candidate, should be an integer
    - cell_df_row: a pandas dataframe row of the cell_df of the PBCounter object containing this candidate
        - the dataframe should have the following columns: [cell_id, name, coords, confidence, VoL, cellnames[0], ..., cellnames[num_classes - 1]

    """

    def __init__(self,
                 snap_shot,
                 YOLO_bbox_image,
                 padded_YOLO_bbox_image,
                 snap_shot_bbox,
                 YOLO_bbox,
                 confidence):
        """ Initialize a WBCCandidate object. """

        self.snap_shot_bbox = snap_shot_bbox
        self.YOLO_bbox = YOLO_bbox
        self.YOLO_bbox_image = YOLO_bbox_image

        self.snap_shot = snap_shot
        self.padded_YOLO_bbox_image = padded_YOLO_bbox_image
        self.VoL = VoL(snap_shot)

        self.confidence = confidence
        self.softmax_vector = None
        self.name = None
        self.cell_id = None
        self.cell_df_row = None

    def compute_cell_info(self, cell_id):
        """ Return a pandas dataframe row of the cell_df of the PBCounter object containing this candidate. """

        if self.softmax_vector is None:
            raise CellNotClassifiedError(
                "The softmax vector is not computed yet.")
        
        elif self.cell_df_row is not None:
            return self.cell_df_row

        else:
            sofmax_vector_np = np.array(self.softmax_vector)
            self.name = str(cell_id) + '-' + '-'.join([cellnames[i]
                                                       for i in sofmax_vector_np.argsort()[-4:][::-1]]) + '.jpg'
            self.cell_id = cell_id
            cell_df_row = [self.cell_id, self.name, self.YOLO_bbox,
                           self.confidence, self.VoL] + list(self.softmax_vector)

            # convert the list to a pandas dataframe row
            self.cell_df_row = pd.DataFrame([cell_df_row], columns=[
                                            'cell_id', 'name', 'coords', 'confidence', 'VoL'] + [cellnames[i] for i in range(num_classes)])

            return self.cell_df_row


class CellNotClassifiedError(ValueError):
    """ An error raised when the cell is not classified. """

    def __init__(self, message):
        """ Initialize a CellNotClassifiedError object. """

        super().__init__(message)
