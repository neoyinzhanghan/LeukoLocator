####################################################################################################
# Imports ###########################################################################################
####################################################################################################

# Outside imports ##################################################################################
from PIL import Image

# Within package imports ###########################################################################
from WCW.resources.assumptions import *
from WCW.vision.image_quality import VoL, WMP

class FocusRegion:
    """ A focus region class object representing all the information needed at the focus region of the WSI. 

    === Class Attributes ===
    - coordinate : the coordinate of the focus region in the level 0 view in the format of (TL_x, TL_y, BR_x, BR_y)
    - image : the image of the focus region
    - downsampled_image : the downsampled image of the focus region corresponding to the search view magnification
    - VoL : the variance of the laplacian of the focus region
    - WMP : the white mask proportion of the focus region
    - wbc_candidate_bbox : a list of bbox of the WBC candidates in the level 0 view in the format of (TL_x, TL_y, BR_x, BR_y)
    """

    def __init__(self, coordinate, image, downsampled_image):
        """ Initialize a FocusRegion object. """

        self.coordinate = coordinate
        self.image = image
        self.downsampled_image = downsampled_image

        # Calculate the VoL and WMP
        self.VoL = VoL(downsampled_image)
        self.WMP = WMP(downsampled_image)
