import os
import torch
from torchvision import datasets, transforms

image_dir = "/media/ssd1/neo/regions_50k_reduced"
checkpoint_path = "/media/ssd1/neo/models/resnet50/PB_region_1.ckpt"
save_dir = "/media/ssd1/neo/regions_50_reduced_classified"


### the goal of this script is to first load the checkpoint
# then classify the images in the image_dir
# create folders in the save_dir for each class
# then save the images in the corresponding folder
# also save a csv file with two columns -- image_name, class

# load the checkpoint
checkpoint = torch.load(checkpoint_path)
model = checkpoint["model"]

# create the save_dir
if not os.path.exists(save_dir):
    os.mkdir(save_dir)

# create the folders for each class
for i in range(2):
    if not os.path.exists(os.path.join(save_dir, str(i))):
        os.mkdir(os.path.join(save_dir, str(i)))

# create the csv file
csv_file = open(os.path.join(save_dir, "region_clf.csv"), "w")

# create the dataloader
dataset = datasets.ImageFolder(image_dir, transform=transforms.ToTensor())

dataloader = torch.utils.data.DataLoader(dataset, batch_size=1, shuffle=False)

# iterate through the dataloader
for i, (image, label) in enumerate(dataloader):
    # predict the label
    output = model(image)
    _, pred = torch.max(output, 1)
    pred = pred.item()

    # save the image
    image_name = dataset.imgs[i][0].split("/")[-1]
    image.save(os.path.join(save_dir, str(pred), image_name))

    # write to the csv file
    csv_file.write(image_name + "," + str(pred) + "\n")

csv_file.close()

print("Done!")
