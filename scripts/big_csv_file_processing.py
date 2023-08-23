import pandas as pd
from WCW.brain.regex import *
from WCW.resources.assumptions import *
from tqdm import tqdm
import os

csv_path = "/Users/neo/Documents/Research/results/final_results/PB_annotations_filtered_processed.csv"
save_dir = "/Users/neo/Documents/Research/results/final_results/"


class TargetError(Exception):

    def __init__(self, message):
        self.message = message


PB_annotations_df_processed = pd.read_csv(csv_path)

# create a new column named is_rtf
is_rtf = [False] * len(PB_annotations_df_processed)
# create a new column named text_data_final_plain
text_data_final_plain = ['N/A'] * len(PB_annotations_df_processed)
# create a new column named PB_text_data_final
PB_text_data_final = ['N/A'] * len(PB_annotations_df_processed)

# create a new column in PB_text_data_final named second_paragraph
PB_annotations_df_processed['second_paragraph'] = [
    'N/A'] * len(PB_annotations_df_processed)

# for each name in PB_final_classes, create an empty column in the dataframe with name + '_label' with value 'N/A'
for name in PB_final_classes:
    PB_annotations_df_processed[name + '_label'] = ['N/A'] * \
        len(PB_annotations_df_processed)

# add a column named ran_without_error which is False for all rows by default
PB_annotations_df_processed['text_processed_without_error'] = [
    False] * len(PB_annotations_df_processed)

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

        PB_text_data_final[i] = remove_unwanted_lines(extract_peripheral_blood_text_chunk(
            text_data_final_plain[i]))

        second_par = extract_second_paragraph(PB_text_data_final[i])
        # PB_annotations_df_processed.loc[i, 'second_paragraph'] = second_par

        print(second_par)

        diff_dict = convert_to_dict(second_par)

        print(diff_dict)

        # traverse through the keys of diff_dict
        for key in diff_dict:
            if key in translate:
                translation = translate[key]
            else:
                translation = 'Other'

            if translation in PB_final_classes:
                PB_annotations_df_processed.loc[i, translation +
                                                '_label'] = diff_dict[key]

        PB_annotations_df_processed.loc[i, 'text_processed_without_error'] = True

    except Exception as e:

        is_rtf[i] = 'ERROR'
        text_data_final_plain[i] = 'ERROR'
        PB_text_data_final[i] = 'ERROR'

        for name in PB_final_classes:
            PB_annotations_df_processed.loc[i, name + '_label'] = 'ERROR'

# add the is_rtf column to the dataframe
PB_annotations_df_processed['is_rtf'] = is_rtf
# add the text_data_final_plain column to the dataframe
PB_annotations_df_processed['text_data_final_plain'] = text_data_final_plain
# add the PB_text_data_final column to the dataframe
PB_annotations_df_processed['PB_text_data_final'] = PB_text_data_final

# Convert the values in the columns of PB_final_classes to either float or NaN
for name in PB_final_classes:
    PB_annotations_df_processed[name] = pd.to_numeric(
        PB_annotations_df_processed[name], errors='coerce')

# for the columns in PB_final_classes, if the value is a float, round it to 4 decimal places and multiply by 100
for name in PB_final_classes:
    PB_annotations_df_processed[name] = PB_annotations_df_processed[name].apply(
        lambda x: round(x * 100, 4) if isinstance(x, float) else x)

# now create a new dataframe with only the columns that we need
columns_we_need = ['wsi_fname', 'is_rtf', 'text_processed_without_error'] + \
    PB_final_classes + [name + '_label' for name in PB_final_classes] + \
    ['num_wbcs_scanned', 'num_focus_regions_scanned', 'processing_time']

# save the dataframe as a csv file in the save_dir with file name PB_annotations_final.csv
PB_annotations_df_processed.to_csv(os.path.join(
    save_dir, "PB_annotations_final.csv"), index=False)

# save the dataframe restricted to the columns we need as a csv file in the save_dir with file name PB_annotations_final_abridged.csv
PB_annotations_df_processed[columns_we_need].to_csv(os.path.join(
    save_dir, "PB_annotations_final_abridged.csv"), index=False)
