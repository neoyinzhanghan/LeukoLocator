import os
import torch
import pytorch_lightning as pl
from torch import nn
from torch.nn import functional as F
from torchvision import transforms
from torchvision.datasets import ImageFolder
from torchvision.models import resnet50, ResNet50_Weights
from torch.utils.data import DataLoader
from PIL import Image
from LL.resources.assumptions import specimen_clf_checkpoint_path

class_dct = {
    0: "Bone Marrow Aspirate",
    1: "Manual Peripheral Blood or Inadequate Bone Marrow Aspirate",
    2: "Others",
    3: "Peripheral Blood",
}


class ImageDataModule(pl.LightningDataModule):
    def __init__(self, data_dir: str, batch_size: int = 32):
        super().__init__()
        self.data_dir = data_dir
        self.batch_size = batch_size

        # Define transformations
        self.transform = transforms.Compose(
            [
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
                ),
            ]
        )

    def setup(self, stage=None):
        if stage == "fit" or stage is None:
            self.train_dataset = ImageFolder(
                os.path.join(self.data_dir, "train"), self.transform
            )
            self.val_dataset = ImageFolder(
                os.path.join(self.data_dir, "val"), self.transform
            )

    def train_dataloader(self):
        return DataLoader(
            self.train_dataset, batch_size=self.batch_size, shuffle=True, num_workers=24
        )

    def val_dataloader(self):
        return DataLoader(self.val_dataset, batch_size=self.batch_size, num_workers=24)


class ResNetClassifier(pl.LightningModule):
    def __init__(
        self,
        num_classes: int,
        learning_rate: float = 0.001,
        use_pretrained_weights=True,
    ):
        super().__init__()
        self.save_hyperparameters()
        if use_pretrained_weights:
            weights = ResNet50_Weights.IMAGENET1K_V1
        else:
            weights = None
        self.model = resnet50(weights=weights)
        in_features = self.model.fc.in_features
        self.model.fc = nn.Linear(in_features, num_classes)
        self.learning_rate = learning_rate

        # ... rest of your class code ...

    def forward(self, x):
        return self.model(x)

    def training_step(self, batch, batch_idx):
        x, y = batch
        logits = self(x)
        loss = F.cross_entropy(logits, y)
        self.log("train_loss", loss)

        # Calculate and log additional metrics
        preds = torch.argmax(logits, dim=1)
        self.log("train_acc", self.train_accuracy(preds, y))
        self.log("train_f1", self.train_f1(preds, y))
        self.log("train_auroc", self.train_auroc(F.softmax(logits, dim=1), y))

        return loss

    def validation_step(self, batch, batch_idx):
        x, y = batch
        logits = self(x)
        loss = F.cross_entropy(logits, y)
        self.log("val_loss", loss)

        # Calculate and log additional metrics
        preds = torch.argmax(logits, dim=1)
        self.log("val_acc", self.val_accuracy(preds, y))
        self.log("val_f1", self.val_f1(preds, y))
        self.log("val_auroc", self.val_auroc(F.softmax(logits, dim=1), y))

        return loss

    def configure_optimizers(self):
        optimizer = torch.optim.Adam(self.parameters(), lr=self.learning_rate)
        return optimizer


def main():
    # Set data directory
    data_dir = "/media/hdd3/neo/topviews_1k_split"

    # Set the number of classes in your dataset
    num_classes = 4

    # Initialize the data module and model
    data_module = ImageDataModule(data_dir)
    model = ResNetClassifier(num_classes=num_classes)

    # Initialize PyTorch Lightning trainer
    trainer = pl.Trainer(max_epochs=100, devices=3, accelerator="gpu")
    trainer.fit(model, data_module)


# Function to load the model from a checkpoint
def load_model_from_checkpoint(checkpoint_path, num_classes):
    model = ResNetClassifier.load_from_checkpoint(
        checkpoint_path, num_classes=num_classes
    )
    model.eval()  # Set the model to evaluation mode
    return model


def predict_image(model, image):
    # Define the same transformations as used during training
    transform = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Lambda(
                lambda x: x[:3, :, :]
            ),  # Keep only the first three channels
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )

    image = transform(image).unsqueeze(0)  # Add batch dimension

    # Move the image tensor to the same device as the model
    device = next(model.parameters()).device  # Get the device of the model
    image = image.to(device)

    # Perform inference
    with torch.no_grad():
        logits = model(image)
        predictions = torch.argmax(logits, dim=1)
    return class_dct[predictions.item()]


def get_region_type(image_path):
    # Load the model from the checkpoint
    model = load_model_from_checkpoint(
        specimen_clf_checkpoint_path,
        num_classes=4,
    )

    # Perform inference
    region_type = predict_image(model, image_path)

    return region_type
