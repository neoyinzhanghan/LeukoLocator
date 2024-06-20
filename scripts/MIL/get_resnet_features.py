import ray

from LL.resources.BMAassumptions import *
from LL.brain.HemeLabelLightningManager import *
from LL.brain.utils import *
from ray.exceptions import RayTaskError
from tqdm import tqdm

# dump_dir is the source of all the data
# each directory in dump_dir whose name does not start with "ERROR" is a WSI folder
# each WSI folder has a subdirectory called "cells"
# each cells folder contains a bunch of subdirectories, each of which is a cell type and contains a bunch of images in .jpg format
# get the list of all the cell image paths

dump_dir = "/media/hdd3/neo/resultsv5"

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

ray.shutdown()
# ray.init(num_cpus=num_cpus, num_gpus=num_gpus)
ray.init()

list_of_batches = create_list_of_batches_from_list(
    cell_image_paths, cell_clf_batch_size
)

task_managers = [
    HemeLabelLightningManager.remote(HemeLabel_ckpt_path) for _ in range(num_labellers)
]

tasks = {}

for i, batch in enumerate(list_of_batches):
    manager = task_managers[i % num_labellers]
    task = manager.async_save_wbc_image_feature_batch.remote(batch)
    tasks[task] = batch

with tqdm(
    total=len(cell_image_paths), desc="Classifying WBCs & extracting features"
) as pbar:
    while tasks:
        done_ids, _ = ray.wait(list(tasks.keys()))

        for done_id in done_ids:
            try:
                batch = ray.get(done_id)
                for wbc_candidate in batch:
                    pbar.update()

            except RayTaskError as e:
                print(f"Task for WBC candidate {tasks[done_id]} failed with error: {e}")

            del tasks[done_id]

ray.shutdown()
