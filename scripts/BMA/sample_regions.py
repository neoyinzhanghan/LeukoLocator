import os
import random
import shutil
import pandas as pd

data_dir = "/media/hdd3/neo/results_bma_v2"
save_dir = "/media/hdd3/neo/bma_region_clf_data_iter_2"

num_images_per_wsi = 20

tracker = {"wsi_name": [], "region_name": []}

chosen_folders = []
# traverse through all folders in data_dir, if the folder name does not contain ERROR, then process the folder
for folder in os.listdir(data_dir):
    if not folder.startswith("ERROR"):
        print("Processing", folder)

        # randomly sample num_images_per_wsi images from the folder/focus_regions/high_mag_unannotated
        high_mag_unannotated_dir = os.path.join(data_dir, folder, "focus_regions", "high_mag_unannotated")

        if os.path.exists(high_mag_unannotated_dir):
            files = os.listdir(high_mag_unannotated_dir)
            if len(files) > num_images_per_wsi:
                chosen_files = random.sample(files, num_images_per_wsi)
            else:
                chosen_files = files

            # copy the chosen_files to the save_dir
            for file in chosen_files:

                # the new filename should be the folder name + the file name
                new_file_name = folder + "_" + file
                save_path = os.path.join(save_dir, new_file_name)
                shutil.copy(os.path.join(high_mag_unannotated_dir, file), save_path)

            # update the tracker
            tracker["wsi_name"].extend([folder] * len(chosen_files))
            tracker["region_name"].extend(chosen_files)

# save the tracker as a csv file
tracker_df = pd.DataFrame(tracker)

tracker_df.to_csv(os.path.join(save_dir, "tracker.csv"), index=False)