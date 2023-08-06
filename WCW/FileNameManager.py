####################################################################################################
# Imports ###########################################################################################
####################################################################################################

# Outside imports ##################################################################################
import os

# Within package imports ############################################################################
from assumptions import *

class FileNameManager:
    """ A Class representing a FileNameManager of a whole slide image (WSI).
    Parsing the name of a WSI can be tricky because many file names are not standardized and have characters that make standard approaches difficult.
    
    === Class Attributes ===
    - wsi_path : the path to the WSI
    - basename : the basename of the WSI
    - ext : the file extension of the WSI
    """

    def __init__(self, wsi_path):
        
        # For each file extension in supported_extensions, check if the WSI path's last several characters has that file extension, if so, return the file extension
        # If none of the file extensions match, raise a FileExtensionError

        self.wsi_path = wsi_path
        self.basename = os.path.basename(wsi_path)
        
        for ext in supported_extensions:
            if self.basename.endswith(ext):
                self.ext = ext
                return None
        
        raise FileExtensionError
        

class FileExtensionError(Exception):
    """ A Class representing an error that occurs when the file extension of a WSI is not supported. """
    
    def __str__(self):
        return f"File extension not supported. The list of supported file extensions are: {str(supported_extensions)}."