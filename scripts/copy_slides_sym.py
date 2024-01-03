import os
from pathlib import Path

# symbolically copy slides from one directory to another
wsi_dir = "pesgisipth/NDPI"
save_dir = "/media/hdd3/neo/AllSlidesSym"

os.makedirs(save_dir, exist_ok=True)

# for each file in wsi_dir that ends with .ndpi and starts with H or S, copy via symbolic link to save_dir
for wsi_fname in os.listdir(wsi_dir):
    if Path(wsi_fname).suffix == ".ndpi" and Path(wsi_fname).stem[0] in ["H", "S"]:
        os.symlink(os.path.join(wsi_dir, wsi_fname), os.path.join(save_dir, wsi_fname))
