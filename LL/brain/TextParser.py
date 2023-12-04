import pandas as pd


def read_and_transpose_as_df(fname):
    """Read a csv file as a dataframe."""
    df = pd.read_csv(fname)
    df = df.transpose()
    df.columns = df.iloc[0]
    return df
