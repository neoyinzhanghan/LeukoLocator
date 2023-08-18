####################################################################################################
# Imports ##########################################################################################
####################################################################################################

# Outside imports ##################################################################################
from PIL import Image, ImageOps
import cv2
import numpy as np


def annotate_focus_region(image, bboxes):
    """ Return the image of the focus region annotated with the WBC candidates. 
    bboxes is a list of tuples of the form (TL_x, TL_y, BR_x, BR_y).
    The input image is a PIL image.
    """

    # convert the image to numpy array
    image = np.array(image)

    # draw the bounding boxes in color red
    for bbox in bboxes:
        image = cv2.rectangle(image, (bbox[0], bbox[1]),
                              (bbox[2], bbox[3]), (255, 0, 0), 3)

    # convert the image back to PIL image
    image = Image.fromarray(image)

    return image
