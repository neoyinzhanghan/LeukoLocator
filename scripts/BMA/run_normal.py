print("Importing packages")
import os
import random
from LLRunner.SlideTracker import SlidePoolMetadataTracker
from tqdm import tqdm
from LL.resources.BMAassumptions import dump_dir
from LL.BMACounter import BMACounter

print("Getting all the slides with the diagnosis 'Normal BMA'")
# get a list of all directories in the dump_dir
dump_dirs = [
    dname
    for dname in os.listdir(dump_dir)
    if os.path.isdir(os.path.join(dump_dir, dname))
]


def already_processed(fname, dump_dirs):
    for dump_dir in dump_dirs:
        if dump_dir in fname:
            return True

    return False


slides_folder = "/pesgisipth/NDPI"
tmp_dir = "/media/hdd1/BMA_tmp"

print("Assembling slide paths")
# first get the paths to all the ndpi files in the slides_folder
slide_paths = [
    os.path.join(slides_folder, fname)
    for fname in os.listdir(slides_folder)
    if fname.endswith(".ndpi") and fname.startswith("H")
]


print("Getting all the normal slides")
# get the all the slide metadata
slide_pool_metadata_tracker = SlidePoolMetadataTracker(slide_paths)


# what are all the slides with the diagnosis "AML" AND are predicted to be a bone marrow aspirate?
normal_slides = slide_pool_metadata_tracker.get_slides_from_dx("Normal BMA")

print("Found", len(normal_slides), "Normal slides")

# # what are all the slides with the diagnosis "Plasma cell myeloma" AND are predicted to be a bone marrow aspirate?
# pcm_slides = slide_pool_metadata_tracker.get_slides_from_dx("Plasma cell myeloma")

for slide_metadata in tqdm(normal_slides, "Processing Normal Slides: "):

    bma_fname = slide_metadata.slide_name

    if already_processed(bma_fname, dump_dirs):
        print("Already processed", bma_fname)

    else:
        print("Processing", bma_fname)

        # try:
        bma_slide_path = os.path.join(slides_folder, bma_fname)

        print("Copying slide to tmp directory")
        # use rsync to copy the slide to the tmp_dir
        os.system(f"rsync -av {bma_slide_path} {tmp_dir}")

        accessible_bma_slide_path = os.path.join(tmp_dir, bma_fname)

        bma_counter = BMACounter(
            accessible_bma_slide_path,
            hoarding=True,
            continue_on_error=True,
            do_extract_features=False,
        )
        bma_counter.tally_differential()

        print("Saving to", bma_counter.save_dir)

        print("Removing slide from tmp directory")
        # delete the slide from the tmp directory
        os.system(f"rm '{accessible_bma_slide_path}'")
