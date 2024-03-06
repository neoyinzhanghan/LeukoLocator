import numpy as np
import ray
from LL.vision.image_quality import VoL, WMP
from LL.brain.BMARegionClfManager import load_clf_model, predict_batch, load_clf_model_cpu, predict_batch_cpu
from PIL import Image

def VoL_n(image_path, n):
    """Compute the VoL of an image, the variance is computed after removing all data sds standard deviations away from the mean.
    The image must be a PIL RGB image."""
    image = Image.open(image_path)
    image = image.resize((image.width // n, image.height // n))
    return VoL(image)

def WMP_n(image_path, n):
    """Compute the otsu white mask's white pixel proportion of an image.
    The image must be a PIL RGB image."""
    image = Image.open(image_path)
    image = image.resize((image.width // n, image.height // n))
    return float(WMP(image)[0])

def RBI_n(image_path, n):
    """Compute the sum of the blue channel intensities divided by the sum of all channel intensities for the downsampled image by a factor of n."""
    image = Image.open(image_path)
    image = image.resize((image.width // n, image.height // n), Image.ANTIALIAS)
    image = np.array(image)
    # Corrected to index 2 for the blue channel
    blue_sum = np.sum(image[:, :, 2])
    total_sum = np.sum(image)
    return blue_sum / total_sum

def RGI_n(image_path, n):
    """Compute the sum of the green channel intensities divided by the sum of all channel intensities for the downsampled image by a factor of n."""
    image = Image.open(image_path)
    image = image.resize((image.width // n, image.height // n), Image.ANTIALIAS)
    image = np.array(image)
    # Corrected to index 1 for the green channel
    green_sum = np.sum(image[:, :, 1])
    total_sum = np.sum(image)
    return green_sum / total_sum

def RRI_n(image_path, n):
    """Compute the sum of the red channel intensities divided by the sum of all channel intensities for the downsampled image by a factor of n."""
    image = Image.open(image_path)
    image = image.resize((image.width // n, image.height // n), Image.ANTIALIAS)
    image = np.array(image)
    # Corrected to index 0 for the red channel
    red_sum = np.sum(image[:, :, 0])
    total_sum = np.sum(image)
    return red_sum / total_sum


####################################################################################################
# This part is for defining the ResNet_n function
####################################################################################################

checkpoint_path_dct = {
    1: "/media/hdd3/neo/MODELS/2024-03-04 Region Clf Binary/lightning_logs/1/version_0/checkpoints/epoch=99-step=5500.ckpt",
    2: "/media/hdd3/neo/MODELS/2024-03-04 Region Clf Binary/lightning_logs/2/version_0/checkpoints/epoch=99-step=5500.ckpt",
    4: "/media/hdd3/neo/MODELS/2024-03-04 Region Clf Binary/lightning_logs/4/version_0/checkpoints/epoch=99-step=5500.ckpt",
    8: "/media/hdd3/neo/MODELS/2024-03-04 Region Clf Binary/lightning_logs/8/version_0/checkpoints/epoch=99-step=5500.ckpt",
    16: "/media/hdd3/neo/MODELS/2024-03-04 Region Clf Binary/lightning_logs/16/version_0/checkpoints/epoch=99-step=5500.ckpt"
}

@ray.remote(num_gpus=1)
class ResNetModelActor:
    def __init__(self, n):
        assert n in checkpoint_path_dct, f"Invalid downsampling factor: {n}"
        # Assume load_clf_model_cpu loads the model correctly and is adjusted for CPU or GPU usage as needed
        self.model = load_clf_model(checkpoint_path_dct[n])
        self.n = n

    def predict_batch(self, image_paths):

        images = [Image.open(image_path) for image_path in image_paths]

        n = self.n
        # subsample the images by the factor of n
        images = [image.resize((image.width // n, image.height // n), Image.ANTIALIAS) for image in images]

        return predict_batch(images, self.model)