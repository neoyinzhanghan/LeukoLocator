####################################################################################################
# Imports ##########################################################################################
####################################################################################################

# Outside imports #################################################################################
import re
import Levenshtein


def extract_peripheral_blood_text_chunk(text):
    pattern = r"(PERIPHERAL BLOOD[\s\S]*?Peripheral Blood Analysis Performed at)"
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    else:
        return "Not found"


def says_peripheral_blood_smear(s):
    """ Returns True if the string s contains the phrase "peripheral blood smear.
    Doc tests:
    >>> says_peripheral_blood_smear("I have a Peripherall    Blood     Smere here")
    True
    >>> says_peripheral_blood_smear("Peripherall\t Blood Smere")
    True
    >>> says_peripheral_blood_smear("Peripheral  Blood")
    False
    >>> says_peripheral_blood_smear("Peripheral  Blood  Smear, Bone Marrow Aspirate, and Bone Marrow Biopsy")
    True """

    # Convert input to lowercase and normalize whitespace
    s = re.sub(r'\s+', ' ', s.lower()).strip()

    # Find all words to handle additional content
    words = re.findall(r'\b\w+\b', s)

    # Construct possible string sequences
    sequences = [' '.join(words[i:i+3]) for i in range(len(words)-2)]

    for seq in sequences:
        # Calculate the Levenshtein distance
        distance = Levenshtein.distance(seq, "peripheral blood smear")

        # Let's say if the distance is less than or equal to 3, it's a match
        # This threshold accounts for one typo and one or two extra spaces.
        if distance <= 3:
            return True

    return False


def get_date_from_fname(fname):
    """ The name is in the format of H23-852;S12;MSKW - 2023-06-15 16.42.50.ndpi
    The part right after space dash space and before the next space is the string for the date.
    """

    # Split the string by space dash space
    second_part = fname.split(" - ")[1]

    # Split the second part by space
    date = second_part.split(" ")[0]

    return date


def after(date1, date2):
    """ Return whether date1 is after date2. Assuming that the date is in the format of YYYY-MM-DD """

    # Split the date by dash
    date1 = date1.split("-")
    date2 = date2.split("-")

    # Compare the year
    if int(date1[0]) < int(date2[0]):
        return False
    elif int(date1[0]) > int(date2[0]):
        return True

    # Compare the month
    if int(date1[1]) < int(date2[1]):
        return False
    elif int(date1[1]) > int(date2[1]):
        return True

    # Compare the day
    if int(date1[2]) < int(date2[2]):
        return False
    elif int(date1[2]) > int(date2[2]):
        return True

    # If the dates are the same, return False
    return False


def last_date(dates):
    """ Return the latest date in the list of dates. Assuming that the date is in the format of YYYY-MM-DD """

    # Initialize the earliest date
    earliest_date = dates[0]

    # Iterate through the list of dates
    for date in dates:
        if after(date, earliest_date):
            earliest_date = date

    return earliest_date


def last_dated_fname(fnames):
    """ Return the fname of the latest date. Assuming that the date is in the format of YYYY-MM-DD and the filename is in the format of H23-852;S12;MSKW - 2023-06-15 16.42.50.ndpi """

    # Initialize the earliest date and fname
    latest_date = get_date_from_fname(fnames[0])
    latest_fname = fnames[0]

    # Iterate through the list of fnames
    for fname in fnames:
        date = get_date_from_fname(fname)
        if after(date, latest_date):
            latest_date = date
            latest_fname = fname

    return latest_fname


def get_barcode_from_fname(fname):
    """ The name is in the format of H23-852;S12;MSKW - 2023-06-15 16.42.50.ndpi
    The part right before the space dash space is the string for the barcode.
    """

    # Split the string by space dash space
    first_part = fname.split(" - ")[0]

    return first_part