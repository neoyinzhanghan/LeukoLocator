import os
import pandas as pd
from tqdm import tqdm

LL_report_path = (
    "/Users/neo/Documents/Research/DeepHeme/LLResults/V3 FullExtract/all_cells_info.csv"
)
machine_report_paths = [
    "/Users/neo/Documents/Research/DeepHeme/LLResults/MachineResults/CBC_PB_H18-H23.csv",
    "/Users/neo/Documents/Research/DeepHeme/LLResults/MachineResults/CBC_PB_H15-H18.csv",
]
diagnosis_path = "/Users/neo/Documents/Research/DeepHeme/LLResults/diagnoses.csv"
output_dir = "/Users/neo/Documents/Research/DeepHeme/LLResults/V3 FullExtract"

# open the LL report
LL_report = pd.read_csv(LL_report_path)

# open the machine reports and combine them
machine_reports = []
for machine_report_path in machine_report_paths:
    machine_reports.append(pd.read_csv(machine_report_path))
machine_report = pd.concat(machine_reports)

# print the number of rows in the machine report
# print("Number of rows in the machine report: {}".format(machine_report.shape[0]))


def _format_dcts(lst_of_dct):
    """Format the list of dictionaries to a dataframe."""
    # convert the list of dictionaries to a dataframe
    # the challenge is that the machine may contain no result for a slide or the machine may contain multiple results for a slide
    # machine_results is a list of varying length
    # we want to find the longest length of machine_results, and create that many columns like machine_result_0, machine_result_1, machine_result_2, ...
    # for list not long enough, we will pad it with missing values

    # get the longest length of machine_results
    longest_length = max([len(dct["machine_results"]) for dct in lst_of_dct])

    # modify the list of dictionaries
    for dct in lst_of_dct:
        # get the length of machine_results
        length = len(dct["machine_results"])

        # pad the list with missing values
        dct["machine_results"] = dct["machine_results"] + [None] * (
            longest_length - length
        )

    # convert the list of dictionaries to a dataframe using columns machine_result_0, machine_result_1, machine_result_2, ... instead of a list
    df = pd.DataFrame(lst_of_dct)
    for i in range(longest_length):
        df["machine_result_{}".format(i)] = df["machine_results"].apply(
            lambda lst: lst[i]
        )

    # drop the column machine_results
    df = df.drop(columns=["machine_results"])

    return df


def _add_diagnoses(df):
    """For each slide, add the diagnoses."""

    # traverse the dataframe
    for idx, row in df.iterrows():
        # The "Accession Number" column is the slide name (make sure to strip the space on the left and right just in case)
        # we want the "General Dx" and "Sub Dx" columms
        slide_name = row["slide_name"].strip()

        # get the diagnosis for this slide
        diagnosis_df = pd.read_csv(diagnosis_path)

        # there should be only one diagnosis for each accession number
        # if the general_dx or sub_dx is missing, then the diagnosis is "NA"
        if len(diagnosis_df[diagnosis_df["Accession Number"] == slide_name]) != 1:
            general_dx = "NA"
            sub_dx = "NA"
        else:
            general_dx = diagnosis_df[diagnosis_df["Accession Number"] == slide_name][
                "General Dx"
            ].tolist()[0]
            sub_dx = diagnosis_df[diagnosis_df["Accession Number"] == slide_name][
                "Sub Dx"
            ].tolist()[0]

        # add the diagnosis to the dataframe
        df.loc[idx, "General Dx"] = general_dx
        df.loc[idx, "Sub Dx"] = sub_dx

    return df


blast_report_dct_lst = []
neutrophil_report_dct_lst = []
eosinophil_report_dct_lst = []
monocyte_report_dct_lst = []
lymphocyte_report_dct_lst = []
nucleated_rbc_report_dct_lst = []
basophil_report_dct_lst = []

# traverse the LL report with tqdm
for idx, row in tqdm(LL_report.iterrows(), total=LL_report.shape[0]):
    # get the wsi_fname_stem
    wsi_fname_stem = row["wsi_fname_stem"]

    slide_name = wsi_fname_stem.split(";")[0]

    # print(slide_name)

    # total number of cells in this slide is the sum of the number of cells in each cell_name
    total_num_cells = (
        row["Neutrophil"]
        + row["Eosinophil"]
        + row["Blast"]
        + row["Monocyte"]
        + row["Lymphocyte"]
        + row["Nucleated RBC"]
        + row["Basophil"]
    )

    # for each cell_name in Neutrophil, Eosinophil, Blast, Monocyte, Lymphocyte, Nucleated RBC, Basophil
    # get the LL result and get the machine result
    # create a dictionary mapping cell_name to LL result and machine result

    # now let's work on neutrophils
    # get the LL result
    neutrophil_LL_result = round(row["Neutrophil"] * 100 / total_num_cells)

    # the machine may contain no neutrophil result for this slide or the machine may contain multiple neutrophil results for this slide
    # so return a list of machine results
    neutrophil_machine_results = machine_report[
        (machine_report["slide_name"] == slide_name)
        & (machine_report["cell_name"] == "Neutrophil")
    ]["machine_result"].tolist()

    # create a dictionary mapping cell_name to LL result and machine result
    neutrophil_report_dct = {
        "slide_name": slide_name,
        "LL_result": neutrophil_LL_result,
        "machine_results": neutrophil_machine_results,
    }

    # append the dictionary to the list
    neutrophil_report_dct_lst.append(neutrophil_report_dct)

    # now let's work on eosinophils
    # get the LL result
    eosinophil_LL_result = round(row["Eosinophil"] * 100 / total_num_cells)

    # the machine may contain no eosinophil result for this slide or the machine may contain multiple eosinophil results for this slide
    # so return a list of machine results
    eosinophil_machine_results = machine_report[
        (machine_report["slide_name"] == slide_name)
        & (machine_report["cell_name"] == "Eosinophil")
    ]["machine_result"].tolist()

    # create a dictionary mapping cell_name to LL result and machine result
    eosinophil_report_dct = {
        "slide_name": slide_name,
        "LL_result": eosinophil_LL_result,
        "machine_results": eosinophil_machine_results,
    }

    # append the dictionary to the list
    eosinophil_report_dct_lst.append(eosinophil_report_dct)

    # now let's work on blasts
    # get the LL result
    blast_LL_result = round(row["Blast"] * 100 / total_num_cells)

    # the machine may contain no blast result for this slide or the machine may contain multiple blast results for this slide\
    # so return a list of machine results
    blast_machine_results = machine_report[
        (machine_report["slide_name"] == slide_name)
        & (machine_report["cell_name"] == "Blast")
    ]["machine_result"].tolist()

    # create a dictionary mapping cell_name to LL result and machine result
    blast_report_dct = {
        "slide_name": slide_name,
        "LL_result": blast_LL_result,
        "machine_results": blast_machine_results,
    }

    # append the dictionary to the list
    blast_report_dct_lst.append(blast_report_dct)

    # now let's work on monocytes
    # get the LL result
    monocyte_LL_result = round(row["Monocyte"] * 100 / total_num_cells)

    # the machine may contain no monocyte result for this slide or the machine may contain multiple monocyte results for this slide
    # so return a list of machine results
    monocyte_machine_results = machine_report[
        (machine_report["slide_name"] == slide_name)
        & (machine_report["cell_name"] == "Monocyte")
    ]["machine_result"].tolist()

    # create a dictionary mapping cell_name to LL result and machine result
    monocyte_report_dct = {
        "slide_name": slide_name,
        "LL_result": monocyte_LL_result,
        "machine_results": monocyte_machine_results,
    }

    # append the dictionary to the list
    monocyte_report_dct_lst.append(monocyte_report_dct)

    # now let's work on lymphocytes
    # get the LL result
    lymphocyte_LL_result = round(row["Lymphocyte"] * 100 / total_num_cells)

    # the machine may contain no lymphocyte result for this slide or the machine may contain multiple lymphocyte results for this slide
    # so return a list of machine results
    lymphocyte_machine_results = machine_report[
        (machine_report["slide_name"] == slide_name)
        & (machine_report["cell_name"] == "Lymphocyte")
    ]["machine_result"].tolist()

    # create a dictionary mapping cell_name to LL result and machine result
    lymphocyte_report_dct = {
        "slide_name": slide_name,
        "LL_result": lymphocyte_LL_result,
        "machine_results": lymphocyte_machine_results,
    }

    # append the dictionary to the list
    lymphocyte_report_dct_lst.append(lymphocyte_report_dct)

    # now let's work on nucleated_rbc
    # get the LL result
    nucleated_rbc_LL_result = round(row["Nucleated RBC"] * 100 / total_num_cells)

    # the machine may contain no nucleated_rbc result for this slide or the machine may contain multiple nucleated_rbc results for this slide
    # so return a list of machine results
    nucleated_rbc_machine_results = machine_report[
        (machine_report["slide_name"] == slide_name)
        & (machine_report["cell_name"] == "Nucleated RBC")
    ]["machine_result"].tolist()

    # create a dictionary mapping cell_name to LL result and machine result
    nucleated_rbc_report_dct = {
        "slide_name": slide_name,
        "LL_result": nucleated_rbc_LL_result,
        "machine_results": nucleated_rbc_machine_results,
    }

    # append the dictionary to the list
    nucleated_rbc_report_dct_lst.append(nucleated_rbc_report_dct)

    # now let's work on basophils
    # get the LL result
    basophil_LL_result = round(row["Basophil"] * 100 / total_num_cells)

    # the machine may contain no basophil result for this slide or the machine may contain multiple basophil results for this slide
    # so return a list of machine results
    basophil_machine_results = machine_report[
        (machine_report["slide_name"] == slide_name)
        & (machine_report["cell_name"] == "Basophil")
    ]["machine_result"].tolist()

    # create a dictionary mapping cell_name to LL result and machine result
    basophil_report_dct = {
        "slide_name": slide_name,
        "LL_result": basophil_LL_result,
        "machine_results": basophil_machine_results,
    }

    # append the dictionary to the list
    basophil_report_dct_lst.append(basophil_report_dct)

# convert the list of dictionaries to a dataframe
blast_report_df = _format_dcts(blast_report_dct_lst)
neutrophil_report_df = _format_dcts(neutrophil_report_dct_lst)
eosinophil_report_df = _format_dcts(eosinophil_report_dct_lst)
monocyte_report_df = _format_dcts(monocyte_report_dct_lst)
lymphocyte_report_df = _format_dcts(lymphocyte_report_dct_lst)
nucleated_rbc_report_df = _format_dcts(nucleated_rbc_report_dct_lst)
basophil_report_df = _format_dcts(basophil_report_dct_lst)

# add the diagnoses to the dataframe
blast_report_df = _add_diagnoses(blast_report_df)
neutrophil_report_df = _add_diagnoses(neutrophil_report_df)
eosinophil_report_df = _add_diagnoses(eosinophil_report_df)
monocyte_report_df = _add_diagnoses(monocyte_report_df)
lymphocyte_report_df = _add_diagnoses(lymphocyte_report_df)
nucleated_rbc_report_df = _add_diagnoses(nucleated_rbc_report_df)
basophil_report_df = _add_diagnoses(basophil_report_df)

# save the dataframe to the output_dir
blast_report_df.to_csv(os.path.join(output_dir, "blast_report.csv"), index=False)
neutrophil_report_df.to_csv(
    os.path.join(output_dir, "neutrophil_report.csv"), index=False
)
eosinophil_report_df.to_csv(
    os.path.join(output_dir, "eosinophil_report.csv"), index=False
)
monocyte_report_df.to_csv(os.path.join(output_dir, "monocyte_report.csv"), index=False)
lymphocyte_report_df.to_csv(
    os.path.join(output_dir, "lymphocyte_report.csv"), index=False
)
nucleated_rbc_report_df.to_csv(
    os.path.join(output_dir, "nucleated_rbc_report.csv"), index=False
)
basophil_report_df.to_csv(os.path.join(output_dir, "basophil_report.csv"), index=False)
