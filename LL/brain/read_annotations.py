####################################################################################################
# Imports ##########################################################################################
####################################################################################################

# Outside imports ##################################################################################
import re
import pandas as pd

# Within package imports ###########################################################################
from LL.brain.regex import says_peripheral_blood_smear, get_barcode_from_fname, last_date


def read_annotation_csv(csv_path):
    """ Read annotation csv file and return a pandas dataframe. Make sure the column names are good.
    All the data should be strings.
    """

    # Read the csv file
    df = pd.read_csv(csv_path, dtype=str)


def get_PB_annotations_from_csv(csv_path):
    """ Read annotation csv file and return a pandas dataframe. Make sure the column names are good.
    Only include the rows where the column 'part_description' says 'peripheral blood smear'."""

    # Read the csv file
    df = pd.read_csv(csv_path, dtype=str)

    # Filter the rows where the column 'part_description' says 'peripheral blood smear'
    # use the function says_peripheral_blood_smear
    df = df[df['part_description'].apply(says_peripheral_blood_smear)]

    # Return the dataframe
    return df


def get_PB_metadata(wsi_fname, PB_annotations_df):
    """ Get the metadata for the peripheral blood smear from the dataframe of PB annotations.
    Return a dictionary that contains wsi_fname, part_description, processed_date, text_data_clindx, text_data_final
    """

    # first get barcode from wsi_fname
    barcode = get_barcode_from_fname(wsi_fname).strip()

    # filter the dataframe by barcode, make sure to strip blank spaces
    df = PB_annotations_df[PB_annotations_df['barcode'].str.strip() == barcode]

    # if the dataframe is empty, raise a NotAnnotatedError
    if df.empty:
        raise NotAnnotatedError

    # turn df['processed_date']) into a list
    processed_dates = df['processed_date'].tolist()

    # get the row with the latest processed_date
    row = df[df['processed_date'] == last_date(processed_dates)].iloc[0]

    # get the part_description, processed_date, text_data_clindx, text_data_final
    part_description = row['part_description']
    processed_date = row['processed_date']
    text_data_clindx = row['text_data_clindx']
    text_data_final = row['text_data_final']

    # return a dictionary
    return {'wsi_fname': wsi_fname,
            'part_description': part_description,
            'processed_date': processed_date,
            'text_data_clindx': text_data_clindx,
            'text_data_final': text_data_final}


class NotAnnotatedError(Exception):
    pass
