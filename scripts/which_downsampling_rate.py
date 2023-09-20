import openslide

wsi_path = "/media/hdd3/neo/666 - 2023-05-31 22.53.12.ndpi"
level = 3

print("Opening WSI...")
wsi = openslide.OpenSlide(wsi_path)

# find out the downsample rate of the level 3 compared to the level 0
downsample_rate = wsi.level_downsamples[level]

print("Downsample rate: {}".format(downsample_rate))