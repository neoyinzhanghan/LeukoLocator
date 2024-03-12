import ray

from LL.brain.feature_extractors.ResNetExtractor import ResNetExtractor

@ray.remote(num_gpus=1)
class CellFeatureEngineer():
    """
    For extracting, passing down and saving pretrained features of cell images.

    === Attributes ===
    - arch: a string representing the architecture of the model
        - currently only support 'resnet50' and 'simclr'
    - ckpt_path: a string representing the path to the checkpoint of the model
    - extractor: a FeatureExtractor object 
    """ # NOTE the design choice of having a generic feature engineer is that in the future we might do multiple feature extraction in parallel

    def __init__(self, arch, ckpt_path) -> None:
        self.arch = arch
        self.ckpt_path = ckpt_path
        if arch == "resnet50":
            self.extractor = ResNetExtractor(ckpt_path)
        else:
            raise ValueError(f"Unsupported architecture: {arch}")

    def async_extract_batch(self, wbc_candidates):

        images = [wbc_candidate.snap_shot for wbc_candidate in wbc_candidates]
        features = self.extractor.extract(images)

        for i, wbc_candidate in enumerate(wbc_candidates):
            feature = features[i]
            wbc_candidate.features[self.arch] = feature
        
        return wbc_candidates