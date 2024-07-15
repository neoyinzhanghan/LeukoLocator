import os
import pandas as pd
import random
from tqdm import tqdm

results_dirs_dct = {
    "AML": "/media/hdd1/neo/results_bma_aml_v3",
    "NL": "/media/hdd1/neo/results_bma_normal_v3",
}

metadata = {
    "idx": [],
    "slide_result_path": [],
    "label": [],
    "split": [],
}

train_proportion, val_proportion, test_proportion = 0.7, 0.3, 0.0

for key in results_dirs_dct:
    results_dir = results_dirs_dct[key]
    subfolders = [f.path for f in os.scandir(results_dir) if f.is_dir()]
    subfolders = [f for f in subfolders if not f.split("/")[-1].startswith("ERROR")]

    for subfolder in tqdm(subfolders, desc=f"Processing {key} subfolders"):
        slide_result_path = subfolder
        label = key
        split = random.choices(
            ["train", "val", "test"],
            [train_proportion, val_proportion, test_proportion],
        )[0]

        metadata["idx"].append(len(metadata["idx"]))
        metadata["slide_result_path"].append(slide_result_path)
        metadata["label"].append(label)
        metadata["split"].append(split)


metadata_df = pd.DataFrame(metadata)
save_path = "/media/hdd1/neo/BMA_WSI-clf_AML-Normal_v3_metadata.csv"


metadata_df.to_csv(save_path, index=False)
