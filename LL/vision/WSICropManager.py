####################################################################################################
# Imports ##########################################################################################
####################################################################################################

# Outside imports ##################################################################################`
import openslide
import ray
import pyvips

# Within package imports ###########################################################################
from LL.vision.image_quality import VoL
from LL.BMAFocusRegion import FocusRegion
from LL.resources.BMAassumptions import search_view_level, search_view_downsample_rate


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
            coords, level, (coords[2] - coords[0], coords[3] - coords[1]) ## <<<< THIS SHIT IS FUCKED TODO
        )

        image = image.convert("RGB")

        return image

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

            level_0_coord = (
                focus_region_coord[0] * search_view_downsample_rate,
                focus_region_coord[1] * search_view_downsample_rate,
                focus_region_coord[2] * search_view_downsample_rate,
                focus_region_coord[3] * search_view_downsample_rate,
            )

            image = self.crop(level_0_coord, level=search_view_level)

            focus_region = FocusRegion(downsampled_coordinate=focus_region_coord, downsampled_image=image)
            focus_regions.append(focus_region)

        return focus_regions
