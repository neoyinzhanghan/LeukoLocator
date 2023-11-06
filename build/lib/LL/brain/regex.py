####################################################################################################
# Imports ##########################################################################################
####################################################################################################

# Outside imports #################################################################################
import warnings
import re
import Levenshtein
import subprocess


def extract_peripheral_blood_text_chunk(text):
    pattern = r"(PERIPHERAL BLOOD[\s\S]*?Peripheral Blood Analysis)"
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
    latest_date = dates[0]

    # Iterate through the list of dates
    for date in dates:
        if after(date, latest_date):
            latest_date = date

    return latest_date


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


def rtf_to_text(rtf_string):
    result = subprocess.run(['unrtf', '--text'],
                            input=rtf_string, text=True, capture_output=True)
    return result.stdout


def is_rtf_string(s):
    """Check if the given string is in RTF format."""
    s = s.strip()  # Remove leading and trailing whitespaces
    return s.startswith('{\\rtf') and s.endswith('}')


def convert_to_dict(data_string):
    # Splitting the data by new lines
    lines = data_string.split('\n')

    # Creating the dictionary
    result = {}
    for line in lines:
        # Finding the index of the first digit
        first_digit_index = next(
            (i for i, char in enumerate(line) if char.isdigit()), None)

        # If no digit is found, continue to the next iteration
        if first_digit_index is None:
            print('User warning: Skipped line due to format issues: ' + line)
            continue

        # Splitting the line into name and value based on the first occurrence of a digit
        parts = line[first_digit_index:].split()
        if not parts:
            warnings.warn(f"Skipped line due to format issues: {line}")
            continue

        try:
            value = float(parts[0])
            name = line[:first_digit_index].strip()
            result[name] = value
        except ValueError:
            warnings.warn(f"Skipped line due to format issues: {line}")
            continue

    return result


def extract_second_paragraph(data):
    # Split data into paragraphs using two consecutive newline characters
    paragraphs = data.split("\n\n")

    # Return the second paragraph if it exists
    return paragraphs[1] if len(paragraphs) > 1 else ""


def remove_unwanted_lines(text):
    # Remove lines containing "PERIPHERAL BLOOD" or "CBC" and the following empty lines
    pattern = r'^(PERIPHERAL BLOOD|CBC.*)(\n\s*){1,2}'
    cleaned_text = re.sub(pattern, '', text, flags=re.MULTILINE)
    return cleaned_text


data = """PERIPHERAL BLOOD
CBC (01/11/2023):






WBC 12.6 H [4.0-11.0 K/mcL]
RBC 4.02 [3.95-5.54 M/mcL]
HGB 12.1 L [12.5-16.2 g/dL]
HCT 35.1 L [37.5-49.3 %]
MCV 87 [80-98 fL]
MCH 30.1 [27.0-33.0 pg]
MCHC 34.5 [31.0-36.5 g/dL]
RDW 13.8 [12.2-15.1 %]
Platelets 33 L [160-400 K/mcL]

Neutrophil 33.0 [32.5-74.8 %]
Mono 9.0 [0.0-12.3 %]
Eos 1.0 [0.0-4.9 %]
Baso 0.0 [0.0-1.5 %]
Blast 2.0 H [0.0-0.0 %]
Myelocyte 5.0 H [0.0-0.0 %]
Metamyelocyte 3.0 H [0.0-0.0 %]
Lymph 14.0 [12.2-47.4 %]
Other 33.0 H [0.0-0.0 %]
Mononuclear cells with prominent nucleoli, some with irregular nuclear contours.
Nucleated RBC 0.0 [0.0-0.0 /100(WBCs)]

Abs Neut 4.2 [1.5-7.5 K/mcL]
Abs Mono 1.1 [0.0-1.3 K/mcL]
Absolute Eosinophil 0.1 [0.0-0.7 K/mcL]
Absolute Basophil 0.0 [0.0-0.2 K/mcL]
Absolute Blasts 0.3 H [0.0-0.0 K/mcL]
Abs Myelocytes 0.6 H [0.0-0.0 K/mcL]
Abs Meta 0.4 H [0.0-0.0 K/mcL]
Abs Lymph 1.8 [0.9-3.2 K/mcL]
Abs Others 4.2 H [0.0-0.0 K/mcL]

Morphology: Frequent atypical lymphoid cells noted.

Peripheral Blood Analysis"""

print(remove_unwanted_lines(data))
print(extract_second_paragraph(remove_unwanted_lines(data)))
print(convert_to_dict(extract_second_paragraph(remove_unwanted_lines(data))))
