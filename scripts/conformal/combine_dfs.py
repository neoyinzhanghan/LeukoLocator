import pandas as pd

df_paths = [
    "/Users/neo/Documents/Research/DeepHeme/LLResults/LLCKPTS/tmp/ucsf_normal.csv",
    "/Users/neo/Documents/Research/DeepHeme/LLResults/LLCKPTS/tmp/mskcc_pb_abnormal.csv",
    "/Users/neo/Documents/Research/DeepHeme/LLResults/LLCKPTS/tmp/mskcc_bma_abnormal.csv",
    "/Users/neo/Documents/Research/DeepHeme/LLResults/LLCKPTS/tmp/mskcc_bma_normal.csv",
]

save_path = "/Users/neo/Documents/Research/DeepHeme/LLResults/LLCKPTS/tmp/conformal_data_cell_info.csv"

# Specify the desired column order
desired_column_order = [
    "fpath",
    "institution",
    "abnormal",
    "specimen_type",
    "scanner",
    "split",
    "label",
    "sample_method",
]

# Read each dataframe, reorder the columns, and then concatenate
df = pd.concat(
    [pd.read_csv(df_path)[desired_column_order] for df_path in df_paths], axis=0
)

# Save the combined dataframe
df.to_csv(save_path, index=False)
