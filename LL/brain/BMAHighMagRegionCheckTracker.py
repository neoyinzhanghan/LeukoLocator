import os
import ray
import pandas as pd
from LL.brain.BMAHighMagRegionChecker import BMAHighMagRegionChecker
from LL.resources.BMAassumptions import (
    num_region_clf_managers,
    high_mag_region_clf_ckpt_path,
    min_num_focus_regions,
)
from LL.brain.utils import create_list_of_batches_from_list
from tqdm import tqdm
from ray.exceptions import RayTaskError


class BMAHighMagRegionCheckTracker:
    """A class that keeps track of focus regions that made it past the low magnification checks.
    This class keeps track of the high magnification quality control of these regions.

    === Class Attributes ===
    - focus_regions: a list of focus regions that made it past the low magnification checks
    - info_df: a pandas DataFrame that stores the information of the focus regions

    """

    def __init__(self, focus_regions) -> None:

        tasks = {}
        new_focus_regions = []

        high_mag_checkers = [
            BMAHighMagRegionChecker.remote(high_mag_region_clf_ckpt_path)
            for _ in range(num_region_clf_managers)
        ]

        list_of_batches = create_list_of_batches_from_list(focus_regions, 10)

        for i, batch in enumerate(list_of_batches):
            manager = high_mag_checkers[i % num_region_clf_managers]
            task = manager.check_batch.remote(batch)
            tasks[task] = batch

        with tqdm(
            total=len(focus_regions),
            desc="Getting high magnification focus regions diagnostics...",
        ) as pbar:
            while tasks:
                done_ids, _ = ray.wait(list(tasks.keys()))

                for done_id in done_ids:
                    try:
                        results = ray.get(done_id)
                        for result in results:
                            new_focus_regions.append(result)

                            pbar.update()

                    except RayTaskError as e:
                        print(
                            f"Task for focus region {tasks[done_id]} failed with error: {e}"
                        )
                    del tasks[done_id]

        ray.shutdown()

        self.focus_regions = new_focus_regions

        # populate the info_df with the information of the focus regions
        info_dct = {
            "idx": [],
            "VoL_high_mag": [],
            "adequate_confidence_score_high_mag": [],
        }

        for focus_region in self.focus_regions:
            info_dct["idx"].append(focus_region.idx)
            info_dct["VoL_high_mag"].append(focus_region.VoL_high_mag)
            info_dct["adequate_confidence_score_high_mag"].append(
                focus_region.adequate_confidence_score_high_mag
            )

        # create a pandas DataFrame to store the information of the focus regions
        # it should have the following columns:
        # --idx: the index of the focus region
        # --VoL_high_mag: the volume of the focus region at high magnification
        # --adequate_confidence_score_high_mag: the confidence score of the focus region at high magnification

        self.info_df = pd.DataFrame(info_dct)

    def get_good_focus_regions(self):
        """The criterion for a good focus region is that it has an adequate confidence score at high magnification:
        - VoL_high_mag > 7
        - adequate_confidence_score_high_mag > 0.5
        """

        good_focus_regions = []

        for focus_region in self.focus_regions:
            if (
                focus_region.VoL_high_mag > 8
                and focus_region.adequate_confidence_score_high_mag > 0.3
            ):
                good_focus_regions.append(focus_region)

        # if len(good_focus_regions) < min_num_focus_regions:
        #     raise HighMagCheckFailedError(
        #         f"Only {len(good_focus_regions)} good focus regions remain after the high magnification check, and the minimum number of focus regions required is {min_num_focus_regions}."
        #     )

        return good_focus_regions

    def save_results(self, save_dir):

        # save the df in the save_dir/focus_regions/high_mag_focus_regions_info.csv
        self.info_df.to_csv(f"{save_dir}/focus_regions/high_mag_focus_regions_info.csv")

    def hoard_results(self, save_dir):
        os.makedirs(f"{save_dir}/focus_regions/high_mag_rejected", exist_ok=True)

        good_focus_regions = self.get_good_focus_regions()
        bad_focus_regions = [
            focus_region
            for focus_region in self.focus_regions
            if focus_region not in good_focus_regions
        ]

        for focus_region in tqdm(
            bad_focus_regions, desc="Saving rejected focus regions..."
        ):
            focus_region.image.save(
                f"{save_dir}/focus_regions/high_mag_rejected/{focus_region.idx}.jpg"
            )


class HighMagCheckFailedError(Exception):
    """This error is raised when not enough good focus regions remain after the high magnification check."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
