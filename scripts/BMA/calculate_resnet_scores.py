import os
import csv
import ray
import numpy as np
from tqdm.auto import tqdm

# Assume these are defined as per your context
from LL.vision.ad_hoc_image_metric_functions import ResNetModelActor
from your_module import create_list_of_batches_from_list

ray.shutdown()
print("Ray initialization for ResNet confidence score")
ray.init(num_cpus=12, num_gpus=3)  # Adjust based on your setup
print("Ray initialization for ResNet confidence score done")

pooled_dir = "/media/hdd3/neo/results_bma_v4_regions_pooled"
output_csv = os.path.join(pooled_dir, "resnet_scores.csv")
downsampling_factors = [1, 2, 4, 8, 16]
num_resnet_model_actors = 3  # Or adjust based on your resources and needs

image_files = [os.path.join(pooled_dir, f) for f in os.listdir(pooled_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff'))]

# Assuming downsampling_factors influence batch creation in some way
list_of_batches = create_list_of_batches_from_list(image_files, batch_size=12)  # Adjust batch_size as needed

resnet_model_actors = [
    ResNetModelActor.remote(n) for n in range(num_resnet_model_actors)
]

tasks = {}
resnet_scores = {}

with tqdm(total=len(image_files), desc="Processing Images for ResNet Scores") as pbar:
    for i, batch in enumerate(list_of_batches):
        actor = resnet_model_actors[i % num_resnet_model_actors]
        task = actor.predict_batch.remote(batch)
        tasks[task] = batch

    while tasks:
        done_ids, _ = ray.wait(list(tasks.keys()), num_returns=len(tasks))

        for done_id in done_ids:
            try:
                results = ray.get(done_id)
                for file_path, score in zip(tasks[done_id], results):
                    resnet_scores[os.path.basename(file_path)] = score
                pbar.update(len(tasks[done_id]))

            except Exception as e:  # Consider specifying the exception if possible
                print(f"Task for batch {tasks[done_id]} failed with error: {e}")
            del tasks[done_id]

# Assuming the next steps involve saving the scores to a CSV
fieldnames = ['Image Name', 'ResNet_Score']
with open(output_csv, 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for image_name, score in resnet_scores.items():
        writer.writerow({'Image Name': image_name, 'ResNet_Score': score})

print(f"ResNet scores for all images have been saved to {output_csv}")
ray.shutdown()
