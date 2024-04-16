import os
import pandas as pd
import time
from LLRunner.BMAInfo import BMAInfo
from LLRunner.BMAResult import BMAResult
from tqdm import tqdm


start_time = time.time()
bma_info = BMAInfo()

result_dir = "/media/hdd3/neo/results_bma_aml_v2"

print(f"Pooling Results Directories In {result_dir}")
# first get a list of all the directories in the result_dir that does not start with "ERROR_"
result_dirs = [
    dname
    for dname in os.listdir(result_dir)
    if os.path.isdir(os.path.join(result_dir, dname)) and not dname.startswith("ERROR_")
]

# then get all the ones with the "ERROR_" prefix
error_result_dirs = [
    dname
    for dname in os.listdir(result_dir)
    if os.path.isdir(os.path.join(result_dir, dname)) and dname.startswith("ERROR_")
]

print(f"Found {len(result_dirs)} Result Directories")
print(f"Found {len(error_result_dirs)} Error Result Directories")

list_of_dicts = []

# traverse through all the result directories using tqdm
for dname in tqdm(result_dirs, "Processing Results: "):

    # get the BMAResult object for the result directory
    bma_result = BMAResult(os.path.join(result_dir, dname))

    # get the stacked differential
    stacked_differential = bma_result.get_stacked_differential()

    # get the one hot differential
    one_hot_differential = bma_result.get_one_hot_differential()

    # get the grouped differential
    grouped_differential = bma_result.get_grouped_differential()

    # get the row from the BMA info
    bma_info_row = bma_info.get_row_from_slide_name(dname)

    if bma_info_row is None:
        bma_info_row = {
            "specnum_formatted": "NA",
            "accession_date": "NA",
            "part_description": "NA",
            "text_data_clindx": "NA",
            "blasts": "NA",
            "blast-equivalents": "NA",
            "promyelocytes": "NA",
            "myelocytes": "NA",
            "metamyelocytes": "NA",
            "neutrophils/bands": "NA",
            "monocytes": "NA",
            "eosinophils": "NA",
            "erythroid precursors": "NA",
            "lymphocytes": "NA",
            "plasma cells": "NA",
        }

    # make a row for the results with columns as a dictionary
    # -- slide_name: the name of the slide which is the stem of the dname
    # -- one_hot_differential: turn the one_hot_differential dictionary into a df row the column name is the key and the value is the value
    # -- stacked_differential: turn the stacked_differential dictionary into a df row the column name is the key + "_stacked" and the value is the value
    # -- grouped_differential: turn the grouped_differential dictionary into a df row the column name is the key + "_grouped" and the value is the value
    # -- bma_info_row: the row from the BMA info
    # Just make one big dictionary

    big_dict = {"slide_name": dname}

    for key, value in one_hot_differential.items():
        big_dict[key] = int(
            value * 100
        )  # convert to percentage for easier reading and make it an integer

    for key, value in stacked_differential.items():
        big_dict[key + "_stacked"] = int(
            value * 100
        )  # convert to percentage for easier reading and make it an integer

    for key, value in grouped_differential.items():
        big_dict[key + "_grouped"] = int(
            value * 100
        )  # convert to percentage for easier reading and make it an integer

    for key, value in bma_info_row.items():
        big_dict[key] = value

    list_of_dicts.append(big_dict)

print("Finished Processing Results")
# make a dataframe from the list of dictionaries
df = pd.DataFrame(list_of_dicts)

# save the dataframe to a csv in the result_dir as "pooled_results.csv"
df.to_csv(os.path.join(result_dir, "pooled_results.csv"), index=False)

print(f"Finished Pooling Results In {time.time() - start_time} Seconds.")
