import os
import csv
from tqdm import tqdm

regions_dir = "/media/hdd3/neo/results_bma_v4_regions_pooled"
tmp_dir = ""
column_name = "RBI_2"
csv_path = os.path.join(regions_dir, "image_metrics.csv")

# open the image_metrics.csv file, create symbolic links to the images in the regions_dir, make a symbolic link of all the images in regions_dir to the tmp_dir
# the new file name should be X_m.jpg where X is the image metric specified in column_name and m is the id of the image in the csv file

# open the image_metrics.csv file
with open(csv_path, 'r') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in tqdm(reader, desc="Creating Symbolic Links"):
        image_name = row['Image Name'] # might not be image name
        image_metric = row[column_name]
        new_file_name = f"{image_metric}_{image_name}"
        new_file_path = os.path.join(tmp_dir, new_file_name)
        os.symlink(os.path.join(regions_dir, image_name), new_file_path)
        print(f"Created symbolic link {new_file_path}")
        # do something with the new_file_path