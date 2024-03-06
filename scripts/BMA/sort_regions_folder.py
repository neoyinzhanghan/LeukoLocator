import os
import pandas as pd
from tqdm import tqdm

regions_dir = "/Users/neo/Documents/Research/MODELS/results_bma_v4_regions_pooled_subsampled"
plot_dir = "/Users/neo/Documents/Research/MODELS/plots"
column_name = "ResNet_Score_1"
csv_path = os.path.join(regions_dir, "image_metrics.csv")
resnet_path = os.path.join(regions_dir, "resnet_scores.csv")


os.makedirs(plot_dir, exist_ok=True)

# open the image_metrics.csv file, create symbolic links to the images in the regions_dir, make a symbolic link of all the images in regions_dir to the tmp_dir
# the file name should be X_m.jpg where X is the image metric specified in column_name and m is the id of the image in the csv file

# get a list of all the images in the regions_dir
image_files = [f for f in os.listdir(regions_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff'))]

# open the image_metrics.csv file as a pandas dataframe
df = pd.read_csv(csv_path)

# open the resnet_scores.csv file as a pandas dataframe
df_resnet = pd.read_csv(resnet_path)

for image_file in tqdm(image_files, desc="Processing Images"):
    
    # image name is the last part of splitting by _ 
    image_name = image_file.split("_")[-1]

    # get the row of the image in the dataframe
    row = df[df["Image Name"] == image_name]
    resnet_row = df_resnet[df_resnet["Image Name"] == image_name]

    if "ResNet" not in column_name:
        # get the column value of the image
        value = row[column_name].values[0]

        # round value to 2 decimal places
        value = round(value, 2)
    else:
        value = resnet_row[column_name].values[0]

        # round value to 2 decimal places
        value = round(value, 2)

    # new image name is value + _ + image_name
    new_image_name = f"{value}_{image_name}"

    # rename the image file to the new image name
    os.rename(os.path.join(regions_dir, image_file), os.path.join(regions_dir, new_image_name))