####################################################################################################
# Imports ##########################################################################################
####################################################################################################

# Outside imports ##################################################################################
import os
import numpy as np
import pandas as pd
import torch
from tqdm import tqdm

# Within package imports ###########################################################################
from LL.resources.PBassumptions import *


def save_wbc_candidates(
    pbc,
    save_dir=os.path.join(dump_dir, "wbc_candidates"),
    image_type="padded_YOLO_bbox_image",
):
    """Save the wbc_candidates of the PBCounter object to the save_path.
    image_type must be either 'snap_shot' or 'YOLO_bbox_image' or 'padded_YOLO_bbox_image'.
    """

    # if the save_dir does not exist, create it
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    for wbc_candidate in tqdm(pbc.wbc_candidates, desc="Saving wbc_candidates"):
        if image_type == "snap_shot":
            image = wbc_candidate.snap_shot
        elif image_type == "YOLO_bbox_image":
            image = wbc_candidate.YOLO_bbox_image
        elif image_type == "padded_YOLO_bbox_image":
            image = wbc_candidate.padded_YOLO_bbox_image
        else:
            raise ValueError(
                "image_type must be either 'snap_shot' or 'YOLO_bbox_image' or 'padded_YOLO_bbox_image'."
            )

        # save the image as a jpg file
        image.save(os.path.join(save_dir, str(wbc_candidate.snap_shot_bbox) + ".jpg"))


def save_focus_regions(pbc, save_dir=os.path.join(dump_dir, "focus_regions")):
    """Save the focus region images of the PBCounter object to the save_path."""

    # if the save_dir does not exist, create it
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    for focus_region in tqdm(pbc.focus_regions, desc="Saving focus regions"):
        # save the image as a jpg file
        focus_region.image.save(
            os.path.join(save_dir, str(focus_region.coordinate) + ".jpg")
        )


def save_focus_regions_annotated(pbc, save_dir=dump_dir):
    """Create three subdirectories in save_dir: 'focus_regions', 'focus_regions_annotated', 'annotations'.
    Save the focus region images in the 'focus_regions' subdirectory.
    Save the focus region images annotated with the wbc_candidate_bboxes in the 'focus_regions_annotated' subdirectory.
    Save the focus region wbc_candidate_bboxes in the 'annotations' subdirectory."""

    # create the subdirectories if they do not exist
    images_save_dir = os.path.join(save_dir, "focus_regions")
    annotated_images_save_dir = os.path.join(save_dir, "focus_regions_annotated")
    annotations_save_dir = os.path.join(save_dir, "annotations")

    if not os.path.exists(images_save_dir):
        os.makedirs(images_save_dir)
    if not os.path.exists(annotated_images_save_dir):
        os.makedirs(annotated_images_save_dir)
    if not os.path.exists(annotations_save_dir):
        os.makedirs(annotations_save_dir)

    for focus_region in tqdm(
        pbc.focus_regions, desc="Saving focus regions annotations"
    ):
        # save the image as a jpg file
        focus_region.image.save(
            os.path.join(images_save_dir, str(focus_region.coordinate) + ".jpg")
        )

        # save the annotated image as a jpg file
        focus_region.get_annotated_image().save(
            os.path.join(
                annotated_images_save_dir, str(focus_region.coordinate) + ".jpg"
            )
        )

        # get the df of the annotations
        df = focus_region.get_annotation_df()

        # save the df as a csv file
        df.to_csv(
            os.path.join(annotations_save_dir, str(focus_region.coordinate) + ".csv"),
            index=False,
        )


def save_wbc_candidates_sorted(
    pbc,
    save_dir=os.path.join(dump_dir, "wbc_candidates_sorted"),
    image_type="padded_YOLO_bbox_image",
):
    """Save the wbc_candidates of the PBCounter object to the save_path. As well as a csv file containing the differential file."""

    # if the save_dir does not exist, create it
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # for each cellname in the cellnames, create a folder
    for cellname in cellnames:
        cellname_dir = os.path.join(save_dir, cellname)
        if not os.path.exists(cellname_dir):
            os.makedirs(cellname_dir)

    # save the differential file which is a pandas dataframe : pbc.differential.wbc_candidate_df
    pbc.differential.wbc_candidate_df.to_csv(os.path.join(save_dir, "cell_data.csv"))

    # for each wbc_candidate, save the image to the corresponding folder
    for wbc_candidate in tqdm(pbc.wbc_candidates, desc="Saving wbc_candidates"):

        # the class of the wbc_candidate is the argmax of the softmax_vector (which is a tuple so watch out)
        cellname = cellnames[np.argmax(np.array(wbc_candidate.softmax_vector))]

        if image_type == "snap_shot":
            image = wbc_candidate.snap_shot
        elif image_type == "YOLO_bbox_image":
            image = wbc_candidate.YOLO_bbox_image
        elif image_type == "padded_YOLO_bbox_image":
            image = wbc_candidate.padded_YOLO_bbox_image
        else:
            raise ValueError(
                "image_type must be either 'snap_shot' or 'YOLO_bbox_image' or 'padded_YOLO_bbox_image'."
            )

        # save the image as a jpg file
        image.save(os.path.join(save_dir, cellname, wbc_candidate.name))


def save_augmented_cell_features(wbc_candidates, arch, save_dir):

    # start building a dictionary for eventual convertion to a dataframe
    # it should have the following columns: focus_regions_idx, local_idx, augmentation_idx, cell_class
    tracking_dict = {
        "focus_regions_idx": [],
        "local_idx": [],
        "augmentation_idx": [],
        "cell_class": [],
    }

    for wbc_candidate in wbc_candidates:

        augmented_feat_lst = wbc_candidate.augmented_features[
            arch
        ]  # this is a list of triples (augmentation_pipeline, augmented_image, feature)

        # create the function which saves the augmented image and the feature vector in the save_dir if it does not exist
        os.makedirs(os.path.join(save_dir, arch + "_augmented"), exist_ok=True)

        os.makedirs(
            os.path.join(
                save_dir,
                os.path.join(save_dir, arch + "_augmented"),
                cellnames[np.argmax(wbc_candidate.softmax_vector)],
            ),
            exist_ok=True,
        )

        cell_class = cellnames[np.argmax(wbc_candidate.softmax_vector)]

        focus_region_idx, local_idx = (
            wbc_candidate.focus_region_idx,
            wbc_candidate.local_idx,
        )

        # save the augmented feature tensor using the filename focus_region_idx-local_idx-augmentation_idx
        for i, (augmentation_pipeline, augmented_image, feature) in tqdm(
            enumerate(augmented_feat_lst),
            desc=f"Saving augmented features for {cell_class}",
        ):
            # save the feature tensor which is currently as torch tensor you want to save as a .pt file
            torch.save(
                feature,
                os.path.join(
                    save_dir,
                    os.path.join(
                        save_dir,
                        arch + "_augmented",
                        cell_class,
                    ),
                    str(focus_region_idx) + "-" + str(local_idx) + "-" + str(i) + ".pt",
                ),
            )

            # add the tracking info to the tracking_dict
            tracking_dict["focus_regions_idx"].append(focus_region_idx)
            tracking_dict["local_idx"].append(local_idx)
            tracking_dict["augmentation_idx"].append(i)
            tracking_dict["cell_class"].append(cell_class)

    # convert the tracking_dict to a dataframe
    tracking_df = pd.DataFrame(tracking_dict)

    # save the dataframe as a csv file named metadata.csv in the save_dir/arch_augmented
    tracking_df.to_csv(os.path.join(save_dir, arch + "_augmented", "metadata.csv"))
