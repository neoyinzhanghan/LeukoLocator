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
from LL.resources.PBassumptions import *


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

    def crop(self, coords, level=0, downsample_rate=1):
        """Crop the WSI at the lowest level of magnification."""

        if self.wsi is None:
            self.open_slide()

        level_0_coords = (
            coords[0] * downsample_rate,
            coords[1] * downsample_rate,
            coords[2] * downsample_rate,
            coords[3] * downsample_rate,
        )

        image = self.wsi.read_region(
            level_0_coords, level, (coords[2] - coords[0], coords[3] - coords[1])
        )

        image = image.convert("RGB")

        return image

    def async_get_focus_region_image(self, focus_region):
        """Update the image of the focus region."""

        if focus_region.image is None:
            padded_coordinate = (
                focus_region.coordinate[0] - snap_shot_size // 2,
                focus_region.coordinate[1] - snap_shot_size // 2,
                focus_region.coordinate[2] + snap_shot_size // 2,
                focus_region.coordinate[3] + snap_shot_size // 2,
            )
            padded_image = self.crop(padded_coordinate)

            original_width, original_height = focus_region.coordinate[2] - focus_region.coordinate[0], focus_region.coordinate[3] - focus_region.coordinate[1]

            unpadded_image = padded_image.crop(
                (snap_shot_size // 2, snap_shot_size // 2, snap_shot_size // 2 + original_width, snap_shot_size // 2 + original_height)
            )
            
            focus_region.get_image(unpadded_image, padded_image)

        return focus_region

    def async_get_bma_focus_region_batch(self, focus_region_coords):
        """Return a list of focus regions."""

        focus_regions = []
        for focus_region_coord in focus_region_coords:

            image = self.crop(focus_region_coord, level=search_view_level, downsample_rate=search_view_downsample_rate)

            focus_region = FocusRegion(downsampled_coordinate=focus_region_coord, downsampled_image=image)
            focus_regions.append(focus_region)

        return focus_regions
