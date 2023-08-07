####################################################################################################
# Imports ##########################################################################################
####################################################################################################

# Outside imports ##################################################################################
import os
from tqdm import tqdm
import numpy as np

# Within package imports ###########################################################################
from WCW.resources.assumptions import *

def save_wbc_candidates(pbc, save_dir=os.path.join(dump_dir, 'wbc_candidates'), image_type='padded_YOLO_bbox_image'):
    """ Save the wbc_candidates of the PBCounter object to the save_path. 
    image_type must be either 'snap_shot' or 'YOLO_bbox_image' or 'padded_YOLO_bbox_image'. """

    # if the save_dir does not exist, create it
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    for wbc_candidate in tqdm(pbc.wbc_candidates, desc='Saving wbc_candidates'):
        if image_type == 'snap_shot':
            image = wbc_candidate.snap_shot
        elif image_type == 'YOLO_bbox_image':
            image = wbc_candidate.YOLO_bbox_image
        elif image_type == 'padded_YOLO_bbox_image':
            image = wbc_candidate.padded_YOLO_bbox_image
        else:
            raise ValueError("image_type must be either 'snap_shot' or 'YOLO_bbox_image' or 'padded_YOLO_bbox_image'.")

        # save the image as a jpg file
        image.save(os.path.join(save_dir, str(wbc_candidate.snap_shot_bbox) + '.jpg'))

def save_focus_regions(pbc, save_dir=os.path.join(dump_dir, 'focus_regions')):
    """ Save the focus region images of the PBCounter object to the save_path. """

    # if the save_dir does not exist, create it
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    for focus_region in tqdm(pbc.focus_regions, desc='Saving focus regions'):
        # save the image as a jpg file
        focus_region.image.save(os.path.join(save_dir, str(focus_region.coordinate) + '.jpg'))

def save_wbc_candidates_sorted(pbc, save_dir=os.path.join(dump_dir, 'wbc_candidates_sorted'), image_type='padded_YOLO_bbox_image'):
    """ Save the wbc_candidates of the PBCounter object to the save_path. """
    
    # if the save_dir does not exist, create it
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # for each cellname in the cellnames, create a folder
    for cellname in cellnames:
        cellname_dir = os.path.join(save_dir, cellnames_dict[cellname])
        if not os.path.exists(cellname_dir):
            os.makedirs(cellname_dir)

    # for each wbc_candidate, save the image to the corresponding folder
    for wbc_candidate in tqdm(pbc.wbc_candidates, desc='Saving wbc_candidates'):

        # the class of the wbc_candidate is the argmax of the softmax_vector (which is a tuple so watch out)
        cellname = cellnames_dict[cellnames[np.argmax(np.array(wbc_candidate.softmax_vector))]]

        if image_type == 'snap_shot':
            image = wbc_candidate.snap_shot
        elif image_type == 'YOLO_bbox_image':
            image = wbc_candidate.YOLO_bbox_image
        elif image_type == 'padded_YOLO_bbox_image':
            image = wbc_candidate.padded_YOLO_bbox_image
        else:
            raise ValueError("image_type must be either 'snap_shot' or 'YOLO_bbox_image' or 'padded_YOLO_bbox_image'.")

        # save the image as a jpg file
        image.save(os.path.join(save_dir, cellname, str(wbc_candidate.snap_shot_bbox) + '.jpg'))
    
