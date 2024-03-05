import os
import csv
import ray
from tqdm.auto import tqdm

from LL.vision.ad_hoc_image_metric_functions import ResNetModelActor

ray.init(num_cpus=20, num_gpus=2)

def batch_process_images(image_paths, actor, batch_size=32):
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

first_actors = {n: ResNetModelActor.remote(n) for n in downsampling_factors}
second_actors = {n: ResNetModelActor.remote(n) for n in downsampling_factors}

fieldnames = ['Image Name'] + [f'ResNet_{n}' for n in downsampling_factors]
with open(output_csv, 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    
    for image_path in tqdm(image_files, desc="Processing Images"):
        row = {'Image Name': os.path.basename(image_path)}
        for n in downsampling_factors:
            image_batch = [image_path]  # Placeholder for actual batch processing
            # Launch both tasks in parallel
            future_first = first_actors[n].predict_batch.remote(image_batch)
            future_second = second_actors[n].predict_batch.remote(image_batch)
            # Wait for both tasks to complete and then combine their results
            score_first, score_second = ray.get([future_first, future_second])
            # Averaging the scores for demonstration; modify as needed
            averaged_score = (score_first[0] + score_second[0]) / 2
            row[f'ResNet_{n}'] = averaged_score
        writer.writerow(row)

print(f"ResNet scores for all images have been saved to {output_csv}")
