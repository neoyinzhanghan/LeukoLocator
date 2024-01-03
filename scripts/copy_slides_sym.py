import os
from pathlib import Path

# symbolically copy slides from one directory to another
wsi_dir = "/pesgisipth/NDPI"
save_dir = "/media/hdd3/neo/AllSlides"

os.makedirs(save_dir, exist_ok=True)

# for each file in wsi_dir that ends with .ndpi and starts with H or S,
for wsi_fname in os.listdir(wsi_dir):
    if Path(wsi_fname).suffix == ".ndpi" and Path(wsi_fname).stem[0] in ["H", "S"]:
        # sudo copy and duplicate the file in save_dir, DO NOT use symbolic link
        os.system(f"sudo cp -n {os.path.join(wsi_dir, wsi_fname)} {save_dir}")
