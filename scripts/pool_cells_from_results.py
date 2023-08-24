from WCW.resources.assumptions import *
import os
import shutil
from tqdm import tqdm

results_path = "/media/hdd3/neo/results"
save_path = "/media/hdd3/neo/cells_pooled"

# traverse through all folders in results_path
# each folder contains folders named in the list cellnames
# for each such folder, copy all the images there to to the save_path

# get a list of subfolders in results_path
subfolders = [f.path for f in os.scandir(
    results_path) if f.is_dir()]

# traverse through the subfolders
for subfolder in tqdm(subfolders, desc="Saving images"):

    # # create the subfolder in save_path with the same basename
    # save_subfolder = os.path.join(save_path, os.path.basename(subfolder))

    # if not os.path.exists(save_subfolder):
    #     os.mkdir(save_subfolder)

    for cellname in cellnames:

        subsubfolder = os.path.join(subfolder, cellname)

        # if the subsubfolder exists
        if os.path.exists(subsubfolder):

            # get a list of image files in the subsubfolder
            image_files = [f.path for f in os.scandir(
                subsubfolder) if f.is_file()]

            # traverse through the image files
            for image_file in image_files:

                # copy the image file to the save_path
                shutil.copy(image_file, save_path)
