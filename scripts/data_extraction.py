import pandas as pd
import os

from LL.resources.PBassumptions import *
from LL.PBCounter import PBCounter
from LL.brain.TextParser import read_and_transpose_as_df
from pathlib import Path
from tqdm import tqdm
from PIL import Image

# example_slide_path = "/media/ssd1/neo/PBSlides/LL_test_example.ndpi"
# pbc = PBCounter(example_slide_path, hoarding=True)

# pbc.tally_differential()

PB_annotations_path = "/media/hdd3/neo/results/PB_annotations_filtered_processed.csv"
wsi_dir = "/media/hdd3/neo/PB_slides"

PB_annotations_df = pd.read_csv(PB_annotations_path)

num_wsis = len(PB_annotations_df)

exception_list = [
    # "H23-894;S17;MSK7 - 2023-06-15 19.18.03",
    # "H22-5721;S12;MSKV - 2023-04-14 16.13.00",
    # "H22-10246;S15;MSK6 - 2023-06-15 12.37.37",
    # "H22-7118;S11;MSKW - 2023-06-15 17.23.30",
    # "H22-10935;S16;MSKB - 2023-06-15 10.44.43",
    # "H22-6251;S15;MSKX - 2023-06-15 12.44.35",
    # "H21-8723;S14;MSK1 - 2023-05-19 16.23.18",
    # "H21-7705;S13;MSK9 - 2023-05-31 15.31.31",
    # "H21-8526;S10;MSK8 - 2023-05-19 18.10.06",
    # "H21-9688;S11;MSK9 - 2023-04-19 16.55.24",
    # "H21-1589;S11;MSK1 - 2023-05-22 08.07.13",
    # "H20-8172;S11;MSK5 - 2023-06-15 19.59.48",
    # "H20-152;S12;MSKW - 2023-06-27 22.43.39",
    # "H19-8719;S13;MSKB - 2023-06-20 10.03.13",
    # "H19-3488;S11;MSK8 - 2023-06-27 23.12.56",
    # "H19-8904;S10;MSKO - 2023-06-20 10.26.07",
    # "H18-9809;S11;MSKJ - 2023-04-25 09.52.53",
    # "H18-9196;S11;MSK9 - 2023-06-21 21.36.14",
    # "H18-7360;S10;MSKI - 2023-04-25 17.27.10",
    # "H18-7697;S11;MSKC - 2023-06-26 20.39.06",
    # "H18-6717;S12;MSK6 - 2023-06-26 13.28.54",
    # "H18-6286;S2;MSK6 - 2023-04-19 16.08.29",
]
exception_list.append("cartridges")  # this one is problematic during the result pooling

# get the list of folder names in the dump_dir, these are the names of the WSIs that have been processed, the last one may or may not have been fully processed
# because the script may have been interrupted at the last one, so we need to reprocess the last one just in case
# only the folders
processed_wsi_fnames_stem = [
    fname
    for fname in os.listdir(dump_dir)
    if os.path.isdir(os.path.join(dump_dir, fname))
]


# get the length of the list of folder names in the dump_dir, these are the names of the WSIs that have been processed, the last one may or may not have been fully processed
# because the script may have been interrupted at the last one, so we need to reprocess the last one just in case
num_processed_wsi_fnames_stem = len(processed_wsi_fnames_stem)

current_idx = 0

# traverse through the rows of the dataframe of the column 'wsi_fname', which is the filename of the WSI
for i in tqdm(range(num_wsis), desc="Processing WSIs"):
    current_idx += 1
    try:
        if current_idx < num_processed_wsi_fnames_stem:
            # make sure to update the tqdm progress bar
            tqdm.write(
                f"Skipping {PB_annotations_df['wsi_fname'][i]} because it has been processed"
            )
            continue

        # get the wsi_fname
        wsi_fname = PB_annotations_df["wsi_fname"][i]

        # get the wsi_path
        wsi_path = os.path.join(wsi_dir, wsi_fname)

        wsi_fname_stem = Path(wsi_fname).stem

        if wsi_fname_stem in exception_list:
            tqdm.write(f"Skipping {wsi_fname_stem} because it is in the exception list")
            continue

        save_dir = os.path.join(dump_dir, Path(wsi_path).stem)

        print(f"Processing {wsi_fname_stem}...")

        pbc = PBCounter(wsi_path, hoarding=True)

        pbc.tally_differential()

    except Exception as e:
        save_dir = os.path.join(dump_dir, Path(wsi_path).stem)

        # if the save_dir does not exist, create it
        os.makedirs(save_dir, exist_ok=True)

        # save the exception in the save_dir as error.txt

        with open(os.path.join(save_dir, "error.txt"), "w") as f:
            f.write(str(e))

        # rename the save_dir name to "ERROR_" + save_dir
        os.rename(save_dir, os.path.join(dump_dir, "ERROR_" + Path(wsi_path).stem))

# create a list of all the WSIs not in the exception list and did not encounter ERROR
processed_wsi_fnames_stem_good = [
    fname
    for fname in os.listdir(dump_dir)
    if os.path.isdir(os.path.join(dump_dir, fname))
    and fname not in exception_list
    and not fname.startswith("ERROR_")
]

# create a dataframe called PB_results_df
# the columns should be combined from the following csv files
# differential.csv
# differential_full_class.csv
# differential_count.csv
# differential_full_class_count.csv
# runtime_data.csv
# focus_regions/focus_regions_filtering.csv
# cells/cell_detection.csv
# the first column should be the wsi_fname_stem

rows = []
for wsi_fname_stem in tqdm(
    processed_wsi_fnames_stem_good, desc="Creating pooled results dataframe: "
):
    try:
        # open the differential.csv
        differential_df = read_and_transpose_as_df(
            os.path.join(dump_dir, wsi_fname_stem, "differential.csv")
        )

        # print(differential_df)
        # # print the number of rows
        # print(len(differential_df))

        # open the differential_full_class.csv
        differential_full_class_df = read_and_transpose_as_df(
            os.path.join(dump_dir, wsi_fname_stem, "differential_full_class.csv")
        )

        # print(differential_full_class_df)
        # print(len(differential_full_class_df))

        # open the differential_count.csv
        differential_count_df = read_and_transpose_as_df(
            os.path.join(dump_dir, wsi_fname_stem, "differential_count.csv")
        )

        # print(differential_count_df)
        # print(len(differential_count_df))

        # open the differential_full_class_count.csv
        differential_full_class_count_df = read_and_transpose_as_df(
            os.path.join(dump_dir, wsi_fname_stem, "differential_full_class_count.csv")
        )

        # print(differential_full_class_count_df)
        # print(len(differential_full_class_count_df))

        # open the runtime_data.csv
        runtime_data_df = read_and_transpose_as_df(
            os.path.join(dump_dir, wsi_fname_stem, "runtime_data.csv")
        )

        # print(runtime_data_df)
        # print(len(runtime_data_df))

        # open the focus_regions/focus_regions_filtering.csv
        focus_regions_filtering_df = read_and_transpose_as_df(
            os.path.join(
                dump_dir, wsi_fname_stem, "focus_regions", "focus_regions_filtering.csv"
            )
        )

        # print(focus_regions_filtering_df)
        # print(len(focus_regions_filtering_df))

        # open the cells/cell_detection.csv
        cell_detection_df = read_and_transpose_as_df(
            os.path.join(dump_dir, wsi_fname_stem, "cells", "cell_detection.csv")
        )

        # all these dataframes only have one row
        # create a dictionary mapping the column names to the values

        dct = {
            **differential_df,
            **differential_full_class_df,
            **differential_count_df,
            **differential_full_class_count_df,
            **runtime_data_df,
            **focus_regions_filtering_df,
            **cell_detection_df,
        }

        dct["wsi_fname_stem"] = wsi_fname_stem

    except Exception as e:
        print(f"Error in {wsi_fname_stem}: {e}")

    rows.append(dct)

PB_results_df = pd.DataFrame(rows)

# save the dataframe as a csv file in the dump_dir
PB_results_df.to_csv(os.path.join(dump_dir, "PB_results.csv"), index=False)

# # Now we are going to create a folder called "cartridges" in the dump_dir
# os.makedirs(os.path.join(dump_dir, "cartridges"), exist_ok=True)


# def get_a_cell(wsi_result_dir: str):
#     """Look at the cells/cells_info.csv file. Randomly select a cell. Return the corresponding row of the dataframe.
#     Also return the cell image which is contained in the cells/label folder where label is given by the label column of the dataframe.
#     Use the part of the cell name after _ delimitor, that part of the name should be exactly 'focus_region_idx-local_idx' where focus_region_idx is the region id and local_idx is the cell id.
#     They are saved as the columns focus_region_idx and local_idx in the dataframe. Also return the cell name stem.
#     """

#     # open the cells/cells_info.csv file
#     cells_info_df = pd.read_csv(os.path.join(wsi_result_dir, "cells", "cells_info.csv"))

#     # randomly select a cell
#     cell = cells_info_df.sample(n=1)

#     # get the label of the cell
#     label = cell["label"].values[0]

#     # get the focus_region_idx of the cell
#     focus_region_idx = cell["focus_region_idx"].values[0]

#     # get the cell_id of the cell
#     local_idx = cell["local_idx"].values[0]

#     # traverse through all the jpg files in the cells/label folder
#     for fname in os.listdir(os.path.join(wsi_result_dir, "cells", label)):
#         # if the fname contains the focus_region_idx and local_idx, then this is the cell image
#         if str(focus_region_idx) + "-" + str(local_idx) in str(fname):
#             # open the image
#             cell_image = Image.open(os.path.join(wsi_result_dir, "cells", label, fname))

#             # get the cell_name which is the stem of the fname wihout the extension
#             cell_name = Path(fname).stem

#             # four_classes is the string before the _ delimitor in cell_name
#             four_classes = cell_name.split("_")[0]

#             # get the cell_label which is the label
#             cell_label = label

#             # return the cell and the cell_image
#             return (
#                 cell,
#                 cell_image,
#                 four_classes,
#                 cell_label,
#                 focus_region_idx,
#                 local_idx,
#             )

#     raise Exception("Cell image not found")


# def get_accession_number(wsifname: str):
#     """Get the accession number from the wsi_fname_stem."""

#     # the patient id is the first string before the first ; delimitor
#     accession_number = wsifname.split(";")[0]

#     # strip the leading and trailing spaces
#     accession_number = accession_number.strip()

#     return accession_number


# def get_diagnosis_str(
#     wsi_fname_stem: str,
#     diagnosis_file_path: str = "/media/hdd3/neo/resultsv4/diagnoses.csv",
# ):
#     """Get the diagnosis string from the diagnosis_file_path given the wsi_fname_stem."""

#     # open the diagnosis_file_path
#     diagnosis_df = pd.read_csv(diagnosis_file_path)

#     # apply stripping to all the entries in the column 'Accession Number'
#     diagnosis_df["Accession Number"] = diagnosis_df["Accession Number"].apply(
#         lambda x: x.strip()
#     )

#     # get the row of the dataframe where the column 'wsi_fname_stem' is equal to wsi_fname_stem if not found return "NA" as a string
#     if get_accession_number(wsi_fname_stem) not in diagnosis_df[
#         "Accession Number"
#     ].values.astype(str):
#         print("Unable to find diagnosis for " + wsi_fname_stem)
#         print(
#             "Accession Number: " + get_accession_number(wsi_fname_stem) + " not found"
#         )
#         return "NA"
#     else:
#         row = diagnosis_df[
#             diagnosis_df["Accession Number"] == get_accession_number(wsi_fname_stem)
#         ]

#     # get the General Dx column and the Sub Dx columns
#     general_dx = str(row["General Dx"].values[0])
#     sub_dx = str(row["Sub Dx"].values[0])

#     # replace spaces in the general_dx and sub_dx with +
#     general_dx = general_dx.replace(" ", "+")
#     sub_dx = sub_dx.replace(" ", "+")

#     # replace / in the general_dx and sub_dx with +
#     general_dx = general_dx.replace("/", "+")
#     sub_dx = sub_dx.replace("/", "+")

#     diagnosis_str = general_dx + "-" + sub_dx

#     return diagnosis_str


# num_cartridges = 10

# for i in tqdm(range(num_cartridges), desc="Creating cartridges"):
#     # create a folder called cartridge_i
#     cartridge_dir = os.path.join(dump_dir, "cartridges", f"cartridge_{i}")

#     # if the folder exists, skip
#     if os.path.exists(cartridge_dir):
#         continue

#     # create the folder
#     os.makedirs(cartridge_dir)

#     for wsi_fname_stem in tqdm(
#         processed_wsi_fnames_stem_good, desc="Creating cartridge: "
#     ):
#         # create a folder called wsi_fname_stem
#         wsi_result_dir = os.path.join(dump_dir, wsi_fname_stem)

#         diagnosis_str = get_diagnosis_str(wsi_fname_stem)

#         # get a cell
#         (
#             cell,
#             cell_image,
#             four_classes,
#             cell_label,
#             focus_region_idx,
#             local_idx,
#         ) = get_a_cell(wsi_result_dir)

#         # save the cell image in the cartridge_dir under the corresponding label
#         os.makedirs(os.path.join(cartridge_dir, cell_label), exist_ok=True)
#         cell_image.save(
#             os.path.join(
#                 cartridge_dir,
#                 cell_label,
#                 four_classes
#                 + "_"
#                 + diagnosis_str
#                 + "_"
#                 + str(focus_region_idx)
#                 + "-"
#                 + str(local_idx)
#                 + wsi_fname_stem
#                 + ".jpg",
#             )
#         )
