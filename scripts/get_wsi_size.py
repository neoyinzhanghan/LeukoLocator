import openslide

wsi_path = "/pegisipth/NDPI/H23-852;S12;MSKW - 2023-06-15 16.42.50.ndpi"

# open the wsi
wsi = openslide.OpenSlide(wsi_path)

# get the level 0 pixel dimensions of the wsi
level_0_pixel_dims = wsi.level_dimensions[0]

# print the x and y dimensions
print(level_0_pixel_dims)
