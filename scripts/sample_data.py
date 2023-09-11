import os
import random
import pandas as pd

data_dir = "/media/hdd3/neo/results"
save_dir = "/media/hdd3/neo/sampled/focus/regions"


def save_as_centroids(fpath, save_dir):
    """ Open the csv file at fpath, and it should have columns TL_x, TL_y, BR_x, BR_y,
    these are the coordinates of a bounding box in the image, compute the centroid of the bounding box,
    for each row, and make a new dataframe with just the new coordinates of the centroids, save this dataframe in save_dir. """

    # open the csv file at fpath
    df = pd.read_csv(fpath)
    # compute the centroid of each bounding box
    df["centroid_x"] = (df["TL_x"] + df["BR_x"]) // 2
    df["centroid_y"] = (df["TL_y"] + df["BR_y"]) // 2
    # make a new dataframe with just the centroids
    new_df = df[["centroid_x", "centroid_y"]]
    # save this dataframe in save_dir without column names and without the index
    new_df.to_csv(os.path.join(save_dir, os.path.basename(fpath)),
                  header=False, index=False)


num_per_slide = 100
# for each folder in data_dir
for folder in os.listdir(data_dir):
    # create a folder with the same folder name in save_dir if it doesn't exist
    if not os.path.exists(os.path.join(save_dir, folder)):
        os.makedirs(os.path.join(save_dir, folder))

    # in that new folder create a subfolder called focus_regions and one called annotations
    if not os.path.exists(os.path.join(save_dir, folder, "focus_regions")):
        os.makedirs(os.path.join(save_dir, folder, "focus_regions"))

    if not os.path.exists(os.path.join(save_dir, folder, "annotations")):
        os.makedirs(os.path.join(save_dir, folder, "annotations"))

    # there is a subfolder named focus_regions and one named annotations
    # we want to sample 100 images from the focus_regions folder without replacement and save them in the new folder
    # we also want to copy the corresponding annotations to the new folder
    # we want to do this for each folder in data_dir

    # get the list of images in the focus_regions folder
    focus_regions = os.listdir(os.path.join(data_dir, folder, "focus_regions"))
    # get the list of annotations in the annotations folder
    annotations = os.listdir(os.path.join(data_dir, folder, "annotations"))

    # sample 100 images from the focus_regions folder without replacement
    sampled_focus_regions = random.sample(focus_regions, num_per_slide)
    # find the corresponding annotations, same name but with .csv extension
    sampled_annotations = [os.path.splitext(
        x)[0] + ".csv" for x in sampled_focus_regions]

    # copy the sampled images to the new folder
    for img in sampled_focus_regions:
        os.system("cp {} {}".format(os.path.join(data_dir, folder, "focus_regions", img),
                                    os.path.join(save_dir, folder, "focus_regions", img)))

    # copy the corresponding annotations to the new folder using the save_as_centroids function
    for ann in sampled_annotations:
        save_as_centroids(os.path.join(data_dir, folder, "annotations", ann),
                          os.path.join(save_dir, folder, "annotations"))
