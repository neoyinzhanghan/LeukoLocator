####################################################################################################
# Imports ##########################################################################################
####################################################################################################

# Outside imports ##################################################################################
from PIL import Image, ImageOps
import threading

# Within package imports ###########################################################################
from WCW.resources.assumptions import *


def crop_region_view(region_view, crop_width=search_view_crop_size[0], crop_height=search_view_crop_size[1], verbose=False):
    """ Crop the region_view image into crops of size crop_size, if the division is not exact, then start from half of the remainder at the beginning, and ignore the remainder at the end.
    Return a dictionary of crops, where the key is a tuple tracking (TL_x, TL_y, BR_x, BR_y) of the crop. """

    crops = {}
    width, height = region_view.size

    remainder_width = width % crop_width
    remainder_height = height % crop_height

    search_view_padding_x = int(remainder_width / 2)
    search_view_padding_y = int(remainder_height / 2)

    for i in range(search_view_padding_x, width, crop_width):
        for j in range(search_view_padding_y, height, crop_height):
            if i + crop_width <= width and j + crop_height <= height:
                crops[(i, j, i + crop_width, j + crop_height)
                      ] = region_view.crop((i, j, i + crop_width, j + crop_height))

    if verbose:
        print("Total number of crops created: ", len(crops))

    return crops, search_view_padding_x, search_view_padding_y


def zero_pad(image, snap_shot_size):
    """ The input is a PIL RGB image and the output should also be a PIL RGB image.
    Based on the centroid of the image, crop and apply zero padding to the image to make it a square of size snap_shot_size. 
    snap_shot_size must be even."""

    # make sure snap_shot_size is even
    if snap_shot_size % 2 != 0:
        raise ValueError("snap_shot_size must be even")

    width, height = image.size
    centroid = (int(width // 2), int(height // 2))

    # Crop the image such that its width and height do not exceed snap_shot_size.
    left_crop = max(0, centroid[0] - snap_shot_size // 2)
    right_crop = min(width, centroid[0] + snap_shot_size // 2)
    top_crop = max(0, centroid[1] - snap_shot_size // 2)
    bottom_crop = min(height, centroid[1] + snap_shot_size // 2)

    image = image.crop((left_crop, top_crop, right_crop, bottom_crop))

    # Update width and height after cropping
    width, height = image.size

    # Now apply zero padding to achieve snap_shot_size x snap_shot_size
    left_right_padding = (snap_shot_size - width) // 2
    top_bottom_padding = (snap_shot_size - height) // 2

    # Padding is given as (left, top, right, bottom)
    padding = (left_right_padding, top_bottom_padding,
               left_right_padding, top_bottom_padding)
    image = ImageOps.expand(image, padding)

    return image


def read_with_timeout(wsi, location, level, dimensions):
    result = {'top_view': None, 'error': None}

    def target():
        try:
            result['top_view'] = wsi.read_region(location, level, dimensions)
        except Exception as e:
            result['error'] = e

    thread = threading.Thread(target=target)
    thread.start()
    thread.join(timeout=allowed_time)  # 10 seconds timeout

    if thread.is_alive():
        # The method hasn't finished in 10 seconds
        thread.join()  # Wait for it to finish or terminate, up to you.
        raise SlideError(f"read_region took longer than {allowed_time} seconds")

    if result['error']:
        raise result['error']  # Rethrow the error from the thread

    return result['top_view']


class SlideError(ValueError):
    """ The slide file has some issues that has nothing to do with the code. """

    def __init__(self, e):
        self.e = e

    def __str__(self):
        return f"SlideError: {self.e}"
