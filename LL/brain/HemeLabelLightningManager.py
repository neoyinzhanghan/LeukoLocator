#####################################################################################################
# Imports ###########################################################################################
#####################################################################################################

# Outside imports ##################################################################################
import torch
import torch.nn as nn
import ray
import numpy as np
import os
import sys
import pytorch_lightning as pl
from PIL import Image
import torch.optim.lr_scheduler as lr_scheduler
import torch.nn.functional as F
import albumentations as A
from torchvision import transforms
from collections import OrderedDict
from torchvision.transforms.functional import to_pil_image, to_tensor
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader
from torch import nn
from pytorch_lightning.loggers import TensorBoardLogger
from torchvision import transforms, datasets, models
from torchmetrics import Accuracy, AUROC
from torch.utils.data import WeightedRandomSampler


# Within package imports ###########################################################################
from LL.resources.BMAassumptions import *


############################################################################
####### DEFINE HYPERPARAMETERS AND DATA DIRECTORIES ########################
############################################################################

num_epochs = 500
default_config = {"lr": 3.56e-06}  # 1.462801279401232e-06}
data_dir = "/media/hdd1/neo/pooled_deepheme_data"
num_gpus = 3
num_workers = 20
downsample_factor = 1
batch_size = 256
img_size = 96
num_classes = 23


# Model Module
class Myresnext50(pl.LightningModule):
    def __init__(self, num_classes=23, config=default_config):
        super(Myresnext50, self).__init__()
        self.pretrained = models.resnext50_32x4d(pretrained=True)
        self.pretrained.fc = nn.Linear(self.pretrained.fc.in_features, num_classes)
        # self.my_new_layers = nn.Sequential(
        #     nn.Linear(
        #         1000, 100
        #     ),  # Assuming the output of your pre-trained model is 1000
        #     nn.ReLU(),
        #     nn.Linear(100, num_classes),
        # )
        # self.num_classes = num_classes

        task = "multiclass"

        self.train_accuracy = Accuracy(task=task, num_classes=num_classes)
        self.val_accuracy = Accuracy(task=task, num_classes=num_classes)
        self.train_auroc = AUROC(num_classes=num_classes, task=task)
        self.val_auroc = AUROC(num_classes=num_classes, task=task)
        self.test_accuracy = Accuracy(num_classes=num_classes, task=task)
        self.test_auroc = AUROC(num_classes=num_classes, task=task)

        self.config = config

    def forward(self, x):
        x = self.pretrained(x)

        return x

    def training_step(self, batch, batch_idx):
        x, y = batch
        y_hat = self.forward(x)
        loss = F.cross_entropy(y_hat, y)
        self.log("train_loss", loss)
        self.train_accuracy(y_hat, y)
        self.train_auroc(y_hat, y)
        self.log("train_acc", self.train_accuracy, on_step=True, on_epoch=True)
        self.log("train_auroc", self.train_auroc, on_step=True, on_epoch=True)
        return loss

    def configure_optimizers(self):
        optimizer = torch.optim.Adam(self.parameters(), lr=self.config["lr"])
        scheduler = CosineAnnealingLR(optimizer, T_max=num_epochs, eta_min=0)
        return {"optimizer": optimizer, "lr_scheduler": scheduler}

    def validation_step(self, batch, batch_idx):
        x, y = batch
        y_hat = self.forward(x)
        loss = F.cross_entropy(y_hat, y)
        self.log("val_loss", loss, on_step=False, on_epoch=True)
        self.val_accuracy(y_hat, y)
        self.val_auroc(y_hat, y)
        return loss

    def on_validation_epoch_end(self):
        self.log("val_acc_epoch", self.val_accuracy.compute())
        self.log("val_auroc_epoch", self.val_auroc.compute())
        current_lr = self.trainer.optimizers[0].param_groups[0]["lr"]
        self.log("learning_rate", current_lr, on_epoch=True)

    def test_step(self, batch, batch_idx):
        x, y = batch
        y_hat = self.forward(x)
        loss = F.cross_entropy(y_hat, y)
        self.log("test_loss", loss, on_step=False, on_epoch=True)
        self.test_accuracy(y_hat, y)
        self.test_auroc(y_hat, y)
        return loss

    def on_test_epoch_end(self):
        self.log("test_acc_epoch", self.test_accuracy.compute())
        self.log("test_auroc_epoch", self.test_auroc.compute())
        # Handle or reset saved outputs as needed
        current_lr = self.trainer.optimizers[0].param_groups[0]["lr"]
        self.log("learning_rate", current_lr, on_epoch=True)


def model_create(path, num_classes=23):
    """
    Create a model instance from a given checkpoint.

    Parameters:
    - checkpoint_path (str): The file path to the PyTorch Lightning checkpoint.

    Returns:
    - model (Myresnext50): The loaded model ready for inference or further training.
    """
    # Instantiate the model with any required configuration
    # model = Myresnext50(
    #     num_classes=num_classes
    # )  # Adjust the number of classes if needed

    # # Load the model weights from a checkpoint
    model = Myresnext50.load_from_checkpoint(path)

    return model


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

    print("output shape", output.shape)

    print("output", output)

    import sys

    sys.exit()

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
        output = output.detach().cpu().numpy()
        print("output numpy shape", output.shape)
        predictions.append(tuple(output))

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


# @ray.remote(num_gpus=num_gpus_per_manager, num_cpus=num_cpus_per_manager)
@ray.remote(num_gpus=1)
class HemeLabelLightningManager:
    """A class representing a HemeLabel Manager that manages the classification of a WSI.

    === Class Attributes ===
    - model : the HemeLabel model
    - ckpt_path : the path to the checkpoint of the HemeLabel model
    - num_classes : the number of classes of the HemeLabel model
    """

    def __init__(self, ckpt_path, num_classes=23) -> None:
        """Initialize the HemeLabelManager object."""

        self.model = model_create(num_classes=num_classes, path=ckpt_path)
        self.ckpt_path = ckpt_path
        self.num_classes = num_classes

    def async_label_wbc_candidate(self, wbc_candidate):
        """Label a WBC candidate."""

        image_transforms = transforms.Compose(
            [
                transforms.Resize(96),
                transforms.ToTensor(),
            ]
        )

        if do_zero_pad:
            image = wbc_candidate.padded_YOLO_bbox_image
        else:
            image = wbc_candidate.snap_shot

        self.model.eval()
        # self.model.to("cpu")
        # self.model.to("cuda") # commented for debugging # TODO we need GPU implementation

        image = image_transforms(image).float().unsqueeze(0)

        # move the image to a cuda tensor
        image = image.to(
            "cuda"
        )  # commented for debugging # TODO we need GPU implementation

        ### BELOW MAY BECOME DEPRECATED ###

        # image = np.array(image)
        # image = cv2.resize(image, (96, 96), interpolation=cv2.INTER_AREA)

        # image = np.einsum('ijk->kij', image)

        # image = image / 255.0
        # # image = np.transpose(image, (2, 0, 1))
        # image = torch.from_numpy(image).float().unsqueeze(0)

        # image = image.to("cuda") # commented for debugging # TODO we need GPU implementation
        output = self.model(image)
        output = torch.flatten(output, start_dim=1).detach().cpu().numpy()

        # make a clone of the output vector, use tuple to avoid deprecation and aliasing errors down the road
        wbc_candidate.softmax_vector = tuple(output[0])

        return wbc_candidate

    def async_label_wbc_candidate_batch(self, wbc_candidates):
        processed_wbc_candidates = []

        if not do_zero_pad:
            pil_images = [wbc_candidate.snap_shot for wbc_candidate in wbc_candidates]
        else:
            pil_images = [
                wbc_candidate.padded_YOLO_bbox_image for wbc_candidate in wbc_candidates
            ]

        results = predict_batch(pil_images, self.model)

        for i, wbc_candidate in enumerate(wbc_candidates):
            wbc_candidate.softmax_vector = results[i]
            processed_wbc_candidates.append(wbc_candidate)

        return processed_wbc_candidates

    def async_save_wbc_image_feature_batch(self, image_paths):
        """For each image, save the image;s feature vector to save_dir."""

        # first read in the batch of images using PIL
        if not do_zero_pad:
            pil_images = [Image.open(image_path) for image_path in image_paths]
        else:
            pil_images = [
                Image.open(image_path).convert("RGB") for image_path in image_paths
            ]

        features = get_features_batch(pil_images, self.model)

        # for each image, save the feature vector
        for i, image_path in enumerate(image_paths):
            # save the feature vector as a torch tensor
            os.makedirs(
                os.path.join(os.path.dirname(image_path), "features"), exist_ok=True
            )

            save_path = os.path.join(
                os.path.dirname(image_path),
                "features",
                os.path.basename(image_path).replace(".jpg", ".pt"),
            )

            torch.save(
                features[i],
                save_path,
            )

        return image_paths


if __name__ == "__main__":
    from LL.resources.BMAassumptions import *

    model = Myresnext50.load_from_checkpoint(HemeLabel_ckpt_path)
    print(model)

    print("Model loaded successfully")

    # generate a list of 10 random PIL images of size 96x96
    pil_images = [Image.new("RGB", (96, 96)) for _ in range(10)]

    # make predictions on the batch of images
    predictions = predict_batch(pil_images, model)
