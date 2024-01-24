import pandas as pd
from LL.resources.PBassumptions import *

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

# open the diagnosis file
diagnosis = pd.read_csv(diagnosis_path)


def accession_num(wsi_name):
    return wsi_name.split(";")[0]
