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
from PIL import Image
from tqdm import tqdm
from ray.exceptions import RayTaskError

# Within package imports ###########################################################################
from LL.resources.assumptions import *
from LL.FileNameManager import FileNameManager
from LL.TopView import TopView, SpecimenError, RelativeBlueSignalTooWeakError
from LL.SearchView import SearchView
from LL.FocusRegion import FocusRegion, FocusRegionsTracker
from LL.brain.HemeLabelManager import HemeLabelManager
from LL.brain.YOLOManager import YOLOManager
from LL.Differential import Differential
from LL.vision.processing import SlideError, read_with_timeout
from LL.vision.WSICropManager import WSICropManager
from LL.communication.write_config import numpy_to_python


class PBCounter:

    """A Class representing a Counter of WBCs inside a peripheral blood (PB) whole slide image.

    === Class Attributes ===
    - file_name_manager : the FileNameManager class object of the WSI
    - top_view : the TopView class object of the WSI
    - search_view : the SearchView class object of the WSI
    - wbc_candidates : a list of WBCCandidate class objects that represent candidates for being WBCs
    - focus_regions : a list of FocusRegion class objects representing the focus regions of the search view
    - differential : a Differential class object representing the differential of the WSI
    - save_dir : the directory to save the diagnostic logs, dataframes (and images if hoarding is True)

    - verbose : whether to print out the progress of the PBCounter object
    - hoarding : whether to hoard regions and cell images processed into permanent storage
    """

    def __init__(
        self,
        wsi_path: str,
        verbose: bool = False,
        hoarding: bool = False,
    ):
        """Initialize a PBCounter object."""

        self.verbose = verbose
        self.hoarding = hoarding

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

    def find_focus_regions(self):
        """Find the focus regions of the WSI."""

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

        fr_tracker.filter(save_dir=self.save_dir, hoarding=self.hoarding)

        # add num_sds to the save_dir/focus_regions/focus_regions_filtering.yaml file using yaml
        fr_filtering_yaml_path = os.path.join(
            self.save_dir, "focus_regions", "focus_regions_filtering.yaml"
        )

        fr_filtering_yaml = open(fr_filtering_yaml_path, "a")
        fr_filtering_yaml.write(f"relative_blue_signal_num_sds_thres: {num_sds}\n")
        fr_filtering_yaml.close()

        self.focus_regions = fr_tracker.get_filtered_focus_regions()

        if self.verbose:
            print(f"Initializing {num_croppers} Ray workers")

        ray.shutdown()
        ray.init(num_cpus=num_cpus)

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

    def find_wbc_candidates(self):
        """Update the wbc_candidates of the PBCounter object."""

        # make the directory save_dir/focus_regions/YOLO_df
        os.makedirs(
            os.path.join(self.save_dir, "focus_regions", "YOLO_df"), exist_ok=True
        )

        # make the directory save_dir/focus_regions/YOLO_df_unfiltered
        os.makedirs(
            os.path.join(self.save_dir, "focus_regions", "YOLO_df_unfiltered"),
            exist_ok=True,
        )

        if self.verbose:
            print(f"Initializing {num_gpus} Ray workers")

        ray.shutdown()
        ray.init(num_cpus=num_cpus, num_gpus=num_gpus)

        if self.verbose:
            print("Initializing YOLOManager")
        task_managers = [
            YOLOManager.remote(
                YOLO_ckpt_path,
                YOLO_conf_thres,
                save_dir=self.save_dir,
                hoarding=self.hoarding,
            )
            for _ in range(num_gpus)
        ]

        tasks = {}
        all_results = []
        new_focus_regions = []

        for i, focus_region in enumerate(self.focus_regions):
            manager = task_managers[i % num_gpus]
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
            cell_info = wbc_candidate.cell_info

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

        # plot the distribution of confidence score for all the detected cells
        plt.hist(big_cell_df["confidence"], bins=100)

        # save the plot
        plt.savefig(
            os.path.join(self.save_dir, "focus_regions", "YOLO_confidence.jpg"),
            dpi=300,
        )

        # plot the distribution of number of cells detected per region
        plt.hist(num_cells_per_region_df["num_cells"], bins=100)

        # save the plot
        plt.savefig(
            os.path.join(self.save_dir, "focus_regions", "num_cells_per_region.jpg"),
            dpi=300,
        )

        plt.close("all")

        # grab the info for the yaml file as a dictionary
        num_cells_per_region_mean = num_cells_per_region_df["num_cells"].mean()
        num_cells_per_region_sd = num_cells_per_region_df["num_cells"].std()

        YOLO_confidence_mean = big_cell_df["confidence"].mean()
        YOLO_confidence_sd = big_cell_df["confidence"].std()

        # add the mean and sd to the save_dir/cells/cell_detection.yaml file using yaml
        cell_detection_yaml_path = os.path.join(
            self.save_dir, "cells", "cell_detection.yaml"
        )

        cell_detection_yaml = open(cell_detection_yaml_path, "a")
        cell_detection_yaml.write(
            f"num_cells_per_region_mean: {numpy_to_python(num_cells_per_region_mean)}\n"
        )
        cell_detection_yaml.write(
            f"num_cells_per_region_sd: {numpy_to_python(num_cells_per_region_sd)}\n"
        )
        cell_detection_yaml.write(
            f"YOLO_confidence_mean: {numpy_to_python(YOLO_confidence_mean)}\n"
        )
        cell_detection_yaml.write(
            f"YOLO_confidence_sd: {numpy_to_python(YOLO_confidence_sd)}\n"
        )

        cell_detection_yaml.close()

    def label_wbc_candidates(self):
        """Update the labels of the wbc_candidates of the PBCounter object."""

        if self.wbc_candidates == [] or self.wbc_candidates is None:
            raise NoCellFoundError(
                "No WBC candidates found. Please run find_wbc_candidates() first. If problem persists, the slide may be problematic."
            )

        if self.verbose:
            print(f"Initializing {num_gpus} Ray workers")

        ray.shutdown()
        ray.init(num_cpus=num_cpus, num_gpus=num_gpus)

        if self.verbose:
            print("Initializing HemeLabelManager")
        task_managers = [
            HemeLabelManager.remote(HemeLabel_ckpt_path) for _ in range(num_gpus)
        ]

        tasks = {}
        all_results = []

        for i, wbc_candidate in enumerate(self.wbc_candidates):
            manager = task_managers[i % num_gpus]
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

    def tally_differential(self):
        """Just run everything."""

        if self.focus_regions is None:
            self.find_focus_regions()

        if self.wbc_candidates is None:
            self.find_wbc_candidates()

        if self.differential is None:
            self.label_wbc_candidates()


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
