import os
import random
import shutil
from tqdm import tqdm

source_folder = "/media/hdd3/neo/results_bma_v4_regions_pooled"
output_folder = "/media/hdd3/neo/results_bma_v4_regions_pooled_subsampled"
num = 5000

os.makedirs(output_folder, exist_ok=True)

# for all the image files in the source folder, create a list of the image files
# then randomly subsample N images from the list and copy them to the output folder
# the output folder should contain N images

# get a list of all the images in the source folder
image_files = [
    f
    for f in os.listdir(source_folder)
    if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"))
]

# randomly subsample without replacement N images from the list
subsampled_images = random.sample(image_files, num)

# copy the subsampled images to the output folder
for image in tqdm(subsampled_images, desc="Copying Images"):
    shutil.copy2(os.path.join(source_folder, image), os.path.join(output_folder, image))
