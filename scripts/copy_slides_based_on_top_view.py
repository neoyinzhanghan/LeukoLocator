import os
from tqdm import tqdm

topview_dir = "/media/hdd3/neo/topviews_chosen"
source_dir = "/pesgisipth/NDPI"
save_dir = "/media/hdd1/BMAs_chosen"

# for all the images in topview_dir, there is a corresponding file in source_dir with same name but .ndpi extension
# copy the corresponding .ndpi file to save_dir using rsync

# get a list of ndpi files in source_dir
ndpi_files = [
    fname
    for fname in os.listdir(source_dir)
    if fname.endswith(".ndpi")
]

for img_name in tqdm(os.listdir(topview_dir), "Copying slides"):

    # check that it is actually an image
    if not img_name.endswith(".png"):
        continue
    
    # remove the .png extension
    img_name = img_name[:-4]

    # look for the corresponding .ndpi file in source_dir
    # note that _ is interchangeable with ; and " " space

    for fname in ndpi_files:
        # modified named is removing all -, _, ; and spaces
        modified_name = fname.replace("_", "").replace("-", "").replace(" ", "").replace(";", "")

        modified_img_name = img_name.replace("_", "").replace("-", "").replace(" ", "").replace(";", "")

        if modified_name.lower() == modified_img_name.lower():
            # copy the file to save_dir
            os.system(f'rsync -av "{os.path.join(source_dir, fname)}" "{save_dir}"')
            break


    print("No corresponding .ndpi file found for", img_name)