import os
import pandas as pd
from tqdm import tqdm
import pathlib

data_dir = '/media/hdd3/neo/resultsv5'  # Adjust this to your data directory
save_dir = '/media/hdd3/neo/resultsv5_pooled_cells'  # Adjust this to your save directory
metadata_path = os.path.join(save_dir, 'metadata.csv')

# Ensure save_dir exists
os.makedirs(save_dir, exist_ok=True)

# Initialize a DataFrame to store metadata
metadata_df = pd.DataFrame(columns=['Symbolic_Link', 'Original_Path'])

# Function to handle the symbolic link creation and update metadata DataFrame
def handle_cell_images(class_dir, class_name, metadata_df):
    global link_counter  # Use a global counter for unique link names across classes
    for img_name in tqdm(os.listdir(class_dir), desc=f"Processing {class_name}"):
        src_path = os.path.join(class_dir, img_name)
        dst_dir = os.path.join(save_dir, class_name)
        os.makedirs(dst_dir, exist_ok=True)
        dst_path = os.path.join(dst_dir, str(link_counter))
        os.symlink(src_path, dst_path)
        # Update DataFrame using concat
        new_row = pd.DataFrame({'Symbolic_Link': [dst_path], 'Original_Path': [src_path]})
        metadata_df = pd.concat([metadata_df, new_row], ignore_index=True)
        link_counter += 1
    return metadata_df

link_counter = 1  # Start numbering symbolic links from 1
for folder_name in tqdm(os.listdir(data_dir), desc="Iterating folders"):
    if not folder_name.startswith('ERROR'):
        cells_dir = os.path.join(data_dir, folder_name, 'cells')
        if os.path.isdir(cells_dir):
            for class_name in tqdm(os.listdir(cells_dir), desc=f"Processing cells in {folder_name}"):
                class_dir = os.path.join(cells_dir, class_name)
                if os.path.isdir(class_dir):
                    metadata_df = handle_cell_images(class_dir, class_name, metadata_df)

# Save the DataFrame to a CSV file
metadata_df.to_csv(metadata_path, index=False)
