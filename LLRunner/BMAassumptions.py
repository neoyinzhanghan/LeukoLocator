cellnames = [
    "B1",
    "B2",
    "E1",
    "E4",
    "ER1",
    "ER2",
    "ER3",
    "ER4",
    "ER5",
    "ER6",
    "L2",
    "L4",
    "M1",
    "M2",
    "M3",
    "M4",
    "M5",
    "M6",
    "MO2",
    "PL2",
    "PL3",
    "U1",
    "U4",
]

differential_group_dict = {
    "blasts": ["M1", "M2", "ER1"],
    "blast-equivalents": [],
    "promyelocytes": ["M2"],
    "myelocytes": ["M3"],
    "metamyelocytes": ["M4"],
    "neutrophils/bands": ["M5", "M6"],
    "monocytes": ["MO2"],
    "eosinophils": ["E1", "E4"],
    "erythroid precursors": ["ER1", "ER2", "ER3", "ER4"],
    "lymphocytes": ["L2"],
    "plasma cells": ["L4"],
}
BMA_final_classes = list(differential_group_dict.keys())

omitted_classes = ["B1", "B2"]
removed_classes = ["U1", "PL2", "PL3", "ER5", "ER6", "U4"]
