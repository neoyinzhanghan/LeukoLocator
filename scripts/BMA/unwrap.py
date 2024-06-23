import os
import shutil
from tqdm import tqdm

data_dir = "/media/hdd2/neo/BMA_Normal_lite"

# move all the files in the subfolders of data_dir to the data_dir
subfolders = [
    f.path
    for f in os.scandir(data_dir)
    if f.is_dir() and not f.name.startswith("ERROR_")
]

for subfolder in tqdm(subfolders, desc="Moving Files"):
    for f in os.scandir(subfolder):
        shutil.move(f.path, os.path.join(data_dir, f.name))

# remove the subfolders
for subfolder in subfolders:
    shutil.rmtree(subfolder)