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

from PIL import Image as pil_image

transform = transforms.Compose(
    [
        transforms.Resize((256, 256)),
        transforms.ToTensor(),
    ]
)


class Myresnext50(nn.Module):
    def __init__(self, my_pretrained_model, num_classes=3):
        super(Myresnext50, self).__init__()
        self.pretrained = my_pretrained_model
        self.my_new_layers = nn.Sequential(
            nn.Linear(1000, 100), nn.ReLU(), nn.Linear(100, num_classes)
        )
        self.num_classes = num_classes

    def forward(self, x):
        x = self.pretrained(x)
        x = self.my_new_layers(x)

        pred = torch.sigmoid(x.reshape(x.shape[0], 1, self.num_classes))
        return pred
    
    def load_from_checkpoint(ckpt_path):
        # Load the model from a checkpoint
        model = torch.load(ckpt_path)
        return model


def load_clf_model(ckpt_path):
    """Load the classifier model."""

    # To deploy a checkpoint and use for inference
    trained_model = Myresnext50.load_from_checkpoint(
        ckpt_path
    )  # , map_location=torch.device("cpu"))
    trained_model.freeze()

    # move the model to the GPU
    trained_model.to("cuda")

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

    transform_pipeline = albumentations.Compose(
        [
            albumentations.Normalize(
                mean=(0.5637, 0.5637, 0.5637), std=(0.2381, 0.2381, 0.2381)
            ),
        ]
    )

    # Transform each image and stack them into a batch
    batch = torch.stack([transform(image.convert("RGB")) for image in pil_images])

    # Move the batch to the GPU
    batch = batch.to("cuda")

    with torch.no_grad():  # No need to compute gradients for inference
        logits = model(batch)
        probs = torch.softmax(logits, dim=1)

        peripheral_confidence_scores = probs[
            :, 1
        ].tolist()  # Get confidence score for label `1` for each image
        clot_confidence_scores = probs[
            :, 2
        ].tolist()  # Get confidence score for label `2` for each image
        adequate_confidence_scores = probs[
            :, 0
        ].tolist()  # Get confidence score for label `0` for each image

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
    """

    def __init__(self, ckpt_path):
        """Initialize the RegionClfManager object."""

        self.model = load_clf_model(ckpt_path)
        self.ckpt_path = ckpt_path

    def async_predict_batch_key_dct(self, batch_key, dct):
        """Classify the focus region probability score."""

        focus_regions = [dct[k] for k in batch_key]
        pil_images = [focus_region.image for focus_region in focus_regions]

        confidence_scores = predict_batch(pil_images, self.model)

        for i in range(len(pil_images)):
            focus_regions[i].resnet_confidence_score = confidence_scores[i]

        processed_batch = {}

        for focus_region in focus_regions:
            processed_batch[focus_region.idx] = focus_region

        return processed_batch
