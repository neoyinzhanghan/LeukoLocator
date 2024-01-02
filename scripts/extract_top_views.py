import os
import openslide
from LL.vision.processing import read_with_timeout
from pathlib import Path
from tqdm import tqdm
from LL.PBCounter import PBCounter

wsi_dir = "/pesgisipth/NDPI"
save_dir = "/media/hdd3/neo/topviews"
log_dir = "/media/hdd3/neo/topviews/extract_logs"

# get a list of .ndpi files in wsi_dir whose file name stem starts with H or S
wsi_paths = [
    os.path.join(wsi_dir, wsi_fname)
    for wsi_fname in os.listdir(wsi_dir)
    if Path(wsi_fname).suffix == ".ndpi" and Path(wsi_fname).stem[0] in ["H", "S"]
]


def extract_top_view(wsi_path):
    stem = Path(wsi_path).stem

    try:
        pbc = PBCounter(wsi_path)
        topview = pbc.top_view.image
        topview.save(os.path.join(save_dir, stem + ".jpg"))

    except Exception as e:
        # write the error as a txt file in log_dir using the same filename stem as the wsi
        with open(os.path.join(log_dir, stem + ".txt"), "w") as f:
            f.write(str(e))


for wsi_path in tqdm(wsi_paths, desc="Extracting top views"):
    extract_top_view(wsi_path)
