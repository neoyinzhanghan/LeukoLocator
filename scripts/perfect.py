import cv2

img_path = "/Users/neo/Downloads/aaaa.png"

# first open the image in black and white using CV2 and display it until the user presses a key
img = cv2.imread(img_path, 0)

# and then change the black pixels to white and white to black
img = cv2.bitwise_not(img)

# display the image
cv2.imshow("image", img)
cv2.waitKey(0)


coin_path = "/Users/neo/Downloads/sample.png"

# open coin path as color image
coin = cv2.imread(coin_path, 1)

# calculate the laplacian of hte gaussian blur of the image
coin = cv2.GaussianBlur(coin, (5, 5), 0)
laplacian = cv2.Laplacian(coin, cv2.CV_64F)

# normalize the laplacian
laplacian = cv2.normalize(laplacian, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)

# display the laplacian
cv2.imshow("laplacian", laplacian)
cv2.waitKey(0)