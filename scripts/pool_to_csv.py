import os
from tqdm import tqdm
import shutil

positive_dir = "/Users/neo/Documents/Research/DeepHeme/HemeYolo_data/regions_50k_reduced_classified/1"
negative_dir = "/Users/neo/Documents/Research/DeepHeme/HemeYolo_data/regions_50k_reduced_classified/-1"
save_dir = "/Users/neo/Documents/Research/DeepHeme/HemeYolo_data/regions_50k_reduced_classified/leukolocator_region_clf"

# positive dir contains images labelled as 1
# negative dir contains images labelled as 0

# while moving images to the save_dir/images, rename them to 1.jpg, 2.jpg, 3.jpg, etc.
# in the meantime, create one big csv file with two columns image_path, class

# if the save_dir does not exist, create it
if not os.path.exists(save_dir):
    os.mkdir(save_dir)

# create a subdir named images
if not os.path.exists(os.path.join(save_dir, "images")):
    os.mkdir(os.path.join(save_dir, "images"))

# create a csv file
csv_file = open(os.path.join(save_dir, "image_class.csv"), "w")

# iterate through the positive_dir
positives = [fname for fname in os.listdir(positive_dir) if fname.endswith(".jpg")]
for i, image_name in tqdm(enumerate(positives)):
    # get the image_path
    image_path = os.path.join(positive_dir, image_name)

    # use shutil to copy and paste the image to the save_dir/images
    shutil.copy(image_path, os.path.join(save_dir, "images", str(i) + ".jpg"))

    # write the image_path and class to the csv file
    csv_file.write(
        os.path.join(
            "/media/ssd1/neo/leukolocator_regions_clf", "images", str(i) + ".jpg"
        )
        + ",1\n"
    )

# iterate through the negative_dir, make sure to enforce the extension .jpg
negatives = [fname for fname in os.listdir(negative_dir) if fname.endswith(".jpg")]
for i, image_name in tqdm(enumerate(negatives)):
    # get the image_name
    image_path = os.path.join(negative_dir, image_name)

    # use shutil to copy and paste the image to the save_dir/images
    shutil.copy(
        image_path,
        os.path.join(
            save_dir,
            "images",
            str(i + len(os.listdir(positive_dir))) + ".jpg",
        ),
    )
    # write the image_path and class to the csv file
    csv_file.write(
        os.path.join(
            "/media/ssd1/neo/leukolocator_regions_clf",
            "images",
            str(i + len(os.listdir(positive_dir))) + ".jpg",
        )
        + ",0\n"
    )
