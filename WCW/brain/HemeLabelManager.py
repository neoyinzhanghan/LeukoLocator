#####################################################################################################
# Imports ###########################################################################################
#####################################################################################################

# Outside imports ##################################################################################
import torch
import torch.nn as nn
import ray
from collections import OrderedDict
import numpy as np
import cv2

# Within package imports ###########################################################################
from WCW.resources.assumptions import *


class Myresnext50(nn.Module):
    def __init__(self, my_pretrained_model, num_classes=23):
        super(Myresnext50, self).__init__()
        self.pretrained = my_pretrained_model
        self.my_new_layers = nn.Sequential(nn.Linear(1000, 100),
                                           nn.ReLU(),
                                           nn.Linear(100, num_classes))
        self.num_classes = num_classes

    def forward(self, x):
        x = self.pretrained(x)
        x = self.my_new_layers(x)

        pred = torch.sigmoid(x.reshape(x.shape[0], 1, self.num_classes))
        return pred


def model_create(num_classes=23, path='not_existed_path'):

    resnext50_pretrained = torch.hub.load(
        'pytorch/vision:v0.10.0', 'resnext50_32x4d')
    My_model = Myresnext50(
        my_pretrained_model=resnext50_pretrained, num_classes=num_classes)

    checkpoint_PATH = path
    checkpoint = torch.load(checkpoint_PATH)

    checkpoint = remove_data_parallel(checkpoint['model_state_dict'])

    My_model.load_state_dict(checkpoint, strict=True)

    return My_model


def remove_data_parallel(old_state_dict):
    new_state_dict = OrderedDict()

    for k, v in old_state_dict.items():
        name = k[7:]  # remove `module.`

        new_state_dict[name] = v

    return new_state_dict


@ray.remote(num_gpus=num_gpus_per_manager, num_cpus=num_cpus_per_manager)
class HemeLabelManager:
    """ A class representing a HemeLabel Manager that manages the classification of a WSI.

    === Class Attributes ===
    - model : the HemeLabel model
    - ckpt_path : the path to the checkpoint of the HemeLabel model
    - num_classes : the number of classes of the HemeLabel model
    """

    def __init__(self, ckpt_path, num_classes=23) -> None:
        """ Initialize the HemeLabelManager object. """

        self.model = model_create(num_classes=num_classes, path=ckpt_path)
        self.ckpt_path = ckpt_path
        self.num_classes = num_classes

    def async_label_wbc_candidate(self, wbc_candidate):
        """ Label a WBC candidate. """

        if zero_pad:
            image = wbc_candidate.padded_YOLO_bbox_image
        else:
            image = wbc_candidate.snap_shot

        self.model.eval()
        self.model.to('cuda')

        image = np.array(image)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        image = cv2.resize(image, (96, 96), interpolation=cv2.INTER_AREA)

        image = np.einsum('ijk->kij', image)

        image = image / 255.0
        # image = np.transpose(image, (2, 0, 1))
        image = torch.from_numpy(image).float().unsqueeze(0)
        image = image.to('cuda')
        output = self.model(image)
        output = torch.flatten(output, start_dim=1).detach().cpu().numpy()

        # make a clone of the output vector, use tuple to avoid deprecation and aliasing errors down the road
        wbc_candidate.softmax_vector = tuple(output[0])

        print(len(wbc_candidate.softmax_vector()))

        return wbc_candidate
