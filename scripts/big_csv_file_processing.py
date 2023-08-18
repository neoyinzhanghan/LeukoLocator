import pandas as pd
from WCW.brain.regex import *
from tqdm import tqdm
import os

csv_path = "/Users/neo/Documents/Research/results/results/PB_annotations_filtered_processed.csv"
save_dir = "/Users/neo/Documents/Research/results/results/"


PB_annotations_df_processed = pd.read_csv(csv_path)

# create a new column named is_rtf
is_rtf = [False] * len(PB_annotations_df_processed)
# create a new column named text_data_final_plain
text_data_final_plain = ['N/A'] * len(PB_annotations_df_processed)
# create a new column named PB_text_data_final
PB_text_data_final = ['N/A'] * len(PB_annotations_df_processed)

# traverse through the rows of the dataframe
for i in tqdm(range(len(PB_annotations_df_processed))):

    try:
        # get the text_data_final
        text_data_final = PB_annotations_df_processed['text_data_final'][i]

        # if the text_data_final contains the string "RTF", then set is_rtf to True
        if is_rtf_string(text_data_final):
            is_rtf[i] = True
            text_data_final_plain[i] = rtf_to_text(text_data_final)
        else:
            text_data_final_plain[i] = text_data_final

        PB_text_data_final[i] = extract_peripheral_blood_text_chunk(
            text_data_final_plain[i])

    except Exception as e:
        print(e)

        is_rtf[i] = 'ERROR'
        text_data_final_plain[i] = 'ERROR'
        PB_text_data_final[i] = 'ERROR'

# add the is_rtf column to the dataframe
PB_annotations_df_processed['is_rtf'] = is_rtf
# add the text_data_final_plain column to the dataframe
PB_annotations_df_processed['text_data_final_plain'] = text_data_final_plain
# add the PB_text_data_final column to the dataframe
PB_annotations_df_processed['PB_text_data_final'] = PB_text_data_final

# save the dataframe as a csv file in the save_dir with file name PB_annotations_final.csv
PB_annotations_df_processed.to_csv(os.path.join(
    save_dir, "PB_annotations_final.csv"), index=False)
