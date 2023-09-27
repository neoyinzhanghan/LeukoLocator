import os

clf_pool_dir = ""
save_dir = ""

# clf_pool_dir contains the folders for each class
# each folder contains the images for that class
# create a csv file with two columns -- image_name, class
# save the csv file in the save_dir

# create the save_dir
if not os.path.exists(save_dir):
    os.mkdir(save_dir)

# create the csv file
csv_file = open(os.path.join(save_dir, "region_clf.csv"), "w")

# iterate through the folders make sure to ONLY look at image files
for i in range(2):
    for image_name in os.listdir(os.path.join(clf_pool_dir, str(i))):
        if image_name.endswith(".jpg"):
            csv_file.write(image_name + "," + str(i) + "\n")
