from LL.resources.PBassumptions import dump_dir
import os
import pandas as pd
from tqdm import tqdm

# in dump dir, fo into each folder whose name does not start with ERROR
# go into the cells subfolder, there is a csv file named cell_info.csv
# add a column named slide, whose value is the name of the folder
# pool all the csv files into one csv file
# save it in the dump dir

# get the list of folders in dump dir
folders = os.listdir(dump_dir)

# remove the folders whose name starts with ERROR
folders = [folder for folder in folders if not folder.startswith("ERROR")]

# create a list of dataframes
dfs = []

# traverse through the folders
for folder in tqdm(folders, desc="Processing folders"):
    # check if folder is a directory
    if not os.path.isdir(os.path.join(dump_dir, folder)):
        continue

    # get the path to the csv file
    csv_path = os.path.join(dump_dir, folder, "cells", "cells_info.csv")

    # read the csv file as a dataframe
    df = pd.read_csv(csv_path)

    # add a column named slide, whose value is the name of the folder
    df["slide"] = folder

    # add the dataframe to the list of dataframes
    dfs.append(df)

# concatenate the dataframes
df = pd.concat(dfs)

# save the dataframe as a csv file
save_path = os.path.join(dump_dir, "all_cells_info.csv")

df.to_csv(save_path, index=False)
