import os
import openslide
import ray
from LL.vision.processing import read_with_timeout
from pathlib import Path
from tqdm import tqdm
from LL.PBCounter import PBCounter

# wsi_dir = "/pesgisipth/NDPI"
wsi_dir = "/media/hdd3/neo/AllSlidesSym"
save_dir = "/media/hdd3/neo/topviews"
log_dir = "/media/hdd3/neo/topviews/extract_logs"

# get a list of .ndpi files in wsi_dir whose file name stem starts with H or S
wsi_paths = [
    os.path.join(wsi_dir, wsi_fname)
    for wsi_fname in os.listdir(wsi_dir)
    if Path(wsi_fname).suffix == ".ndpi" and Path(wsi_fname).stem[0] in ["H", "S"]
]


def extract_top_view(wsi_path, save_dir=save_dir, log_dir=log_dir):
    stem = Path(wsi_path).stem

    try:
        wsi = openslide.OpenSlide(wsi_path)
        toplevel = wsi.level_count - 1
        topview = read_with_timeout(
            openslide.OpenSlide(wsi_path),
            location=(0, 0),
            level=toplevel,
            dimensions=wsi.level_dimensions[toplevel],
        )
        topview.save(os.path.join(save_dir, stem + ".png"))
        wsi.close()
    except Exception as e:
        # write the error as a txt file in log_dir using the same filename stem as the wsi
        with open(os.path.join(log_dir, stem + ".txt"), "w") as f:
            f.write(str(e))


for wsi_path in tqdm(wsi_paths):
    extract_top_view(wsi_path)
