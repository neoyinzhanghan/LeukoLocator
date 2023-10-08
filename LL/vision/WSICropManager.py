####################################################################################################
# Imports ##########################################################################################
####################################################################################################

# Outside imports ##################################################################################`
import openslide
import ray

# Within package imports ###########################################################################
from LL.FocusRegion import FocusRegion
from LL.resources.assumptions import *
from LL.vision.image_quality import VoL


@ray.remote(num_cpus=num_cpus_per_manager)
class WSICropManager:
    """ A class representing a manager that crops WSIs.

    === Class Attributes ===
    - wsi_path : the path to the WSI
    - wsi : the WSI
    """

    def __init__(self, wsi_path) -> None:

        self.wsi_path = wsi_path
        self.wsi = None

    def open_slide(self):
        """ Open the WSI. """

        self.wsi = openslide.OpenSlide(self.wsi_path)

    def close_slide(self):
        """ Close the WSI. """

        self.wsi.close()

        self.wsi = None

    def crop(self, coords):
        """ Crop the WSI at the lowest level of magnification. """

        if self.wsi is None:
            self.open_slide()

        image = self.wsi.read_region(
            coords, 0, (coords[2] - coords[0], coords[3] - coords[1]))
        image = image.convert("RGB")

        return image

    def async_get_focus_region_image(self, focus_region):
        """ Update the image of the focus region. """

        if focus_region.image is None:
            image = self.crop(focus_region.coordinate)

        vol = VoL(image)
        if vol < min_VoL:
            return None

        else:
            focus_region.get_image(image)
            focus_region.VoL = vol

            return focus_region