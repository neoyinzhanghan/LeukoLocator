####################################################################################################
# Imports ##########################################################################################
####################################################################################################

# Outside imports ##################################################################################
import numpy as np


# Within package imports ###########################################################################
from LL.resources.assumptions import *


def numpy_to_python(value):
    """Converts numpy objects to Python native objects."""
    if isinstance(value, (np.generic, np.ndarray)):
        return value.item() if np.isscalar(value) else value.tolist()
    else:
        return value


def write_config(save_dir):
    pass  # TODO this will write a config.yaml file to the save_dir logging the configs hidden in the assumption file
