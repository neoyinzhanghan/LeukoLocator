####################################################################################################
# Imports ##########################################################################################
####################################################################################################

# Outside imports ##################################################################################
import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
import openslide
from pathlib import Path
from PIL import Image

# Within package imports ###########################################################################
from LL.vision.masking import get_white_mask, get_obstructor_mask, get_top_view_mask
from LL.resources.BMAassumptions import *
from LL.vision.processing import read_with_timeout
from LL.vision.bma_particle_detection import get_top_view_preselection_mask, get_grid_rep


def extract_top_view(wsi_path, save_dir=None):
    # you can get the stem by removing the last 5 characters from the file name (".ndpi")
    stem = Path(wsi_path).stem[:-5]

    print("Extracting top view")
    # open the wsi in tmp_dir and extract the top view
    wsi = openslide.OpenSlide(wsi_path)
    toplevel = wsi.level_count - 1
    topview = read_with_timeout(
        wsi=wsi,
        location=(0, 0),
        level=toplevel,
        dimensions=wsi.level_dimensions[toplevel],
    )

    # make sure to convert topview tp a PIL image in RGB mode
    if topview.mode != "RGB":
        topview = topview.convert("RGB")

    if save_dir is not None:
        topview.save(os.path.join(save_dir, stem + ".jpg"))
    wsi.close()

    return topview


class TopView:

    """A TopView class object representing all the information needed at the top view of the WSI.

    === Class Attributes ===
    - image : the image of the top view
    - mask : the mask of the top view
    - blue_mask : the blue mask of the top view
    - overlayed_image : the image of the top view with the mask overlayed
    - grid_rep : the grid representation of the top view
    - width : the width of the top view
    - height : the height of the top view
    - downsampling_rate : the downsampling rate of the top view
    - level : the level of the top view in the WSI

    - is_bma : whether the top view is a bone marrow aspirate top view
    - verbose : whether to print out the progress of the top view
    """

    def __init__(self, image, downsampling_rate, level, verbose=False, is_bma=True):
        """Initialize a TopView object.
        Image is a PIL image. Check the type of image. If not PIL image, raise ValueError.
        """
        self.verbose = verbose
        self.is_bma = is_bma
        self.downsampling_rate = downsampling_rate
        self.level = level

        if self.verbose:
            print("Checking the type of image...")
        # check the type of image
        if not isinstance(image, Image.Image):
            raise ValueError("Image must be a PIL image.")

        self.image = image

        if self.verbose:
            print("Printing various masks of the top view...")

        # make sure image is converted to cv2 format
        image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        mask, overlayed_image, final_blue_mask = get_top_view_preselection_mask(image, verbose=False)

        # if the mask is all black then change the mask to all white
        if np.all(mask == 0):
            mask = 255 * np.ones_like(mask)
            print("User Warning: The mask is all black. Changing the mask to all white.")

        # now make sure mask, overlayed_image and final_blue_mask are converted to PIL images after converting to RGB
        mask_pil = Image.fromarray(cv2.cvtColor(mask, cv2.COLOR_BGR2RGB))
        overlayed_image_pil = Image.fromarray(cv2.cvtColor(overlayed_image, cv2.COLOR_BGR2RGB))
        final_blue_mask_pil = Image.fromarray(cv2.cvtColor(final_blue_mask, cv2.COLOR_BGR2RGB))

        self.mask = mask_pil
        self.overlayed_image = overlayed_image_pil
        self.blue_mask = final_blue_mask_pil

        grid_rep = get_grid_rep(image=image,
                                mask=mask,
                                final_blue_mask=final_blue_mask,
                                overlayed_image=overlayed_image)
        
        # make sure grid_rep is converted to PIL image
        grid_rep_pil = Image.fromarray(cv2.cvtColor(grid_rep, cv2.COLOR_BGR2RGB))

        self.grid_rep = grid_rep_pil

    def is_peripheral_blood(self):
        """Return True iff the top view is a peripheral blood top view."""
        return True

    def filter_coordinates_with_mask(self, coordinates):
        """Filters out coordinates not in the binary mask area.

        Args:
            coordinates (list of tuples): List of (TL_x, TL_y, BR_x, BR_y) boxes.

        Returns:
            list of tuples: Filtered list of coordinates.
        """

        # make sure to get a cv2 format of the mask as a binary numpy array
        mask_np = cv2.cvtColor(np.array(self.mask), cv2.COLOR_RGB2GRAY)

        # make sure to convert mask_np to a binary mask
        _, mask_np = cv2.threshold(mask_np, 127, 255, cv2.THRESH_BINARY)

        filtered_coordinates = []

        for box in coordinates:
            # Adjust coordinates by downsampling factor
            TL_x_adj, TL_y_adj, BR_x_adj, BR_y_adj = [int(coord / (topview_downsampling_factor//search_view_downsample_rate)) for coord in box]

            # Check if the box is within the mask area
            # Ensuring the coordinates are within the mask dimensions
            TL_x_adj, TL_y_adj = max(0, TL_x_adj), max(0, TL_y_adj)
            BR_x_adj, BR_y_adj = min(mask_np.shape[1], BR_x_adj), min(mask_np.shape[0], BR_y_adj)

            if np.any(mask_np[TL_y_adj:BR_y_adj, TL_x_adj:BR_x_adj]):
                # If any part of the box is within the mask, keep it
                filtered_coordinates.append(box)

        assert len(filtered_coordinates) > 0, "No coordinates are within the mask area."

        return coordinates # TO CHANGE BACK TODO

    def save_images(self, save_dir):
        """ Save the image, mask, overlayed image, blue_mask and grid representation of the top view in save_dir."""

        self.image.save(os.path.join(save_dir, "top_view_image.png"))
        self.mask.save(os.path.join(save_dir, "top_view_mask.png"))
        self.overlayed_image.save(os.path.join(save_dir, "top_view_overlayed_image.png"))
        self.blue_mask.save(os.path.join(save_dir, "top_view_blue_mask.png"))
        self.grid_rep.save(os.path.join(save_dir, "top_view_grid_rep.png"))
    

    


class SpecimenError(ValueError):
    """Exception raised when the specimen is not the correct type for the operation."""

    pass


class RelativeBlueSignalTooWeakError(ValueError):
    """Exception raised when the blue signal is too weak."""

    def __init__(self, message):
        """Initialize a BlueSignalTooWeakError object."""

        super().__init__(message)

    def __str__(self):
        """Return the error message."""

        return self.args[0]
