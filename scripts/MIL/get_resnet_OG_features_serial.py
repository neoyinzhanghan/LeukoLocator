from LL.resources.BMAassumptions import *
from LL.brain.HemeLabelManagerSerial import *
from LL.brain.utils import *
from tqdm import tqdm

# dump_dir is the source of all the data
# each directory in dump_dir whose name does not start with "ERROR" is a WSI folder
# each WSI folder has a subdirectory called "cells"
# each cells folder contains a bunch of subdirectories, each of which is a cell type and contains a bunch of images in .jpg format
# get the list of all the cell image paths

dump_dir = "/media/hdd1/neo/results_bma_aml_v3_cleaned"

cell_image_paths = []

for wsi_folder in tqdm(os.listdir(dump_dir), desc="Gathering cell image paths"):
    if not wsi_folder.startswith("ERROR") and os.path.isdir(
        os.path.join(dump_dir, wsi_folder)
    ):
        cells_folder = os.path.join(dump_dir, wsi_folder, "cells")
        if os.path.isdir(cells_folder):
            for cell_type in os.listdir(cells_folder):
                if os.path.isdir(os.path.join(cells_folder, cell_type)):
                    cell_type_folder = os.path.join(cells_folder, cell_type)
                    for f in os.listdir(cell_type_folder):
                        if f.endswith(".jpg"):
                            cell_image_paths.append(os.path.join(cell_type_folder, f))

print(f"Found {len(cell_image_paths)} cell images.")

model = model_create(path=HemeLabel_ckpt_path)

for cell_path in tqdm(cell_image_paths, desc="Processing cell images"):

    # the cell_path is of format image_dir/cell_name.jpg
    image_dir = os.path.dirname(cell_path)
    os.makedirs(os.path.join(image_dir, "OG_features"), exist_ok=True)

    # open the image using pil
    image = Image.open(cell_path)

    image_lst = [image]

    # get the predictions
    features = get_features_batch(image_lst, model)

    feature = features[0]

    # make sure the features have shape (d,)
    feature = feature.reshape(-1)

    # save the features as a .pt file in the OG_features folder
    torch.save(
        feature,
        os.path.join(
            image_dir, "OG_features", f"{os.path.basename(cell_path).split('.')[0]}.pt"
        ),
    )
