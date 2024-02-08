import os
import shutil
import matplotlib.pyplot as plt
from PIL import Image
from torchvision import transforms as T
from cell_segmentation.inference.inference_cellvit_experiment_pannuke import InferenceCellViT, InferenceCellViTParser


def run_one_image(inf_class, image_path):
    # Load the image
    image = Image.open(image_path).convert("RGB")

    # Define the transformation
    transform = T.Compose(
        [
            T.Resize((224, 224)),  # Resize the image to 224x224
            T.ToTensor(),  # Convert the image to a tensor
        ]
    )

    # Apply the transformation to the image
    batch = transform(image).unsqueeze(0)  # Unsqueeze to add the batch dimension
    # tensor_image now has shape (1, 3, 224, 224)

    inf_class.logger.info("Loading inference transformations")

    transform_settings = inf_class.run_conf["transformations"]
    if "normalize" in transform_settings:
        mean = transform_settings["normalize"].get("mean", (0.5, 0.5, 0.5))
        std = transform_settings["normalize"].get("std", (0.5, 0.5, 0.5))
    else:
        mean = (0.5, 0.5, 0.5)
        std = (0.5, 0.5, 0.5)
    inf_class.inference_transforms = T.Compose(
        [T.ToTensor(), T.Normalize(mean=mean, std=std)]
    )

    # patches = batch[0].to(inf_class.device)
    batch = batch.to(inf_class.device)

    # print the dimensions of the patches
    # print("Patches shape: {}".format(patches.shape))
    # print("Batch shape: {}".format(batch.shape))
    inf_class.logger.info("Patches shape: {}".format(batch.shape))

    model = inf_class.get_model(model_type='CellViT256')

    # move the model to the GPU
    model.to(inf_class.device)

    predictions = model.forward(batch, retrieve_tokens=True)

    predictions = inf_class.unpack_predictions(predictions=predictions, model=model)

    print(predictions.hv_map)

    # this has shape (1,2,224,224)
    # make two heatmaps for the two classes and save them in run_dir
    for i in range(2):
        heatmap = predictions.hv_map[0, i, :, :].cpu().detach().numpy()
        plt.imsave(
            os.path.join(inf_class.run_dir, f"heatmap_{i}.png"),
            heatmap,
            cmap="gray",
        )

    # copy the image from image_path to run_dir
    shutil.copy(image_path, inf_class.run_dir)
    
    # for each element of the dictionary, print the shape of the tensor


if __name__ == "__main__":


    image_path = "/media/hdd1/pannuke/images/train/image_0035.jpg"

    print("Running the inference on", image_path, "\n")

    configuration_parser = InferenceCellViTParser()
    configuration = configuration_parser.parse_arguments()
    print(configuration)
    inf_class = InferenceCellViT(
        run_dir=configuration["run_dir"],
        checkpoint_name=configuration["checkpoint_name"],
        gpu=0,
        magnification=configuration["magnification"],
    )
    
    prediction = run_one_image(inf_class, image_path)