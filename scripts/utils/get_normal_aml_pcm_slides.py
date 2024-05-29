import os
import openslide
from tqdm import tqdm
from LLRunner.SlideTracker import SlidePoolMetadataTracker
from LL.brain.SpecimenClf import load_model_from_checkpoint, predict_image
from LL.resources.BMAassumptions import *
from LL.vision.processing import SlideError, read_with_timeout


slides_folder = "/pesgisipth/NDPI"
aml_folder = "/media/hdd1/neo/BMA_AML"
normal_folder = "/media/hdd2/neo/BMA_Normal"
pcm_folder = "/media/hdd3/neo/BMA_PCM"

os.makedirs(aml_folder, exist_ok=True)
os.makedirs(normal_folder, exist_ok=True)
os.makedirs(pcm_folder, exist_ok=True)

# create a subfolder called "topview" in the aml_folder
os.makedirs(os.path.join(aml_folder, "topview"), exist_ok=True)
# create a subfolder called "topview" in the normal_folder
os.makedirs(os.path.join(normal_folder, "topview"), exist_ok=True)
# create a subfolder called "topview" in the pcm_folder
os.makedirs(os.path.join(pcm_folder, "topview"), exist_ok=True)

# first get the paths to all the ndpi files in the slides_folder that start with H and ends with .ndpi
slide_paths = [
    os.path.join(slides_folder, fname)
    for fname in os.listdir(slides_folder)
    if fname.endswith(".ndpi") and fname.startswith("H")
]

# get the all the slide metadata
slide_pool_metadata_tracker = SlidePoolMetadataTracker(slide_paths)

# set up the specimen clf model
specimen_clf_model = load_model_from_checkpoint(
    specimen_clf_checkpoint_path, num_classes=4
)


# what are all the slides with the diagnosis "AML" AND are predicted to be a bone marrow aspirate?
normal_slides = slide_pool_metadata_tracker.get_slides_from_dx("Normal BMA")
print("Found", len(normal_slides), "Normal slides")

aml_slides = slide_pool_metadata_tracker.get_slides_from_dx("AML")
print("Found", len(aml_slides), "AML slides")

pcm_slides = slide_pool_metadata_tracker.get_slides_from_dx("Plasma cell myeloma")
print("Found", len(pcm_slides), "PCM slides")

import sys

sys.exit()

for slide_path in tqdm(normal_slides, desc="Copying Normal Slides: "):
    slide_name = slide_path.slide_name

    new_slide_path = os.path.join(normal_folder, slide_name)

    if not os.path.exists(new_slide_path):
        # use rsync to copy the slide to the normal_folder
        os.system(f'rsync -av "{slide_path}" "{normal_folder}"')

    try:
        wsi = openslide.OpenSlide(new_slide_path)

        top_view = read_with_timeout(
            wsi, (0, 0), topview_level, wsi.level_dimensions[topview_level]
        )

        # if the top view image is RGBA, convert it to RGB
        if top_view.mode == "RGBA":
            top_view = top_view.convert("RGB")

        specimen_type = predict_image(specimen_clf_model, top_view)

    except Exception as e:
        print(f"Error occurred: {e}")

        # remove the slide from the normal_folder
        os.system(f'rm -rf "{new_slide_path}"')

        print("Removed", new_slide_path, "due to slide error")

        # then skip to the next slide
        continue

    if specimen_type != "Bone Marrow Aspirate":
        # remove the slide from the normal_folder
        os.system(f'rm -rf "{new_slide_path}"')

        print("Removed", new_slide_path, "due to incorrect specimen type")

    else:
        # save the topview image to the topview subfolder as a jpg file with the same name as the slide (make sure to remove the .ndpi extension)
        topview_path = os.path.join(
            normal_folder, "topview", slide_name.replace(".ndpi", ".jpg")
        )

        # save the RGB image as a jpg file (the image comes out of openslide read region)
        top_view.save(topview_path)

        print("Saved", topview_path)


for slide_path in tqdm(aml_slides, desc="Copying AML Slides: "):

    slide_name = slide_path.slide_name

    new_slide_path = os.path.join(aml_folder, slide_name)

    if not os.path.exists(new_slide_path):
        # use rsync to copy the slide to the aml_folder
        os.system(f'rsync -av "{slide_path}" "{aml_folder}"')

    try:
        wsi = openslide.OpenSlide(new_slide_path)

        top_view = read_with_timeout(
            wsi, (0, 0), topview_level, wsi.level_dimensions[topview_level]
        )

        # if the top view image is RGBA, convert it to RGB
        if top_view.mode == "RGBA":
            top_view = top_view.convert("RGB")

        specimen_type = predict_image(specimen_clf_model, top_view)

    except Exception as e:
        print(f"Error occurred: {e}")

        # remove the slide from the aml_folder
        os.system(f'rm -rf "{new_slide_path}"')

        print("Removed", new_slide_path, "due to slide error")

        # then skip to the next slide
        continue

    if specimen_type != "Bone Marrow Aspirate":
        # remove the slide from the aml_folder
        os.system(f'rm -rf "{new_slide_path}"')

        print("Removed", new_slide_path, "due to incorrect specimen type")

    else:
        # save the topview image to the topview subfolder as a jpg file with the same name as the slide (make sure to remove the .ndpi extension)
        topview_path = os.path.join(
            aml_folder, "topview", slide_name.replace(".ndpi", ".jpg")
        )

        # save the RGB image as a jpg file (the image comes out of openslide read region)
        top_view.save(topview_path)

        print("Saved", topview_path)

for slide_path in tqdm(pcm_slides, desc="Copying PCM Slides: "):

    slide_name = slide_path.slide_name

    new_slide_path = os.path.join(pcm_folder, slide_name)

    if not os.path.exists(new_slide_path):
        # use rsync to copy the slide to the pcm_folder
        os.system(f'rsync -av "{slide_path}" "{pcm_folder}"')

    try:
        wsi = openslide.OpenSlide(new_slide_path)

        top_view = read_with_timeout(
            wsi, (0, 0), topview_level, wsi.level_dimensions[topview_level]
        )

        # if the top view image is RGBA, convert it to RGB
        if top_view.mode == "RGBA":
            top_view = top_view.convert("RGB")

        specimen_type = predict_image(specimen_clf_model, top_view)

    except Exception as e:
        print(f"Error occurred: {e}")

        # remove the slide from the pcm_folder
        os.system(f'rm -rf "{new_slide_path}"')

        print("Removed", new_slide_path, "due to slide error")

        # then skip to the next slide
        continue

    if specimen_type != "Bone Marrow Aspirate":
        # remove the slide from the pcm_folder
        os.system(f'rm -rf "{new_slide_path}"')

        print("Removed", new_slide_path, "due to incorrect specimen type")

    else:
        # save the topview image to the topview subfolder as a jpg file with the same name as the slide (make sure to remove the .ndpi extension)
        topview_path = os.path.join(
            pcm_folder, "topview", slide_name.replace(".ndpi", ".jpg")
        )

        # save the RGB image as a jpg file (the image comes out of openslide read region)
        top_view.save(topview_path)

        print("Saved", topview_path)
