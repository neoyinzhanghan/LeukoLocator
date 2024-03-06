import os
import csv
import ray
from tqdm.auto import tqdm

# Assuming these are predefined
from LL.vision.ad_hoc_image_metric_functions import ResNetModelActor
from LL.brain.utils import create_list_of_batches_from_list

ray.shutdown()
print("Initializing Ray for ResNet confidence score...")
ray.init()  # Adjust based on your setup
print("Ray initialization done.")

pooled_dir = "/media/hdd3/neo/results_bma_v4_regions_pooled"
output_csv = os.path.join(pooled_dir, "resnet_scores.csv")
downsampling_factors = [1, 2, 4, 8, 16]

image_files = [os.path.join(pooled_dir, f) for f in os.listdir(pooled_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff'))]

# Adjust the number of actors based on your resources and needs
num_resnet_model_actors = 3  

resnet_scores = {}

ray.init()  # Initialize Ray outside the loop, adjusted for your setup

for n in downsampling_factors:
    print(f"Processing with downsampling factor {n}...")

    # Create actors for this specific downsampling factor
    resnet_model_actors = [ResNetModelActor.remote(n) for _ in range(num_resnet_model_actors)]
    
    # Prepare your batches
    list_of_batches = create_list_of_batches_from_list(image_files, batch_size=12)

    tasks = {}
    
    with tqdm(total=len(image_files), desc=f"Processing for factor {n}") as pbar:
        for i, batch in enumerate(list_of_batches):
            actor = resnet_model_actors[i % num_resnet_model_actors]
            task = actor.predict_batch.remote(batch)
            tasks[task] = batch

        # Wait for all tasks to complete
        while tasks:
            done_ids, _ = ray.wait(list(tasks.keys()))
            for done_id in done_ids:
                results = ray.get(done_id)
                # Process results
                pbar.update(len(tasks[done_id]))
                del tasks[done_id]

# Optionally shutdown Ray at the end if this is the end of your script
ray.shutdown()
# Write the collected ResNet scores to a CSV file
fieldnames = ['Image Name'] + [f'ResNet_Score_{n}' for n in downsampling_factors]
with open(output_csv, 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for image_name, scores in resnet_scores.items():
        row = {'Image Name': image_name}
        row.update({f'ResNet_Score_{n}': scores.get(n, '') for n in downsampling_factors})
        writer.writerow(row)

print(f"ResNet scores for all images have been saved to {output_csv}.")
ray.shutdown()
