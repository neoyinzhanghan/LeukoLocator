import os
import pandas as pd
import random

results_dirs_dct = {
    "AML": "/media/hdd3/neo/results_bma_aml_v3",
    "NL": "/media/hdd3/neo/results_bma_normal_v3",
}

metadata = {
    "idx": [],
    "slide_result_path": [],
    "label": [],
    "split": [],
}

train_proportion, val_proportion, test_proportion = 0.7, 0.3, 0.0

# Function to split data
def split_data(paths, train_prop, val_prop, test_prop):
    random.shuffle(paths)
    total = len(paths)
    train_end = int(total * train_prop)
    val_end = train_end + int(total * val_prop)
    
    train_split = paths[:train_end]
    val_split = paths[train_end:val_end]
    test_split = paths[val_end:]
    
    return train_split, val_split, test_split

# Collect paths and labels
for label, dir_path in results_dirs_dct.items():
    for root, _, files in os.walk(dir_path):
        for file in files:
            if file.endswith('.h5'):
                file_path = os.path.join(root, file)
                metadata["idx"].append(len(metadata["idx"]))
                metadata["slide_result_path"].append(file_path)
                metadata["label"].append(label)
                metadata["split"].append("")

# Create a DataFrame
metadata_df = pd.DataFrame(metadata)

# Split data and assign splits
aml_paths = metadata_df[metadata_df['label'] == 'AML']['slide_result_path'].tolist()
nl_paths = metadata_df[metadata_df['label'] == 'NL']['slide_result_path'].tolist()

aml_train, aml_val, aml_test = split_data(aml_paths, train_proportion, val_proportion, test_proportion)
nl_train, nl_val, nl_test = split_data(nl_paths, train_proportion, val_proportion, test_proportion)

for split, paths in zip(['train', 'val', 'test'], [aml_train, aml_val, aml_test]):
    metadata_df.loc[metadata_df['slide_result_path'].isin(paths), 'split'] = split

for split, paths in zip(['train', 'val', 'test'], [nl_train, nl_val, nl_test]):
    metadata_df.loc[metadata_df['slide_result_path'].isin(paths), 'split'] = split

# Save metadata to CSV
metadata_csv_path = '/media/hdd3/neo/BMA_WSI_AML-Normal_clf_metadata.csv'
metadata_df.to_csv(metadata_csv_path, index=False)

print(f"Metadata saved to {metadata_csv_path}")
