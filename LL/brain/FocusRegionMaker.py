import numpy as np
import ray

from LL.PBFocusRegion import FocusRegion


@ray.remote
class FocusRegionMaker:
    """This class is responsible for creating a focus region from a given
    === Class Attributes ===
    -- search_view : the search view that the focus region is from

    """

    def __init__(self, search_view) -> None:
        self.search_view = search_view

    def async_get_focus_region(self, focus_region_coord, idx):
        """Return the focus region at the given location."""

        focus_region = FocusRegion(
            idx=idx,
            coordinate=focus_region_coord,
            search_view_image=self.search_view.image,
            downsample_rate=int(self.search_view.downsampling_rate),
        )

        new_row = {
            "focus_region_id": idx,
            "x": focus_region_coord[0],
            "y": focus_region_coord[1],
            "VoL": focus_region.VoL,
            "WMP": focus_region.WMP,
            "confidence_score": np.nan,
            "rejected": 0,
            "region_classification_passed": np.nan,
            "max_WMP_passed": np.nan,
            "min_WMP_passed": np.nan,
            "min_VoL_passed": np.nan,
            # "lm_outier_removal_passed": np.nan,
            "reason_for_rejection": np.nan,
            "num_wbc_candidates": np.nan,
        }

        return focus_region, new_row
