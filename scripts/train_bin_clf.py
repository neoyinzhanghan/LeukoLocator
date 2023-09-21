import os
import argparse
import pandas as pd
from sklearn.metrics import f1_score, roc_auc_score
from torchvision import transforms
from torch.utils.data import DataLoader, Dataset
from torchvision.models import resnet50
import torch
import pytorch_lightning as pl
from pytorch_lightning.loggers import TensorBoardLogger
from pytorch_lightning.callbacks import ModelCheckpoint
from torch.utils.data import random_split
from PIL import Image

class CustomDataset(Dataset):
    def __init__(self, dataframe, transform=None):
        self.dataframe = dataframe
        self.transform = transform

    def __len__(self):
        return len(self.dataframe)

    def __getitem__(self, idx):
        img_name = os.path.abspath(self.dataframe.iloc[idx, 0])
        image = Image.open(img_name).convert("RGB")
        label = int(self.dataframe.iloc[idx, 1])

        if self.transform:
            image = self.transform(image)

        return image, label

class ImageClassifier(pl.LightningModule):
    def __init__(self):
        super(ImageClassifier, self).__init__()
        self.model = resnet50(pretrained=True)
        in_features = self.model.fc.in_features
        self.model.fc = torch.nn.Linear(in_features, 1)
        self.criterion = torch.nn.BCEWithLogitsLoss()

    def forward(self, x):
        return self.model(x)

    def training_step(self, batch, batch_idx):
        x, y = batch
        y = y.float().view(-1, 1)
        logits = self(x)
        loss = self.criterion(logits, y)
        self.log('train_loss', loss)
        return loss

    def validation_step(self, batch, batch_idx):
        x, y = batch
        y = y.float().view(-1, 1)
        logits = self(x)
        loss = self.criterion(logits, y)
        self.log('val_loss', loss)
        return {'val_loss': loss, 'y': y, 'logits': logits}

    def validation_epoch_end(self, outputs):
        avg_loss = torch.stack([x['val_loss'] for x in outputs]).mean()
        logits = torch.cat([x['logits'] for x in outputs])
        y = torch.cat([x['y'] for x in outputs])
        f1 = f1_score(y.cpu(), torch.round(torch.sigmoid(logits)).cpu())
        auc = roc_auc_score(y.cpu(), torch.sigmoid(logits).cpu())
        self.log('avg_val_loss', avg_loss)
        self.log('val_f1', f1)
        self.log('val_auc', auc)

    def configure_optimizers(self):
        optimizer = torch.optim.Adam(self.parameters(), lr=1e-3)
        return optimizer

def main(args):
    transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.ToTensor()
    ])
    
    df = pd.read_csv(args.csv_file)
    train_df = df[df['split'] == 'train']
    val_df = df[df['split'] == 'val']
    
    train_dataset = CustomDataset(dataframe=train_df, transform=transform)
    val_dataset = CustomDataset(dataframe=val_df, transform=transform)
    
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, num_workers=args.num_workers)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False, num_workers=args.num_workers)
    
    model = ImageClassifier()
    
    logger = TensorBoardLogger('lightning_logs', name='image_classifier')
    checkpoint_callback = ModelCheckpoint(monitor='avg_val_loss', save_top_k=1, mode='min')
    
    trainer = pl.Trainer(
        devices=args.gpus,
        max_epochs=args.epochs,
        logger=logger,
        callbacks=[checkpoint_callback],
        accelerator="ddp" if args.gpus > 1 else None
    )
    
    trainer.fit(model, train_loader, val_loader)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv_file', type=str, required=True, help="Path to the CSV file containing the dataset.")
    parser.add_argument('--batch_size', type=int, default=32, help="Batch size for training.")
    parser.add_argument('--num_workers', type=int, default=4, help="Number of workers for data loading.")
    parser.add_argument('--epochs', type=int, default=10, help="Number of epochs to train.")
    parser.add_argument('--gpus', type=int, default=1, help="Number of GPUs. Set to 0 for CPU.")

    args = parser.parse_args()
    main(args)
