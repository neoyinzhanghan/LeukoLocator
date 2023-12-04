import pandas as pd


def read_and_transpose_as_df(fname):
    """Read a csv file as a dataframe."""
    df = pd.read_csv(fname)
    # if num_sds is a column name, remove the column, and store the first number as num_sds
    process_sds = False
    if "num_sds" in df.columns:
        num_sds = int(df["num_sds"][0])
        df = df.drop(columns=["num_sds"])
        process_sds = True
    df = df.transpose()
    df.columns = df.iloc[0]
    df = df.drop(df.index[0])
    # add the num_sds column back
    if process_sds:
        df["num_sds"] = num_sds

    # this df has only one row
    # we are going to convert it to a dictionary mapping the column names to the values

    dct = df.to_dict(orient="records")[0]

    return dct  # TODO WE NEED TO DEBUG THE EXTRACTION SCRIPT SO THIS CAN BE SIMPLIFIED - no need for transposing and no need for num_sds handling
