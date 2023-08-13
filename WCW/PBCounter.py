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
from WCW.resources.assumptions import *
from WCW.FileNameManager import FileNameManager
from WCW.TopView import TopView, SpecimenError
from WCW.SearchView import SearchView
from WCW.FocusRegion import FocusRegion
from WCW.brain.HemeLabelManager import HemeLabelManager
from WCW.brain.YOLOManager import YOLOManager
from WCW.Differential import Differential
from WCW.brain.statistics import focus_region_filtering
from WCW.vision.processing import SlideError, read_with_timeout
from WCW.vision.WSICropManager import WSICropManager


class PBCounter:

    """ A Class representing a Counter of WBCs inside a peripheral blood (PB) whole slide image. 

    === Class Attributes ===
    - file_name_manager : the FileNameManager class object of the WSI
    - top_view : the TopView class object of the WSI
    - search_view : the SearchView class object of the WSI
    - wbc_candidates : a list of WBCCandidate class objects that represent candidates for being WBCs
    - focus_regions : a list of FocusRegion class objects representing the focus regions of the search view
    - differential : a Differential class object representing the differential of the WSI

    - verbose : whether to print out the progress of the PBCounter object

    """

    def __init__(self,
                 wsi_path: str,
                 verbose: bool = False):
        """ Initialize a PBCounter object. """

        self.verbose = verbose

        if self.verbose:
            print(f"Initializing FileNameManager object for {wsi_path}")
        # Initialize the manager
        self.file_name_manager = FileNameManager(wsi_path)

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
            wsi, (0, 0), top_level, wsi.level_dimensions[top_level])

        # top_view = wsi.read_region(
        #     (0, 0), top_level, wsi.level_dimensions[top_level])

        top_view = top_view.convert("RGB")
        top_view_downsampling_rate = wsi.level_downsamples[top_level]
        self.top_view = TopView(
            top_view, top_view_downsampling_rate, top_level, verbose=self.verbose)

        if self.verbose:
            print(f"Checking if the specimen is peripheral blood")
        if not self.top_view.is_peripheral_blood():
            raise SpecimenError("The specimen is not peripheral blood.")

        if self.verbose:
            print(f"Processing WSI search view as SearchView object")
        # Processing the search level image

        search_view = read_with_timeout(
            wsi, (0, 0), search_view_level, wsi.level_dimensions[search_view_level])

        # search_view = wsi.read_region(
        #     (0, 0), search_view_level, wsi.level_dimensions[search_view_level])
        search_view_downsampling_rate = wsi.level_downsamples[search_view_level]
        self.search_view = SearchView(
            search_view, search_view_downsampling_rate, verbose=self.verbose)

        if self.verbose:
            print(f"Closing WSI")
        wsi.close()

        # The focus regions and WBC candidates are None until they are processed
        self.focus_regions = None
        self.wbc_candidates = None
        self.differential = None

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
        for focus_region_coord in tqdm(focus_regions_coords, desc="Creating focus regions"):

            focus_region = FocusRegion(focus_region_coord, self.search_view.image, int(
                self.search_view.downsampling_rate))

            unfiltered_focus_regions.append(focus_region)

        filtered_focus_regions = focus_region_filtering(
            unfiltered_focus_regions)

        self.focus_regions = filtered_focus_regions

        if self.verbose:
            print(f"Initializing {num_gpus} Ray workers")
        ray.init(num_cpus=num_cpus)

        if self.verbose:
            print('Initializing WSICropManager')
        crop_managers = [WSICropManager.remote(
            self.file_name_manager.wsi_path) for _ in range(num_gpus)]

        tasks = {}
        all_results = []

        for i, focus_region in enumerate(self.focus_regions):
            manager = crop_managers[i % num_gpus]
            task = manager.async_get_focus_region_image.remote(focus_region)
            tasks[task] = focus_region

        with tqdm(total=len(self.focus_regions), desc="Getting focus region images") as pbar:
            while tasks:
                done_ids, _ = ray.wait(list(tasks.keys()))

                for done_id in done_ids:
                    try:

                        result = ray.get(done_id)
                        all_results.append(result)

                    except RayTaskError as e:
                        print(
                            f"Task for focus region {tasks[done_id]} failed with error: {e}")

                    pbar.update()
                    del tasks[done_id]

        if self.verbose:
            print(f"Shutting down Ray")
        ray.shutdown()

        self.focus_regions = all_results

    def find_wbc_candidates(self):
        """ Update the wbc_candidates of the PBCounter object. """

        if self.verbose:
            print(f"Initializing {num_gpus} Ray workers")
        ray.init(num_cpus=num_cpus, num_gpus=num_gpus)

        if self.verbose:
            print('Initializing YOLOManager')
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
                        for wbc_candidate in result:
                            all_results.append(wbc_candidate)

                    except RayTaskError as e:
                        print(
                            f"Task for focus {tasks[done_id]} failed with error: {e}")

                    pbar.update()
                    del tasks[done_id]

        self.wbc_candidates = all_results

        if self.verbose:
            print(f"Shutting down Ray")
        ray.shutdown()

    def label_wbc_candidates(self):
        """ Update the labels of the wbc_candidates of the PBCounter object. """

        if self.verbose:
            print(f"Initializing {num_gpus} Ray workers")
        ray.init(num_cpus=num_cpus, num_gpus=num_gpus)

        if self.verbose:
            print('Initializing HemeLabelManager')
        task_managers = [HemeLabelManager.remote(
            HemeLabel_ckpt_path) for _ in range(num_gpus)]

        tasks = {}
        all_results = []

        for i, wbc_candidate in enumerate(self.wbc_candidates):
            manager = task_managers[i % num_gpus]
            task = manager.async_label_wbc_candidate.remote(wbc_candidate)
            tasks[task] = wbc_candidate

        with tqdm(total=len(self.wbc_candidates), desc="Classifying WBC candidates") as pbar:
            while tasks:
                done_ids, _ = ray.wait(list(tasks.keys()))

                for done_id in done_ids:
                    try:
                        wbc_candidate = ray.get(done_id)
                        if wbc_candidate is not None:
                            all_results.append(wbc_candidate)

                    except RayTaskError as e:
                        print(
                            f"Task for WBC candidate {tasks[done_id]} failed with error: {e}")

                    pbar.update()
                    del tasks[done_id]
        if self.verbose:
            print(f"Shutting down Ray")
        ray.shutdown()

        self.wbc_candidates = all_results
        self.differential = Differential(self.wbc_candidates)

    def tally_differential(self):
        """ Just run everything. """

        if self.focus_regions is None:
            self.find_focus_regions()

        if self.wbc_candidates is None:
            self.find_wbc_candidates()

        if self.differential is None:
            self.label_wbc_candidates()
