import cv2
from LL.vision.masking import otsu_white_mask

img_path = "/Users/neo/Documents/Research/DeepHeme/LLResults/V2/H23-306;S14;MSK2 - 2023-06-15 19.11.48/focus_regions/passed/focus_region_436.png"

# first open the image using CV2 and display it until the user presses a key
img = cv2.imread(img_path)
cv2.imshow("image", img)
cv2.waitKey(0)



# then calculate the otsu mask and display it
otsu_mask = otsu_white_mask(img)
cv2.imshow("otsu_mask", otsu_mask)
cv2.waitKey(0)

# calculate the laplacian of the gaussian blur of the image
imgg = cv2.GaussianBlur(img, (5, 5), 0)
laplacian = cv2.Laplacian(imgg, cv2.CV_64F)

# normalize the laplacian
# laplacian = cv2.normalize(laplacian, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)

# display the laplacian
cv2.imshow("laplacian", laplacian)
cv2.waitKey(0)