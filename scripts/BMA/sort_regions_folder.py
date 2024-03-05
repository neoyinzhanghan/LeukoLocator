import os
import pandas as pd
from tqdm import tqdm

regions_dir = "/Users/neo/Documents/Research/MODELS/results_bma_v4_regions_pooled"
tmp_dir = "/Users/neo/Documents/Research/MODELS/sorted"
column_name = "RBI_2"
csv_path = os.path.join(regions_dir, "image_metrics.csv")
resnet_path = os.path.join(regions_dir, "resnet_scores.csv")

# open the image_metrics.csv file, create symbolic links to the images in the regions_dir, make a symbolic link of all the images in regions_dir to the tmp_dir
# the new file name should be X_m.jpg where X is the image metric specified in column_name and m is the id of the image in the csv file

# open the image_metrics.csv file, traverse though all images in regions_dir and look for the corresponding row in the csv file
# if the image is found in the csv file, create a symbolic link to the image in the tmp_dir
# the new file name should be X_m.jpg where X is the image metric specified in column_name and m is the id of the image in the csv file

# get a list of all the images in the regions_dir
image_files = [f for f in os.listdir(regions_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff'))]

# open the image_metrics.csv file as a pandas dataframe
df = pd.read_csv(csv_path)

# open the resnet_scores.csv file as a pandas dataframe
df_resnet = pd.read_csv(resnet_path)

# create a symbolic link of all the images in regions_dir to the tmp_dir
for image_file in tqdm(image_files, desc="Creating symbolic links"):
    if "ResNet" not in column_name:
        src_path = os.path.join(regions_dir, image_file)

        new_file_name = f"{df.loc[df['Image Name'] == image_file][column_name].values[0]}_{image_file}"
        dst_path = os.path.join(tmp_dir, new_file_name)
        os.symlink(src_path, dst_path)
    
    else:
        src_path = os.path.join(regions_dir, image_file)

        new_file_name = f"{df_resnet.loc[df_resnet['Image Name'] == image_file][column_name].values[0]}_{image_file}"
        dst_path = os.path.join(tmp_dir, new_file_name)
        os.symlink(src_path, dst_path)