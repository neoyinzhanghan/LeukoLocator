import cv2
from LL.vision.masking import otsu_white_mask

img_path = "/Users/neo/Documents/Research/DeepHeme/LLResults/V3/ERROR_H19-10014;S12;MSKB - 2023-06-20 16.27.24/top_view_image.png"

# first open the image using CV2 and display it until the user presses a key
img = cv2.imread(img_path)
cv2.imshow("image", img)
cv2.waitKey(0)



# then calculate the otsu mask and display it
otsu_mask = otsu_white_mask(img)
cv2.imshow("otsu_mask", otsu_mask)
cv2.waitKey(0)


