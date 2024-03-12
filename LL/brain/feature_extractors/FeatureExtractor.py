from abc import ABC, abstractmethod
import torch

class FeatureExtractor(ABC):
    """
    A class for extracting features from images.

    === Attributes ===
    - ckpt_path: a pretrained model's checkpoint path
    """

    def __init__(self, ckpt_path) -> None:
        self.ckpt_path = ckpt_path

    @abstractmethod
    def extract(self, images) -> torch.Tensor:
        """
        Extracts features from an image. Must be implemented by subclasses.

        :param image: The image to extract features from.
        :return: The extracted features as a torch.Tensor.
        """
        pass