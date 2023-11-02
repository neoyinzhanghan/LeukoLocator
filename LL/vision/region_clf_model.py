import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
import torchvision.models as models
import pytorch_lightning as pl
import torchmetrics
import pandas as pd
from PIL import Image


# Define a custom LightningModule
class ResNet50Classifier(pl.LightningModule):
    def __init__(self, learning_rate=0.001):
        super(ResNet50Classifier, self).__init__()

        self.resnet50 = models.resnet50(weights='ResNet50_Weights.IMAGENET1K_V1')
        num_features = self.resnet50.fc.in_features
        self.resnet50.fc = torch.nn.Linear(num_features, 2)  # Binary classification
        self.loss_fn = torch.nn.CrossEntropyLoss()
        self.lr = learning_rate

        self.f1_score = torchmetrics.F1Score(num_classes=2, task="binary")
        self.auc = torchmetrics.AUROC(pos_label=1, task="binary")
        self.acc = torchmetrics.Accuracy(task="binary")

        self.validation_step_outputs = []

    def forward(self, x):
        return self.resnet50(x)

    def training_step(self, batch, batch_idx):
        x, y = batch
        logits = self(x)
        loss = self.loss_fn(logits, y)
        probs = torch.softmax(logits, dim=1)[:, 1]

        # Update and log the metrics with current batch values
        self.log(
            "train_loss", loss, on_step=True, on_epoch=True, prog_bar=True, logger=True
        )

        # Log the F1 score
        train_f1 = self.f1_score(probs.round(), y)
        self.log(
            "train_f1",
            train_f1,
            on_step=True,
            on_epoch=True,
            prog_bar=True,
            logger=True,
        )

        # Log the AUC
        train_auc = self.auc(probs, y)
        self.log(
            "train_auc",
            train_auc,
            on_step=True,
            on_epoch=True,
            prog_bar=True,
            logger=True,
        )

        # Log the accuracy
        train_acc = self.acc(probs.round(), y)
        self.log(
            "train_acc",
            train_acc,
            on_step=True,
            on_epoch=True,
            prog_bar=True,
            logger=True,
        )

        return loss

    def validation_step(self, batch, batch_idx):
        x, y = batch
        logits = self(x)
        loss = self.loss_fn(logits, y)
        probs = torch.softmax(logits, dim=1)[:, 1]

        # Update the metrics with current batch values
        f1_score = self.f1_score(probs.round(), y)
        auc_val = self.auc(probs, y)
        acc_val = self.acc(probs.round(), y)

        self.validation_step_outputs.append(loss)

        return {"val_loss": loss, "probs": probs, "labels": y}

    def on_validation_epoch_end(self):
        avg_loss = torch.stack(self.validation_step_outputs).mean()

        # Get the aggregated metric values
        avg_f1 = self.f1_score.compute()
        avg_auc = self.auc.compute()
        avg_acc = self.acc.compute()

        # Log the aggregated metric values
        self.log("val_loss", avg_loss)
        self.log("val_auc", avg_auc)
        self.log("val_f1", avg_f1)
        self.log("val_acc", avg_acc)

        # Optionally, reset the metrics at the end of validation
        self.f1_score.reset()
        self.auc.reset()
        self.acc.reset()

    def configure_optimizers(self):
        optimizer = torch.optim.SGD(self.parameters(), lr=self.lr, momentum=0.9)
        return optimizer
