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
from PIL import Image
from tqdm import tqdm
from ray.exceptions import RayTaskError
from pathlib import Path

# Within package imports ###########################################################################
from LL.resources.assumptions import *
from LL.FileNameManager import FileNameManager
from LL.TopView import TopView, SpecimenError, RelativeBlueSignalTooWeakError
from LL.SearchView import SearchView
from LL.FocusRegion import FocusRegion, FocusRegionsTracker
from LL.brain.HemeLabelManager import HemeLabelManager
from LL.brain.YOLOManager import YOLOManager
from LL.Differential import Differential, to_count_dict
from LL.vision.processing import SlideError, read_with_timeout
from LL.vision.WSICropManager import WSICropManager
from LL.communication.write_config import *
from LL.communication.visualization import *


class PBCounter:

    """A Class representing a Counter of WBCs inside a peripheral blood (PB) whole slide image.

    === Class Attributes ===
    - file_name_manager : the FileNameManager class object of the WSI
    - top_view : the TopView class object of the WSI
    - search_view : the SearchView class object of the WSI
    - wbc_candidates : a list of WBCCandidate class objects that represent candidates for being WBCs
    - focus_regions : a list of FocusRegion class objects representing the focus regions of the search view
    - differential : a Differential class object representing the differential of the WSI
    - save_dir : the directory to save the diagnostic logs, dataframes (and images if hoarding is True
    - profiling_data : a dictionary containing the profiling data of the PBCounter object

    - verbose : whether to print out the progress of the PBCounter object
    - hoarding : whether to hoard regions and cell images processed into permanent storage
    - continue_on_error : whether to continue processing the WSI if an error occurs
    """

    def __init__(
        self,
        wsi_path: str,
        verbose: bool = False,
        hoarding: bool = False,
        continue_on_error: bool = False,
    ):
        """Initialize a PBCounter object."""

        self.profiling_data = {}

        start_time = time.time()

        self.verbose = verbose
        self.hoarding = hoarding
        self.continue_on_error = continue_on_error

        if self.verbose:
            print(f"Initializing FileNameManager object for {wsi_path}")
        # Initialize the manager
        self.file_name_manager = FileNameManager(wsi_path)

        self.save_dir = os.path.join(dump_dir, self.file_name_manager.stem)

        # if the save_dir does not exist, create it
        os.makedirs(self.save_dir, exist_ok=True)

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
        top_level = len(wsi.level_dimensions) - 2

        if self.verbose:
            print(f"Obtaining top view image")

        # if the read_region takes longer than 10 seconds, then raise a SlideError

        top_view = read_with_timeout(
            wsi, (0, 0), top_level, wsi.level_dimensions[top_level]
        )

        # top_view = wsi.read_region(
        #     (0, 0), top_level, wsi.level_dimensions[top_level])

        top_view = top_view.convert("RGB")
        top_view_downsampling_rate = wsi.level_downsamples[top_level]
        self.top_view = TopView(
            top_view, top_view_downsampling_rate, top_level, verbose=self.verbose
        )

        self.top_view.save_images(self.save_dir)

        if self.verbose:
            print(f"Checking if the specimen is peripheral blood")
        if not self.top_view.is_peripheral_blood():
            raise SpecimenError("The specimen is not peripheral blood.")

        if self.verbose:
            print(f"Processing WSI search view as SearchView object")
        # Processing the search level image

        search_view = read_with_timeout(
            wsi, (0, 0), search_view_level, wsi.level_dimensions[search_view_level]
        )

        # search_view = wsi.read_region(
        #     (0, 0), search_view_level, wsi.level_dimensions[search_view_level])
        search_view_downsampling_rate = wsi.level_downsamples[search_view_level]
        self.search_view = SearchView(
            search_view, search_view_downsampling_rate, verbose=self.verbose
        )

        if self.verbose:
            print(f"Closing WSI")
        wsi.close()

        # The focus regions and WBC candidates are None until they are processed
        self.focus_regions = None
        self.wbc_candidates = None
        self.differential = None

        self.profiling_data["init_time"] = time.time() - start_time

    def find_focus_regions(self):
        """Find the focus regions of the WSI."""

        start_time = time.time()

        os.makedirs(os.path.join(self.save_dir, "focus_regions"), exist_ok=True)

        focus_regions_coords = []
        locations = self.search_view.get_locations()

        num_sds = foci_sds

        for location in tqdm(
            locations, desc=f"Finding focus regions at num_sds={num_sds}"
        ):
            crop = self.search_view[location]

            more_focus_regions_coords = list(
                self.top_view.find_focus_regions(
                    crop,
                    location,
                    focus_regions_size,
                    self.search_view.padding_x,
                    self.search_view.padding_y,
                    num_sds=num_sds,
                    top_to_search_zoom_ratio=int(
                        self.top_view.downsampling_rate
                        / self.search_view.downsampling_rate
                    ),
                    search_to_0_zoom_ratio=int(self.search_view.downsampling_rate),
                )
            )

            focus_regions_coords.extend(more_focus_regions_coords)

        print(f"{len(focus_regions_coords)} regions found at num_sds={num_sds}")

        while (
            len(focus_regions_coords) < min_num_regions_within_foci_sd and num_sds > 0
        ):
            num_sds -= foci_sd_inc
            if num_sds == 0:
                raise RelativeBlueSignalTooWeakError(
                    f"Relative blue signal is too weak. min_num_regions_within_foci_sd {min_num_regions_within_foci_sd} is not reached. Only {len(focus_regions_coords)} regions found at num_sds=1. Check slide for potential poor staining/imaging.)"
                )

            focus_regions_coords = []

            for location in tqdm(
                locations, desc=f"Finding focus regions at num_sds={num_sds}"
            ):
                crop = self.search_view[location]

                more_focus_regions_coords = list(
                    self.top_view.find_focus_regions(
                        crop,
                        location,
                        focus_regions_size,
                        self.search_view.padding_x,
                        self.search_view.padding_y,
                        num_sds=num_sds,
                        top_to_search_zoom_ratio=int(
                            self.top_view.downsampling_rate
                            / self.search_view.downsampling_rate
                        ),
                        search_to_0_zoom_ratio=int(self.search_view.downsampling_rate),
                    )
                )

                focus_regions_coords.extend(more_focus_regions_coords)

            print(f"{len(focus_regions_coords)} regions found at num_sds={num_sds}")

        fr_tracker = FocusRegionsTracker(
            search_view=self.search_view, focus_regions_coords=focus_regions_coords
        )

        self.profiling_data["find_focus_regions_time"] = time.time() - start_time

        start_time = time.time()

        _, hoarding_time = fr_tracker.filter(
            save_dir=self.save_dir, hoarding=self.hoarding
        )

        self.profiling_data["low_mag_focus_regions_hoarding_time"] = hoarding_time

        # add num_sds to the save_dir/focus_regions/focus_regions_filtering.csv file as a column
        # first read the csv file as a dataframe
        focus_regions_filtering_csv_path = os.path.join(
            self.save_dir, "focus_regions", "focus_regions_filtering.csv"
        )
        focus_regions_filtering_df = pd.read_csv(focus_regions_filtering_csv_path)

        # add the num_sds column
        focus_regions_filtering_df["num_sds"] = num_sds

        # save the dataframe
        focus_regions_filtering_df.to_csv(focus_regions_filtering_csv_path, index=False)

        self.focus_regions = fr_tracker.get_filtered_focus_regions()

        self.profiling_data["filter_focus_regions_time"] = (
            time.time() - start_time - hoarding_time
        )

        if self.verbose:
            print(f"Initializing {num_croppers} Ray workers")

        ray.shutdown()
        # ray.init(num_cpus=num_cpus)
        ray.init()

        start_time = time.time()

        if self.verbose:
            print("Initializing WSICropManager")
        crop_managers = [
            WSICropManager.remote(self.file_name_manager.wsi_path)
            for _ in range(num_croppers)
        ]

        tasks = {}
        all_results = []

        for i, focus_region in enumerate(self.focus_regions):
            manager = crop_managers[i % num_croppers]
            task = manager.async_get_focus_region_image.remote(focus_region)
            tasks[task] = focus_region

        with tqdm(
            total=len(self.focus_regions), desc="Getting focus region images"
        ) as pbar:
            while tasks:
                done_ids, _ = ray.wait(list(tasks.keys()))

                for done_id in done_ids:
                    try:
                        result = ray.get(done_id)
                        if result is not None:
                            all_results.append(result)

                    except RayTaskError as e:
                        print(
                            f"Task for focus region {tasks[done_id]} failed with error: {e}"
                        )

                    pbar.update()
                    del tasks[done_id]

        if self.verbose:
            print(f"Shutting down Ray")
        ray.shutdown()

        print(f"{len(all_results)} focus regions successfully processed.")
        self.focus_regions = all_results

        self.profiling_data["get_focus_region_full_images_time"] = (
            time.time() - start_time
        )

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

        tasks = {}
        all_results = []
        new_focus_regions = []

        for i, focus_region in enumerate(self.focus_regions):
            manager = task_managers[i % num_YOLOManagers]
            task = manager.async_find_wbc_candidates.remote(focus_region)
            tasks[task] = focus_region

        with tqdm(
            total=len(self.focus_regions), desc="Detecting WBC candidates"
        ) as pbar:
            while tasks:
                done_ids, _ = ray.wait(list(tasks.keys()))

                for done_id in done_ids:
                    try:
                        new_focus_region = ray.get(done_id)
                        for wbc_candidate in new_focus_region.wbc_candidates:
                            all_results.append(wbc_candidate)
                        if len(all_results) > max_num_candidates:
                            raise TooManyCandidatesError(
                                f"Too many candidates found. max_num_candidates {max_num_candidates} is exceeded. Increase max_num_candidates or check code and slide for error."
                            )
                        new_focus_regions.append(new_focus_region)

                    except RayTaskError as e:
                        print(f"Task for focus {tasks[done_id]} failed with error: {e}")

                    pbar.update()
                    del tasks[done_id]

        self.wbc_candidates = all_results  # the candidates here should be aliased with the candidates saved in focus_regions
        self.focus_regions = new_focus_regions

        if self.verbose:
            print(f"Shutting down Ray")

        ray.shutdown()

        # Regardless of hoarding, save a plot of the distribution of confidence score for all the detected cells, the distribution of number of cells detected per region, and the mean and sd thereof.
        # Plots should be saved at save_dir/focus_regions/YOLO_confidence.jpg and save_dir/focus_regions/num_cells_per_region.jpg
        # Save a dataframe which trackers the number of cells detected for each region in save_dir/focus_regions/num_cells_per_region.csv
        # Save a big cell dataframe which have the cell id, region_id, confidence, VoL, and coordinates in save_dir/cells/cells_info.csv
        # The mean and sd should be saved as a part of the save_dir/cells/cell_detection.yaml file using yaml

        # first compile the big cell dataframe
        # traverse through the wbc_candidates and add their info
        # create a list of dictionaries
        big_cell_df_list = []

        for i in range(len(self.wbc_candidates)):
            # get the ith wbc_candidate
            wbc_candidate = self.wbc_candidates[i]

            # get the cell_info of the wbc_candidate as a dictionary
            cell_info = {
                "local_idx": wbc_candidate.local_idx,
                "region_idx": wbc_candidate.focus_region_idx,
                "confidence": wbc_candidate.confidence,
                "VoL": wbc_candidate.VoL,
                "TL_x": wbc_candidate.YOLO_bbox[0],
                "TL_y": wbc_candidate.YOLO_bbox[1],
                "BR_x": wbc_candidate.YOLO_bbox[2],
                "BR_y": wbc_candidate.YOLO_bbox[3],
            }

            # add the cell_info to the list
            big_cell_df_list.append(cell_info)

        # create the big cell dataframe
        big_cell_df = pd.DataFrame(big_cell_df_list)

        # save the big cell dataframe
        big_cell_df.to_csv(
            os.path.join(self.save_dir, "cells", "cells_info.csv"), index=False
        )

        # second compile the num_cells_per_region dataframe which can be found from len(focus_region.wbc_candidate_bboxes) for each focus_region in self.focus_regions

        # create a list of dictionaries
        num_cells_per_region_df_list = []

        for i in range(len(self.focus_regions)):
            # get the ith focus_region
            focus_region = self.focus_regions[i]

            # get the number of cells detected in the focus_region
            num_cells = len(focus_region.wbc_candidate_bboxes)

            # add the num_cells to the list
            num_cells_per_region_df_list.append(
                {"focus_region_idx": focus_region.idx, "num_cells": num_cells}
            )

        # create the num_cells_per_region dataframe
        num_cells_per_region_df = pd.DataFrame(num_cells_per_region_df_list)

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

        if self.verbose:
            print("Initializing HemeLabelManager")
        task_managers = [
            HemeLabelManager.remote(HemeLabel_ckpt_path) for _ in range(num_labellers)
        ]

        tasks = {}
        all_results = []

        for i, wbc_candidate in enumerate(self.wbc_candidates):
            manager = task_managers[i % num_labellers]
            task = manager.async_label_wbc_candidate.remote(wbc_candidate)
            tasks[task] = wbc_candidate

        with tqdm(
            total=len(self.wbc_candidates), desc="Classifying WBC candidates"
        ) as pbar:
            while tasks:
                done_ids, _ = ray.wait(list(tasks.keys()))

                for done_id in done_ids:
                    try:
                        wbc_candidate = ray.get(done_id)
                        if wbc_candidate is not None:
                            all_results.append(wbc_candidate)

                    except RayTaskError as e:
                        print(
                            f"Task for WBC candidate {tasks[done_id]} failed with error: {e}"
                        )

                    pbar.update()
                    del tasks[done_id]
        if self.verbose:
            print(f"Shutting down Ray")
        ray.shutdown()

        self.wbc_candidates = all_results
        self.differential = Differential(self.wbc_candidates)

        self.profiling_data["label_wbc_candidates_time"] = time.time() - start_time

    def _save_results(self):
        """Save the results of the PBCounter object."""

        start_time = time.time()

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

        else:
            self.profiling_data["cells_hoarding_time"] = 0

    def tally_differential(self):
        """Run all steps with time profiling and save the profiling data to YAML."""
        try:
            save_selected_variables_to_yaml(
                selected_variable_names,
                os.path.join(self.save_dir, "global_config.yaml"),
            )

            if self.focus_regions is None:
                self.find_focus_regions()

            if self.wbc_candidates is None:
                self.find_wbc_candidates()

            if self.differential is None:
                self.label_wbc_candidates()

            self._save_results()

            # Save profiling data as a csv file
            self.profiling_data["total_time"] = sum(self.profiling_data.values())
            self.profiling_data["hoarding_time"] = (
                self.profiling_data["high_mag_focus_regions_hoarding_time"]
                + self.profiling_data["low_mag_focus_regions_hoarding_time"]
                + self.profiling_data["cells_hoarding_time"]
            )

            self.profiling_data["total_non_hoarding_time"] = (
                self.profiling_data["total_time"] - self.profiling_data["hoarding_time"]
            )

            # save runtime_dct as a csv file, first row is the keys and second row is the values
            runtime_df = pd.DataFrame.from_dict(self.profiling_data, orient="index")
            runtime_df.to_csv(
                os.path.join(self.save_dir, "runtime_data.csv"), header=False
            )

        except Exception as e:
            if self.continue_on_error:
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


class TooManyCandidatesError(ValueError):
    """An exception raised when too many candidates are found."""

    def __init__(self, message):
        """Initialize a TooManyCandidatesError object."""

        super().__init__(message)
