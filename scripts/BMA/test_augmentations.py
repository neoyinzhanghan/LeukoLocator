from PIL import Image
import numpy as np
import albumentations as A
import io
import matplotlib.pyplot as plt

# Load the image
img_path = '/Users/neo/Documents/Research/DeepHeme/LLResults/V2-full extract/H23-852;S12;MSKW - 2023-06-15 16.42.50/cells/L2/L2-M1-ER4-ER3_1738-5.jpg'
image = np.array(Image.open(img_path))

# Define the augmentation pipeline as per the user's script
def get_feat_extract_augmentation_pipeline(image_size):
    """Returns a randomly chosen augmentation pipeline for SSL."""

    # Simple augmentation to improve the data generability
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

    # Compose the two augmentation pipelines
    return A.Compose(
        [A.Resize(image_size, image_size), A.OneOf([transform_shape, transform_color])]
    )

# Apply the augmentation pipeline to the image 5 times
augmented_images = []
for i in range(20):
    augmentation_pipeline = get_feat_extract_augmentation_pipeline(image.shape[0])
    augmented_images.append(augmentation_pipeline(image=image)['image'])

# Display the augmented images
fig, axs = plt.subplots(4, 5, figsize=(20, 10))
for i, ax in enumerate(axs.flatten()):
    ax.imshow(augmented_images[i])
    ax.axis('off')

plt.show()