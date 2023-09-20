import os
import random
import pandas as pd


input_dir = '/Users/neo/Documents/Research/DeepHeme/HemeYolo_data/PB_regions_10k'

data_dir = '/home/greg/Documents/neo/data/PB_regions_10k'

save_dir = '/Users/neo/Documents/Research/DeepHeme/HemeYolo_data/PB_regions_10k'

train_prop = 0.8
val_prop = 0.1
test_prop = 0.1

# there are two folders in input_dir: Good and Bad, these are the two classes
# take around train_prop of each class for training, val_prop for validation, and test_prop for testing
# create csv file with the following columns: fpath, label, split
# the fpath will be of the form: datadir/class/basefilename
# the label will be 0 or 1, and 1 stands for Good
# the split will be train, val, or test

# get list of files in each class
good_files = os.listdir(os.path.join(input_dir, 'Good'))
bad_files = os.listdir(os.path.join(input_dir, 'Bad'))

# shuffle the files
random.shuffle(good_files)
random.shuffle(bad_files)

# get the number of files in each class
num_good = len(good_files)
num_bad = len(bad_files)

# get the number of files for each split
num_good_train = int(num_good * train_prop)
num_good_val = int(num_good * val_prop)
num_good_test = num_good - num_good_train - num_good_val

num_bad_train = int(num_bad * train_prop)
num_bad_val = int(num_bad * val_prop)
num_bad_test = num_bad - num_bad_train - num_bad_val

# get the files for each split
good_train_files = good_files[:num_good_train]
good_val_files = good_files[num_good_train:num_good_train+num_good_val]
good_test_files = good_files[num_good_train+num_good_val:]

bad_train_files = bad_files[:num_bad_train]
bad_val_files = bad_files[num_bad_train:num_bad_train+num_bad_val]
bad_test_files = bad_files[num_bad_train+num_bad_val:]

# create the csv file
# start with initializing the dataframe
df = pd.DataFrame(columns=['fpath', 'label', 'split'])

# add the good files
for f in good_train_files:  # use concat to append rows to dataframe
    df = pd.concat([df, pd.DataFrame({'fpath': os.path.join(
        data_dir, 'Good', f), 'label': 1, 'split': 'train'}, index=[0])])
for f in good_val_files:
    df = pd.concat([df, pd.DataFrame({'fpath': os.path.join(
        data_dir, 'Good', f), 'label': 1, 'split': 'val'}, index=[0])])
for f in good_test_files:
    df = pd.concat([df, pd.DataFrame({'fpath': os.path.join(
        data_dir, 'Good', f), 'label': 1, 'split': 'test'}, index=[0])])

# add the bad files
for f in bad_train_files:
    df = pd.concat([df, pd.DataFrame({'fpath': os.path.join(
        data_dir, 'Bad', f), 'label': 0, 'split': 'train'}, index=[0])])
for f in bad_val_files:
    df = pd.concat([df, pd.DataFrame({'fpath': os.path.join(
        data_dir, 'Bad', f), 'label': 0, 'split': 'val'}, index=[0])])
for f in bad_test_files:
    df = pd.concat([df, pd.DataFrame({'fpath': os.path.join(
        data_dir, 'Bad', f), 'label': 0, 'split': 'test'}, index=[0])])

# shuffle the dataframe
df = df.sample(frac=1).reset_index(drop=True)

# save the dataframe to csv
df.to_csv(os.path.join(save_dir, 'clf_data.csv'), index=False)
