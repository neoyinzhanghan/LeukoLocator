import os
import random
import shutil

sorted_folder = "/media/hdd3/neo/dump/wbc_candidates_sorted"
save_dir = "/media/hdd3/neo/dump/"

# for each subdirectory in sorted_folder, create a subdirectory in save_dir of the same name
# then copy a random 100 images from sorted_folder to the new subdirectory
for subdir in os.listdir(sorted_folder):
    os.mkdir(os.path.join(save_dir, subdir))
    for file in random.sample(os.listdir(os.path.join(sorted_folder, subdir)), min(100, len(os.listdir(os.path.join(sorted_folder, subdir))))):
        shutil.copy(os.path.join(sorted_folder, subdir, file), os.path.join(save_dir, subdir, file))

