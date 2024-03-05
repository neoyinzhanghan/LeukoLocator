# FOR EACH IMAGE IN THE POOLED DIRECTORY, OBTAIN THE FOLLOWING METRICS USIGN THE CORRESPONDING FUNCTION, AND LOG THAT IN A CSV FILE
# -- VoL_n : VoL applied to the downsampled image by a factor of n, output of function VoL_n
# -- WMP_n : WMP applied to the downsampled image by a factor of n, output of function WMP_n
# -- RBI_n : the sum of the blue channel intensities divided by the sum of all channel intensities for the downsampled image by a factor of n, output of function RBI_n
# -- RGI_n : the sum of the green channel intensities divided by the sum of all channel intensities for the downsampled image by a factor of n, output of function RGI_n
# -- RRI_n : the sum of the red channel intensities divided by the sum of all channel intensities for the downsampled image by a factor of n, output of function RRI_n
# -- ResNet_n : the output function ResNet_n

# The functions VoL_n, WMP_n, RBI_n, RGI_n, RRI_n, and ResNet_n are not provided, but you can assume that they take an image path and return the corresponding metric.
# n take the following values 1, 2, 4, 8, 16

from LL.vision.ad_hoc_image_metric_functions import VoL_n, WMP_n, RBI_n, RGI_n, RRI_n, ResNet_n
import os
import csv
from tqdm import tqdm

pooled_dir = "/media/hdd3/neo/results_bma_v3_regions_pooled"
output_csv = os.path.join(pooled_dir, "image_metrics.csv")

# Downsampling factors to be used for metrics calculation
downsampling_factors = [1, 2, 4, 8, 16]

# Prepare the CSV file for logging the metrics
with open(output_csv, 'w', newline='') as csvfile:
    fieldnames = ['Image Name'] + [f'{metric}_n{factor}' for factor in downsampling_factors for metric in ['VoL', 'WMP', 'RBI', 'RGI', 'RRI', 'ResNet']]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    # List all image files in the directory
    image_files = [f for f in os.listdir(pooled_dir) if os.path.isfile(os.path.join(pooled_dir, f)) and f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff'))]
    
    # Iterate over each image in the pooled directory with a progress bar
    for image_name in tqdm(image_files, desc="Processing Images"):
        image_path = os.path.join(pooled_dir, image_name)
        metrics_row = {'Image Name': image_name}
        # Calculate and log metrics for each downsampling factor
        for factor in downsampling_factors:
            metrics_row.update({
                f'VoL_{factor}': VoL_n(image_path, factor),
                f'WMP_{factor}': WMP_n(image_path, factor),
                f'RBI_n{factor}': RBI_n(image_path, factor),
                f'RGI_{factor}': RGI_n(image_path, factor),
                f'RRI_{factor}': RRI_n(image_path, factor),
                f'ResNet_{factor}': ResNet_n(image_path, factor)
            })
        writer.writerow(metrics_row)

print(f"Metrics for all images have been saved to {output_csv}")
