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
    - downsample_rate : the downsampling rate of the focus region
    - downsampled_image : the downsampled image of the focus region corresponding to the search view magnification
    - VoL : the variance of the laplacian of the focus region
    - WMP : the white mask proportion of the focus region
    - wbc_candidate_bbox : a list of bbox of the WBC candidates in the level 0 view in the format of (TL_x, TL_y, BR_x, BR_y)
    """

    def __init__(self, coordinate, search_view_image, downsample_rate):
        """ Initialize a FocusRegion object. The full resolution image is None at initialization. """

        self.coordinate = coordinate
        self.image = None

        # calculate the downsampled coordinate

        downsampled_coordinate = (int(coordinate[0] / downsample_rate), int(coordinate[1] / downsample_rate), int(coordinate[2] / downsample_rate), int(coordinate[3] / downsample_rate))

        self.downsampled_image = search_view_image.crop(downsampled_coordinate)
        self.downsample_rate = downsample_rate

        # Calculate the VoL and WMP
        self.VoL = VoL(self.downsampled_image)
        self.WMP = WMP(self.downsampled_image)

    def get_image(self, slide):
        """ Use the slide object to get the full resolution image of the focus region at level 0. """

        self.image = slide.read_region(
            (self.coordinate[0], self.coordinate[1]), 0, (self.coordinate[2] - self.coordinate[0], self.coordinate[3] - self.coordinate[1]))
        self.image = self.image.convert("RGB")