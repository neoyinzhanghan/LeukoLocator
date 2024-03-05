import os
import shutil
import csv
from tqdm import tqdm

root_dir = "/media/hdd3/neo/results_bma_v4"  # Set your root directory path here
save_dir = "/media/hdd3/neo/results_bma_v4_regions_pooled"  # Set your save directory path here

os.makedirs(save_dir, exist_ok=True)  # Ensure save_dir exists

# Prepare to write metadata.csv
metadata_file = os.path.join(save_dir, 'metadata.csv')
file_counter = 1  # Start naming files from 1

# Initialize a list to hold all image paths for progress tracking
image_paths = []

# First pass to collect all image paths
for root, dirs, files in os.walk(root_dir):
    if 'focus_regions' in dirs:
        focus_regions_path = os.path.join(root, 'focus_regions')
        if 'high_mag_unannotated' in os.listdir(focus_regions_path):
            high_mag_path = os.path.join(focus_regions_path, 'high_mag_unannotated')
            for image_file in os.listdir(high_mag_path):
                if image_file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff')):
                    image_paths.append(os.path.join(high_mag_path, image_file))

# Open metadata.csv for writing
with open(metadata_file, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['File Number', 'Original Path'])  # Write header

    # Process images with progress tracking
    for image_path in tqdm(image_paths, desc="Copying Images"):
        new_file_name = f"{file_counter}.jpg"  # Assuming all images are converted to jpg for uniformity
        new_file_path = os.path.join(save_dir, new_file_name)
        
        # Copy the image to the new location
        shutil.copy2(image_path, new_file_path)
        
        # Write the mapping to metadata.csv
        writer.writerow([file_counter, image_path])
        file_counter += 1
