#####################################################################################################
# Imports ###########################################################################################
#####################################################################################################

# Outside imports ##################################################################################
import torch
import torch.nn as nn
import numpy as np
import os
import sys
from PIL import Image
from torchvision import transforms
from collections import OrderedDict

# Within package imports ###########################################################################
from LL.resources.BMAassumptions import *


# class Myresnext50(nn.Module):
#     def __init__(self, my_pretrained_model, num_classes=23):
#         super(Myresnext50, self).__init__()
#         self.pretrained = my_pretrained_model
#         self.my_new_layers = nn.Sequential(
#             nn.Linear(1000, 100), nn.ReLU(), nn.Linear(100, num_classes)
#         )
#         self.num_classes = num_classes

#     def forward(self, x):
#         x = self.pretrained(x)
#         x = self.my_new_layers(x)

#         pred = torch.sigmoid(x.reshape(x.shape[0], 1, self.num_classes))
#         return pred


class Myresnext50(nn.Module):
    def __init__(self, my_pretrained_model, num_classes=23):
        super(Myresnext50, self).__init__()
        self.pretrained = my_pretrained_model
        self.my_new_layers = nn.Sequential(
            nn.Linear(1000, 100), nn.ReLU(), nn.Linear(100, num_classes)
        )
        self.num_classes = num_classes

    def forward(self, x, return_features=False):
        features = self.pretrained(x)
        x = self.my_new_layers(features)
        pred = torch.sigmoid(x.reshape(x.shape[0], 1, self.num_classes))

        if return_features:
            return pred, features
        else:
            return pred


def model_create(num_classes=23, path="not_existed_path"):
    resnext50_pretrained = torch.hub.load("pytorch/vision:v0.10.0", "resnext50_32x4d")
    My_model = Myresnext50(
        my_pretrained_model=resnext50_pretrained, num_classes=num_classes
    )

    checkpoint_PATH = path
    checkpoint = torch.load(checkpoint_PATH)  # , map_location=torch.device("cpu"))

    checkpoint = remove_data_parallel(checkpoint["model_state_dict"])

    My_model.load_state_dict(checkpoint, strict=True)

    My_model.eval()
    My_model.to("cuda")

    return My_model


def remove_data_parallel(old_state_dict):
    new_state_dict = OrderedDict()

    for k, v in old_state_dict.items():
        name = k[7:]  # remove `module.`

        new_state_dict[name] = v

    return new_state_dict


def predict_on_cpu(image, model):
    # Define the transformations

    # make sure the image is RGB if it is not already
    if image.mode != "RGB":
        image = image.convert("RGB")

    image_transforms = transforms.Compose(
        [
            transforms.Resize(96),
            transforms.ToTensor(),
            transforms.Normalize([0.5594, 0.4984, 0.6937], [0.2701, 0.2835, 0.2176]),
        ]
    )

    # Apply transformations to the input image and create a batch
    image = image_transforms(image).float().unsqueeze(0)

    # Set the model to evaluation mode and make predictions
    model.to("cpu")
    model.eval()

    # Move the image to the CPU if available
    device = torch.device("cpu")

    image = image.to(device)

    with torch.no_grad():
        output = model(image)

    # Process the output as in the original code snippet
    output = torch.flatten(output, start_dim=1).detach().cpu().numpy()
    prediction = tuple(output[0])

    # Return the prediction
    return prediction


def predict_batch(pil_images, model):
    # Define the transformations
    image_transforms = transforms.Compose(
        [
            transforms.Resize(96),
            transforms.ToTensor(),
            transforms.Normalize([0.5594, 0.4984, 0.6937], [0.2701, 0.2835, 0.2176]),
        ]
    )

    # Apply transformations to each image and create a batch
    batch = torch.stack([image_transforms(image).float() for image in pil_images])

    # Move the batch to the GPU if available
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    batch = batch.to(device)

    # Set the model to evaluation mode and make predictions
    model.eval()
    with torch.no_grad():
        outputs = model(batch)

    # Process each output as in the original code snippet
    predictions = []
    for output in outputs:
        output = torch.flatten(output, start_dim=1).detach().cpu().numpy()
        predictions.append(tuple(output[0]))

    # Return a list of predictions in the same order as the input images
    return predictions


def get_features_batch(pil_images, model):
    # Define the transformations
    image_transforms = transforms.Compose(
        [
            transforms.Resize((96, 96)),
            transforms.ToTensor(),
            transforms.Normalize([0.5594, 0.4984, 0.6937], [0.2701, 0.2835, 0.2176]),
        ]
    )

    # Apply transformations to each image and create a batch
    batch = torch.stack([image_transforms(image).float() for image in pil_images])

    # Move the batch to the GPU if available
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    batch = batch.to(device)

    # Set the model to evaluation mode and make predictions
    model.eval()
    with torch.no_grad():
        _, outputs = model(batch, return_features=True)

    # Process each output as in the original code snippet
    features = []
    for output in outputs:
        # print the shape of the output
        # print(output.shape)
        output = output.detach().cpu().numpy()
        features.append(output)

    # Return a list of predictions in the same order as the input images
    return features

