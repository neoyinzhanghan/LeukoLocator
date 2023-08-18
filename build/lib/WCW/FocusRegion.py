####################################################################################################
# Imports ###########################################################################################
####################################################################################################

# Outside imports ##################################################################################
from PIL import Image
import numpy as np
import pandas as pd

# Within package imports ###########################################################################
from WCW.resources.assumptions import *
from WCW.vision.image_quality import VoL, WMP
from WCW.communication.visualization import annotate_focus_region


class FocusRegion:
    """ A focus region class object representing all the information needed at the focus region of the WSI. 

    === Class Attributes ===
    - coordinate : the coordinate of the focus region in the level 0 view in the format of (TL_x, TL_y, BR_x, BR_y)
    - image : the image of the focus region
    - annotated_image : the image of the focus region annotated with the WBC candidates
    - downsample_rate : the downsampling rate of the focus region
    - downsampled_image : the downsampled image of the focus region corresponding to the search view magnification
    - VoL : the variance of the laplacian of the focus region
    - WMP : the white mask proportion of the focus region
    - wbc_candidate_bboxes : a list of bbox of the WBC candidates in the level 0 view in the format of (TL_x, TL_y, BR_x, BR_y) in relative to the focus region
    """

    def __init__(self, coordinate, search_view_image, downsample_rate):
        """ Initialize a FocusRegion object. The full resolution image is None at initialization. """

        self.coordinate = coordinate
        self.image = None
        self.annotated_image = None

        # calculate the downsampled coordinate

        downsampled_coordinate = (int(coordinate[0] / downsample_rate), int(coordinate[1] / downsample_rate), int(
            coordinate[2] / downsample_rate), int(coordinate[3] / downsample_rate))

        self.downsampled_image = search_view_image.crop(downsampled_coordinate)
        self.downsample_rate = downsample_rate

        # Calculate the VoL and WMP
        self.VoL = VoL(self.downsampled_image)
        self.WMP = WMP(self.downsampled_image)

        self.wbc_candidate_bboxes = None

    def get_image(self, image):
        """ Update the image of the focus region. """

        self.image = image

    def get_annotated_image(self):
        """ Return the image of the focus region annotated with the WBC candidates. """

        if self.image is None or self.wbc_candidate_bboxes is None:
            raise self.FocusRegionNotAnnotatedError

        elif self.annotated_image is not None:
            return self.annotated_image

        else:
            self.annotated_image = annotate_focus_region(
                self.image, self.wbc_candidate_bboxes)
            return self.annotated_image

    def get_annotation_df(self):
        """ Return a dataframe containing the annotations of the focus region. Must have columns ['TL_x', 'TL_y', 'BR_x', 'BR_y']. """

        if self.wbc_candidate_bboxes is None:
            raise self.FocusRegionNotAnnotatedError

        else:
            return pd.DataFrame(self.wbc_candidate_bboxes, columns=['TL_x', 'TL_y', 'BR_x', 'BR_y'])

class FocusRegionNotAnnotatedError(ValueError):
    """ Raised when the focus region is not annotated. """

    def __init__(self, message="The focus region is not annotated."):
        self.message = message
        super().__init__(self.message)
