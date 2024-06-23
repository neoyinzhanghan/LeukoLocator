import os
import numpy as np
from pathlib import Path
from tqdm import tqdm

data_dir = "/media/hdd2/neo/BMA_Normal"
save_dir = "/media/hdd2/neo/BMA_Normal_lite"
num_slides = 25

# make the save_dir if it does not exist
os.makedirs(save_dir, exist_ok=True)

# gather the path fo all the .ndpi files in the data_dir
ndpi_files = list(Path(data_dir).rglob("*.ndpi"))

# randomly select num_slides slides
selected_slides = np.random.choice(ndpi_files, num_slides, replace=False)

# make a symbolic link to the selected slides in the save_dir
for slide in tqdm(selected_slides, desc="Creating Lite Slide Repo"):
    os.symlink(slide, os.path.join(save_dir, slide.name))
