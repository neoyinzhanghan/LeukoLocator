import os
import openslide
from LL.vision.processing import read_with_timeout
from pathlib import Path
from tqdm import tqdm

wsi_dir = "/pesgisipth/NDPI"
save_dir = "/media/hdd3/neo/topviews"
log_dir = "/media/hdd3/neo/topviews/extract_logs"

# get a list of .ndpi files in wsi_dir whose file name stem starts with H or S
wsi_paths = [
    os.path.join(wsi_dir, wsi_fname)
    for wsi_fname in os.listdir(wsi_dir)
    if Path(wsi_fname).suffix == ".ndpi" and Path(wsi_fname).stem[0] in ["H", "S"]
]

num_to_skip = 1
num_processed = 0


def extract_top_view(wsi_path):
    stem = Path(wsi_path).stem

    try:
        print("Processing: " + wsi_path)
        print("Opening slide ... ")
        wsi = openslide.OpenSlide(wsi_path)
        print("Finished opening slide ... ")

        top_level = len(wsi.level_dimensions) - 1

        print("Extracting view ... ")
        top_view = read_with_timeout(
            wsi, (0, 0), top_level, wsi.level_dimensions[top_level]
        )
        # top_view = wsi.read_region((0, 0), top_level, wsi.level_dimensions[top_level])
        print("Finished extracting view ... ")

        print("Saving topview ...")
        # save the topview as a jpg file in the save_dir using the same filename stem as the wsi
        top_view.save(os.path.join(save_dir, stem + ".jpg"))
        print("Finished saving topview ...")

        print("Closing slide ... ")
        wsi.close()
        print("Finished closing slide ... ")

    except Exception as e:
        # write the error as a txt file in log_dir using the same filename stem as the wsi
        with open(os.path.join(log_dir, stem + ".txt"), "w") as f:
            f.write(str(e))


for wsi_path in tqdm(wsi_paths, desc="Extracting top views"):
    if num_processed < num_to_skip:
        num_processed += 1
        continue

    extract_top_view(wsi_path)
