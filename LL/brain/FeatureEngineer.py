import ray

from LL.brain.feature_extractors.ResNetExtractor import ResNetExtractor
from LL.resources.BMAassumptions import (
    get_feat_extract_augmentation_pipeline,
    num_augmentations_per_image,
)


def apply_augmentation(
    wbc_candidates, num_augmentations_per_image=num_augmentations_per_image
):
    """For each images, apply num_augmentations_per_image augmentations which are randomly chosen from the augmentation pipeline using the
    get_feat_extract_augmentation_pipeline function.

    The return should be a dictionary which maps the wbc_candidate's (focus_region_idx, local_idx) tuple to a list of augmented images.
    The list index is the augmentation id.
    """

    augmented_images = {}
    for wbc_candidate in wbc_candidates:
        image = wbc_candidate.snap_shot
        augmentation_list = []

        for _ in range(num_augmentations_per_image):
            augmentation_pipeline = get_feat_extract_augmentation_pipeline()
            augmented_image = augmentation_pipeline(image=image)["image"]
            augmentation_list.append(tuple([augmentation_pipeline, augmented_image]))

        augmented_images[(wbc_candidate.focus_region_idx, wbc_candidate.local_idx)] = (
            augmentation_list
        )

    return augmented_images


def dict_to_list(d):
    """Input is a list valued dictionary, output is all those lists concatenated together."""
    return [item for sublist in d.values() for item in sublist]


def list_to_dict(d, lst):
    """Assumes lst is the output of applying a function to each element of dict_to_list(d).
    Returns a dictionary with the same keys as d but the values are elements of lst grouped in the same structure as in d.
    """
    it = iter(lst)
    return {k: [next(it) for _ in range(len(v))] for k, v in d.items()}


@ray.remote(num_gpus=1)
class CellFeatureEngineer:
    """
    For extracting, passing down and saving pretrained features of cell images.

    === Attributes ===
    - arch: a string representing the architecture of the model
        - currently only support 'resnet50' and 'simclr'
    - ckpt_path: a string representing the path to the checkpoint of the model
    - extractor: a FeatureExtractor object
    """  # NOTE the design choice of having a generic feature engineer is that in the future we might do multiple feature extraction in parallel

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

    def async_extract_batch_with_augmentation(self, wbc_candidates):

        augmented_images = apply_augmentation(wbc_candidates)

        big_augmentation_list = dict_to_list(augmented_images)

        big_list_of_images = [
            augmented_image[1] for augmented_image in big_augmentation_list
        ]

        features = self.extractor.extract(big_list_of_images)

        # now create list of triplets (augmentation_pipeline, augmented_image, feature)
        triplet_lst = []
        for _ in range(len(big_augmentation_list)):
            triplet_lst.append(
                (
                    big_augmentation_list[_][0],
                    big_augmentation_list[_][1],
                    features,
                )
            )

        features = list_to_dict(augmented_images, triplet_lst)

        # add the features to the wbc_candidates
        for wbc_candidate in wbc_candidates:
            wbc_candidate.augmented_features[self.arch] = features[
                (wbc_candidate.focus_region_idx, wbc_candidate.local_idx)
            ]

            print(wbc_candidate.augmented_features.keys())

            import sys
            sys.exit()

        return wbc_candidates
