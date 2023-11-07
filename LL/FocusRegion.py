####################################################################################################
# Imports ###########################################################################################
####################################################################################################

# Outside imports ##################################################################################
import os
import numpy as np
import pandas as pd
import yaml
import statsmodels.api as sm
import torch
from torchvision import transforms
from PIL import Image
from matplotlib import pyplot as plt
from PIL import Image
from tqdm import tqdm

# Within package imports ###########################################################################
from LL.resources.assumptions import *
from LL.vision.image_quality import VoL, WMP
from LL.communication.visualization import annotate_focus_region
from LL.vision.region_clf_model import ResNet50Classifier


class FocusRegion:
    """A focus region class object representing all the information needed at the focus region of the WSI.

    === Class Attributes ===
    - coordinate : the coordinate of the focus region in the level 0 view in the format of (TL_x, TL_y, BR_x, BR_y)
    - image : the image of the focus region
    - annotated_image : the image of the focus region annotated with the WBC candidates
    - downsample_rate : the downsampling rate of the focus region
    - downsampled_image : the downsampled image of the focus region corresponding to the search view magnification
    - VoL : the variance of the laplacian of the focus region
    - WMP : the white mask proportion of the focus region
    - wbc_candidate_bboxes : a list of bbox of the WBC candidates in the level 0 view in the format of (TL_x, TL_y, BR_x, BR_y) in relative to the focus region
    """

    def __init__(self, coordinate, search_view_image, downsample_rate):
        """Initialize a FocusRegion object. The full resolution image is None at initialization."""

        self.coordinate = coordinate
        self.image = None
        self.annotated_image = None

        # calculate the downsampled coordinateF

        downsampled_coordinate = (
            int(coordinate[0] / downsample_rate),
            int(coordinate[1] / downsample_rate),
            int(coordinate[2] / downsample_rate),
            int(coordinate[3] / downsample_rate),
        )

        self.downsampled_image = search_view_image.crop(downsampled_coordinate)
        self.downsample_rate = downsample_rate

        # Calculate the VoL and WMP
        self.VoL = VoL(self.downsampled_image)
        self.WMP = WMP(self.downsampled_image)

        self.wbc_candidate_bboxes = None

    def get_image(self, image):
        """Update the image of the focus region."""

        self.image = image

    def get_annotated_image(self):
        """Return the image of the focus region annotated with the WBC candidates."""

        if self.image is None or self.wbc_candidate_bboxes is None:
            raise self.FocusRegionNotAnnotatedError

        elif self.annotated_image is not None:
            return self.annotated_image

        else:
            self.annotated_image = annotate_focus_region(
                self.image, self.wbc_candidate_bboxes
            )
            return self.annotated_image

    def get_annotation_df(self):
        """Return a dataframe containing the annotations of the focus region. Must have columns ['TL_x', 'TL_y', 'BR_x', 'BR_y']."""

        if self.wbc_candidate_bboxes is None:
            raise self.FocusRegionNotAnnotatedError

        else:
            return pd.DataFrame(
                self.wbc_candidate_bboxes, columns=["TL_x", "TL_y", "BR_x", "BR_y"]
            )


def _gather_focus_regions_and_metrics(
    search_view, focus_regions_coords
):  # eventually we might need to implement distributed computing here
    """Return a dictionary mapping focus region indices to FocusRegion objects and a dataframe containing the metrics of the focus regions."""
    focus_regions_dct = (
        {}
    )  # key is the index of the focus region, value is the FocusRegion object
    # start collecting rows for a dataframe containing the metrics of the focus regions

    image_metrics = []  # columns are x, y, VoL, WMP

    for i, focus_region_coord in tqdm(
        enumerate(focus_regions_coords), desc="Gathering focus regions and metrics"
    ):
        focus_region = FocusRegion(
            coordinate=focus_region_coord,
            search_view_image=search_view.image,
            downsample_rate=int(search_view.downsampling_rate),
        )

        focus_regions_dct[i] = focus_region
        new_row = {
            "focus_region_id": i,
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
        }

        image_metrics.append(new_row)

    image_metrics_df = pd.DataFrame(image_metrics)

    return focus_regions_dct, image_metrics_df


def numpy_to_python(value):
    """Converts numpy objects to Python native objects."""
    if isinstance(value, (np.generic, np.ndarray)):
        return value.item() if np.isscalar(value) else value.tolist()
    else:
        return value


import torch
from torchvision import transforms
from PIL import Image

# Assuming the ResNet50Classifier class definition is already loaded


def load_model_from_checkpoint(checkpoint_path):
    """
    Load the model from a given checkpoint path.
    """
    model = ResNet50Classifier()
    checkpoint = torch.load(
        checkpoint_path, map_location=lambda storage, loc: storage
    )  # This allows loading to CPU
    model.load_state_dict(checkpoint["state_dict"])
    model.eval()  # Set to evaluation mode

    return model


def predict(pil_image, model):
    """
    Predict the confidence score for the given PIL image.

    Parameters:
    - pil_image (PIL.Image.Image): Input PIL Image object.
    - model (torch.nn.Module): Trained model.

    Returns:
    - float: Confidence score for the class label `1`.
    """
    # Transform the input image to the format the model expects
    transform = transforms.Compose(
        [
            transforms.Resize(256),
            transforms.ToTensor(),
        ]
    )
    image = pil_image.convert("RGB")
    image = transform(image).unsqueeze(0)  # Add batch dimension

    with torch.no_grad():  # No need to compute gradients for inference
        logits = model(image)
        probs = torch.softmax(logits, dim=1)
        confidence_score = probs[0][1].item()

    return confidence_score


class FocusRegionsTracker:
    """A class representing a focus region tracker object that tracks the metrics, objects, files related to focus region filtering.

    === Class Attributes ===
    - focus_regions_dct : a dictionary mapping focus region indices to FocusRegion objects
    - num_unfiltered : the total number of focus regions before filtering
    - num_filtered : the total number of focus regions after filtering
    - info_df : a dataframe containing the information of the focus regions

    - final_min_VoL : the final minimum VoL of the focus regions
    - final_min_WMP : the final minimum WMP of the focus regions
    - final_max_WMP : the final maximum WMP of the focus regions

    - lm_intercept : the intercept of the linear model
    - lm_slope : the slope of the linear model
    - lm_std_resid : the standard deviation of the residuals of the linear model

    - region_clf_model : the region classifier
    """

    def __init__(self, search_view, focus_regions_coords) -> None:
        """Initialize a FocusRegionsTracker object."""

        self.focus_regions_dct, self.info_df = _gather_focus_regions_and_metrics(
            search_view, focus_regions_coords
        )

        # self.info_df["VoL/WMP"] = self.info_df["VoL"] / self.info_df["WMP"]

        self.num_unfiltered = len(self.focus_regions_dct)
        self.num_filtered = self.num_unfiltered

        self.final_min_VoL = None
        self.final_min_WMP = None
        self.final_max_WMP = None

        self.lm_intercept = None
        self.lm_slope = None
        self.lm_std_resid = None

        self.final_min_conf_thres = None

    def save_focus_regions_info(self, save_dir):
        """Save the information of the focus regions to a csv file."""

        self.info_df.to_csv(
            os.path.join(save_dir, "focus_regions", "focus_regions_info.csv")
        )

    def _filter_min_VoL(self):
        """
        We start with the min_VoL parameter from assumption,
        and if less that min_num_regions_after_VoL_filter focus regions are left,
        we sort the remaining focus regions by VoL in descending order, and take the top ones just enough to have min_num_regions_after_VoL_filter focus regions left.
        """

        # first filter the dataframe to keep only ones that are not rejected
        unrejected_df = self.info_df[self.info_df["rejected"] == 0]

        # first filter out the focus regions that do not satisfy the min_VoL requirement using self.info_df
        good_ones = unrejected_df[unrejected_df["VoL"] >= min_VoL]
        bad_ones = unrejected_df[unrejected_df["VoL"] < min_VoL]

        if len(good_ones) < min_num_regions_after_VoL_filter:
            # sort the bad ones by VoL in descending order
            bad_ones = bad_ones.sort_values(by=["VoL"], ascending=False)

            # take the top ones just enough to have min_num_regions_after_VoL_filter focus regions left
            okay_ones = bad_ones.iloc[
                : min_num_regions_after_VoL_filter - len(good_ones)
            ]

            # concatenate the good ones and the bad ones
            selected = pd.concat([good_ones, okay_ones])

        else:
            selected = good_ones

        # find the minimum VoL of the selected focus regions
        self.final_min_VoL = selected["VoL"].min()

        # get the focus_region_id of the selected focus regions
        selected_focus_region_ids = selected["focus_region_id"].tolist()

        # update the rejected column of the info_df and the min_VoL_passed column
        self.info_df.loc[
            self.info_df["focus_region_id"].isin(selected_focus_region_ids),
            "min_VoL_passed",
        ] = 1
        self.info_df.loc[
            ~self.info_df["focus_region_id"].isin(selected_focus_region_ids),
            "rejected",
        ] = 1

        # update the reason_for_rejection column of the info_df, only those reason for rejection is nan
        self.info_df.loc[
            ~self.info_df["focus_region_id"].isin(selected_focus_region_ids)
            & self.info_df["reason_for_rejection"].isna(),
            "reason_for_rejection",
        ] = "too_low_VoL"

    def _filter_max_WMP(self):
        """
        We start with the max_WMP parameter from assumption,
        and if less that min_num_regions_after_WMP_max_filter focus regions are left,
        we sort the remaining focus regions
        """

        # first filter the dataframe to keep only ones that are not rejected
        unrejected_df = self.info_df[self.info_df["rejected"] == 0]

        # first filter out the focus regions that do not satisfy the max_WMP requirement using self.info_df
        good_ones = unrejected_df[unrejected_df["WMP"] < max_WMP]
        bad_ones = unrejected_df[unrejected_df["WMP"] >= max_WMP]

        if len(good_ones) < min_num_regions_after_WMP_max_filter:
            # sort the bad ones by WMP in descending order
            bad_ones = bad_ones.sort_values(by=["WMP"], ascending=True)

            # take the top ones just enough to have min_num_regions_after_WMP_filter focus regions left
            okay_ones = bad_ones.iloc[
                : min_num_regions_after_WMP_max_filter - len(good_ones)
            ]

            # concatenate the good ones and the bad ones
            selected = pd.concat([good_ones, okay_ones])

        else:
            selected = good_ones

        # find the minimum WMP of the selected focus regions
        self.final_max_WMP = selected["WMP"].max()

        # get the focus_region_id of the selected focus regions
        selected_focus_region_ids = selected["focus_region_id"].tolist()

        # update the rejected column of the info_df and the min_WMP_passed column
        self.info_df.loc[
            self.info_df["focus_region_id"].isin(selected_focus_region_ids),
            "max_WMP_passed",
        ] = 1
        self.info_df.loc[
            ~self.info_df["focus_region_id"].isin(selected_focus_region_ids),
            "rejected",
        ] = 1
        # update the reason_for_rejection column of the info_df
        self.info_df.loc[
            ~self.info_df["focus_region_id"].isin(selected_focus_region_ids)
            & self.info_df["reason_for_rejection"].isna(),
            "reason_for_rejection",
        ] = "too_high_WMP"

    def _filter_min_WMP(self):
        """We start with the min_WMP parameter from assumption,
        and if less that min_num_regions_after_WMP_min_filter focus regions are left,
        we sort the remaining focus regions by WMP in descending order, and take the top ones just enough to have min_num_regions_after_WMP_min_filter focus regions left.
        """

        # first filter the dataframe to keep only ones that are not rejected
        unrejected_df = self.info_df[self.info_df["rejected"] == 0]

        # first filter out the focus regions that do not satisfy the min_WMP requirement using self.info_df
        good_ones = unrejected_df[unrejected_df["WMP"] >= min_WMP]
        bad_ones = unrejected_df[unrejected_df["WMP"] < min_WMP]

        if len(good_ones) < min_num_regions_after_WMP_min_filter:
            # sort the bad ones by WMP in descending order
            bad_ones = bad_ones.sort_values(by=["WMP"], ascending=False)

            # take the top ones just enough to have min_num_regions_after_WMP_filter focus regions left
            okay_ones = bad_ones.iloc[
                : min_num_regions_after_WMP_min_filter - len(good_ones)
            ]

            # concatenate the good ones and the bad ones
            selected = pd.concat([good_ones, okay_ones])

        else:
            selected = good_ones

        # find the minimum WMP of the selected focus regions
        self.final_min_WMP = selected["WMP"].min()

        # get the focus_region_id of the selected focus regions
        selected_focus_region_ids = selected["focus_region_id"].tolist()

        # update the rejected column of the info_df and the min_WMP_passed column
        self.info_df.loc[
            self.info_df["focus_region_id"].isin(selected_focus_region_ids),
            "min_WMP_passed",
        ] = 1
        self.info_df.loc[
            ~self.info_df["focus_region_id"].isin(selected_focus_region_ids),
            "rejected",
        ] = 1
        # update the reason_for_rejection column of the info_df
        self.info_df.loc[
            ~self.info_df["focus_region_id"].isin(selected_focus_region_ids)
            & self.info_df["reason_for_rejection"].isna(),
            "reason_for_rejection",
        ] = "too_low_WMP"

    # def _lm_outlier_filtering(self): # TODO deprecated to remove by keeping now coz why not
    #     """Perform a linear model outlier removal using 1 SD."""

    #     unrejected_df = self.info_df[self.info_df["rejected"] == 0]

    #     X = unrejected_df["WMP"]
    #     X = sm.add_constant(X)
    #     y = unrejected_df["VoL/WMP"]

    #     model = sm.OLS(y, X).fit()

    #     residuals = y - model.predict(X)
    #     std_resid = np.std(residuals)
    #     mean_resid = np.mean(residuals)

    #     self.lm_intercept = model.params[0]
    #     self.lm_slope = model.params[1]
    #     self.lm_std_resid = std_resid

    #     # Define inliers based on residuals
    #     inlier_mask = (
    #         residuals >= mean_resid - focus_region_outlier_tolerance * std_resid
    #     ) & (residuals <= mean_resid + focus_region_outlier_tolerance * std_resid)

    #     # Filter out outliers
    #     selected = unrejected_df[inlier_mask]

    #     # get the focus_region_id of the selected focus regions
    #     selected_focus_region_ids = selected["focus_region_id"].tolist()

    #     # update the rejected column of the info_df and the min_WMP_passed column
    #     self.info_df.loc[
    #         self.info_df["focus_region_id"].isin(selected_focus_region_ids),
    #         "lm_outier_removal_passed",
    #     ] = 1
    #     self.info_df.loc[
    #         ~self.info_df["focus_region_id"].isin(selected_focus_region_ids),
    #         "rejected",
    #     ] = 1
    #     # update the reason_for_rejection column of the info_df
    #     self.info_df.loc[
    #         ~self.info_df["focus_region_id"].isin(selected_focus_region_ids)
    #         & self.info_df["reason_for_rejection"].isna(),
    #         "reason_for_rejection",
    #     ] = "lm_outlier"

    def _get_resnet_confidence_score(self, model_ckpt_path=region_clf_ckpt_path):
        """For all the regions that haven't been rejected yet, get the confidence score from the resnet model."""

        model = load_model_from_checkpoint(model_ckpt_path)
        unrejected_df = self.info_df[self.info_df["rejected"] == 0]

        for i, row in tqdm(
            unrejected_df.iterrows(), desc="Getting ResNet confidence score"
        ):
            focus_region = self.focus_regions_dct[row["focus_region_id"]]

            confidence_score = predict(focus_region.downsampled_image, model)

            self.info_df.loc[i, "confidence_score"] = confidence_score

    def _resnet_conf_filtering(self):
        """Filter out the regions that do not satisfy the confidence score requirement."""

        unrejected_df = self.info_df[self.info_df["rejected"] == 0]

        # first filter out the focus regions that do not satisfy the confidence score requirement using self.info_df
        good_ones = unrejected_df[
            unrejected_df["confidence_score"] >= region_clf_conf_thres
        ]
        bad_ones = unrejected_df[
            unrejected_df["confidence_score"] < region_clf_conf_thres
        ]

        if len(good_ones) < min_num_regions_after_region_clf:
            # sort the bad ones by confidence score in descending order
            bad_ones = bad_ones.sort_values(by=["confidence_score"], ascending=False)

            # take the top ones just enough to have min_num_regions_after_region_clf focus regions left
            okay_ones = bad_ones.iloc[
                : min_num_regions_after_region_clf - len(good_ones)
            ]

            # concatenate the good ones and the bad ones
            selected = pd.concat([good_ones, okay_ones])

        else:
            selected = good_ones

        # get the focus_region_id of the selected focus regions
        selected_focus_region_ids = selected["focus_region_id"].tolist()

        self.final_min_conf_thres = selected["confidence_score"].min()

        # update the rejected column of the info_df and the min_WMP_passed column
        self.info_df.loc[
            self.info_df["focus_region_id"].isin(selected_focus_region_ids),
            "region_classification_passed",
        ] = 1
        self.info_df.loc[
            ~self.info_df["focus_region_id"].isin(selected_focus_region_ids),
            "rejected",
        ] = 1
        # update the reason_for_rejection column of the info_df
        self.info_df.loc[
            ~self.info_df["focus_region_id"].isin(selected_focus_region_ids)
            & self.info_df["reason_for_rejection"].isna(),
            "reason_for_rejection",
        ] = "resnet_conf_too_low"

    def _save_VoL_plot(self, save_dir, after_filtering=False):
        """Save the VoL plot, with the final_min_VoL as a vertical line."""

        # if save_dir/focus_regions does not exist, then create it
        if not os.path.exists(os.path.join(save_dir, "focus_regions")):
            os.makedirs(os.path.join(save_dir, "focus_regions"))

        # if after_filtering is True, then filter out the focus regions that are rejected
        if after_filtering:
            filtered = self.info_df[self.info_df["rejected"] == 0]
        else:
            filtered = self.info_df

        # save the plot of the unnormalized density of the VoL and WMP of the focus regions and the max_WMP, min_WMP and min_VoL as vertical lines
        # use the info_df to plot the density
        plt.figure(figsize=(10, 10))
        plt.hist(filtered["VoL"], bins=100, alpha=0.5)

        if not after_filtering:  # no need to plot the vertical lines if after filtering
            plt.axvline(
                x=self.final_min_VoL, color="r", linestyle="-", label="final_min_VoL"
            )
            plt.legend()

        plt.title(
            f"Unnormalized density of the VoL of the focus regions, filtered == {after_filtering}"
        )
        plt.xlabel("VoL")
        plt.ylabel("Count")
        plt.savefig(
            os.path.join(
                save_dir,
                "focus_regions",
                f"VoL_unnormalized_density_filtered_{after_filtering}.png",
            )
        )

    def _save_WMP_plot(self, save_dir, after_filtering=False):
        """Save the WMP plot, with the final_max_WMP and final_min_WMP as vertical lines."""

        # if save_dir/focus_regions does not exist, then create it
        if not os.path.exists(os.path.join(save_dir, "focus_regions")):
            os.makedirs(os.path.join(save_dir, "focus_regions"))

        # if after_filtering is True, then filter out the focus regions that are rejected
        if after_filtering:
            filtered = self.info_df[self.info_df["rejected"] == 0]
        else:
            filtered = self.info_df

        # save the plot of the unnormalized density of the VoL and WMP of the focus regions and the max_WMP, min_WMP and min_VoL as vertical lines
        # use the info_df to plot the density
        plt.figure(figsize=(10, 10))
        plt.hist(filtered["WMP"], bins=100, alpha=0.5)

        if not after_filtering:  # no need to plot the vertical lines if after filtering
            plt.axvline(
                x=self.final_min_WMP, color="r", linestyle="-", label="final_min_WMP"
            )
            plt.axvline(
                x=self.final_max_WMP, color="r", linestyle="-", label="final_max_WMP"
            )
            plt.legend()

        plt.title(
            f"Unnormalized density of the WMP of the focus regions, filtered == {after_filtering}"
        )
        plt.xlabel("WMP")
        plt.ylabel("Count")

        plt.savefig(
            os.path.join(
                save_dir,
                "focus_regions",
                f"WMP_unnormalized_density_filtered_{after_filtering}.png",
            )
        )

    def _save_VoL_WMP_scatter(self, save_dir, filtered=True):
        """Save a scatter plot of VoL and WMP for all all the data if not filtered and for the filtered data if filtered."""

        # if save_dir/focus_regions does not exist, then create it
        os.path.mkdir(os.path.join(save_dir, "focus_regions"), exist_ok=True)

        # if filtered is True, then filter out the focus regions that are rejected
        if filtered:
            filtered = self.info_df[self.info_df["rejected"] == 0]
        else:
            filtered = self.info_df

        # save the plot of the unnormalized density of the VoL and WMP of the focus regions and the max_WMP, min_WMP and min_VoL as vertical lines
        # use the info_df to plot the density
        plt.figure(figsize=(10, 10))
        plt.scatter(filtered["WMP"], filtered["VoL"], alpha=0.5)

        plt.title(
            f"Scatter plot of the VoL and WMP of the focus regions, filtered == {filtered}"
        )
        plt.xlabel("WMP")
        plt.ylabel("VoL")

        plt.savefig(
            os.path.join(
                save_dir,
                "focus_regions",
                f"VoL_WMP_scatter_filtered_{filtered}.png",
            )
        )

    # def _save_lm_plot(self, save_dir):
    #     """Save the lm plot."""

    #     # if save_dir/focus_regions does not exist, then create it
    #     if not os.path.exists(os.path.join(save_dir, "focus_regions")):
    #         os.makedirs(os.path.join(save_dir, "focus_regions"))

    #     # only pick things that passed the VoL and WMP tests
    #     filtered = self.info_df[
    #         (self.info_df["min_VoL_passed"] == 1)
    #         & (self.info_df["min_WMP_passed"] == 1)
    #         & (self.info_df["max_WMP_passed"] == 1)
    #     ]

    #     # use self.lm_intercept and self.lm_slope to plot the linear model
    #     plt.figure(figsize=(10, 10))
    #     plt.scatter(filtered["WMP"], filtered["VoL/WMP"], alpha=0.5)
    #     plt.plot(
    #         filtered["WMP"],
    #         self.lm_intercept + self.lm_slope * filtered["WMP"],
    #         color="r",
    #     )

    #     # plot the outlier tolerance lines
    #     plt.plot(
    #         filtered["WMP"],
    #         self.lm_intercept
    #         + (self.lm_slope + focus_region_outlier_tolerance * self.lm_std_resid)
    #         * filtered["WMP"],
    #         color="g",
    #     )

    #     plt.plot(
    #         filtered["WMP"],
    #         self.lm_intercept
    #         + (self.lm_slope - focus_region_outlier_tolerance * self.lm_std_resid)
    #         * filtered["WMP"],
    #         color="g",
    #     )

    #     plt.title("Linear model of WMP and VoL/WMP")

    #     plt.xlabel("WMP")
    #     plt.ylabel("VoL/WMP")
    #     plt.savefig(
    #         os.path.join(save_dir, "focus_regions", "lm_plot.png"),
    #     )

    def _save_resnet_conf_plot(self, save_dir, after_filtering=False):
        """Save the resnet confidence score plot."""

        # if save_dir/focus_regions does not exist, then create it
        if not os.path.exists(os.path.join(save_dir, "focus_regions")):
            os.makedirs(os.path.join(save_dir, "focus_regions"))

        # only pick things that passed the VoL and WMP tests
        filtered = self.info_df[
            (self.info_df["min_VoL_passed"] == 1)
            & (self.info_df["min_WMP_passed"] == 1)
            & (self.info_df["max_WMP_passed"] == 1)
            # & (self.info_df["lm_outier_removal_passed"] == 1)
        ]

        if after_filtering:
            filtered = filtered[filtered["rejected"] == 0]

        # after filtering, we can plot the resnet confidence score
        plt.figure(figsize=(10, 10))
        plt.hist(filtered["confidence_score"], bins=100, alpha=0.5)

        plt.title("Unnormalized density of the resnet confidence score")
        plt.xlabel("Confidence score")

        plt.savefig(
            os.path.join(
                save_dir,
                "focus_regions",
                f"resnet_confidence_score_unnormalized_density_filtered_{after_filtering}.png",
            )
        )

    def _get_diagnostics(self, save_dir):
        """Calculate the following diagnostics:
        - mean and variance of VoL, WMP before and after filtering for both the passed and accepted
        - percentage of focus regions rejected because of low VoL, high WMP, low WMP, and resnet confidence score

        Return as a dictionary.
        """

        # if save_dir/focus_regions does not exist, then create it
        if not os.path.exists(os.path.join(save_dir, "focus_regions")):
            os.makedirs(os.path.join(save_dir, "focus_regions"))

        passed_df = self.info_df[self.info_df["rejected"] == 0]
        accepted_df = self.info_df[self.info_df["rejected"] == 0]
        total_df = self.info_df

        passed_VoL_mean = passed_df["VoL"].mean()
        passed_VoL_sd = passed_df["VoL"].std()
        accepted_VoL_mean = accepted_df["VoL"].mean()
        accepted_VoL_sd = accepted_df["VoL"].std()
        total_VoL_mean = total_df["VoL"].mean()
        total_VoL_sd = total_df["VoL"].std()

        percentage_rejected_by_low_VoL = (
            len(self.info_df[(self.info_df["reason_for_rejection"] == "too_low_VoL")])
            / self.num_unfiltered
        )
        percentage_rejected_by_high_WMP = (
            len(self.info_df[(self.info_df["reason_for_rejection"] == "too_high_WMP")])
            / self.num_unfiltered
        )
        percentage_rejected_by_low_WMP = (
            len(self.info_df[(self.info_df["reason_for_rejection"] == "too_low_WMP")])
            / self.num_unfiltered
        )
        percentage_rejected_by_resnet_conf = (
            len(self.info_df[(self.info_df["region_classification_passed"] == 0)])
            / self.num_unfiltered
        )

        diagnostics = {
            "passed_VoL_mean": numpy_to_python(passed_VoL_mean),
            "passed_VoL_sd": numpy_to_python(passed_VoL_sd),
            "accepted_VoL_mean": numpy_to_python(accepted_VoL_mean),
            "accepted_VoL_sd": numpy_to_python(accepted_VoL_sd),
            "total_VoL_mean": numpy_to_python(total_VoL_mean),
            "total_VoL_sd": numpy_to_python(total_VoL_sd),
            "percentage_rejected_by_low_VoL": numpy_to_python(
                percentage_rejected_by_low_VoL
            ),
            "percentage_rejected_by_high_WMP": numpy_to_python(
                percentage_rejected_by_high_WMP
            ),
            "percentage_rejected_by_low_WMP": numpy_to_python(
                percentage_rejected_by_low_WMP
            ),
            "percentage_rejected_by_resnet_conf": numpy_to_python(
                percentage_rejected_by_resnet_conf
            ),
        }

        return diagnostics

    def _save_yaml(self, save_dir):
        """Save the class attributes as a YAML file."""

        # if save_dir/focus_regions does not exist, then create it
        if not os.path.exists(os.path.join(save_dir, "focus_regions")):
            os.makedirs(os.path.join(save_dir, "focus_regions"))

        # the class attributes to save include num_unfiltered, num_filtered, final_min_VoL, final_min_WMP, final_max_WMP, lm_intercept, lm_slope
        yaml_dict = {
            "num_unfiltered": numpy_to_python(self.num_unfiltered),
            "num_unrejected_after_VoL_filter": numpy_to_python(
                len(self.info_df[(self.info_df["min_VoL_passed"] == 1)])
            ),
            "num_unrejected_after_WMP_max_filter": numpy_to_python(
                len((self.info_df["max_WMP_passed"] == 1))
            ),
            "num_unrejected_after_WMP_min_filter": numpy_to_python(
                len(self.info_df[(self.info_df["min_WMP_passed"] == 1)])
            ),
            "num_filtered": numpy_to_python(self.num_filtered),
            "final_min_VoL": numpy_to_python(self.final_min_VoL),
            "final_min_WMP": numpy_to_python(self.final_min_WMP),
            "final_max_WMP": numpy_to_python(self.final_max_WMP),
            "final_min_conf_thres": numpy_to_python(self.final_min_conf_thres),
            # "lm_intercept": numpy_to_python(self.lm_intercept),
            # "lm_slope": numpy_to_python(self.lm_slope),
            # "lm_std_resid": numpy_to_python(self.lm_std_resid),
        }

        diagnostics = self._get_diagnostics(save_dir)

        # add the diagnostics to the yaml_dict
        yaml_dict.update(diagnostics)

        with open(
            os.path.join(save_dir, "focus_regions", "focus_regions_filtering.yaml"), "w"
        ) as file:
            yaml.dump(yaml_dict, file)

    def save_results(self, save_dir, hoarding=False):
        """Save the csv files and diagnostic plots.
        If hoarding, then also save the focus regions at the search view magnification sorted into folders.
        """

        # save the info_df as a csv file in save_dir/focus_regions
        self.save_focus_regions_info(save_dir)

        # save the VoL plot, with the final_min_VoL as a vertical line then one after filtering
        self._save_VoL_plot(save_dir, after_filtering=False)
        self._save_VoL_plot(save_dir, after_filtering=True)

        # save the WMP plot, with the final_max_WMP and final_min_WMP as vertical lines then one after filtering
        self._save_WMP_plot(save_dir, after_filtering=False)
        self._save_WMP_plot(save_dir, after_filtering=True)

        # save the lm plot
        # self._save_lm_plot(save_dir)

        # save the resnet confidence score plot
        self._save_resnet_conf_plot(save_dir, after_filtering=False)

        # save the class attributes as a YAML file
        self._save_yaml(save_dir)

        # if hoarding is True, then save the focus regions at the search view magnification sorted into folders
        if hoarding:
            # create some folders -- too_low_VoL, too_high_WMP, too_low_WMP, lm_ouliers
            os.makedirs(
                os.path.join(save_dir, "focus_regions", "passed"), exist_ok=True
            )
            os.makedirs(
                os.path.join(save_dir, "focus_regions", "too_low_VoL"), exist_ok=True
            )
            os.makedirs(
                os.path.join(save_dir, "focus_regions", "too_high_WMP"), exist_ok=True
            )
            os.makedirs(
                os.path.join(save_dir, "focus_regions", "too_low_WMP"), exist_ok=True
            )
            # os.makedirs(
            #     os.path.join(save_dir, "focus_regions", "lm_outlier"), exist_ok=True
            # )
            os.makedirs(
                os.path.join(save_dir, "focus_regions", "resnet_conf_too_low"),
                exist_ok=True,
            )

            for i, focus_region in tqdm(
                self.focus_regions_dct.items(),
                desc="Hoarding",
            ):
                if (
                    self.info_df.loc[
                        self.info_df["focus_region_id"] == i, "rejected"
                    ].values[0]
                    == 1
                ):
                    # save the focus region image to the corresponding folder
                    focus_region.downsampled_image.save(
                        os.path.join(
                            save_dir,
                            "focus_regions",
                            self.info_df.loc[
                                self.info_df["focus_region_id"] == i,
                                "reason_for_rejection",
                            ].values[0],
                            f"focus_region_{i}.png",
                        )
                    )
                else:
                    # save the focus region image to the passed folder
                    focus_region.downsampled_image.save(
                        os.path.join(
                            save_dir,
                            "focus_regions",
                            "passed",
                            f"focus_region_{i}.png",
                        )
                    )

    def filter(self, save_dir, hoarding=False):
        """Run through the filtering pipeline, and if hoarding is True, then save the focus regions
        at the search view magnification sorted into folders."""

        self._filter_min_VoL()
        self._filter_max_WMP()
        self._filter_min_WMP()
        # self._lm_outlier_filtering()

        # print the number of unrejected focus_regions before resnet confidence score filtering
        print(
            f"Number of unrejected focus regions before resnet confidence score filtering: {len(self.info_df[self.info_df['rejected'] == 0])}"
        )

        self._get_resnet_confidence_score()
        self._resnet_conf_filtering()

        self.num_filtered = len(self.info_df[self.info_df["rejected"] == 0])

        # update the reason for rejection column
        self.info_df.loc[
            self.info_df["min_VoL_passed"] == 0, "reason_for_rejection"
        ] = "too_low_VoL"
        self.info_df.loc[
            self.info_df["max_WMP_passed"] == 0, "reason_for_rejection"
        ] = "too_high_WMP"
        self.info_df.loc[
            self.info_df["min_WMP_passed"] == 0, "reason_for_rejection"
        ] = "too_low_WMP"
        # self.info_df.loc[
        #     self.info_df["lm_outier_removal_passed"] == 0, "reason_for_rejection"
        # ] = "lm_ouliers"

        self.save_results(save_dir=save_dir, hoarding=hoarding)


class FocusRegionNotAnnotatedError(ValueError):
    """Raised when the focus region is not annotated."""

    def __init__(self, message="The focus region is not annotated."):
        self.message = message
        super().__init__(self.message)
