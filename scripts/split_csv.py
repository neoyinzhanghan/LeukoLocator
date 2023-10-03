import random
import pandas as pd
from tqdm import tqdm

csv_path = "/Users/neo/Documents/Research/DeepHeme/HemeYolo_data/regions_50k_reduced_classified/leukolocator_region_clf/image_class.csv"

# read the csv file, input has two columns, fpath, class
# make a new csv file with three columns: fpath, class, split
# split must be either train, val, or test
# the split must be 80/10/10 created randomly

# create a pandas dataframe with three columns
df = []

# for each row in the csv file, randomly assign a split with 80/10/10 probability
with open(csv_path, "r") as csv_file:
    for line in tqdm(csv_file):
        # get the fpath
        fpath = line.split(",")[0]
        # get the class
        class_ = line.split(",")[1]
        # get the split
        split = random.choices(["train", "val", "test"], weights=[80, 10, 10])[0]
        # add a dictionary to the dataframe list
        df.append({"fpath": fpath, "class": class_, "split": split})

# create a pandas dataframe
df = pd.DataFrame(df)

# save the dataframe to a csv file at "/Users/neo/Documents/Research/DeepHeme/HemeYolo_data/regions_50k_reduced_classified/leukolocator_region_clf/image_class_split.csv"
df.to_csv(
    "/Users/neo/Documents/Research/DeepHeme/HemeYolo_data/regions_50k_reduced_classified/leukolocator_region_clf/image_class_split.csv",
    index=False,
)
