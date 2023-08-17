import cv2

# PB
# image_path = "/Users/neo/Documents/Research/DeepHeme/bma_top_views/H22-9370_S27_MSKE_2023-06-15_13.png"
# image_path = "/Users/neo/Documents/Research/DeepHeme/bma_top_views/H22-5219_S13_MSKY_2023-04-14_16.png"
image_path = "/Users/neo/Documents/Research/DeepHeme/bma_top_views/H18-8967_S13_MSKF_2023-06-20_15.png"

# BMA
# image_path = "/Users/neo/Documents/Research/DeepHeme/bma_top_views/H22-3398_S9_MSK9_2023-03-23_16.png"

# open the image
image = cv2.imread(image_path)

# apply otsu thresholding to compute the mask
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

# compute the mask
mask = cv2.bitwise_and(image, image, mask=thresh)

# display the mask
cv2.imshow("mask", thresh)
cv2.waitKey(0)
cv2.destroyAllWindows()
