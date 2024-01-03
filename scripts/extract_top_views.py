import os
import openslide
from LL.vision.processing import read_with_timeout
from tqdm import tqdm
from pathlib import Path

wsi_dir = "/pesgisipth/NDPI"
save_dir = "/media/hdd3/neo/topviews"
tmp_dir = "/media/hdd3/neo/tmp"
log_dir = "/media/hdd3/neo/topviews/extract_logs"

# get a list of .ndpi files in wsi_dir whose file name stem starts with H or S
wsi_paths = [
    os.path.join(wsi_dir, wsi_fname)
    for wsi_fname in os.listdir(wsi_dir)
    if Path(wsi_fname).suffix == ".ndpi" and Path(wsi_fname).stem[0] in ["H", "S"]
]


def extract_top_view(wsi_path, save_dir=save_dir, log_dir=log_dir):
    # you can get the stem by removing the last 5 characters from the file name (".ndpi")
    stem = Path(wsi_path).stem[:-5]

    print("Copying wsi to tmp_dir")
    # create a symbolic link to the wsi in tmp_dir
    os.system(f'sudo ln -s "{wsi_path}" {tmp_dir}')

    # tmp_dir should contain only one file, the wsi
    assert len(os.listdir(tmp_dir)) == 1

    tmp_path = os.path.join(tmp_dir, os.listdir(tmp_dir)[0])
    print(stem)

    print("Extracting top view")
    try:
        # open the wsi in tmp_dir and extract the top view
        wsi = openslide.OpenSlide(tmp_path)
        toplevel = wsi.level_count - 1
        topview = read_with_timeout(
            wsi=wsi,
            location=(0, 0),
            level=toplevel,
            dimensions=wsi.level_dimensions[toplevel],
        )
        topview.save(os.path.join(save_dir, stem + ".jpg"))
        wsi.close()
    except Exception as e:
        # write the error as a txt file in log_dir using the same filename stem as the wsi
        with open(os.path.join(log_dir, stem + ".txt"), "w") as f:
            f.write(str(e))

    print("Removing wsi from tmp_dir")
    # remove the wsi from tmp_dir
    os.system(f'sudo rm "{tmp_path}"')


for wsi_path in tqdm(wsi_paths):
    extract_top_view(wsi_path)
