import os
from tqdm import tqdm

results_dir = "/media/hdd3/neo/results_bma_aml_v3"
save_dir = "/media/hdd3/neo/results_bma_aml_v3_cleaned"

os.makedirs(save_dir, exist_ok=True)

# get a list of all the subfolders in the results directory
subfolders = [f.path for f in os.scandir(results_dir) if f.is_dir()]

# get a list of all the subfolders in the results directory that does not start with "ERROR"
subfolders = [f for f in subfolders if not f.split("/")[-1].startswith("ERROR")]


# copy all the subfolders to the save directory recursively all the files in the subfolders
for subfolder in tqdm(subfolders, desc="Copying subfolders"):
    os.system(f"cp -r \'{subfolder}\' \'{save_dir}\'")

print("Done!")
