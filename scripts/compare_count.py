import os

input_dir = "/Users/neo/Documents/Research/DeepHeme/HemeYolo_data/sampled_focus_regions_to_annotate"
output_dir = (
    "/Users/neo/Documents/Research/DeepHeme/HemeYolo_data/focus_regions_50k_reduced"
)

# print the number of images in input_dir recursively
count = 0
for folder in os.listdir(input_dir):
    if not os.path.isdir(os.path.join(input_dir, folder)):
        continue
    for image in os.listdir(os.path.join(input_dir, folder, "focus_regions")):
        if not image.endswith(".jpg") and not image.endswith(".png"):
            continue
        count += 1

print(count)

# print the number of images in output_dir
count = 0
for image in os.listdir(output_dir):
    if not image.endswith(".jpg") and not image.endswith(".png"):
        continue
    count += 1

print(count)
