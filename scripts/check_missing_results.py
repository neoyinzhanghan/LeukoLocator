import os
import pandas as pd

data_dir = '/media/hdd3/neo/resultsv5'
diagnosis_file = '/media/hdd3/neo/resultsv4/diagnoses.csv'

# Reading all the patient directories and extracting the patient accession names
data_patients = [x.split(';')[0] for x in os.listdir(data_dir)]

# Creating a set of all the patient accession names from the data directory
datapateints_set = set(data_patients)

# Reading the patient accession names from the diagnosis file
diagnosis = pd.read_csv(diagnosis_file, header=0)
diagnosis_patients_set = set(diagnosis['Accession Number'])

# Finding the difference between the patient accession names from the data directory and the diagnosis file
not_in_diagnosis = datapateints_set - diagnosis_patients_set

print(not_in_diagnosis)

print(len(not_in_diagnosis))