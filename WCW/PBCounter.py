####################################################################################################
# Imports ##########################################################################################
####################################################################################################

# Outside imports ##################################################################################
from PIL import Image
import openslide
from tqdm import tqdm
import ray
from ray.exceptions import RayTaskError

# Within package imports ###########################################################################
from assumptions import *
from FileNameManager import FileNameManager
from TopView import TopView, SpecimenError
from SearchView import SearchView
from FocusRegion import FocusRegion
from WCW.brain.HemeLabelManager import HemeLabelManager
from WCW.brain.YOLOManager import YOLOManager
from WCW.Differential import Differential
from WCW.brain.statistics import focus_region_filtering


class PBCounter:

    """ A Class representing a Counter of WBCs inside a peripheral blood (PB) whole slide image. 

    === Class Attributes ===
    - file_name_manager : the FileNameManager class object of the WSI
    - top_view : the TopView class object of the WSI
    - search_view : the SearchView class object of the WSI
    - wbc_candidates : a list of WBCCandidate class objects that represent candidates for being WBCs
    - focus_regions : a list of FocusRegion class objects representing the focus regions of the search view
    - differential : a Differential class object representing the differential of the WSI

    """

    def __init__(self,
                 wsi_path: str):
        """ Initialize a PBCounter object. """

        # Initialize the manager
        self.file_name_manager = FileNameManager(wsi_path)

        # Processing the WSI
        try:
            wsi = openslide.OpenSlide(wsi_path)
        except Exception as e:
            raise SlideError(e)

        # Processing the top level image
        top_level = len(wsi.level_dimensions) - 1
        top_view = wsi.read_region(
            (0, 0), top_level, wsi.level_dimensions[top_level])
        top_view = top_view.convert("RGB")
        top_view_downsampling_rate = wsi.level_downsamples[top_level]
        self.top_view = TopView(
            top_view, top_view_downsampling_rate, top_level)

        if not self.top_view.is_peripheral_blood():
            raise SpecimenError("The specimen is not peripheral blood.")

        # Processing the search level image
        search_view = wsi.read_region(
            (0, 0), search_view_level, wsi.level_dimensions[search_view_level])
        search_view_downsampling_rate = wsi.level_downsamples[search_view_level]
        self.search_view = SearchView(
            search_view, search_view_downsampling_rate)

        # The focus regions and WBC candidates are None until they are processed
        self.focus_regions = None
        self.wbc_candidates = None
        self.differential = None

        wsi.close()

    def find_focus_regions(self):
        """ Find the focus regions of the WSI. """

        focus_regions_coords = []
        locations = self.search_view.get_locations()

        for location in tqdm(locations, desc="Finding focus regions"):

            crop = self.search_view[location]

            focus_region_coords = list(self.top_view.find_focus_regions(crop,
                                                                        location,
                                                                        focus_regions_size,
                                                                        self.search_view.padding_x,
                                                                        self.search_view.padding_y,
                                                                        num_sds=foci_sds,
                                                                        top_to_search_zoom_ratio=int(
                                                                            self.top_view.downsampling_rate / self.search_view.downsampling_rate),
                                                                        search_to_0_zoom_ratio=int(
                                                                            self.search_view.downsampling_rate)
                                                                        ))

            focus_regions_coords.extend(focus_region_coords)

        unfiltered_focus_regions = []
        wsi = openslide.OpenSlide(self.file_name_manager.wsi_path)
        for focus_region_coord in tqdm(focus_regions_coords, desc="Creating focus regions"):
            focus_region_image = wsi.read_region(
                (focus_region_coord[0], focus_region_coord[1]), 0, (focus_regions_size, focus_regions_size))
            focus_region_image = focus_region_image.convert("RGB")

            focus_region = FocusRegion(focus_region_coord, focus_region_image)

            unfiltered_focus_regions.append(focus_region)

        filtered_focus_regions = focus_region_filtering(
            unfiltered_focus_regions)

        self.focus_regions = filtered_focus_regions

    def find_wbc_candidates(self):
        """ Update the wbc_candidates of the PBCounter object. """

        ray.init(num_cpus=num_cpus, num_gpus=num_gpus)

        task_managers = [YOLOManager.remote(
            YOLO_ckpt_path, YOLO_conf_thres) for _ in range(num_gpus)]

        tasks = {}
        all_results = []

        for i, focus_region in enumerate(self.focus_regions):
            manager = task_managers[i % num_gpus]
            task = manager.async_find_wbc_candidates.remote(focus_region)
            tasks[task] = focus_region

        with tqdm(total=len(self.focus_regions), desc="Detecting WBC candidates") as pbar:
            while tasks:
                done_ids, _ = ray.wait(list(tasks.keys()))

                for done_id in done_ids:
                    try:
                        result = ray.get(done_id)
                        all_results.extend(result)

                    except RayTaskError as e:
                        print(
                            f"Task for focus {tasks[done_id]} failed with error: {e}")

                    pbar.update()
                    del tasks[done_id]

        self.wbc_candidates = all_results

        ray.shutdown()

    def label_wbc_candidates(self):
        """ Update the labels of the wbc_candidates of the PBCounter object. """

        ray.init(num_cpus=num_cpus, num_gpus=num_gpus)

        task_managers = [HemeLabelManager.remote(
            HemeLabel_ckpt_path) for _ in range(num_gpus)]

        tasks = {}

        for i, wbc_candidate in enumerate(self.wbc_candidates):
            manager = task_managers[i % num_gpus]
            task = manager.async_label_wbc_candidate.remote(wbc_candidate)
            tasks[task] = wbc_candidate

        with tqdm(total=len(self.wbc_candidates), desc="Classifying WBC candidates") as pbar:
            while tasks:
                done_ids, _ = ray.wait(list(tasks.keys()))

                for done_id in done_ids:
                    try:
                        _ = ray.get(done_id)

                    except RayTaskError as e:
                        print(
                            f"Task for WBC candidate {tasks[done_id]} failed with error: {e}")

                    pbar.update()
                    del tasks[done_id]

        ray.shutdown()

        self.differential = Differential(self.wbc_candidates)

    def tally_differential(self):
        """ Just run everything. """

        if self.focus_regions is None:
            self.find_focus_regions()

        if self.wbc_candidates is None:
            self.find_wbc_candidates()

        if self.differential is None:
            self.label_wbc_candidates()


class SlideError(ValueError):
    """ The slide file has some issues that has nothing to do with the code. """

    def __init__(self, e):
        self.e = e

    def __str__(self):
        return f"SlideError: {self.e}"
