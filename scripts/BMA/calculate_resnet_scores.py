import os
import csv
import ray
from tqdm.auto import tqdm

from LL.vision.ad_hoc_image_metric_functions import ResNetModelActor

ray.init(num_cpus=12, num_gpus=3)

def batch_process_images(image_paths, actor, batch_size=12):
    """Process images in batches and collect ResNet scores."""
    num_images = len(image_paths)
    scores = []
    for start_idx in range(0, num_images, batch_size):
        end_idx = min(start_idx + batch_size, num_images)
        batch = image_paths[start_idx:end_idx]
        scores.extend(ray.get(actor.predict_batch.remote(batch)))
    return scores

pooled_dir = "/media/hdd3/neo/results_bma_v4_regions_pooled"
output_csv = os.path.join(pooled_dir, "resnet_scores.csv")
downsampling_factors = [1, 2, 4, 8, 16]

image_files = [os.path.join(pooled_dir, f) for f in os.listdir(pooled_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff'))]

# Assuming M actors and you have 3 GPUs
M = 3  # This matches the number of available GPUs

# Create M sets of actors for each downsampling factor
# Ensure each actor is allocated a maximum of 1 GPU.
actor_sets = [[ResNetModelActor.options(num_gpus=1).remote(n) for n in downsampling_factors] for _ in range(M)]

fieldnames = ['Image Name'] + [f'ResNet_{n}' for n in downsampling_factors]
with open(output_csv, 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    
    for image_path in tqdm(image_files, desc="Processing Images"):
        row = {'Image Name': os.path.basename(image_path)}
        for n in downsampling_factors:
            image_batch = [image_path]
            # Launch tasks in parallel for all actor sets
            futures = [actor_sets[i][n].predict_batch.remote(image_batch) for i in range(M)]
            # Wait for all tasks to complete
            scores = ray.get(futures)
            # Combine the results, e.g., averaging the scores
            averaged_score = sum(scores) / len(scores)
            row[f'ResNet_{n}'] = averaged_score
        writer.writerow(row)

print(f"ResNet scores for all images have been saved to {output_csv}")
