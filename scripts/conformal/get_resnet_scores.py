import pandas as pd
from tqdm import tqdm
from PIL import Image
from LL.resources.assumptions import *
from LL.brain.HemeLabelManager import model_create, predict_on_cpu

df_path = "/home/greg/Documents/neo/tmp/conformal_data_cell_info.csv"
save_path = "/home/greg/Documents/neo/tmp/conformal_data_cell_info_with_scores.csv"

# for each row, the fpath is the path to an image
# open the image and run it through the model HemeLabel
# the output is a 23-dim vector
# there is a column name list called cellnames
# the 23-dim vector is the prediction score for each cell type
# save the 23-dim vector to a csv file with column names cell_names respectively

print("Loading the model...")
model = model_create(path=HemeLabel_ckpt_path, num_classes=num_classes)

print("Loading the dataframe...")
df = pd.read_csv(df_path)

# create a new column for each cell type
for cellname in cellnames:
    df[cellname] = 0

# create a new column called "cell_id" and set it to be 'ohshoot'
df["cell_id"] = "ohshoot"

for i in tqdm(range(len(df))):
    row = df.loc[i]
    fpath = row["fpath"]
    image = Image.open(fpath)
    prediction = predict_on_cpu(image, model)
    for prediction_score, cellname in zip(prediction, cellnames):
        df.loc[i, cellname] = prediction_score

    # create a new column called "cell_id" and set it to be index i
    df.loc[i, "cell_id"] = i

# save the dataframe
df.to_csv(save_path, index=False)
