import os
import torch
import pytorch_lightning as pl
import torch.optim.lr_scheduler as lr_scheduler
import torch.nn.functional as F
import albumentations as A
import numpy as np
import ray
from LL.vision.image_quality import VoL
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader
from torch import nn
from pytorch_lightning.loggers import TensorBoardLogger
from torchvision import transforms, datasets, models
from torchmetrics import Accuracy, AUROC


default_config = {"lr": 3.56e-06}  # 3.56e-07
num_epochs = 100


def get_feat_extract_augmentation_pipeline(image_size):
    """Returns a randomly chosen augmentation pipeline for SSL."""

    ## Simple augumentation to improtve the data generalibility
    transform_shape = A.Compose(
        [
            A.ShiftScaleRotate(p=0.8),
            A.HorizontalFlip(p=0.5),
            A.VerticalFlip(p=0.5),
            A.Affine(shear=(-10, 10), p=0.3),
            A.ISONoise(
                color_shift=(0.01, 0.02),
                intensity=(0.05, 0.01),
                always_apply=False,
                p=0.2,
            ),
        ]
    )
    transform_color = A.Compose(
        [
            A.RandomBrightnessContrast(
                contrast_limit=0.4, brightness_by_max=0.4, p=0.5
            ),
            A.CLAHE(p=0.3),
            A.ColorJitter(p=0.2),
            A.RandomGamma(p=0.2),
        ]
    )

    # compose the two augmentation pipelines
    return A.Compose(
        [A.Resize(image_size, image_size), A.OneOf([transform_shape, transform_color])]
    )


# Define a custom dataset that applies downsampling
class DownsampledDataset(torch.utils.data.Dataset):
    def __init__(self, dataset, downsample_factor, apply_augmentation=True):
        self.dataset = dataset
        self.downsample_factor = downsample_factor
        self.apply_augmentation = apply_augmentation

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, idx):
        image, label = self.dataset[idx]
        if self.downsample_factor > 1:
            size = (512 // self.downsample_factor, 512 // self.downsample_factor)
            image = transforms.functional.resize(image, size)

            if self.apply_augmentation:
                # Apply augmentation
                image = get_feat_extract_augmentation_pipeline(
                    image_size=512 // self.downsample_factor
                )(image=np.array(image))["image"]

        return image, label


# Data Module
class ImageDataModule(pl.LightningDataModule):
    def __init__(self, data_dir, batch_size, downsample_factor):
        super().__init__()
        self.data_dir = data_dir
        self.batch_size = batch_size
        self.downsample_factor = downsample_factor
        self.transform = transforms.Compose(
            [
                transforms.ToTensor(),
                # transforms.Normalize(mean=(0.61070228, 0.54225375, 0.65411311), std=(0.1485182, 0.1786308, 0.12817113))
            ]
        )

    def setup(self, stage=None):
        # Load train, validation and test datasets
        train_dataset = datasets.ImageFolder(
            root=os.path.join(self.data_dir, "train"),
            transform=self.transform,
        )
        val_dataset = datasets.ImageFolder(
            root=os.path.join(self.data_dir, "val"),
            transform=self.transform,
        )
        test_dataset = datasets.ImageFolder(
            root=os.path.join(self.data_dir, "test"),
            transform=self.transform,
        )

        self.train_dataset = DownsampledDataset(
            train_dataset, self.downsample_factor, apply_augmentation=True
        )
        self.val_dataset = DownsampledDataset(
            val_dataset, self.downsample_factor, apply_augmentation=False
        )
        self.test_dataset = DownsampledDataset(
            test_dataset, self.downsample_factor, apply_augmentation=False
        )

    def train_dataloader(self):
        return DataLoader(
            self.train_dataset, batch_size=self.batch_size, shuffle=True, num_workers=20
        )

    def val_dataloader(self):
        return DataLoader(
            self.val_dataset, batch_size=self.batch_size, shuffle=False, num_workers=20
        )

    def test_dataloader(self):
        return DataLoader(
            self.test_dataset, batch_size=self.batch_size, shuffle=False, num_workers=20
        )


# Model Module
class ResNetModel(pl.LightningModule):
    def __init__(self, num_classes=2, config=default_config):
        super().__init__()
        self.model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V1)
        self.model.fc = nn.Linear(self.model.fc.in_features, num_classes)

        assert num_classes >= 2

        if num_classes == 2:
            task = "binary"
        elif num_classes > 2:
            task = "multiclass"

        task = "multiclass"

        self.train_accuracy = Accuracy(task=task, num_classes=num_classes)
        self.val_accuracy = Accuracy(task=task, num_classes=num_classes)
        self.train_auroc = AUROC(num_classes=num_classes, task=task)
        self.val_auroc = AUROC(num_classes=num_classes, task=task)

        self.config = config

    def forward(self, x):
        return self.model(x)

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
        optimizer = torch.optim.Adam(self.model.parameters(), lr=self.config["lr"])

        # T_max is the number of steps until the first restart (here, set to total training epochs).
        # eta_min is the minimum learning rate. Adjust these parameters as needed.
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
        # Handle or reset saved outputs as needed


# Main training loop
def train_model(downsample_factor):
    data_module = ImageDataModule(
        data_dir="/media/hdd2/neo/bma_region_clf_data_full_v2_split",
        batch_size=32,
        downsample_factor=downsample_factor,
    )
    model = ResNetModel(num_classes=2)

    # Logger
    logger = TensorBoardLogger("lightning_logs", name=str(downsample_factor))

    # Trainer configuration for distributed training
    trainer = pl.Trainer(
        max_epochs=num_epochs,
        logger=logger,
        devices=3,
        accelerator="gpu",  # 'ddp' for DistributedDataParallel
    )
    trainer.fit(model, data_module)


from train import ResNetModel
import torch
from torchvision import transforms
from PIL import Image


def load_model_checkpoint(checkpoint_path):
    """
    Load a model checkpoint and return the model object.

    Parameters:
    - checkpoint_path: str, path to the model checkpoint.

    Returns:
    - model: PyTorch model loaded with checkpoint weights.
    """
    # Assuming ResNetModel is defined elsewhere as in your provided code
    model = ResNetModel(
        num_classes=2
    )  # num_classes should match your training configuration
    model.load_state_dict(torch.load(checkpoint_path)["state_dict"])
    return model


def predict_image(model, image):
    """
    Takes a model object and an image path, preprocesses the image, and returns the classification confidence score.

    Parameters:
    - model: The model object for prediction.
    - image_path: str, path to the image file.

    Returns:
    - confidence_score: The confidence score of the classification.
    """
    # Image preprocessing
    preprocess = transforms.Compose(
        [
            transforms.Resize(
                (512, 512)
            ),  # Assuming you want to keep the original size used in training
            transforms.ToTensor(),
        ]
    )

    image = image.convert("RGB")
    image = preprocess(image)
    image = image.unsqueeze(0)  # Add batch dimension

    # move the image to the GPU
    image = image.to("cuda")

    with torch.no_grad():  # Inference without tracking gradients
        outputs = model(image)
        # Assuming binary classification with softmax at the end
        confidence_score = torch.softmax(outputs, dim=1).numpy()[0]

    return float(confidence_score[0])


@ray.remote(num_gpus=1)
class BMAHighMagRegionChecker:
    def __init__(self, ckpt_path):
        self.resnet_model = load_model_checkpoint(ckpt_path)
        self.model.eval()
        # move the model to the GPU
        self.model.to("cuda")

    def resnet_check(self, focus_region):
        image = focus_region.image
        confidence = predict_image(self.model, image)
        focus_region.adequate_confidence_score_high_mag = confidence
        return focus_region

    def VoL_check(self, focus_region):
        vol = VoL(focus_region.image)
        focus_region.VoL_high_mag = vol
        return focus_region

    def check(self, focus_region):
        focus_region = self.resnet_check(focus_region)
        focus_region = self.VoL_check(focus_region)
        return focus_region

    def check_batch(self, focus_regions):
        return [self.check(focus_region) for focus_region in focus_regions]
