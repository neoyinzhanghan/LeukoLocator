####################################################################################################
# Imports ##########################################################################################
####################################################################################################

# Outside imports ##################################################################################
import os
import pandas as pd
from tqdm import tqdm

# Within package imports ###########################################################################
from WCW.brain.read_annotations import get_PB_annotations_from_csv, get_PB_metadata, NotAnnotatedError

H23_csv_path = "/media/ssd2/clinical_text_data/PathReports_Heme/H23-20230720.csv"
WSI_dir = "/pesgisipth/NDPI"
save_dir = "/home/greg/Documents/neo"

# Get the dataframe of PB annotations
PB_annotations_df = get_PB_annotations_from_csv(H23_csv_path)

# Only keep the rows the processed_date is not empty NaN
PB_annotations_df = PB_annotations_df[~PB_annotations_df['processed_date'].isnull()]

# further subset so that barcode and text_data_final and text_data_clindx are not empty
PB_annotations_df = PB_annotations_df[~PB_annotations_df['barcode'].isnull()]
PB_annotations_df = PB_annotations_df[~PB_annotations_df['text_data_final'].isnull()]
PB_annotations_df = PB_annotations_df[~PB_annotations_df['text_data_clindx'].isnull()]

# save the dataframe as a csv file in the save_dir with file name H23_PB_annotations.csv
PB_annotations_df.to_csv(os.path.join(save_dir, "H23_PB_annotations_filtered.csv"), index=False)

# Get a list of files in WSI_dir that end with .ndpi and start with H23
fnames = [fname for fname in os.listdir(WSI_dir) if fname.endswith(
    ".ndpi") and fname.startswith("H23")]

# the metadata are dictionaries, get them and concatenate them into a pandas dataframe
# use tqdm to show a progress bar

lst = []

for fname in tqdm(fnames):
    try:
        lst.append(get_PB_metadata(fname, PB_annotations_df))
    except NotAnnotatedError:
        print("NotAnnotatedError")
        continue

df_lst = [pd.DataFrame(row, index=[0]) for row in tqdm(lst)]
    
metadata_df = pd.concat(df_lst, ignore_index=True)

# save the dataframe as a csv file in the save_dir with file name H23_PB_metadata.csv
metadata_df.to_csv(os.path.join(save_dir, "H23_PB_metadata.csv"), index=False)
