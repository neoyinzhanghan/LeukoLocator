####################################################################################################
# Imports ##########################################################################################
####################################################################################################

# Outside imports ##################################################################################
import os
import ray
import openslide
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yaml
import time
import sys
import shutil
from PIL import Image
from tqdm import tqdm
from ray.exceptions import RayTaskError
from pathlib import Path

# Within package imports ###########################################################################
from LL.PBDifferential import Differential, to_count_dict
from LL.FileNameManager import FileNameManager
from LL.BMATopView import TopView, SpecimenError, TopViewError
from LL.brain.HemeLabelManager import HemeLabelManager
from LL.brain.YOLOManager import YOLOManager
from LL.brain.FeatureEngineer import CellFeatureEngineer
from LL.vision.processing import SlideError, read_with_timeout
from LL.vision.BMAWSICropManager import WSICropManager
from LL.communication.write_config import *
from LL.communication.visualization import *
from LL.brain.utils import *
from LL.communication.saving import *
from LL.brain.SpecimenClf import get_specimen_type
from LL.SearchView import SearchView
from LL.BMAFocusRegion import *
from LL.BMAFocusRegionTracker import FocusRegionsTracker, NotEnoughFocusRegionsError
from LL.brain.BMAHighMagRegionCheckTracker import BMAHighMagRegionCheckTracker
from LL.resources.BMAassumptions import *


class BMACounter:
    """A Class representing a Counter of WBCs inside a bone marrow aspirate (BMA)) whole slide image.

    === Class Attributes ===
    - file_name_manager : the FileNameManager class object of the WSI
    - top_view : the TopView class object of the WSI
    - wbc_candidates : a list of WBCCandidate class objects that represent candidates for being WBCs
    - focus_regions : a list of FocusRegion class objects representing the focus regions of the search view
    - differential : a Differential class object representing the differential of the WSI
    - save_dir : the directory to save the diagnostic logs, dataframes (and images if hoarding is True
    - profiling_data : a dictionary containing the profiling data of the PBCounter object

    - verbose : whether to print out the progress of the PBCounter object
    - hoarding : whether to hoard regions and cell images processed into permanent storage
    - continue_on_error : whether to continue processing the WSI if an error occurs
    - ignore_specimen_type : whether to ignore the specimen type of the WSI
    - do_extract_features : whether to extract features from the WBC candidates
    - fr_tracker : a FocusRegionsTracker object that tracks the focus regions

    - predicted_specimen_type: the predicted specimen type of the WSI
    - wsi_path : the path to the WSI
    """

    def __init__(
        self,
        wsi_path: str,
        verbose: bool = False,
        hoarding: bool = False,
        continue_on_error: bool = False,
        ignore_specimen_type: bool = False,
        do_extract_features: bool = False,
        overwrite: bool = True,
        error: bool = False,
    ):
        """Initialize a PBCounter object."""

        self.profiling_data = {}

        start_time = time.time()

        self.verbose = verbose
        self.hoarding = hoarding
        self.continue_on_error = continue_on_error
        self.ignore_specimen_type = ignore_specimen_type
        self.wsi_path = wsi_path
        self.do_extract_features = do_extract_features
        self.overwrite = overwrite
        self.error = error

        if self.verbose:
            print(f"Initializing FileNameManager object for {wsi_path}")
        # Initialize the manager
        self.file_name_manager = FileNameManager(wsi_path)

        self.save_dir = os.path.join(dump_dir, self.file_name_manager.stem)

        # if the save_dir already exists, then delete it and make a new one
        if os.path.exists(self.save_dir):
            if self.overwrite:
                os.system(f"rm -r {self.save_dir}")

        else:
            # if the save_dir does not exist, create it
            os.makedirs(self.save_dir, exist_ok=True)

        try:

            # Processing the WSI
            try:
                if self.verbose:
                    print(f"Opening WSI as {wsi_path}")

                wsi = openslide.OpenSlide(wsi_path)
            except Exception as e:
                raise SlideError(e)

            if self.verbose:
                print(f"Processing WSI top view as TopView object")
            # Processing the top level image
            top_level = topview_level

            if self.verbose:
                print(f"Obtaining top view image")

            # if the read_region takes longer than 10 seconds, then raise a SlideError

            top_view = read_with_timeout(
                wsi, (0, 0), top_level, wsi.level_dimensions[top_level]
            )

            print("Checking Specimen Type")
            specimen_type = get_specimen_type(top_view)

            self.predicted_specimen_type = specimen_type

            if specimen_type != "Bone Marrow Aspirate":
                if not self.ignore_specimen_type:
                    if self.continue_on_error:

                        e = SpecimenError(
                            "The specimen is not Bone Marrow Aspirate. Instead, it is "
                            + specimen_type
                            + "."
                        )

                        print(
                            "ERROR: The specimen is not Bone Marrow Aspirate. Instead, it is "
                            + specimen_type
                            + "."
                        )

                        # if the save_dir does not exist, create it
                        os.makedirs(self.save_dir, exist_ok=True)

                        # save the exception and profiling data
                        with open(os.path.join(self.save_dir, "error.txt"), "w") as f:
                            f.write(str(e))

                        # Save profiling data even in case of error
                        with open(
                            os.path.join(self.save_dir, "runtime_data.yaml"), "w"
                        ) as file:
                            yaml.dump(
                                self.profiling_data,
                                file,
                                default_flow_style=False,
                                sort_keys=False,
                            )

                        # rename the save_dir name to "ERROR_" + save_dir
                        os.rename(
                            self.save_dir,
                            os.path.join(
                                dump_dir,
                                "ERROR_" + Path(self.file_name_manager.wsi_path).stem,
                            ),
                        )

                        print(f"Error occurred and logged. Continuing to next WSI.")

                        # update the save_dir
                        self.save_dir = os.path.join(
                            dump_dir,
                            "ERROR_" + Path(self.file_name_manager.wsi_path).stem,
                        )

                    else:
                        raise SpecimenError(
                            "The specimen is not Bone Marrow Aspirate. Instead, it is "
                            + specimen_type
                            + "."
                        )

                else:
                    print(
                        "USERWarning: The specimen is not Bone Marrow Aspirate. Instead, it is "
                        + specimen_type
                        + "."
                    )

            # top_view = wsi.read_region(
            #     (0, 0), top_level, wsi.level_dimensions[top_level])

            top_view = top_view.convert("RGB")
            top_view_downsampling_rate = wsi.level_downsamples[top_level]

            try:
                self.top_view = TopView(
                    top_view,
                    top_view_downsampling_rate,
                    top_level,
                    verbose=self.verbose,
                )
            except Exception as e:
                raise TopViewError(e)

            self.top_view.save_images(self.save_dir)

            if self.verbose:
                print(f"Processing WSI search view as SearchView object")
            # Processing the search level image

            if self.verbose:
                print(f"Closing WSI")
            wsi.close()

            # The focus regions and WBC candidates are None until they are processed
            self.focus_regions = None
            self.wbc_candidates = None
            self.fr_tracker = None
            self.differential = None

            self.profiling_data["init_time"] = time.time() - start_time

        except Exception as e:
            if self.continue_on_error:
                print(f"Error occurred: {e}")
                print(f"Continuing to next WSI.")

                # remame the save_dir to "ERROR_" + save_dir
                error_path = os.path.join(
                    dump_dir, "ERROR_" + self.file_name_manager.stem
                )

                # if the error_path already exists, then delete it and make a new one
                if os.path.exists(error_path) and os.listdir(error_path):
                    os.system(f"rm -r {error_path}")

                os.rename(
                    self.save_dir,
                    os.path.join(
                        dump_dir, "ERROR_" + Path(self.file_name_manager.wsi_path).stem
                    ),
                )

                self.error = True
            else:
                self.error = True
                raise e

    def find_focus_regions(self):
        """Return the focus regions of the highest magnification view."""

        start_time = time.time()

        os.makedirs(os.path.join(self.save_dir, "focus_regions"), exist_ok=True)

        # First get a list of the focus regions coordinates based on focus_regions_size at highest level of magnification
        # if the dimension is not divisible by the focus_regions_size, then we simply omit the last focus region

        # get the dimension of the highest mag, which is the level 0
        # get the level 0 dimension using
        wsi = openslide.OpenSlide(self.wsi_path)
        search_view_dimension = wsi.level_dimensions[search_view_level]
        wsi.close()

        dimx, dimy = search_view_dimension

        # get the number of focus regions in the x and y direction
        num_focus_regions_x = dimx // search_view_focus_regions_size
        num_focus_regions_y = dimy // search_view_focus_regions_size

        # get the list of focus regions coordinates
        focus_regions_coordinates = []

        for i in range(num_focus_regions_x):
            for j in range(num_focus_regions_y):
                focus_regions_coordinates.append(
                    (
                        i * search_view_focus_regions_size,
                        j * search_view_focus_regions_size,
                        (i + 1) * search_view_focus_regions_size,
                        (j + 1) * search_view_focus_regions_size,
                    )
                )

        focus_regions_coordinates = self.top_view.filter_coordinates_with_mask(
            focus_regions_coordinates
        )

        # # take the 300 focus regions from the middle of the list which is len(focus_regions_coordinates) // 2 - 150 to len(focus_regions_coordinates) // 2 + 150
        # half = 300 // 2
        # focus_regions_coordinates = focus_regions_coordinates[
        #     len(focus_regions_coordinates) // 2
        #     - half : len(focus_regions_coordinates) // 2
        #     + half
        # ]

        ray.shutdown()
        # ray.init(num_cpus=num_cpus, num_gpus=num_gpus)
        ray.init()

        list_of_batches = create_list_of_batches_from_list(
            focus_regions_coordinates, region_cropping_batch_size
        )

        if self.verbose:
            print("Initializing WSICropManager")
        task_managers = [
            WSICropManager.remote(self.wsi_path) for _ in range(num_croppers)
        ]

        tasks = {}
        all_results = []

        for i, batch in enumerate(list_of_batches):
            manager = task_managers[i % num_labellers]
            task = manager.async_get_bma_focus_region_batch.remote(batch)
            tasks[task] = batch

        with tqdm(
            total=len(focus_regions_coordinates), desc="Cropping focus regions"
        ) as pbar:
            while tasks:
                done_ids, _ = ray.wait(list(tasks.keys()))

                for done_id in done_ids:
                    try:
                        batch = ray.get(done_id)
                        for focus_region in batch:
                            all_results.append(focus_region)

                            pbar.update()

                    except RayTaskError as e:
                        print(
                            f"Task for focus region {tasks[done_id]} failed with error: {e}"
                        )

                    del tasks[done_id]

        if self.verbose:
            print(f"Shutting down Ray")
        ray.shutdown()

        self.focus_regions = all_results

        self.profiling_data["cropping_focus_regions_time"] = time.time() - start_time

    def filter_focus_regions(self):
        start_time = time.time()

        fr_tracker = FocusRegionsTracker(self.focus_regions)

        self.fr_tracker = fr_tracker

        self.fr_tracker.compute_resnet_confidence()
        selected_focus_regions = self.fr_tracker.get_top_n_focus_regions()
        self.fr_tracker.save_results(self.save_dir)

        self.focus_regions = selected_focus_regions

        self.profiling_data["filtering_focus_regions_time"] = time.time() - start_time

        if self.hoarding:
            start_time = time.time()
            self.fr_tracker.save_all_focus_regions(self.save_dir)
            self.profiling_data["hoarding_focus_regions_time"] = (
                time.time() - start_time
            )
        else:
            self.profiling_data["hoarding_focus_regions_time"] = 0

        # now for each focus region, we will find get the image

        start_time = time.time()

        for focus_region in tqdm(
            self.focus_regions, desc="Getting high magnification focus region images"
        ):
            wsi = openslide.OpenSlide(self.wsi_path)

            pad_size = snap_shot_size // 2

            padded_coordinate = (
                focus_region.coordinate[0] - pad_size,
                focus_region.coordinate[1] - pad_size,
                focus_region.coordinate[2] + pad_size,
                focus_region.coordinate[3] + pad_size,
            )
            padded_image = wsi.read_region(
                padded_coordinate,
                0,
                (
                    focus_region.coordinate[2]
                    - focus_region.coordinate[0]
                    + pad_size * 2,
                    focus_region.coordinate[3]
                    - focus_region.coordinate[1]
                    + pad_size * 2,
                ),
            )

            original_width = focus_region.coordinate[2] - focus_region.coordinate[0]
            original_height = focus_region.coordinate[3] - focus_region.coordinate[1]

            unpadded_image = padded_image.crop(
                (
                    pad_size,
                    pad_size,
                    pad_size + original_width,
                    pad_size + original_height,
                )
            )

            focus_region.get_image(unpadded_image, padded_image)

        self.profiling_data["getting_high_mag_images_time"] = time.time() - start_time

        start_time = time.time()

        high_mag_check_tracker = BMAHighMagRegionCheckTracker(
            focus_regions=self.focus_regions
        )

        good_focus_regions = high_mag_check_tracker.get_good_focus_regions()

        self.focus_regions = good_focus_regions

        high_mag_check_tracker.save_results(self.save_dir)

        self.profiling_data["high_mag_check_time"] = time.time() - start_time

        if self.hoarding:
            start_time = time.time()
            high_mag_check_tracker.hoard_results(self.save_dir)
            self.profiling_data["hoarding_high_mag_check_time"] = (
                time.time() - start_time
            )
        else:
            self.profiling_data["hoarding_high_mag_check_time"] = 0

    def find_wbc_candidates(self):
        """Update the wbc_candidates of the PBCounter object."""

        start_time = time.time()

        # make the directory save_dir/focus_regions/YOLO_df
        os.makedirs(
            os.path.join(self.save_dir, "focus_regions", "YOLO_df"), exist_ok=True
        )

        # make the directory save_dir/cells
        os.makedirs(os.path.join(self.save_dir, "cells"), exist_ok=True)

        ray.shutdown()
        # ray.init(num_cpus=num_cpus, num_gpus=num_gpus)
        ray.init()

        if self.verbose:
            print("Initializing YOLOManager")
        task_managers = [
            YOLOManager.remote(
                YOLO_ckpt_path,
                YOLO_conf_thres,
                save_dir=self.save_dir,
                hoarding=self.hoarding,
            )
            for _ in range(num_YOLOManagers)
        ]

        list_of_batches = create_list_of_batches_from_list(
            self.focus_regions, YOLO_batch_size
        )

        tasks = {}
        all_results = []
        new_focus_regions = []

        for i, batch in enumerate(list_of_batches):
            manager = task_managers[i % num_YOLOManagers]
            task = manager.async_find_wbc_candidates_batch.remote(batch)
            tasks[task] = batch

        with tqdm(
            total=len(self.focus_regions), desc="Detecting WBC candidates"
        ) as pbar:
            while tasks:
                done_ids, _ = ray.wait(list(tasks.keys()))

                for done_id in done_ids:
                    try:
                        batch_focus_regions = ray.get(done_id)
                        for focus_region in batch_focus_regions:
                            if focus_region is not None:
                                new_focus_regions.append(focus_region)
                                for wbc_candidate in focus_region.wbc_candidates:
                                    all_results.append(wbc_candidate)

                            pbar.update()

                    except RayTaskError as e:
                        print(f"Task for focus {tasks[done_id]} failed with error: {e}")

                    del tasks[done_id]

        if self.verbose:
            print(f"Shutting down Ray")

        self.wbc_candidates = all_results  # the candidates here should be aliased with the candidates saved in focus_regions
        self.focus_regions = new_focus_regions  # these do not include all the focus regions, only the ones that have wbc_candidates before the max_num_candidates is reached

        # for i, focus_region in enumerate(self.focus_regions):
        #     manager = task_managers[i % num_YOLOManagers]
        #     task = manager.async_find_wbc_candidates.remote(focus_region)
        #     tasks[task] = focus_region

        # with tqdm(
        #     total=len(self.focus_regions), desc="Detecting WBC candidates"
        # ) as pbar:
        #     while tasks:
        #         done_ids, _ = ray.wait(list(tasks.keys()))

        #         for done_id in done_ids:
        #             try:
        #                 new_focus_region = ray.get(done_id)
        #                 for wbc_candidate in new_focus_region.wbc_candidates:
        #                     all_results.append(wbc_candidate)
        #                 if len(all_results) > max_num_candidates:
        #                     raise TooManyCandidatesError(
        #                         f"Too many candidates found. max_num_candidates {max_num_candidates} is exceeded. Increase max_num_candidates or check code and slide for error."
        #                     )
        #                 new_focus_regions.append(new_focus_region)

        #             except RayTaskError as e:
        #                 print(f"Task for focus {tasks[done_id]} failed with error: {e}")

        #             pbar.update()
        #             del tasks[done_id]

        # Regardless of hoarding, save a plot of the distribution of confidence score for all the detected cells, the distribution of number of cells detected per region, and the mean and sd thereof.
        # Plots should be saved at save_dir/focus_regions/YOLO_confidence.jpg and save_dir/focus_regions/num_cells_per_region.jpg
        # Save a dataframe which trackers the number of cells detected for each region in save_dir/focus_regions/num_cells_per_region.csv
        # Save a big cell dataframe which have the cell id, region_id, confidence, VoL, and coordinates in save_dir/cells/cells_info.csv
        # The mean and sd should be saved as a part of the save_dir/cells/cell_detection.yaml file using yaml

        # first compile the big cell dataframe
        # traverse through the wbc_candidates and add their info
        # create a list of dictionaries

        # Initiate remote calls and get futures
        futures = [manager.get_num_detected.remote() for manager in task_managers]

        # Wait for all futures to complete and retrieve the results
        num_detected_values = ray.get(futures)

        # Sum the results
        total_detected = sum(num_detected_values)

        ray.shutdown()

        big_cell_df_dct = {
            "local_idx": [],
            "region_idx": [],
            "confidence": [],
            "VoL": [],
            "TL_x": [],
            "TL_y": [],
            "BR_x": [],
            "BR_y": [],
        }

        big_cell_df_list = []

        for i in range(len(self.wbc_candidates)):
            # get the ith wbc_candidate
            wbc_candidate = self.wbc_candidates[i]

            big_cell_df_dct["local_idx"].append(wbc_candidate.local_idx)
            big_cell_df_dct["region_idx"].append(wbc_candidate.focus_region_idx)
            big_cell_df_dct["confidence"].append(wbc_candidate.confidence)
            big_cell_df_dct["VoL"].append(wbc_candidate.VoL)
            big_cell_df_dct["TL_x"].append(wbc_candidate.YOLO_bbox[0])
            big_cell_df_dct["TL_y"].append(wbc_candidate.YOLO_bbox[1])
            big_cell_df_dct["BR_x"].append(wbc_candidate.YOLO_bbox[2])
            big_cell_df_dct["BR_y"].append(wbc_candidate.YOLO_bbox[3])

            # # get the cell_info of the wbc_candidate as a dictionary
            # cell_info = {
            #     "local_idx": wbc_candidate.local_idx,
            #     "region_idx": wbc_candidate.focus_region_idx,
            #     "confidence": wbc_candidate.confidence,
            #     "VoL": wbc_candidate.VoL,
            #     "TL_x": wbc_candidate.YOLO_bbox[0],
            #     "TL_y": wbc_candidate.YOLO_bbox[1],
            #     "BR_x": wbc_candidate.YOLO_bbox[2],
            #     "BR_y": wbc_candidate.YOLO_bbox[3],
            # }

            # # add the cell_info to the list
            # big_cell_df_list.append(cell_info)

        # create the big cell dataframe
        big_cell_df = pd.DataFrame(big_cell_df_dct)

        # save the big cell dataframe
        big_cell_df.to_csv(
            os.path.join(self.save_dir, "cells", "cells_info.csv"), index=False
        )

        # second compile the num_cells_per_region dataframe which can be found from len(focus_region.wbc_candidate_bboxes) for each focus_region in self.focus_regions

        # create a list of dictionaries

        num_cells_per_region_df_dct = {
            "focus_region_idx": [],
            "num_cells": [],
        }
        # num_cells_per_region_df_list = []

        for i in range(len(self.focus_regions)):
            # get the ith focus_region
            focus_region = self.focus_regions[i]

            # get the number of cells detected in the focus_region
            num_cells = len(focus_region.wbc_candidate_bboxes)

            num_cells_per_region_df_dct["focus_region_idx"].append(focus_region.idx)
            num_cells_per_region_df_dct["num_cells"].append(num_cells)
            # # add the num_cells to the list
            # num_cells_per_region_df_list.append(
            #     {"focus_region_idx": focus_region.idx, "num_cells": num_cells}
            # )

        # create the num_cells_per_region dataframe
        num_cells_per_region_df = pd.DataFrame(num_cells_per_region_df_dct)

        # save the num_cells_per_region dataframe
        num_cells_per_region_df.to_csv(
            os.path.join(self.save_dir, "focus_regions", "num_cells_per_region.csv"),
            index=False,
        )

        save_hist_KDE_rug_plot(
            df=big_cell_df,
            column_name="confidence",
            save_path=os.path.join(self.save_dir, "cells", "YOLO_confidence.jpg"),
            title="YOLO Confidence Distribution of Selected Cells",
        )

        save_hist_KDE_rug_plot(
            df=num_cells_per_region_df,
            column_name="num_cells",
            save_path=os.path.join(
                self.save_dir, "focus_regions", "num_cells_per_region.jpg"
            ),
            title="Number of Cells Detected in Selected Focus Regions",
        )

        # grab the info for the csv file as a dictionary
        num_cells_per_region_mean = num_cells_per_region_df["num_cells"].mean()
        num_cells_per_region_sd = num_cells_per_region_df["num_cells"].std()

        YOLO_confidence_mean = big_cell_df["confidence"].mean()
        YOLO_confidence_sd = big_cell_df["confidence"].std()

        # total number of cells detected
        num_cells_detected = len(big_cell_df)
        # total number of focus regions scanned
        num_focus_regions_scanned = len(self.focus_regions)

        VoL_passed = []
        VoL_rejected = []
        for candidate in tqdm(self.wbc_candidates, desc="Cell VoL Filtering"):
            if candidate.VoL >= min_cell_VoL:
                VoL_passed.append(candidate)
            else:
                VoL_rejected.append(candidate)

        self.wbc_candidates = VoL_passed

        # number of VoL passed cells
        num_VoL_passed = len(VoL_passed)

        # number of VoL rejected cells
        num_VoL_rejected = len(VoL_rejected)

        # add the mean and sd to the save_dir/cells/cell_detection.yaml file using yaml
        cell_detection_csv_path = os.path.join(
            self.save_dir, "cells", "cell_detection.csv"
        )

        # first create the dictionary
        cell_detection_dict = {
            "num_cells_detected": numpy_to_python(num_cells_detected),
            "num_VoL_passed": numpy_to_python(num_VoL_passed),
            "num_VoL_rejected": numpy_to_python(num_VoL_rejected),
            "num_focus_regions_scanned": numpy_to_python(num_focus_regions_scanned),
            "num_cells_per_region_mean": numpy_to_python(num_cells_per_region_mean),
            "num_cells_per_region_sd": numpy_to_python(num_cells_per_region_sd),
            "YOLO_confidence_mean": numpy_to_python(YOLO_confidence_mean),
            "YOLO_confidence_sd": numpy_to_python(YOLO_confidence_sd),
        }

        # then write the dictionary to the csv file with keys as the first row and values as the second row use panda
        cell_detection_df = pd.DataFrame.from_dict(cell_detection_dict, orient="index")
        cell_detection_df.to_csv(cell_detection_csv_path, header=False)

        self.profiling_data["find_wbc_candidates_time"] = time.time() - start_time

        if self.hoarding:
            start_time = time.time()
            os.makedirs(
                os.path.join(self.save_dir, "focus_regions", "high_mag_annotated"),
                exist_ok=True,
            )
            os.makedirs(
                os.path.join(self.save_dir, "focus_regions", "high_mag_unannotated"),
                exist_ok=True,
            )
            os.makedirs(
                os.path.join(self.save_dir, "focus_regions", "low_mag_selected"),
                exist_ok=True,
            )
            for focus_region in tqdm(
                self.focus_regions, desc="Saving focus regions high mag images"
            ):
                focus_region.save_high_mag_image(self.save_dir)

            os.makedirs(os.path.join(self.save_dir, "cells", "blurry"), exist_ok=True)
            for candidate in tqdm(VoL_rejected, desc="Saving VoL rejected cell images"):
                candidate._save_YOLO_bbox_image(self.save_dir)

            self.profiling_data["high_mag_focus_regions_hoarding_time"] = (
                time.time() - start_time
            )

        else:
            self.profiling_data["high_mag_focus_regions_hoarding_time"] = 0

        if len(self.focus_regions) < min_num_focus_regions:
            raise NotEnoughFocusRegionsError(
                f"Too few focus regions found. min_num_focus_regions {min_num_focus_regions} is not reached by {len(self.focus_regions)} focus regions. Decrease min_num_focus_regions or check code and slide for error."
            )

        # Check if the sum is below the minimum required number
        if total_detected < min_num_cells:
            raise TooFewCandidatesError(
                f"Too few candidates found. min_num_cells {min_num_cells} is not reached by {total_detected} candidates. Decrease min_num_cells or check code and slide for error."
                "Decrease min_num_cells or check code and slide for error."
            )

    def label_wbc_candidates(self):
        """Update the labels of the wbc_candidates of the PBCounter object."""

        start_time = time.time()

        if self.wbc_candidates == [] or self.wbc_candidates is None:
            raise NoCellFoundError(
                "No WBC candidates found. Please run find_wbc_candidates() first. If problem persists, the slide may be problematic."
            )
        ray.shutdown()
        # ray.init(num_cpus=num_cpus, num_gpus=num_gpus)
        ray.init()

        list_of_batches = create_list_of_batches_from_list(
            self.wbc_candidates, cell_clf_batch_size
        )

        if self.verbose:
            print("Initializing HemeLabelManager")
        task_managers = [
            HemeLabelManager.remote(HemeLabel_ckpt_path) for _ in range(num_labellers)
        ]

        tasks = {}
        all_results = []

        for i, batch in enumerate(list_of_batches):
            manager = task_managers[i % num_labellers]
            task = manager.async_label_wbc_candidate_batch.remote(batch)
            tasks[task] = batch

        with tqdm(
            total=len(self.wbc_candidates), desc="Classifying WBC candidates"
        ) as pbar:
            while tasks:
                done_ids, _ = ray.wait(list(tasks.keys()))

                for done_id in done_ids:
                    try:
                        batch = ray.get(done_id)
                        for wbc_candidate in batch:
                            all_results.append(wbc_candidate)

                            pbar.update()

                    except RayTaskError as e:
                        print(
                            f"Task for WBC candidate {tasks[done_id]} failed with error: {e}"
                        )

                    del tasks[done_id]

        if self.verbose:
            print(f"Shutting down Ray")
        ray.shutdown()

        self.wbc_candidates = all_results
        self.differential = Differential(self.wbc_candidates)

        self.profiling_data["label_wbc_candidates_time"] = time.time() - start_time

    def extract_features(self):
        """Extract features"""
        if not self.do_extract_features:
            for arch in supported_feature_extraction_archs:
                self.profiling_data[f"cell_feature_extraction_time_{arch}"] = 0

            return None

        for arch in supported_feature_extraction_archs:
            ckpt_path = feature_extractor_ckpt_dict[arch]
            start_time = time.time()

            if self.wbc_candidates == [] or self.wbc_candidates is None:
                raise NoCellFoundError(
                    "No WBC candidates found. Please run find_wbc_candidates() first. If problem persists, the slide may be problematic."
                )
            ray.shutdown()
            # ray.init(num_cpus=num_cpus, num_gpus=num_gpus)
            ray.init()

            list_of_batches = create_list_of_batches_from_list(
                self.wbc_candidates, cell_clf_batch_size
            )

            if self.verbose:
                print(f"Initializing CellFeatureEngineer for architecture {arch}")
            task_managers = [
                CellFeatureEngineer.remote(arch=arch, ckpt_path=ckpt_path)
                for _ in range(num_labellers)
            ]

            tasks = {}
            all_results = []

            for i, batch in enumerate(list_of_batches):
                manager = task_managers[i % num_labellers]
                task = manager.async_extract_batch.remote(batch)
                tasks[task] = batch

            with tqdm(
                total=len(self.wbc_candidates),
                desc=f"Extract WBC candidates features for architecture {arch}",
            ) as pbar:
                while tasks:
                    done_ids, _ = ray.wait(list(tasks.keys()))

                    for done_id in done_ids:
                        try:
                            batch = ray.get(done_id)
                            for wbc_candidate in batch:
                                all_results.append(wbc_candidate)

                                pbar.update()

                        except RayTaskError as e:
                            print(
                                f"Task for WBC candidate {tasks[done_id]} failed with error: {e}"
                            )

                        del tasks[done_id]

            if self.verbose:
                print(f"Shutting down Ray")
            ray.shutdown()

            self.wbc_candidates = all_results
            self.differential = Differential(self.wbc_candidates)

            self.profiling_data[f"cell_feature_extraction_time_{arch}"] = (
                time.time() - start_time
            )

    def extract_features_with_augmentation(self):
        """Extract features with augmentation."""

        if not self.do_extract_features:
            for arch in supported_feature_extraction_archs:
                self.profiling_data[
                    f"cell_augmented_feature_extraction_time_{arch}"
                ] = 0

            return None

        for arch in supported_feature_extraction_archs:
            ckpt_path = feature_extractor_ckpt_dict[arch]
            start_time = time.time()

            if self.wbc_candidates == [] or self.wbc_candidates is None:
                raise NoCellFoundError(
                    "No WBC candidates found. Please run find_wbc_candidates() first. If problem persists, the slide may be problematic."
                )
            ray.shutdown()
            # ray.init(num_cpus=num_cpus, num_gpus=num_gpus)
            ray.init()

            list_of_batches = create_list_of_batches_from_list(
                self.wbc_candidates, cell_clf_batch_size
            )

            if self.verbose:
                print(f"Initializing CellFeatureEngineer for architecture {arch}")
            task_managers = [
                CellFeatureEngineer.remote(arch=arch, ckpt_path=ckpt_path)
                for _ in range(num_labellers)
            ]

            tasks = {}
            all_results = []

            for i, batch in enumerate(list_of_batches):
                manager = task_managers[i % num_labellers]
                task = manager.async_extract_batch_with_augmentation.remote(batch)
                tasks[task] = batch

            with tqdm(
                total=len(self.wbc_candidates),
                desc=f"Extract Augmented WBC candidates features for architecture {arch}",
            ) as pbar:
                while tasks:
                    done_ids, _ = ray.wait(list(tasks.keys()))

                    for done_id in done_ids:
                        try:
                            batch = ray.get(done_id)
                            for wbc_candidate in batch:
                                all_results.append(wbc_candidate)

                                pbar.update()

                        except RayTaskError as e:
                            print(
                                f"Task for WBC candidate {tasks[done_id]} failed with error: {e}"
                            )

                        del tasks[done_id]

            if self.verbose:
                print(f"Shutting down Ray")
            ray.shutdown()

            self.wbc_candidates = all_results
            self.differential = Differential(self.wbc_candidates)

            self.profiling_data[f"cell_augmented_feature_extraction_time_{arch}"] = (
                time.time() - start_time
            )

    def _save_results(self):
        """Save the results of the PBCounter object."""

        start_time = time.time()

        self.fr_tracker.save_confidence_heatmap(self.top_view.image, self.save_dir)

        diff_full_class_dict = self.differential.tally_diff_full_class_dict()
        diff_class_dict = self.differential.tally_dict()
        diff_dict = self.differential.compute_PB_differential()

        # save the diff_full_class_dict as a csv file called save_dir/differential_full.csv, where the first row is the class and the second row is the value
        diff_full_csv_path = os.path.join(self.save_dir, "differential_full_class.csv")
        diff_full_df = pd.DataFrame.from_dict(diff_full_class_dict, orient="index")
        diff_full_df.to_csv(diff_full_csv_path, header=False)

        # save the diff_class_dict as a csv file called save_dir/differential_class.csv, where the first row is the class and the second row is the value
        diff_class_csv_path = os.path.join(self.save_dir, "differential_class.csv")
        diff_class_df = pd.DataFrame.from_dict(diff_class_dict, orient="index")
        diff_class_df.to_csv(diff_class_csv_path, header=False)

        # save the diff_dict as a csv file called save_dir/differential.csv, where the first row is the class and the second row is the value
        diff_csv_path = os.path.join(self.save_dir, "differential.csv")
        diff_df = pd.DataFrame.from_dict(diff_dict, orient="index")
        diff_df.to_csv(diff_csv_path, header=False)

        # total number of cells detected
        num_cells_detected = len(self.wbc_candidates)

        diff_full_class_count_dict = to_count_dict(
            diff_full_class_dict, num_cells_detected
        )
        diff_class_count_dict = to_count_dict(
            dct=diff_class_dict, num_cells=num_cells_detected
        )
        diff_count_dict = to_count_dict(dct=diff_dict, num_cells=num_cells_detected)

        # save the diff_full_class_count_dict as a csv file called save_dir/differential_full_class_count.csv, where the first row is the class and the second row is the value
        diff_full_count_csv_path = os.path.join(
            self.save_dir, "differential_full_class_count.csv"
        )
        diff_full_count_df = pd.DataFrame.from_dict(
            diff_full_class_count_dict, orient="index"
        )
        diff_full_count_df.to_csv(diff_full_count_csv_path, header=False)

        # save the diff_class_count_dict as a csv file called save_dir/differential_class_count.csv, where the first row is the class and the second row is the value
        diff_class_count_csv_path = os.path.join(
            self.save_dir, "differential_class_count.csv"
        )
        diff_class_count_df = pd.DataFrame.from_dict(
            diff_class_count_dict, orient="index"
        )
        diff_class_count_df.to_csv(diff_class_count_csv_path, header=False)

        # save the diff_count_dict as a csv file called save_dir/differential_count.csv, where the first row is the class and the second row is the value
        diff_count_csv_path = os.path.join(self.save_dir, "differential_count.csv")
        diff_count_df = pd.DataFrame.from_dict(diff_count_dict, orient="index")
        diff_count_df.to_csv(diff_count_csv_path, header=False)

        # save a bar chart of the differential_full_class_count_dict as save_dir/differential_full_class_count.jpg
        save_bar_chart(
            data_dict=diff_full_class_count_dict,
            save_path=os.path.join(self.save_dir, "differential_full_class_count.jpg"),
            title="Differential Count of Full Classes",
            xaxis_name="Class",
            yaxis_name="Count",
        )

        # save a bar chart of the diff_class_count_dict as save_dir/differential_class_count.jpg
        save_bar_chart(
            data_dict=diff_class_count_dict,
            save_path=os.path.join(self.save_dir, "differential_class_count.jpg"),
            title="Differential Count of Selected Classes",
            xaxis_name="Class",
            yaxis_name="Count",
        )

        # save a bar chart of the diff_count_dict as save_dir/differential_count.jpg
        save_bar_chart(
            data_dict=diff_count_dict,
            save_path=os.path.join(self.save_dir, "differential_count.jpg"),
            title="Differential Count",
            xaxis_name="Class",
            yaxis_name="Count",
        )

        # save a bar chart of the diff_full_class_dict as save_dir/differential_full_class.jpg
        save_bar_chart(
            data_dict=diff_full_class_dict,
            save_path=os.path.join(self.save_dir, "differential_full_class.jpg"),
            title="Differential of Full Classes",
            xaxis_name="Class",
            yaxis_name="Differential",
        )

        # save a bar chart of the diff_class_dict as save_dir/differential_class.jpg
        save_bar_chart(
            data_dict=diff_class_dict,
            save_path=os.path.join(self.save_dir, "differential_class.jpg"),
            title="Differential of Selected Classes",
            xaxis_name="Class",
            yaxis_name="Differential",
        )

        # save a bar chart of the diff_dict as save_dir/differential.jpg
        save_bar_chart(
            data_dict=diff_dict,
            save_path=os.path.join(self.save_dir, "differential.jpg"),
            title="Differential",
            xaxis_name="Class",
            yaxis_name="Differential",
        )

        # save a big dataframe of the cell info in save_dir/cells/cells_info.csv
        self.differential.save_cells_info(self.save_dir)

        self.profiling_data["save_results_time"] = time.time() - start_time

        # if hoarding, the save all cells images in save_dir/cells/class for each of the classes under the file name of the cell
        if self.hoarding:
            start_time = time.time()
            for wbc_candidate in tqdm(self.wbc_candidates, desc="Saving cell images"):
                wbc_candidate._save_cell_image(self.save_dir)

            self.profiling_data["cells_hoarding_time"] = time.time() - start_time

            if self.do_extract_features:
                for arch in supported_feature_extraction_archs:
                    start_time = time.time()
                    for wbc_candidate in tqdm(
                        self.wbc_candidates, desc=f"Saving {arch} features"
                    ):
                        wbc_candidate._save_cell_feature(self.save_dir, arch)

                    save_augmented_cell_features(
                        self.wbc_candidates, arch, self.save_dir
                    )

                    self.profiling_data[
                        f"cell_extracted_features_hoarding_time_{arch}"
                    ] = (time.time() - start_time)

            else:
                for arch in supported_feature_extraction_archs:
                    self.profiling_data[
                        f"cell_extracted_features_hoarding_time_{arch}"
                    ] = 0

        else:
            self.profiling_data["cells_hoarding_time"] = 0

    def tally_differential(self):
        """Run all steps with time profiling and save the profiling data to YAML."""

        if self.error == True:
            print("Error occurred in previous run. Skipping this run.")
            pass
        try:
            save_selected_variables_to_yaml(
                selected_variable_names,
                os.path.join(self.save_dir, "global_config.yaml"),
            )

            if self.focus_regions is None:
                self.find_focus_regions()
                self.filter_focus_regions()

            if self.wbc_candidates is None:
                self.find_wbc_candidates()

            if self.differential is None:
                self.label_wbc_candidates()
                self.extract_features()
                self.extract_features_with_augmentation()
            self._save_results()

            # Save profiling data as a csv file
            self.profiling_data["total_time"] = sum(self.profiling_data.values())

            self.profiling_data["total_feature_extraction_time"] = sum(
                [
                    self.profiling_data[f"cell_feature_extraction_time_{arch}"]
                    for arch in supported_feature_extraction_archs
                ]
            ) + sum(
                [
                    self.profiling_data[
                        f"cell_augmented_feature_extraction_time_{arch}"
                    ]
                    for arch in supported_feature_extraction_archs
                ]
            )

            self.profiling_data["total_features_hoarding_time"] = sum(
                [
                    self.profiling_data[f"cell_extracted_features_hoarding_time_{arch}"]
                    for arch in supported_feature_extraction_archs
                ]
            )

            self.profiling_data["hoarding_time"] = (
                self.profiling_data["high_mag_focus_regions_hoarding_time"]
                + self.profiling_data["hoarding_focus_regions_time"]
                + self.profiling_data["cells_hoarding_time"]
                + self.profiling_data["total_features_hoarding_time"]
                + self.profiling_data["hoarding_high_mag_check_time"]
            )

            self.profiling_data["total_non_hoarding_time"] = (
                self.profiling_data["total_time"] - self.profiling_data["hoarding_time"]
            )

            # save runtime_dct as a csv file, first row is the keys and second row is the values
            runtime_df = pd.DataFrame.from_dict(self.profiling_data, orient="index")
            runtime_df.to_csv(
                os.path.join(self.save_dir, "runtime_data.csv"), header=False
            )

        # except SpecimenError as e:
        #     raise e

        except Exception as e:
            if self.continue_on_error:
                print(
                    f"An error has occured, and continue on error status is : {self.continue_on_error}"
                )

                # if the save_dir does not exist, create it
                os.makedirs(self.save_dir, exist_ok=True)

                if isinstance(e, NotEnoughFocusRegionsError) or isinstance(
                    e, TooFewCandidatesError
                ):
                    self.fr_tracker.save_confidence_heatmap(
                        self.top_view.image, self.save_dir
                    )

                # save the exception and profiling data
                with open(os.path.join(self.save_dir, "error.txt"), "w") as f:
                    f.write(str(e))

                # Save profiling data even in case of error
                with open(
                    os.path.join(self.save_dir, "runtime_data.yaml"), "w"
                ) as file:
                    yaml.dump(
                        self.profiling_data,
                        file,
                        default_flow_style=False,
                        sort_keys=False,
                    )

                # rename the save_dir name to "ERROR_" + save_dir
                # if the ERROR folder already exists, delete it
                error_path = os.path.join(
                    dump_dir, "ERROR_" + Path(self.file_name_manager.wsi_path).stem
                )
                if os.path.exists(error_path) and os.listdir(error_path):
                    os.system(f"rm -r {error_path}")
                os.rename(
                    self.save_dir,
                    os.path.join(
                        dump_dir, "ERROR_" + Path(self.file_name_manager.wsi_path).stem
                    ),
                )

                print(f"Error occurred and logged. Continuing to next WSI.")

            else:
                raise e


class NoCellFoundError(ValueError):
    """An exception raised when no cell is found."""

    def __init__(self, message):
        """Initialize a NoCellFoundError object."""

        super().__init__(message)


class TooFewCandidatesError(ValueError):
    """An exception raised when too few candidates are found."""

    def __init__(self, message):
        """Initialize a TooFewCandidatesError object."""

        super().__init__(message)


class TooManyCandidatesError(ValueError):
    """An exception raised when too many candidates are found."""

    def __init__(self, message):
        """Initialize a TooManyCandidatesError object."""

        super().__init__(message)
