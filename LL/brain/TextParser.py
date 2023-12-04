import pandas as pd


def read_and_transpose_as_df(fname):
    """Read a csv file as a dataframe."""
    df = pd.read_csv(fname)
    # if num_sds is a column name, remove the column, and store the first number as num_sds
    if "num_sds" in df.columns:
        num_sds = int(df["num_sds"][0])
        df = df.drop(columns=["num_sds"])
    df = df.transpose()
    df.columns = df.iloc[0]
    df = df.drop(df.index[0])
    # add the num_sds column back
    df["num_sds"] = num_sds

    return df
