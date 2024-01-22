import pandas as pd
from LL.resources.assumptions import *


csv_path = "/Users/neo/Documents/Research/DeepHeme/LLResults/LLCKPTS/tmp/conformal_data_cell_info_with_scores.csv"
df = pd.read_csv(csv_path)

# remove the column named fpath

df = df.drop(columns=["fpath"])

# the abnormal column is either 0 or 1, change it to true or false

df["abnormal"] = df["abnormal"].apply(lambda x: True if x == 1 else False)

# for the column with names in the list cellnames, add prob_ in front of the name, for example, M5 -> prob_M5

for cellname in cellnames:
    df.rename(columns={cellname: "prob_" + cellname}, inplace=True)

save_path = "/Users/neo/Documents/Research/DeepHeme/LLResults/LLCKPTS/tmp/conformal_data_cell_info_with_scores_final.csv"

df.to_csv(save_path, index=False)
