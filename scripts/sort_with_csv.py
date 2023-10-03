import os
import shutil
from tqdm import tqdm

csv_fpath = "/Users/neo/Documents/Research/DeepHeme/HemeYolo_data/region_clf.csv"
images_dir = "/Users/neo/Documents/Research/DeepHeme/HemeYolo_data/regions_50k_reduced"
save_dir = "/Users/neo/Documents/Research/DeepHeme/HemeYolo_data/regions_50k_reduced_classified"

# read the csv file, it should have only two columns -- image_name, prob
# however the image_name contains spaces and commas, so we need to manually parse it, only divide each line by the last comma

# create a dictionary with key as image_name and value as prob
image_prob_dict = {}
with open(csv_fpath, "r") as csv_file:
    for line in csv_file:
        # get the image_name
        image_name = line.rsplit(",", 1)[0]
        # get the prob
        prob = line.rsplit(",", 1)[1]
        # add to the dictionary
        image_prob_dict[image_name] = prob

# find the threshold on prob such that 50% of the images are above the threshold
# sort the images by prob
sorted_images = sorted(image_prob_dict.items(), key=lambda x: x[1], reverse=True)

# get the threshold
threshold = sorted_images[int(len(sorted_images) * 0.5)][1]

# create a folder for each class
if not os.path.exists(save_dir):
    os.mkdir(save_dir)

for i in range(2):
    if not os.path.exists(os.path.join(save_dir, str(i))):
        os.mkdir(os.path.join(save_dir, str(i)))

# iterate through the images_dir
for image_name in tqdm(os.listdir(images_dir)):
    # make sure the image_name is in the dictionary
    if image_name in image_prob_dict:
        # get the prob
        prob = image_prob_dict[image_name]
        # get the class
        class_ = 1 if prob > threshold else 0
        # copy the image to the corresponding folder
        shutil.copy(
            os.path.join(images_dir, image_name),
            os.path.join(save_dir, str(class_), image_name),
        )
