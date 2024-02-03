import torch
import torchvision.models as models
import ray
import torchvision.models as models
import pytorch_lightning as pl
import torchmetrics
import torch.nn as nn
import albumentations

from LL.resources.BMAassumptions import *
from torchvision import transforms
from torchvision.models import resnext50_32x4d
from PIL import Image as pil_image
from collections import OrderedDict


def remove_data_parallel(old_state_dict):
    new_state_dict = OrderedDict()

    for k, v in old_state_dict.items():
        name = k[7:]  # remove `module.`

        new_state_dict[name] = v

    return new_state_dict


transform = transforms.Compose(
    [
        transforms.Resize((256, 256)),
        transforms.ToTensor(),
    ]
)


# Assuming ResNetModel is defined as before
class ResNetModel(pl.LightningModule):
    def __init__(self, num_classes=3):
        super().__init__()
        self.model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V1)
        self.model.fc = nn.Linear(self.model.fc.in_features, num_classes)

    def forward(self, x):
        return self.model(x)


def load_clf_model(ckpt_path):
    """Load the classifier model."""

    # To deploy a checkpoint and use for inference
    trained_model = ResNetModel.load_from_checkpoint(
        ckpt_path
    )  # , map_location=torch.device("cpu"))

    # move the model to the GPU
    trained_model.to("cuda")

    # turn off the training mode
    trained_model.eval()

    return trained_model


def predict_batch(pil_images, model):
    """
    Predict the confidence scores for a batch of PIL images.

    Parameters:
    - pil_images (list of PIL.Image.Image): List of input PIL Image objects.
    - model (torch.nn.Module): Trained model.

    Returns:
    - list of float: List of confidence scores for the class label `1` for each image.
    """

    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
    ])

    # Transform each image and stack them into a batch
    batch = torch.stack([transform(image.convert("RGB")) for image in pil_images])

    # Move the batch to the GPU
    batch = batch.to("cuda")

    with torch.no_grad():  # No need to compute gradients for inference
        logits = model(batch)
        probs = torch.softmax(logits, dim=1)

        # prob shape is [44, 1, 3]
        peripheral_confidence_scores = probs[:, 0].cpu().numpy()
        clot_confidence_scores = probs[:, 1].cpu().numpy()
        adequate_confidence_scores = probs[:, 2].cpu().numpy()

    return (
        peripheral_confidence_scores,
        clot_confidence_scores,
        adequate_confidence_scores,
    )


# @ray.remote(num_gpus=num_gpus_per_manager, num_cpus=num_cpus_per_manager)
@ray.remote(num_gpus=1)
class RegionClfManager:
    """A class representing a manager that classifies regions.

    === Class Attributes ===
    - model : the region classification model
    - ckpt_path : the path to the checkpoint of the region classification model
    - conf_thres : the confidence threshold of the region classification model
    - max_num_regions : the maximum number of regions to classify
    """

    def __init__(self, ckpt_path):
        """Initialize the RegionClfManager object."""

        self.model = load_clf_model(ckpt_path)
        self.ckpt_path = ckpt_path

    def async_predict_batch_key_dct(self, focus_regions):
        """Classify the focus region probability score."""

        pil_images = [focus_region.downsampled_image for focus_region in focus_regions]

        confidence_scores = predict_batch(pil_images, self.model)
        (
            peripheral_confidence_scores,
            clot_confidence_scores,
            adequate_confidence_scores,
        ) = confidence_scores

        for i in range(len(pil_images)):
            focus_regions[i].peripheral_confidence_score = float(
                peripheral_confidence_scores[i]
            )
            focus_regions[i].clot_confidence_score = float(clot_confidence_scores[i])
            focus_regions[i].adequate_confidence_score = float(
                adequate_confidence_scores[i]
            )

        processed_batch = {}

        for focus_region in focus_regions:
            processed_batch[focus_region.idx] = focus_region

        return processed_batch
