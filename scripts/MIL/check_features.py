feature_path = "/media/hdd3/neo/resultsv5/H20-6211;S11;MSKX - 2023-06-07 00.42.05/cells/E4/features_imagenet_v3"

"""
Traverse through all folders in root_dir
"""

import torch

tens = torch.load(feature_path)

print(tens.shape)
