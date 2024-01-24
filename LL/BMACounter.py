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
from LL.resources.BMAassumptions import *
from LL.FileNameManager import FileNameManager
from LL.TopView import TopView, SpecimenError, RelativeBlueSignalTooWeakError
from LL.SearchView import SearchView
from LL.BMAFocusRegion import *
from LL.BMAFocusRegionTracker import FocusRegionsTracker
from LL.brain.HemeLabelManager import HemeLabelManager
from LL.brain.YOLOManager import YOLOManager
from LL.Differential import Differential, to_count_dict
from LL.vision.processing import SlideError, read_with_timeout
from LL.vision.WSICropManager import WSICropManager
from LL.communication.write_config import *
from LL.communication.visualization import *
from LL.brain.utils import *
from LL.brain.SpecimenClf import get_region_type


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
    ):
        """Initialize a PBCounter object."""

        self.profiling_data = {}

        start_time = time.time()

        self.verbose = verbose
        self.hoarding = hoarding
        self.continue_on_error = continue_on_error
        self.ignore_specimen_type = ignore_specimen_type
        self.wsi_path = wsi_path

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

        print("Checking Specimen Type")
        specimen_type = get_region_type(top_view)

        self.predicted_specimen_type = specimen_type

        if specimen_type != "Bone Marrow Aspirate":
            if not self.ignore_specimen_type:
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
        self.top_view = TopView(
            top_view, top_view_downsampling_rate, top_level, verbose=self.verbose
        )

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
        self.differential = None

        self.profiling_data["init_time"] = time.time() - start_time

    def find_focus_regions(self):
        """Return the focus regions of the highest magnification view."""

        start_time = time.time()

        # First get a list of the focus regions coordinates based on focus_regions_size at highest level of magnification
        # if the dimension is not divisible by the focus_regions_size, then we simply omit the last focus region

        # get the dimension of the highest mag, which is the level 0
        # get the level 0 dimension using
        wsi = openslide.OpenSlide(self.wsi_path)
        level_0_dimension = wsi.level_dimensions[0]
        wsi.close()

        dimx, dimy = level_0_dimension

        focus_regions_size = focus_regions_size

        # get the number of focus regions in the x and y direction
        num_focus_regions_x = dimx // focus_regions_size[0]
        num_focus_regions_y = dimy // focus_regions_size[1]

        # get the list of focus regions coordinates
        focus_regions_coordinates = []

        for i in range(num_focus_regions_x):
            for j in range(num_focus_regions_y):
                focus_regions_coordinates.append(
                    (
                        i * focus_regions_size,
                        j * focus_regions_size,
                        (i + 1) * focus_regions_size,
                        (j + 1) * focus_regions_size,
                    )
                )

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

        ft_tracker = FocusRegionsTracker(self.focus_regions)

        pass

    def find_wbc_candidates(self):
        """Return the WBC candidates of the highest magnification view."""

        pass  # this is exactly the same function as in PBCounter -- note with different model checkpoint for YOLO -- I should train my own YOLOv8 for this

    def label_wbc_candidates(self):
        """Label the WBC candidates."""

        pass  # this is exactly the same function as in PBCounter

    def tally_differential(self):
        """Return the differential of the WSI."""

        pass  # this is exactly the same function as in PBCounter
