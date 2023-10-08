from LL.resources.assumptions import *
import os
import shutil
from tqdm import tqdm
import random

results_path = "/media/hdd3/neo/results"
save_path = "/media/hdd3/neo/cells_pooled"
train_prop = 0.9

# traverse through all folders in results_path
# each folder contains folders named in the list cellnames
# for each such folder, copy all the images there to to the save_path

# get a list of subfolders in results_path
subfolders = [f.path for f in os.scandir(
    results_path) if f.is_dir()]

# create a subfolder in save_path named train and test
train_path = os.path.join(save_path, 'train')
test_path = os.path.join(save_path, 'test')

if not os.path.exists(train_path):
    os.mkdir(train_path)

if not os.path.exists(test_path):
    os.mkdir(test_path)

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

                # with probability train_prop, copy the image file to the train_path, else copy it to the test_path
                if random.random() < train_prop:
                    # copy the image file to the train_path
                    shutil.copy(image_file, train_path)
                else:
                    # copy the image file to the test_path
                    shutil.copy(image_file, test_path)
