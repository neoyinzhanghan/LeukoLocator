import os
import time
import pandas as pd
import subprocess
import openslide
from LL.brain.SpecimenClf import predict_bma
from LL.BMACounter import BMACounter
from LL.resources.BMAassumptions import dump_dir
from LLRunner.SR import sr, SlideNotFoundError
from LLRunner.SST import sst, AccessionNumberNotFoundError
from tqdm import tqdm


read_only_data_dir = "/pesgisipth/NDPI"
slide_prefix = "H"
file_extension = ".ndpi"
tmp_dir = "/media/hdd1/BMA_tmp"
metadata_path = os.path.join(dump_dir, "run_metadata.csv")
rsync_error_path = os.path.join(dump_dir, "rsync_error_slides.txt")

profiling_dict = {
    "slide_name": [],
    "accession_number": [],
    "predicted_specimen_type": [],
    "reported_specimen_type": [],
    "bma_conf": [],
    "total_processing_time": [],
    "slide_moving_time": [],
    "slide_removing_time": [],
    "specimen_prediction_time": [],
    "slide_processing_time": [],
    "general_dx": [],
    "sub_dx": [],
    "error": [],
    "slide_file_size": [],
    "mpp": [],
}

# populate the profiling dict with the slide names that are already in the metadata file
if os.path.exists(metadata_path):
    metadata_df = pd.read_csv(metadata_path)
    for _, row in metadata_df.iterrows():
        profiling_dict["slide_name"].append(row["slide_name"])
        profiling_dict["accession_number"].append(row["accession_number"])
        profiling_dict["predicted_specimen_type"].append(row["predicted_specimen_type"])
        profiling_dict["reported_specimen_type"].append(row["reported_specimen_type"])
        profiling_dict["bma_conf"].append(row["bma_conf"])
        profiling_dict["total_processing_time"].append(row["total_processing_time"])
        profiling_dict["slide_moving_time"].append(row["slide_moving_time"])
        profiling_dict["slide_removing_time"].append(row["slide_removing_time"])
        profiling_dict["specimen_prediction_time"].append(
            row["specimen_prediction_time"]
        )
        profiling_dict["slide_processing_time"].append(row["slide_processing_time"])
        profiling_dict["general_dx"].append(row["general_dx"])
        profiling_dict["sub_dx"].append(row["sub_dx"])
        profiling_dict["error"].append(row["error"])
        profiling_dict["slide_file_size"].append(row["slide_file_size"])
        profiling_dict["mpp"].append(row["mpp"])

# read the rsync error slides from the rsync_error_path file (each line is a slide name)
if os.path.exists(rsync_error_path):
    with open(rsync_error_path, "r") as f:
        rsync_error_slides = f.read().splitlines()
else:
    rsync_error_slides = []

# get all the slide names which is all the files in the read only data directory that starts with the slide prefix and ends with the file extension
slide_names = [
    f
    for f in os.listdir(read_only_data_dir)
    if f.startswith(slide_prefix) and f.endswith(file_extension)
]


def _is_bma(predicted_specimen_type, reported_specimen_type):
    return predicted_specimen_type == "Bone Marrow Aspirate"


for slide_name in tqdm(slide_names, desc="Processing Slides:"):

    # check if the slide_name is already found in the metadata file, if so, print a message and continue to the next slide
    if os.path.exists(metadata_path):
        metadata_df = pd.read_csv(metadata_path)
        if (
            slide_name in metadata_df["slide_name"].values
            or slide_name in rsync_error_slides
        ):
            print(f"Slide {slide_name} already processed. Skipping it.")
            continue

    start_time = time.time()

    print(f"Processing slide: {slide_name}")

    accession_number = slide_name.split(";")[0]

    try:
        general_dx, sub_dx = sst.get_dx(accession_number)
    except AccessionNumberNotFoundError:
        general_dx = "Accession Number Not Found"
        sub_dx = "Accession Number Not Found"

    try:
        reported_specimen_type = sr.get_recorded_specimen_type(slide_name)
    except SlideNotFoundError:
        reported_specimen_type = "Others"

    command = [
        "rsync",
        "-av",
        "--progress",
        os.path.join(read_only_data_dir, slide_name),
        tmp_dir,
    ]

    try:
        # Run command and capture output
        result = subprocess.run(
            command,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print("Output:", result.stdout)
    except subprocess.CalledProcessError as e:
        print("rsync failed with error code:", e.returncode)
        print("Error message:", e.stderr)

        # write the slide name to the rsync_error_path file
        with open(rsync_error_path, "a") as f:
            f.write(slide_name + "\n")

        continue

    profiling_dict["slide_moving_time"].append(time.time() - start_time)

    # get the file size of the slide in GB
    slide_file_size = os.path.getsize(os.path.join(tmp_dir, slide_name))
    profiling_dict["slide_file_size"].append(slide_file_size)
    intermediate_time = time.time()

    tmp_slide_path = os.path.join(tmp_dir, slide_name)

    try:
        # open the slide to get the mpp
        slide = openslide.OpenSlide(tmp_slide_path)
        mpp = float(slide.properties[openslide.PROPERTY_NAME_MPP_X])
    except Exception as e:
        print(f"Error processing slide {slide_name}. Error: {e}")
        mpp = None

    profiling_dict["mpp"].append(mpp)

    try:
        predicted_specimen_type, bma_conf = predict_bma(tmp_slide_path)
    except Exception as e:
        print(f"Error processing slide {slide_name}. Error: {e}")
        predicted_specimen_type = "Others"
        bma_conf = 0

    profiling_dict["specimen_prediction_time"].append(time.time() - intermediate_time)
    intermediate_time = time.time()

    if not _is_bma(predicted_specimen_type, reported_specimen_type):
        print(f"Slide {slide_name} is not a BMA slide. Removing it from tmp.")

        profiling_dict["slide_processing_time"].append(time.time() - intermediate_time)
        intermediate_time = time.time()

        # delete the slide from the tmp directory
        os.system(f"rm '{tmp_slide_path}'")

        profiling_dict["slide_removing_time"].append(time.time() - intermediate_time)
        intermediate_time = time.time()

        print(f"Slide {slide_name} removed from tmp.")
        # continue to the next slide and make sure the tqdm progress bar is updated

        profiling_dict["slide_name"].append(slide_name)
        profiling_dict["accession_number"].append(accession_number)
        profiling_dict["predicted_specimen_type"].append(predicted_specimen_type)
        profiling_dict["reported_specimen_type"].append(reported_specimen_type)
        profiling_dict["bma_conf"].append(bma_conf)
        profiling_dict["total_processing_time"].append(time.time() - start_time)
        profiling_dict["general_dx"].append(general_dx)
        profiling_dict["sub_dx"].append(sub_dx)
        profiling_dict["error"].append("Not BMA")

        # save the profiling dict to a csv file in the dump_dir as run_metadata.csv, overwriting the file if it already exists
        profiling_df = pd.DataFrame(profiling_dict)
        profiling_df.to_csv(os.path.join(dump_dir, "run_metadata.csv"), index=False)

        continue

    print(f"Slide {slide_name} is a BMA slide. Processing it.")

    bma_counter = BMACounter(
        tmp_slide_path,
        hoarding=True,
        continue_on_error=True,
        do_extract_features=False,
        ignore_specimen_type=True,
    )
    bma_counter.tally_differential()

    profiling_dict["slide_processing_time"].append(time.time() - intermediate_time)
    intermediate_time = time.time()

    # delete the slide from the tmp directory
    os.system(f"rm '{tmp_slide_path}'")

    profiling_dict["slide_removing_time"].append(time.time() - intermediate_time)

    print("Saving to", bma_counter.save_dir)

    profiling_dict["slide_name"].append(slide_name)
    profiling_dict["accession_number"].append(accession_number)
    profiling_dict["predicted_specimen_type"].append(predicted_specimen_type)
    profiling_dict["reported_specimen_type"].append(reported_specimen_type)
    profiling_dict["bma_conf"].append(bma_conf)
    profiling_dict["total_processing_time"].append(time.time() - start_time)
    profiling_dict["general_dx"].append(general_dx)
    profiling_dict["sub_dx"].append(sub_dx)
    profiling_dict["error"].append(bma_counter.error)

    print(f"Slide {slide_name} removed from tmp. Processing finished.")

    # save the profiling dict to a csv file in the dump_dir as run_metadata.csv, overwriting the file if it already exists
    profiling_df = pd.DataFrame(profiling_dict)
    profiling_df.to_csv(os.path.join(dump_dir, "run_metadata.csv"), index=False)

# save the profiling dict to a csv file in the dump_dir as run_metadata.csv, overwriting the file if it already exists
profiling_df = pd.DataFrame(profiling_dict)
profiling_df.to_csv(os.path.join(dump_dir, "run_metadata.csv"), index=False)

print("All slides processed.")
