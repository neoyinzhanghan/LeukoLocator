####################################################################################################
# Imports ##########################################################################################
####################################################################################################

# Outside imports ##################################################################################`
import openslide
import ray
import pyvips

# Within package imports ###########################################################################
from LL.resources.PBassumptions import *
from LL.vision.image_quality import VoL
from LL.BMAFocusRegion import FocusRegion


# @ray.remote(num_cpus=num_cpus_per_cropper)
@ray.remote
class WSICropManager:
    """A class representing a manager that crops WSIs.

    === Class Attributes ===
    - wsi_path : the path to the WSI
    - wsi : the WSI
    """

    def __init__(self, wsi_path) -> None:
        self.wsi_path = wsi_path
        self.wsi = None

    def open_slide(self):
        """Open the WSI."""

        self.wsi = openslide.OpenSlide(self.wsi_path)

    def open_vips(self):
        """Open the WSI with pyvips."""

        self.wsi = pyvips.Image.new_from_file(self.wsi_path, access="sequential")

    def close_slide(self):
        """Close the WSI."""

        self.wsi.close()

        self.wsi = None

    def crop(self, coords, level=0):
        """Crop the WSI at the lowest level of magnification."""

        if self.wsi is None:
            self.open_slide()

        image = self.wsi.read_region(
            coords, level, (coords[2] - coords[0], coords[3] - coords[1])
        )
        image = image.convert("RGB")

        return image

    def crop_vips(self, coords):
        """Crop the WSI at the lowest level of magnification."""

        if self.wsi is None:
            self.open_vips()

        # Ensure that self.wsi is a pyvips Image
        if not isinstance(self.wsi, pyvips.Image):
            raise TypeError("WSI is not a pyvips Image object")

        # Cropping the image
        # coords are expected to be (left, top, right, bottom)
        cropped_image = self.wsi.crop(coords[0], coords[1], coords[2] - coords[0], coords[3] - coords[1])

        return cropped_image

    def async_get_focus_region_image(self, focus_region):
        """Update the image of the focus region."""

        if focus_region.image is None:
            image = self.crop(focus_region.coordinate)

        # vol = VoL(image) # TODO reconsidering whether the second VoL filtering is event necessary
        # if vol < min_VoL:
        #     return None

        # else:
        #     focus_region.get_image(image)
        #     focus_region.VoL = vol

        #     return focus_region

        focus_region.get_image(image)

        return focus_region

    def async_get_bma_focus_region_batch(self, focus_region_coords):
        """Return a list of focus regions."""

        focus_regions = []
        for focus_region_coord in focus_region_coords:
            image = self.crop(focus_region_coord, level=search_view_level)

            focus_region = FocusRegion(downsampled_coordinate=focus_region_coord, downsampled_image=image)
            focus_regions.append(focus_region)

        return focus_regions
