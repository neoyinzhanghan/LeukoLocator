import os
import csv
import ray
from tqdm.auto import tqdm

from LL.vision.ad_hoc_image_metric_functions import ResNetModelActor

def batch_process_images(image_paths, actor, batch_size=32):
    """Process images in batches and collect ResNet scores."""
    num_images = len(image_paths)
    scores = []
    for start_idx in range(0, num_images, batch_size):
        end_idx = min(start_idx + batch_size, num_images)
        batch = image_paths[start_idx:end_idx]
        scores.extend(ray.get(actor.predict.remote(batch)))
    return scores

pooled_dir = "/media/hdd3/neo/results_bma_v4_regions_pooled"
output_csv = os.path.join(pooled_dir, "resnet_scores.csv")
downsampling_factors = [1, 2, 4, 8, 16]

# Assuming you've defined a function `get_image_batch` that loads and preprocesses images for prediction
image_files = [os.path.join(pooled_dir, f) for f in os.listdir(pooled_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff'))]

actors = {n: ResNetModelActor.remote(n) for n in downsampling_factors}

fieldnames = ['Image Name'] + [f'ResNet_{n}' for n in downsampling_factors]
with open(output_csv, 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    
    for image_path in tqdm(image_files, desc="Processing Images"):
        row = {'Image Name': os.path.basename(image_path)}
        for n, actor in actors.items():
            # Here you should load and preprocess the image or images for the batch
            image_batch = [image_path]  # Placeholder for actual batch processing
            score = batch_process_images(image_batch, actor, batch_size=1)  # Adjust batch size as needed
            row[f'ResNet_{n}'] = score[0]
        writer.writerow(row)

print(f"ResNet scores for all images have been saved to {output_csv}")
