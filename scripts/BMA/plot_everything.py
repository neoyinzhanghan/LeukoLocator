import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from tqdm import tqdm

df_path = "/Users/neo/Documents/Research/MODELS/results_bma_v4_regions_pooled/image_metrics.csv"
save_dir = "/Users/neo/Documents/Research/MODELS/PLOTS_results_bma_v4_regions_pooled"

os.makedirs(save_dir, exist_ok=True)

# plot a kernel density of every column in the dataframe
# plot a two columns scatter plot between every pair of columns in the dataframe
# save the plots to the save_dir using the column names as the file names or column1_column2 for the scatter plots

# open the dataframe
df = pd.read_csv(df_path)

# make sure all columns are numeric
for column in df.columns:
    df[column] = pd.to_numeric(df[column], errors='coerce')

# delete the Image Name column, and all columns with name containing "ResNet"
df = df.drop(columns=["Image Name"])
df = df[df.columns.drop(list(df.filter(regex='ResNet')))]

# get the columns of the dataframe
columns = df.columns

# plot a kernel density of every column in the dataframe
for column in tqdm(columns, desc="Processing Individual Columns"):
    # create a kde plot
    sns.kdeplot(df[column], shade=True)
    plt.title(f"{column} Kernel Density Estimate")
    plt.xlabel(column)
    plt.ylabel("Density")
    plt.savefig(os.path.join(save_dir, f"{column}_kde.png"))
    plt.close()

pairs = []
for i in range(len(columns)):
    for j in range(i + 1, len(columns)):
        pairs.append((columns[i], columns[j]))

# plot a two columns scatter plot between every pair of columns in the dataframe
for pair in tqdm(pairs, desc="Processing Column Pairs"):
    # create a scatter plot
    sns.scatterplot(data=df, x=pair[0], y=pair[1])
    plt.title(f"{pair[0]} vs {pair[1]}")
    plt.xlabel(pair[0])
    plt.ylabel(pair[1])
    plt.savefig(os.path.join(save_dir, f"{pair[0]}_{pair[1]}_scatter.png"))
    plt.close()