import os
import openslide
from LL.vision.processing import read_with_timeout
from tqdm import tqdm
from LL.PBCounter import PBCounter
from pathlib import Path

wsi_dir = "/pesgisipth/NDPI"
tmp_dir = "/media/hdd3/neo/tmp"
save_dir = "/media/hdd3/neo/topviews"
log_dir = "/media/hdd3/neo/topviews/extract_logs"

# get a list of .ndpi files in wsi_dir whose file name stem starts with H or S
wsi_paths = [
    os.path.join(wsi_dir, wsi_fname)
    for wsi_fname in os.listdir(wsi_dir)
    if Path(wsi_fname).suffix == ".ndpi" and Path(wsi_fname).stem[0] in ["H", "S"]
]


def extract_top_view(wsi_path, save_dir=save_dir, log_dir=log_dir):
    # you can get the stem by removing the last 5 characters from the file name (".ndpi")
    stem = os.path.basename(wsi_path)[:-5]

    print(stem)

    try:
        print('Copying slide into tmp_dir')
        # first terminal copy of the wsi to tmp_dir
        os.system(f"cp \"{wsi_path}\" {tmp_dir}")
        print('Done copying slide into tmp_dir')

        # open the wsi in tmp_dir and extract the top view
        new_wsi_path = os.path.join(tmp_dir, os.path.basename(wsi_path))
        wsi = openslide.OpenSlide(new_wsi_path)
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
