import os
import sys
import openslide
from LL.vision.processing import read_with_timeout
from tqdm import tqdm
from pathlib import Path

wsi_dir = "/media/hdd4/harry/Slides_repo"
save_dir = "/media/hdd3/neo/topviews"
tmp_dir = "/media/hdd3/neo/tmp"
log_dir = "/media/hdd3/neo/topviews/extract_logs"

print("Finding all .ndpi files in wsi_dir")
# recursively search for all .ndpi files in wsi_dir
wsi_paths = []
for root, dirs, files in os.walk(wsi_dir):
    for file in files:
        if Path(file).suffix == ".ndpi":
            wsi_paths.append(os.path.join(root, file))

print("Found", len(wsi_paths), ".ndpi files")


print("Creating save_dir")
# create save_dir if it does not exist
os.makedirs(save_dir, exist_ok=True)

print("Creating tmp_dir")
# create tmp_dir if it does not exist
os.makedirs(tmp_dir, exist_ok=True)


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
    except KeyboardInterrupt:
        sys.exit()
    except Exception as e:
        # write the error as a txt file in log_dir using the same filename stem as the wsi
        with open(os.path.join(log_dir, stem + ".txt"), "w") as f:
            f.write(str(e))

    print("Removing wsi from tmp_dir")
    # remove the wsi from tmp_dir
    os.system(f'sudo rm "{tmp_path}"')


for wsi_path in tqdm(wsi_paths):
    extract_top_view(wsi_path)
