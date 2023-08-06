####################################################################################################
# Imports ##########################################################################################
####################################################################################################

# Outside imports ##################################################################################`
import numpy as np
import pandas as pd
import statsmodels.api as sm

# Within package imports ###########################################################################
from assumptions import *


def last_min_before_last_max(local_minima, local_maxima, last_n=1):
    """Returns the last local minimum before the last local maximum.
    This is a computation needed for background removal. """

    if not local_minima:
        raise ValueError("last_min_before_last_max: local_minima is empty")
        # print("UserWarning: last_min_before_last_max: local_minima is empty, default value 255 is returned")
        # return 255

    # if last_n is larger than the length of local_maxima, then reduce it by 1 until it is smaller than the length of local_maxima
    while last_n > len(local_maxima):
        last_n -= 1

    if last_n == 0:
        raise ValueError("last_min_before_last_max: last_n is 0")
        # print("UserWarning: last_min_before_last_max: last_n is 0, default value 255 is returned")
        # return 255

    for i in range(len(local_minima)-1, -1, -1):
        if local_minima[i] < local_maxima[-last_n]:
            return local_minima[i]

    raise ValueError(
        "last_min_before_last_max: no local minimum is found before the last_n local maximum")


def first_min_after_first_max(local_minima, local_maxima, first_n=2):
    """Returns the first local minimum after the first local maximum. 
    This is a computation needed for obstructor removal. """

    if not local_minima:
        raise ValueError("first_min_after_first_max: local_minima is empty")
        # print("UserWarning: first_min_after_first_max: local_minima is empty, default value 0 is returned.")
        # return 0

    # if first_n is larger than the length of local_maxima, then reduce it by 1 until it is smaller than the length of local_maxima
    while first_n > len(local_maxima):
        first_n -= 1

    if first_n == 0:
        raise ValueError("first_min_after_first_max: first_n is 0")
        # print("UserWarning: first_min_after_first_max: first_n is 0, default value 0 is returned.")
        # return 0

    for i in range(len(local_minima)):
        if local_minima[i] > local_maxima[first_n-1]:
            return local_minima[i]

    raise ValueError(
        "first_min_after_first_max: no local minimum is found after the first_n local maximum")


def focus_region_filtering(focus_regions, min_VoL=min_VoL, min_WMP=min_WMP, max_WMP=max_WMP):
    """ Filter out the focus regions that do not satisfy the VoL and WMP requirements. 
    And then perform a linear regression based outlier removal on the remaining focus regions. """

    # create a dataframe and a list, each focus_region is given a unique id, and the VoL and WMP are recorded in the dataframe along with the id
    focus_regions_df = pd.DataFrame(
        columns=['id', 'VoL', 'WMP'])

    # create a list of focus_region objects
    focus_regions_list = []

    for i in range(len(focus_regions)):
        focus_regions_list.append(focus_regions[i])

        # use concat to add a row to the dataframe
        focus_regions_df = pd.concat([focus_regions_df, pd.DataFrame(
            [[i, focus_regions[i].VoL, focus_regions[i].WMP]], columns=['id', 'VoL', 'WMP'])])

    # filter out the focus regions that do not satisfy the VoL and WMP requirements
    focus_regions_df = focus_regions_df[(focus_regions_df['VoL'] >= min_VoL) & (
        focus_regions_df['WMP'] >= min_WMP) & (focus_regions_df['WMP'] <= max_WMP)]

    # Linear regression on remaining data
    focus_regions_df["VoL / (White Mask Proportion)^2"] = focus_regions_df["VoL"] / \
        (focus_regions_df["White Mask Proportion"] ** 2)

    X = focus_regions_df["White Mask Proportion"]
    X = sm.add_constant(X)
    y = focus_regions_df["VoL / (White Mask Proportion)^2"]

    model = sm.OLS(y, X).fit()

    residuals = y - model.predict(X)
    std_resid = np.std(residuals)
    mean_resid = np.mean(residuals)

    # Define inliers based on residuals
    inlier_mask = (residuals >= mean_resid - focus_region_outlier_tolerance *
                   std_resid) & (residuals <= mean_resid + focus_region_outlier_tolerance * std_resid)

    # Filter out outliers
    focus_regions_df = focus_regions_df[inlier_mask]

    # Return the focus regions that are not filtered out as a list
    return [focus_regions_list[i] for i in focus_regions_df['id'].tolist()]