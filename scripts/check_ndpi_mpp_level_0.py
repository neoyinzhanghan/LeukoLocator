import os
import openslide
from tqdm import tqdm

ndpi_dir = "/pesgisipth/NDPI"

# get all the ndpi files in the directory, and open them using the openslide package
# get the mpp level 0 for each ndpi file
# put them in a csv file with two columns -- ndpi_name, mpp_level_0

# create the csv file
csv_file = open(os.path.join(ndpi_dir, "zzz_ndpi_mpp_level_0.csv"), "w")

# iterate through the ndpi files
for ndpi_name in tqdm(os.listdir(ndpi_dir)):
    if ndpi_name.endswith(".ndpi"):
        # open the ndpi file
        ndpi = openslide.OpenSlide(os.path.join(ndpi_dir, ndpi_name))

        # get the mpp level 0
        mpp_level_0 = ndpi.properties[openslide.PROPERTY_NAME_MPP_X]

        # write to the csv file
        csv_file.write(ndpi_name + "," + str(mpp_level_0) + "\n")

        # close the ndpi file
        ndpi.close()

# close the csv file
csv_file.close()
