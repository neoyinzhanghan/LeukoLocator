import os
import shutil
import matplotlib.pyplot as plt
import random
from PIL import Image
from torchvision import transforms as T
from cell_segmentation.inference.inference_cellvit_experiment_pannuke import InferenceCellViT, InferenceCellViTParser

# Function to generate a random color
def random_color():
    return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

def run_one_image(inf_class, image_path):
    # Load the image
    image = Image.open(image_path).convert("RGB")
    transform_settings = inf_class.run_conf["transformations"]

    if "normalize" in transform_settings:
        mean = transform_settings["normalize"].get("mean", (0.5, 0.5, 0.5))
        std = transform_settings["normalize"].get("std", (0.5, 0.5, 0.5))
    else:
        mean = (0.5, 0.5, 0.5)
        std = (0.5, 0.5, 0.5)
        

    inf_class.logger.info("Loading inference transformations")
    transforms = T.Compose([T.ToTensor(), T.Normalize(mean=mean, std=std)])

    # Apply the transformation to the image
    batch = transforms(image).unsqueeze(0)  # Unsqueeze to add the batch dimension

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

    print(predictions.instance_map[0].shape)

    # Each instance has its own integer, starting from 1. Shape: (H, W)
    # save all the instances as a binary mask image in run_dir/results as ins_1, ins_2 ,...
    num_instances = int(predictions.instance_map[0].max())

    # print the number of instances
    print("Number of instances: {}".format(num_instances))

    # Create the results directory if it does not exist
    results_dir = os.path.join(inf_class.run_dir, "results")

    if not os.path.exists(results_dir):
        os.makedirs(results_dir)

    # Save the instance map as a binary mask
    for i in range(1, num_instances + 1):
        instance_mask = predictions.instance_map[0] == i
        instance_mask = instance_mask.cpu().numpy().astype("uint8") * 255
        instance_mask = Image.fromarray(instance_mask)
        instance_mask.save(os.path.join(results_dir, f"ins_{i}.png"))

    # cope the image_path to the results directory
    shutil.copy(image_path, os.path.join(results_dir, "image.png"))

    # Ensure num_instances is defined; for example, it might be the max label in your instance_map
    num_instances = int(predictions.instance_map.max())

    # Load the original image
    original_image = Image.open(image_path).convert("RGB")

    # Overlay each instance mask on the original image with a random color
    for i in range(1, num_instances + 1):
        # Load the binary mask
        instance_mask = predictions.instance_map[0] == i
        instance_mask = instance_mask.cpu().numpy().astype("uint8") * 255
        instance_mask = Image.fromarray(instance_mask).convert("L")  # Ensure it's greyscale

        # Generate a random color for the instance
        color = random_color()

        # Create an RGB image of the same size as the original image but filled with the random color
        colored_mask = Image.new("RGB", original_image.size, color=color)

        # Apply the binary mask as an alpha mask to overlay the colored mask onto the original image
        original_image.paste(colored_mask, (0,0), instance_mask)

    # Save or display the modified original image
    original_image.save(os.path.join(results_dir, "image_with_masks.png"))
    # or use original_image.show() to display the image
if __name__ == "__main__":


    image_path = "/media/hdd1/neo/pannuke/images/train/image_0076.jpg"

    print("Running the inference on", image_path, "\n")

    configuration_parser = InferenceCellViTParser()
    configuration = configuration_parser.parse_arguments()
    print(configuration)
    inf_class = InferenceCellViT(
        run_dir=configuration["run_dir"],
        checkpoint_name="CellViT-256-x40.pth",
        gpu=0,
        magnification=40,
    )

    prediction = run_one_image(inf_class, image_path)