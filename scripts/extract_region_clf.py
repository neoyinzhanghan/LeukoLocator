import os
import torch
from torchvision import datasets, transforms, models
from yaimpl.LitSupervisedModel import LitSupervisedModel
from tqdm import tqdm
import timm

image_dir = "/media/ssd1/neo/regions_50k_reduced"
checkpoint_path = "/media/ssd1/neo/models/resnet50/PB_region_1.ckpt"
save_dir = "/media/ssd1/neo/regions_50_reduced_classified"


### the goal of this script is to first load the checkpoint
# then classify the images in the image_dir
# create folders in the save_dir for each class
# then save the images in the corresponding folder
# also save a csv file with two columns -- image_name, class


# TODO -- read the yaimpl package to figure this out
# Initialize the model (ensure these parameters are same as your training script)

checkpoint = torch.load(checkpoint_path, map_location=torch.device("cpu"))

model = timm.create_model(
    model_name="resnet50",  # replace with your model name
    pretrained=True,  # or True, as per your training script
    num_classes=2,  # replace with your number of classes
)

# Initialize the LitSupervisedModel
lit_model = LitSupervisedModel(model=model)  # add other parameters if required

# Load the state dict into the lit_model
lit_model.load_state_dict(checkpoint["state_dict"])
lit_model.eval()  # set the model to evaluation mode


# create the save_dir
if not os.path.exists(save_dir):
    os.mkdir(save_dir)

# create the folders for each class
for i in range(2):
    if not os.path.exists(os.path.join(save_dir, str(i))):
        os.mkdir(os.path.join(save_dir, str(i)))

# create the csv file
csv_file = open(os.path.join(save_dir, "region_clf.csv"), "w")

# traverse through the image_dir
for image_name in tqdm(os.listdir(image_dir)):
    if image_name.endswith(".jpg"):
        # load the image
        image = datasets.folder.default_loader(os.path.join(image_dir, image_name))

        # make use the image is a tensor
        if not torch.is_tensor(image):
            image = transforms.ToTensor()(image)

        # preprocess the image
        # get the prediction
        prediction = lit_model(image.unsqueeze(0))

        # get the class
        class_ = torch.argmax(prediction).item()

        # save the image in the corresponding folder
        os.rename(
            os.path.join(image_dir, image_name),
            os.path.join(save_dir, str(class_), image_name),
        )

        # write the image name and class to the csv file
        csv_file.write(image_name + "," + str(class_) + "\n")
