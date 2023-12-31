import pandas as pd

csv_path = "/media/ssd2/clinical_text_data/PathReports_Heme/H23-20230720.csv"

# open the csv and print a list of its column names
df = pd.read_csv(csv_path, dtype=str)
print(df.columns.tolist())


import pandas as pd

# File paths
file_paths = [
    "/media/ssd2/clinical_text_data/PathReports_Heme/H23-20230720.csv",
    "/media/ssd2/clinical_text_data/PathReports_Heme/H22-20230724.csv",
    "/media/ssd2/clinical_text_data/PathReports_Heme/H21-20230724.csv",
    "/media/ssd2/clinical_text_data/PathReports_Heme/H20-20230724.csv",
    "/media/ssd2/clinical_text_data/PathReports_Heme/H19-20230724.csv",
    "/media/ssd2/clinical_text_data/PathReports_Heme/H18-20230724.csv",
    "/media/ssd2/clinical_text_data/PathReports_Heme/H17-20230724.csv",
    "/media/ssd2/clinical_text_data/PathReports_Heme/H16-20230726-reexported.csv",
    "/media/ssd2/clinical_text_data/PathReports_Heme/H15-20230726.csv"
]

# Columns to remove
columns_to_remove = [
    'text_data_clindx', 'text_data_final', 'text_data_add_dx',
    'lastname', 'firstname', 'middlename', 'date_of_birth', 'gender', 'MRN'
]

# Read and process files
dataframes = []
for file_path in file_paths:
    # Read CSV file
    df = pd.read_csv(file_path)

    # Remove unwanted columns
    df = df.drop(columns=columns_to_remove, errors='ignore')

    # Append to list of dataframes
    dataframes.append(df)

# Merge all dataframes
merged_df = pd.concat(dataframes, ignore_index=True)

# Save the merged dataframe to a CSV file
output_path = "/media/ssd2/clinical_text_data/PathReports_Heme/PB_path_report.csv"
merged_df.to_csv(output_path, index=False)
