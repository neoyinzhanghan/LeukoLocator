####################################################################################################
# Imports ###########################################################################################
####################################################################################################

# Outside imports ##################################################################################
import os
import pandas as pd
import ray
import numpy as np
from LL.brain.utils import create_list_of_batches_from_list
from tqdm import tqdm
from ray.exceptions import RayTaskError


# Within package imports ###########################################################################
from LL.communication.visualization import save_hist_KDE_rug_plot
from LL.brain.utils import *
from LL.resources.BMAassumptions import *
from LL.brain.BMARegionClfManager import RegionClfManager
from LL.BMAFocusRegion import save_focus_region_batch

class FocusRegionsTracker:
    """A class representing a focus region tracker object that tracks the metrics, objects, files related to focus region filtering.

    === Class Attributes ===
    - focus_regions_dct : a dictionary mapping focus region indices to FocusRegion objects
    - info_df : a dataframe containing the information of the focus regions

    - final_min_VoL : the final minimum VoL of the focus regions
    - final_min_WMP : the final minimum WMP of the focus regions
    - final_min_conf_thres : the final minimum confidence threshold of the focus regions
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

        # Prepare a list to hold the dictionaries before creating a DataFrame
        new_rows = []

        for focus_region in focus_regions:
            new_rows.append(
                {
                    "idx": focus_region.idx,
                    "coordinate": focus_region.coordinate,
                    "VoL": focus_region.VoL,
                    "peripheral_confidence_score": focus_region.peripheral_confidence_score,
                    "clot_confidence_score": focus_region.clot_confidence_score,
                    "adequate_confidence_score": focus_region.adequate_confidence_score,
                }
            )

        # Convert the list of dictionaries to a DataFrame
        new_rows_df = pd.DataFrame(new_rows)

        self.info_df = new_rows_df

        self.final_min_VoL = None
        # self.final_min_WMP = None
        # self.final_max_WMP = None
        self.final_min_conf_thres = None

    def compute_resnet_confidence(self):
        """ """

        ray.shutdown()
        print("Ray initialization for resnet confidence score")
        ray.init()
        print("Ray initialization for resnet confidence score done")

        region_clf_managers = [
            RegionClfManager.remote(region_clf_ckpt_path)
            for _ in range(num_region_clf_managers)
        ]

        tasks = {}
        new_focus_region_dct = {}

        focus_regions = list(self.focus_regions_dct.values())

        list_of_batches = create_list_of_batches_from_list(
            focus_regions, region_clf_batch_size
        )

        for i, batch in enumerate(list_of_batches):
            manager = region_clf_managers[i % num_region_clf_managers]
            task = manager.async_predict_batch_key_dct.remote(batch)
            tasks[task] = batch

        with tqdm(
            total=len(self.focus_regions_dct), desc="Getting ResNet Confidence Scores"
        ) as pbar:
            while tasks:
                done_ids, _ = ray.wait(list(tasks.keys()))

                for done_id in done_ids:
                    try:
                        results = ray.get(done_id)
                        for k in results:
                            new_focus_region_dct[k] = results[k]

                            pbar.update()

                    except RayTaskError as e:
                        print(
                            f"Task for focus region {tasks[done_id]} failed with error: {e}"
                        )
                    del tasks[done_id]

        ray.shutdown()

        self.focus_regions_dct = new_focus_region_dct

        # add the peripheral_confidence_score, clot_confidence_score, and adequate_confidence_score columns to the info_df
        self.info_df["adequate_confidence_score"] = np.nan

        # update the info_df with the confidence scores
        for idx in self.focus_regions_dct:
            self.info_df.loc[idx, "adequate_confidence_score"] = self.focus_regions_dct[
                idx
            ].adequate_confidence_score

    def get_top_n_focus_regions(self, n=max_num_regions_after_region_clf):
        """Return the top n focus regions with the highest confidence scores."""

        # get the top n focus regions using the info_df and return a list of focus regions idx
        # in descending order of confidence scores

        top_n_idx = self.info_df.sort_values(
            by=["adequate_confidence_score"], ascending=False
        ).head(n)["idx"]

        # add a column called "selected" which is True if the focus region is selected
        self.info_df["selected"] = False
        self.info_df.loc[self.info_df["idx"].isin(top_n_idx), "selected"] = True

        focus_regions = [self.focus_regions_dct[idx] for idx in top_n_idx]

        return focus_regions

    def save_results(self, save_dir):
        """Save the plots of the VoL, and resnet confidence score distributions.
        For both all focus regions in the info_df and the selected focus regions.

        Use save_hist_KDE_rug_plot
        """

        # calculate the min confidence threshold for the selected focus regions
        self.final_min_conf_thres = min(
            self.info_df[self.info_df["selected"]]["adequate_confidence_score"]
        )

        # calculate the min VoL for the selected focus regions
        self.final_min_VoL = min(self.info_df[self.info_df["selected"]]["VoL"])

        # # calculate the min WMP for the selected focus regions
        # self.final_min_WMP = min(self.info_df[self.info_df["selected"]]["WMP"])

        # # calculate the max WMP for the selected focus regions
        # self.final_max_WMP = max(self.info_df[self.info_df["selected"]]["WMP"])

        # save the resnet confidence score distribution plot for all focus regions
        save_hist_KDE_rug_plot(
            df=self.info_df,
            column_name="adequate_confidence_score",
            save_path=os.path.join(
                save_dir,
                "focus_regions",
                "selected_resnet_confidence_score_distribution.png",
            ),
            title="ResNet Confidence Score Distribution for All Focus Regions",
            lines=[self.final_min_conf_thres],
        )

        # save the resnet confidence score distribution plot for selected focus regions
        save_hist_KDE_rug_plot(
            df=self.info_df[self.info_df["selected"]],
            column_name="adequate_confidence_score",
            save_path=os.path.join(
                save_dir,
                "focus_regions",
                "selected_resnet_confidence_score_distribution.png",
            ),
            title="ResNet Confidence Score Distribution for Selected Focus Regions",
            lines=[self.final_min_conf_thres],
        )

        # save the VoL distribution plot for all focus regions
        save_hist_KDE_rug_plot(
            df=self.info_df,
            column_name="VoL",
            save_path=os.path.join(
                save_dir, "focus_regions", "all_VoL_distribution.png"
            ),
            title="VoL Distribution for All Focus Regions",
            lines=[self.final_min_VoL],
        )

        # save the VoL distribution plot for selected focus regions
        save_hist_KDE_rug_plot(
            df=self.info_df[self.info_df["selected"]],
            column_name="VoL",
            save_path=os.path.join(
                save_dir, "focus_regions", "selected_VoL_distribution.png"
            ),
            title="VoL Distribution for Selected Focus Regions",
            lines=[self.final_min_VoL],
        )

        # # save the WMP distribution plot for all focus regions
        # save_hist_KDE_rug_plot(
        #     df=self.info_df,
        #     column_name="WMP",
        #     save_path=os.path.join(
        #         save_dir, "focus_regions", "all_WMP_distribution.png"
        #     ),
        #     title="WMP Distribution for All Focus Regions",
        #     lines=[self.final_min_WMP, self.final_max_WMP],
        # )

        # # save the WMP distribution plot for selected focus regions
        # save_hist_KDE_rug_plot(
        #     df=self.info_df[self.info_df["selected"]],
        #     column_name="WMP",
        #     save_path=os.path.join(
        #         save_dir, "focus_regions", "selected_WMP_distribution.png"
        #     ),
        #     title="WMP Distribution for Selected Focus Regions",
        #     lines=[self.final_min_WMP, self.final_max_WMP],
        # )

        # save the info_df into a csv file
        self.info_df.to_csv(
            os.path.join(save_dir, "focus_regions", "focus_regions_info.csv"),
            index=False,
        )

        # save a csv file containing the following information:
        # - final_min_VoL
        # - final_min_conf_thres
        # - final_max_peripheral_confidence_score
        # - final_min_peripheral_confidence_score
        # - final_max_clot_confidence_score
        # - final_min_clot_confidence_score
        # - average_resnet_confidence_score
        # - average_peripheral_confidence_score
        # - average_clot_confidence_score
        # - average_VoL
        # - average_resnet_confidence_score_selected
        # - average_peripheral_confidence_score_selected
        # - average_clot_confidence_score_selected
        # - average_VoL_selected
        # - sd_resnet_confidence_score
        # - sd_peripheral_confidence_score
        # - sd_clot_confidence_score
        # - sd_VoL
        # - sd_resnet_confidence_score_selected
        # - sd_peripheral_confidence_score_selected
        # - sd_clot_confidence_score_selected
        # - sd_VoL_selected

        # calculate the average resnet confidence score
        average_adequate_confidence_score = np.mean(
            self.info_df["adequate_confidence_score"]
        )

        # calculate the average VoL
        average_VoL = np.mean(self.info_df["VoL"])

        # # calculate the average WMP
        # average_WMP = np.mean(self.info_df["WMP"])

        # calculate the average resnet confidence score for selected focus regions
        average_adequate_confidence_score_selected = np.mean(
            self.info_df[self.info_df["selected"]]["adequate_confidence_score"]
        )

        # calculate the average VoL for selected focus regions
        average_VoL_selected = np.mean(self.info_df[self.info_df["selected"]]["VoL"])

        # # calculate the average WMP for selected focus regions
        # average_WMP_selected = np.mean(self.info_df[self.info_df["selected"]]["WMP"])

        # calculate the sd resnet confidence score
        sd_adequate_confidence_score = np.std(self.info_df["adequate_confidence_score"])

        # calculate the sd VoL
        sd_VoL = np.std(self.info_df["VoL"])

        # # calculate the sd WMP
        # sd_WMP = np.std(self.info_df["WMP"])

        # calculate the sd resnet confidence score for selected focus regions
        sd_adequate_confidence_score_selected = np.std(
            self.info_df[self.info_df["selected"]]["adequate_confidence_score"]
        )

        # calculate the sd VoL for selected focus regions
        sd_VoL_selected = np.std(self.info_df[self.info_df["selected"]]["VoL"])

        # # calculate the sd WMP for selected focus regions
        # sd_WMP_selected = np.std(self.info_df[self.info_df["selected"]]["WMP"])

        # create a dictionary containing the above information
        info_dct = {
            "final_min_VoL": self.final_min_VoL,
            # "final_min_WMP": self.final_min_WMP,
            # "final_max_WMP": self.final_max_WMP,
            "final_min_conf_thres": self.final_min_conf_thres,
            "average_adequate_confidence_score": average_adequate_confidence_score,
            "average_VoL": average_VoL,
            # "average_WMP": average_WMP,
            "average_adequate_confidence_score_selected": average_adequate_confidence_score_selected,
            "average_VoL_selected": average_VoL_selected,
            # "average_WMP_selected": average_WMP_selected,
            "sd_resnet_confidence_score": sd_adequate_confidence_score,
            # "sd_WMP": sd_WMP,
            "sd_resnet_confidence_score_selected": sd_adequate_confidence_score_selected,
            "sd_VoL_selected": sd_VoL_selected,
            # "sd_WMP_selected": sd_WMP_selected,
        }

        # save the dictionary as a csv file each row is a key-value pair
        with open(
            os.path.join(save_dir, "focus_regions", "focus_regions_filtering.csv"), "a"
        ) as f:
            for key in info_dct.keys():
                f.write("%s,%s\n" % (key, info_dct[key]))

    def save_all_focus_regions(self, save_dir):
        """Save the images of all focus regions in the focus_regions/all folder."""

        # create a folder called all in the focus_regions folder
        os.makedirs(
            os.path.join(save_dir, "focus_regions", "peripheral"), exist_ok=True
        )
        os.makedirs(os.path.join(save_dir, "focus_regions", "clot"), exist_ok=True)
        os.makedirs(os.path.join(save_dir, "focus_regions", "adequate"), exist_ok=True)

        focus_regions_lst = list(self.focus_regions_dct.values())
        batches = create_list_of_batches_from_list(focus_regions_lst, batch_size=region_saving_batch_size)

        # create a list of batch

        # List to store references to the async results
        ray.shutdown()
        ray.init()
        save_tasks = []


        for batch in batches:
            # Queue the task
            task = save_focus_region_batch.remote(batch, save_dir)
            save_tasks.append(task)

        pbar = tqdm(total=len(focus_regions_lst), desc="Saving focus regions")  # total should be the number of batches
        while save_tasks:
            # Wait for any of the tasks to complete
            done_ids, save_tasks = ray.wait(save_tasks)
            # Get the outputs of the completed tasks
            outputs = ray.get(done_ids)
            # Update the progress bar for each completed task
            for output in outputs:
                pbar.update(int(output))

        # Wait for all tasks to complete
        ray.get(save_tasks)

        # Shutdown Ray
        ray.shutdown()