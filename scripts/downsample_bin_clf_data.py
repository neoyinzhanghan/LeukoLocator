import os
import shutil
from tqdm import tqdm
from PIL import Image

input_dir = "/Users/neo/Documents/Research/DeepHeme/HemeYolo_data/PB_regions_10k"

save_dir = '/Users/neo/Documents/Research/DeepHeme/HemeYolo_data/PB_regions_10k_256'

# go through all the image files in input_dir downsample them to 256x256 and save them in save_dir in the same folder structure
# ignore all the non-image files

# get a list of subfolders in input_dir
subfolders = [f.path for f in os.scandir(
    input_dir) if f.is_dir()]

# traverse through the subfolders
for subfolder in tqdm(subfolders, desc="Downsampling images"):

    # create the subfolder in save_dir with the same basename
    save_subfolder = os.path.join(save_dir, os.path.basename(subfolder))

    if not os.path.exists(save_subfolder):
        os.mkdir(save_subfolder)

    # get a list of image files in the subfolder
    image_files = [f.path for f in os.scandir(
        subfolder) if f.is_file()]

    # traverse through the image files
    for image_file in tqdm(image_files):

        # ignore the non-image files
        if not image_file.endswith('.jpg'):
            continue

        # open the image
        image = Image.open(image_file)

        # resize the image
        image = image.resize((256, 256))

        # save the image
        image.save(os.path.join(save_subfolder, os.path.basename(image_file)))