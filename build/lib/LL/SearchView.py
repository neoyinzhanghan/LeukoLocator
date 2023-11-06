####################################################################################################
# Imports ##########################################################################################
####################################################################################################

# Outside imports ##################################################################################
from PIL import Image

# Within package imports ###########################################################################
from LL.resources.assumptions import *
from LL.vision.processing import crop_region_view


class SearchView:
    """ A SearchView class object representing all the information needed at the search view of the WSI. 

    === Class Attributes ===
    - image : the image of the search view
    - crop_dict : a dictionary of crops of the search view, where the key is a tuple tracking (TL_x, TL_y, BR_x, BR_y) of the crop
    - padding_x : the padding of the search view in the x direction (this is so that the search view can be perfectly divided into crops)
    - padding_y : the padding of the search view in the y direction (this is so that the search view can be perfectly divided into crops)
    - downsampling_rate : the downsampling rate of the search view
    - width : the width of the search view
    - height : the height of the search view

    - verbose : whether to print out the progress of the search view

    """

    def __init__(self, image, downsampling_rate, verbose=False):
        """ Initialize a SearchView object. 
        Image is a PIL image. Check the type of image. If not PIL image, raise ValueError."""

        self.verbose = verbose

        if self.verbose:
            print("Checking the type of image...")
        # check the type of image
        if not isinstance(image, Image.Image):
            raise ValueError("Image must be a PIL image.")
        
        self.image = image

        if self.verbose:
            print("Cropping the search view...")
        self.crop_dict, self.padding_x, self.padding_y = crop_region_view(
            image, crop_width=search_view_crop_size[0], crop_height=search_view_crop_size[1])
        self.downsampling_rate = downsampling_rate
        self.width = image.size[0]
        self.height = image.size[1]


    def get_locations(self):
        """ Return a list of locations of the crops in the format of (TL_x, TL_y, BR_x, BR_y). """

        return list(self.crop_dict.keys())

    def __getitem__(self, key):
        """ Return the crop corresponding to the key. """

        return self.crop_dict[key]
