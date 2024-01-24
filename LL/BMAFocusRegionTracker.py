####################################################################################################
# Imports ###########################################################################################
####################################################################################################

# Outside imports ##################################################################################
import os
import time
import pandas as pd
import torch
import seaborn as sns
import ray
import numpy as np
from matplotlib import pyplot as plt
from tqdm import tqdm
from ray.exceptions import RayTaskError


# Within package imports ###########################################################################
from LL.resources.PBassumptions import *
from LL.communication.visualization import save_hist_KDE_rug_plot
from LL.communication.write_config import numpy_to_python
from LL.vision.region_clf_model import ResNet50Classifier
from LL.brain.RegionClfManager import RegionClfManager
from LL.brain.FocusRegionMaker import FocusRegionMaker
from LL.BMAFocusRegion import FocusRegion
from LL.brain.utils import *


class FocusRegionsTracker:
    """A class representing a focus region tracker object that tracks the metrics, objects, files related to focus region filtering.

    === Class Attributes ===
    - focus_regions_dct : a dictionary mapping focus region indices to FocusRegion objects
    - info_df : a dataframe containing the information of the focus regions

    - final_min_VoL : the final minimum VoL of the focus regions
    - final_min_WMP : the final minimum WMP of the focus regions
    - final_max_WMP : the final maximum WMP of the focus regions
    - final_min_conf_thres : the final minimum confidence threshold of the focus regions
    - region_clf_model : the region classifier

    """

    def __init__(self, focus_regions) -> None:
        """Initialize a FocusRegionsTracker object."""

        for i, focus_region in enumerate(focus_regions):
            focus_region.idx = i

        self.focus_regions_dct = {
            focus_region.idx: focus_region for focus_region in focus_regions
        }

        self.info_df = pd.DataFrame(
            columns=[
                "idx",
                "coordinate",
                "VoL",
                "WMP",
                "resnet_confidence_score",
            ]
        )

        for focus_region in focus_regions:
            self.info_df = self.info_df.append(
                {
                    "idx": focus_region.idx,
                    "coordinate": focus_region.coordinate,
                    "VoL": focus_region.VoL,
                    "WMP": focus_region.WMP,
                    "resnet_confidence_score": focus_region.resnet_confidence_score,
                },
                ignore_index=True,
            )

        self.final_min_VoL = None
        self.final_min_WMP = None
        self.final_max_WMP = None
        self.final_min_conf_thres = None

    def compute_resnet_confidence(self):
        """ """

        pass