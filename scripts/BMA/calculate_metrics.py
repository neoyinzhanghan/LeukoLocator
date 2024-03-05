# FOR EACH IMAGE IN THE POOLED DIRECTORY, OBTAIN THE FOLLOWING METRICS USIGN THE CORRESPONDING FUNCTION, AND LOG THAT IN A CSV FILE
# -- VoL_n : VoL applied to the downsampled image by a factor of n, output of function VoL_n
# -- WMP_n : WMP applied to the downsampled image by a factor of n, output of function WMP_n
# -- RBI_n : the sum of the blue channel intensities divided by the sum of all channel intensities for the downsampled image by a factor of n, output of function RBI_n
# -- RGI_n : the sum of the green channel intensities divided by the sum of all channel intensities for the downsampled image by a factor of n, output of function RGI_n
# -- RRI_n : the sum of the red channel intensities divided by the sum of all channel intensities for the downsampled image by a factor of n, output of function RRI_n
# -- ResNet_n : the output function ResNet_n

# The functions VoL_n, WMP_n, RBI_n, RGI_n, RRI_n, and ResNet_n are not provided, but you can assume that they take an image path and return the corresponding metric.
# n take the following values 1, 2, 4, 8, 16

from LL.vision.ad_hoc_image_metric_functions import VoL_n, WMP_n, RBI_n, RGI_n, RRI_n
import os
import csv
import ray
from tqdm import tqdm


# # Prepare the CSV file for logging the metrics
# with open(output_csv, 'w', newline='') as csvfile:
#     fieldnames = ['Image Name'] + [f'{metric}_{factor}' for factor in downsampling_factors for metric in ['VoL', 'WMP', 'RBI', 'RGI', 'RRI', 'ResNet']]
#     writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
#     writer.writeheader()

#     # List all image files in the directory
#     image_files = [f for f in os.listdir(pooled_dir) if os.path.isfile(os.path.join(pooled_dir, f)) and f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff'))]
    
#     # Iterate over each image in the pooled directory with a progress bar
#     for image_name in tqdm(image_files, desc="Processing Images"):
#         image_path = os.path.join(pooled_dir, image_name)
#         metrics_row = {'Image Name': image_name}
#         # Calculate and log metrics for each downsampling factor
#         for factor in downsampling_factors:
#             metrics_row.update({
#                 f'VoL_{factor}': VoL_n(image_path, factor),
#                 f'WMP_{factor}': WMP_n(image_path, factor),
#                 f'RBI_{factor}': RBI_n(image_path, factor),
#                 f'RGI_{factor}': RGI_n(image_path, factor),
#                 f'RRI_{factor}': RRI_n(image_path, factor),
#                 f'ResNet_{factor}': ResNet_n(image_path, factor)
#             })
#         writer.writerow(metrics_row)

# print(f"Metrics for all images have been saved to {output_csv}")


@ray.remote
def calculate_metrics_for_images(image_paths, downsampling_factors):
    batch_metrics = []
    for image_path in image_paths:
        metrics = {}
        for factor in downsampling_factors:
            metrics.update({
                f'VoL_{factor}': VoL_n(image_path, factor),
                f'WMP_{factor}': WMP_n(image_path, factor),
                f'RBI_{factor}': RBI_n(image_path, factor),
                f'RGI_{factor}': RGI_n(image_path, factor),
                f'RRI_{factor}': RRI_n(image_path, factor),
                # f'ResNet_{factor}': ResNet_n(image_path, factor)
            })
        batch_metrics.append((os.path.basename(image_path), metrics))
    return batch_metrics

import os
import csv
from tqdm.auto import tqdm
import ray

ray.init()

pooled_dir = "/media/hdd3/neo/results_bma_v4_regions_pooled"
output_csv = os.path.join(pooled_dir, "image_metrics.csv")
downsampling_factors = [1, 2, 4, 8, 16]
fieldnames = ['Image Name'] + [f'{metric}_{factor}' for factor in downsampling_factors for metric in ['VoL', 'WMP', 'RBI', 'RGI', 'RRI', 'ResNet']]
batch_size = 10  # Adjust based on your requirements

# Create batches of image files
image_files = [f for f in os.listdir(pooled_dir) if os.path.isfile(os.path.join(pooled_dir, f)) and f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff'))]
image_batches = [image_files[i:i + batch_size] for i in range(0, len(image_files), batch_size)]
image_batch_paths = [[os.path.join(pooled_dir, image_name) for image_name in batch] for batch in image_batches]

# Dispatch Ray tasks for each batch
tasks = [calculate_metrics_for_images.remote(batch, downsampling_factors) for batch in image_batch_paths]

# Initialize tqdm progress bar
progress_bar = tqdm(total=len(tasks), desc="Processing Image Batches")

results = []
for _ in range(len(tasks)):
    # Wait for the next task to complete and fetch its result
    done_id, tasks = ray.wait(tasks)
    result = ray.get(done_id[0])
    results.extend(result)  # Append results from the batch
    progress_bar.update(1)

progress_bar.close()

# Write results to CSV
with open(output_csv, 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for image_name, metrics in results:
        metrics_row = {'Image Name': image_name}
        metrics_row.update(metrics)
        writer.writerow(metrics_row)

print(f"Metrics for all images have been saved to {output_csv}")
