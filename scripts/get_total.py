import os

data_dir = (
    "/Users/neo/Documents/Research/DeepHeme/HemeYolo_data/PB_YOLO_2k/annotations_raw"
)

# it is folder with txt files
# calculate the total number of annotations (lines in all txt files)

total = 0

for file in os.listdir(data_dir):
    if not file.endswith(".txt"):
        continue
    with open(os.path.join(data_dir, file), "r") as f:
        total += len(f.readlines())

print(total)