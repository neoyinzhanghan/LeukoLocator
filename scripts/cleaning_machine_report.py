import os
import pandas as pd

machine_report_path = "/Users/neo/Documents/Research/DeepHeme/LLResults/MachineResults/CBC_H15-H18_DataLine Results - PTH29594 (2015-2018).csv"

# open the machine report
machine_report = pd.read_csv(machine_report_path)

# only keep the rows where the column Unit/Measure is equal to '%'
machine_report = machine_report[machine_report["Unit/Measure"] == "%"]

# only keep the following columns - 'Pathology Report', 'Subtest Name', 'Result Value', 'Unit/Measure'
machine_report = machine_report[
    ["Pathology Report", "Subtest Name", "Result Value", "Unit/Measure"]
]
machine_report = machine_report.rename(
    columns={
        "Pathology Report": "slide_name",
        "Subtest Name": "cell_name",
        "Result Value": "machine_result",
    }
)

# remove the rows where cell_name is not equal to Neutrophil, Eos, Baso, Immature Granulocyte, Lymph, Mono, Blast, Nucleated RBC
machine_report = machine_report[
    machine_report["cell_name"].isin(
        [
            "Neutrophil",
            "Eos",
            "Baso",
            "Immature Granulocyte",
            "Lymph",
            "Mono",
            "Blast",
            "Nucleated RBC",
        ]
    )
]

# rename the cell_name to match the cellnames in LL
machine_report["cell_name"] = machine_report["cell_name"].replace(
    {
        "Neutrophil": "Neutrophil",
        "Eos": "Eosinophil",
        "Baso": "Basophil",
        "Immature Granulocyte": "Immature Granulocyte",
        "Lymph": "Lymphocyte",
        "Mono": "Monocyte",
        "Blast": "Blast",
        "Nucleated RBC": "Nucleated RBC",
    }
)

# save the machine report in the same directory as the machine report
machine_report.to_csv(
    os.path.join(os.path.dirname(machine_report_path), "machine_report.csv"),
    index=False,
)
