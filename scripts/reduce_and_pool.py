import os
from PIL import Image
from tqdm import tqdm

input_dir = "/Users/neo/Documents/Research/DeepHeme/HemeYolo_data/sampled_focus_regions_to_annotate"
output_dir = (
    "/Users/neo/Documents/Research/DeepHeme/HemeYolo_data/focus_regions_50k"
)


if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# the input_dir contains a bunch of folders each containing a bunch of images
# take each image and reduce it to 256x256 and save it to the output_dir as jpg

for folder in tqdm(os.listdir(input_dir)):
    # make sure the folder is a folder
    if not os.path.isdir(os.path.join(input_dir, folder)):
        continue
    # for each image in folder, make sure the extension is jpg or png
    for image in os.listdir(os.path.join(input_dir, folder, "focus_regions")):
        if not image.endswith(".jpg") and not image.endswith(".png"):
            continue
        # open the image
        im = Image.open(os.path.join(input_dir, folder, "focus_regions", image))
        # resize it to 256x256
        # im = im.resize((256, 256))
        # save it to output_dir
        # the file name should be concatenated in the folder_img_name

        # get the folder_img_name
        folder_img_name = folder + "_" + image

        # save it to output_dir
        im.save(os.path.join(output_dir, folder_img_name))
