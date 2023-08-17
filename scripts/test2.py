import cv2
import numpy as np

def VoL(image, sds=2):
    """ Compute the VoL of an image, the variance is computed after removing all data sds standard deviations away from the mean. 
    The image must be a PIL RGB image. """

    # make sure that the image is from now on processed using cv2 so must be in BGR format
    image = np.array(image)
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    # apply a small gaussian blur to the image to remove noise
    image = cv2.GaussianBlur(image, (5, 5), 0)

    # compute the laplacian
    laplacian = cv2.Laplacian(image, cv2.CV_64F)

    # first remove all data in laplacian sds standard deviations away from the mean
    mean = laplacian.mean()
    std = laplacian.std()
    laplacian = laplacian[np.abs(laplacian - mean) < sds * std]

    # if laplacian is now has 1 or less then return 0
    if len(laplacian) <= 1:
        return 0

    # compute the variance of the laplacian
    return laplacian.var()

image_path = "/Users/neo/Documents/Research/results/results/H22-1861;S15;MSKZ - 2023-05-22 08.01.16/focus_regions_annotated/(62720, 31488, 64768, 33536).jpg"

# open the image
image = cv2.imread(image_path)

# print the VoL
print(VoL(image))