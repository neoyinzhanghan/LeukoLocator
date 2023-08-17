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
            raise ValueError(
                "image_type must be either 'snap_shot' or 'YOLO_bbox_image' or 'padded_YOLO_bbox_image'.")

        # save the image as a jpg file
        image.save(os.path.join(save_dir, str(
            wbc_candidate.snap_shot_bbox) + '.jpg'))


def save_focus_regions(pbc, save_dir=os.path.join(dump_dir, 'focus_regions')):
    """ Save the focus region images of the PBCounter object to the save_path. """

    # if the save_dir does not exist, create it
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    for focus_region in tqdm(pbc.focus_regions, desc='Saving focus regions'):
        # save the image as a jpg file
        focus_region.image.save(os.path.join(
            save_dir, str(focus_region.coordinate) + '.jpg'))


def save_focus_regions_annotated(pbc, save_dir=dump_dir):
    """ Create three subdirectories in save_dir: 'focus_regions', 'focus_regions_annotated', 'annotations'. 
    Save the focus region images in the 'focus_regions' subdirectory.
    Save the focus region images annotated with the wbc_candidate_bboxes in the 'focus_regions_annotated' subdirectory.
    Save the focus region wbc_candidate_bboxes in the 'annotations' subdirectory. """

    # create the subdirectories if they do not exist
    images_save_dir = os.path.join(save_dir, 'focus_regions')
    annotated_images_save_dir = os.path.join(
        save_dir, 'focus_regions_annotated')
    annotations_save_dir = os.path.join(save_dir, 'annotations')

    if not os.path.exists(images_save_dir):
        os.makedirs(images_save_dir)
    if not os.path.exists(annotated_images_save_dir):
        os.makedirs(annotated_images_save_dir)
    if not os.path.exists(annotations_save_dir):
        os.makedirs(annotations_save_dir)

    for focus_region in tqdm(pbc.focus_regions, desc='Saving focus regions annotations'):
        # save the image as a jpg file
        focus_region.image.save(os.path.join(
            images_save_dir, str(focus_region.coordinate) + '.jpg'))

        # save the annotated image as a jpg file
        focus_region.annotated_image.save(os.path.join(
            annotated_images_save_dir, str(focus_region.coordinate) + '.jpg'))

        # get the df of the annotations
        df = focus_region.get_annotation_df()

        # save the df as a csv file
        df.to_csv(os.path.join(
            annotations_save_dir, str(focus_region.coordinate) + '.csv'))


def save_wbc_candidates_sorted(pbc, save_dir=os.path.join(dump_dir, 'wbc_candidates_sorted'), image_type='padded_YOLO_bbox_image'):
    """ Save the wbc_candidates of the PBCounter object to the save_path. As well as a csv file containing the differential file. """

    # if the save_dir does not exist, create it
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # for each cellname in the cellnames, create a folder
    for cellname in cellnames:
        cellname_dir = os.path.join(save_dir, cellnames_dict[cellname])
        if not os.path.exists(cellname_dir):
            os.makedirs(cellname_dir)

    # save the differential file which is a pandas dataframe : pbc.differential.wbc_candidate_df
    pbc.differential.wbc_candidate_df.to_csv(
        os.path.join(save_dir, 'cell_data.csv'))

    # for each wbc_candidate, save the image to the corresponding folder
    for wbc_candidate in tqdm(pbc.wbc_candidates, desc='Saving wbc_candidates'):

        # the class of the wbc_candidate is the argmax of the softmax_vector (which is a tuple so watch out)
        cellname = cellnames[np.argmax(np.array(wbc_candidate.softmax_vector))]

        if image_type == 'snap_shot':
            image = wbc_candidate.snap_shot
        elif image_type == 'YOLO_bbox_image':
            image = wbc_candidate.YOLO_bbox_image
        elif image_type == 'padded_YOLO_bbox_image':
            image = wbc_candidate.padded_YOLO_bbox_image
        else:
            raise ValueError(
                "image_type must be either 'snap_shot' or 'YOLO_bbox_image' or 'padded_YOLO_bbox_image'.")

        # save the image as a jpg file
        image.save(os.path.join(save_dir, cellname, wbc_candidate.name))
