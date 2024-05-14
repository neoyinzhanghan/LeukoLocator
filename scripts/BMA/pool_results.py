import os
import pandas as pd
import time
from LLRunner.BMAInfo import BMAInfo
from LLRunner.BMAResult import BMAResult
from tqdm import tqdm
from LL.brain.BMASkippocyteDetection import load_model, predict_image


start_time = time.time()
bma_info = BMAInfo()

result_dir = "/media/hdd3/neo/results_bma_normal_v2"

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

    # get the raw count
    raw_count = bma_result.get_raw_counts()

    # get the grouped raw count
    grouped_raw_count = bma_result.get_grouped_raw_counts()

    # get the grouped_stacked differential
    grouped_stacked_differential = bma_result.get_grouped_differential()

    # get the M1L2 results
    M1L2_results = bma_result.get_M1L2_results()

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
    # -- raw_count: turn the raw_count dictionary into a df row the column name is the key + "_count" and the value is the value
    # -- grouped_raw_count: turn the grouped_raw_count dictionary into a df row the column name is the key + "_grouped_count" and the value is the value
    # -- bma_info_row: the row from the BMA info
    # Just make one big dictionary

    big_dict = {"slide_name": dname}

    for key, value in one_hot_differential.items():
        big_dict[key] = value * 100

    for key, value in stacked_differential.items():
        big_dict[key + "_stacked"] = value * 100

    for key, value in grouped_differential.items():
        big_dict[key + "_grouped"] = value * 100

    for key, value in raw_count.items():
        big_dict[key + "_count"] = value

    for key, value in grouped_raw_count.items():
        big_dict[key + "_grouped_count"] = value

    for key, value in grouped_stacked_differential.items():
        big_dict[key] = value * 100

    big_dict["M1L2"] = M1L2_results["M1L2"] * 100
    big_dict["L2M1"] = M1L2_results["L2M1"] * 100
    big_dict["M1L2_count"] = M1L2_results["M1L2_count"]
    big_dict["L2M1_count"] = M1L2_results["L2M1_count"]

    for key, value in bma_info_row.items():
        big_dict[key] = value

    list_of_dicts.append(big_dict)

print("Finished Processing Results")
# make a dataframe from the list of dictionaries
df = pd.DataFrame(list_of_dicts)

# save the dataframe to a csv in the result_dir as "pooled_results.csv"
df.to_csv(os.path.join(result_dir, "pooled_results.csv"), index=False)

print(f"Finished Pooling Results In {time.time() - start_time} Seconds.")
