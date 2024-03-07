import os

topview_dir = "/media/hdd3/neo/topviews_chosen"
source_dir = "/pesgisipth/NDPI"
save_dir = "/media/hdd1/BMAs_chosen"

# for all the images in topview_dir, there is a corresponding file in source_dir with same name but .ndpi extension
# copy the corresponding .ndpi file to save_dir using rsync

for img_name in os.listdir(topview_dir):

    # check that it is actually an image
    if not img_name.endswith(".png"):
        continue
    
    # remove the .png extension
    img_name = img_name[:-4]

    src_path = os.path.join(source_dir, img_name + ".ndpi")
    dst_path = os.path.join(save_dir, img_name + ".ndpi")
    os.system(f'rsync -av "{src_path}" "{dst_path}"')