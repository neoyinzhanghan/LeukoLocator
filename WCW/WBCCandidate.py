####################################################################################################
# Imports ##########################################################################################
####################################################################################################

# Outside imports ##################################################################################
from WCW.vision.image_quality import VoL

# Within package imports ###########################################################################

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