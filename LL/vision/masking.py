####################################################################################################
# Imports ##########################################################################################
####################################################################################################

# Within package imports ###########################################################################
from LL.brain.statistics import first_min_after_first_max, last_min_before_last_max

# External imports ################################################################################
import numpy as np
import pandas as pd
import cv2
import matplotlib.pyplot as plt


####################################################################################################
# Functions ########################################################################################
####################################################################################################


def get_obstructor_mask(image,
                        erosion_radius=25,
                        median_blur_size=25,
                        verbose=False,
                        first_n=2,
                        apply_blur=False):
    """ Returns a mask that covers the complement of the obstructor in the image. 
    The image is always assumed to be a PIL RGB image. """

    image = np.array(image)
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    # Convert the image to grayscale
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Create a histogram of the pixel intensities of the image
    bins = 64
    histogram = cv2.calcHist([gray_image], [0], None, [bins], [0, 256])

    # Calculate the bin midpoints
    bin_midpoints = np.linspace(0, 256, bins+1)[1:] - (256/bins/2)

    if apply_blur:
        # Apply a Gaussian blur to the function
        histogram = cv2.GaussianBlur(histogram, (5, 5), 0)

    if verbose:
        # Display the histogram
        plt.figure()
        plt.title("Grayscale Histogram")
        plt.xlabel("Bins")
        plt.ylabel("# of Pixels")
        plt.plot(bin_midpoints, histogram)
        plt.xlim([0, 256])
        plt.show()

    # There are multiple peaks in the histogram
    # The first peak is the covering label and we want to find a mask that covers the covering label
    # The last peak is the background and we want to find a mask that covers the background

    # grab a list of local minima positions and a list of local maxima positions
    # the first local minima is the first peak, which is the covering label
    # the last local maxima is the last peak, which is the background

    # find the local minima
    local_minima = []
    for i in range(1, len(histogram)-1):

        if histogram[i-1] > histogram[i] < histogram[i+1]:
            local_minima.append(bin_midpoints[i])

    # find the local maxima
    local_maxima = []
    for i in range(0, len(histogram)-1):

        # if the index is the left most boundary, then no need to compare the left value
        if i == 0:
            if histogram[i] > histogram[i+1]:
                local_maxima.append(bin_midpoints[i])
        elif histogram[i-1] < histogram[i] > histogram[i+1]:
            local_maxima.append(bin_midpoints[i])

    if verbose:
        # plot the local minimum and maximum positions, minima are blue, maxima are red
        # plot the minimal maxima positions as vertical lines
        # make the line corresponding to first_min_after_first_max(local_minima, local_maxima) longer than the rest
        plt.figure()
        plt.title("Local Minima and Maxima")
        plt.xlabel("Bins")
        plt.ylabel("# of Pixels")
        plt.plot(bin_midpoints, histogram)
        plt.xlim([0, 256])
        plt.vlines(first_min_after_first_max(local_minima, local_maxima,
                   first_n=first_n), 0, max(histogram), colors="g")
        plt.vlines(local_minima, 0, 1000, colors="b")
        plt.vlines(local_maxima, 0, 3000, colors="r")
        plt.show()

    # get a mask that contains all pixels with intensity smaller than the first local minimum right after the first peak
    mask = np.zeros(gray_image.shape, dtype="uint8")
    mask[gray_image < first_min_after_first_max(
        local_minima, local_maxima, first_n=first_n)] = 255

    if verbose:
        # display the mask
        plt.figure()
        plt.title("Mask")
        plt.imshow(mask, cmap="gray")
        plt.show()

    # Now we use the mask to mask the image.
    # Start by applying a median blur to the mask to get rid of salt and pepper noises
    mask = cv2.medianBlur(mask, median_blur_size)

    if verbose:
        # display the mask
        plt.figure()
        plt.title("Median Blurred Mask")
        plt.imshow(mask, cmap="gray")
        plt.show()

    # Then invert the mask
    mask = cv2.bitwise_not(mask)

    # Then thin the mask to get rid of the obstructor
    kernel = np.ones((erosion_radius, erosion_radius), np.uint8)
    mask = cv2.erode(mask, kernel, iterations=1)

    if verbose:
        # display the mask
        plt.figure()
        plt.title("Eroded Mask")
        plt.imshow(mask, cmap="gray")
        plt.show()

    return mask


def get_white_mask(image, verbose=False):
    """ Return a mask covering the whitest region of the image. 
    The image is always assumed to be a PIL RGB image. """

    image = np.array(image)
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    # Convert the image to grayscale
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Create a histogram of the pixel intensities of the image
    bins = 64
    histogram = cv2.calcHist([gray_image], [0], None, [bins], [0, 256])

    # Calculate the bin midpoints
    bin_midpoints = np.linspace(0, 256, bins+1)[1:] - (256/bins/2)

    # Smooth out the histogram to remove small ups and downs but keep the large peaks
    histogram = cv2.GaussianBlur(histogram, (5, 5), 0)

    if verbose:
        # Display the histogram
        plt.figure()
        plt.title("Grayscale Histogram")
        plt.xlabel("Bins")
        plt.ylabel("# of Pixels")
        plt.plot(bin_midpoints, histogram)
        plt.xlim([0, 256])
        plt.show()

    # There are multiple peaks in the histogram
    # The first peak is the covering label and we want to find a mask that covers the covering label
    # The last peak is the background and we want to find a mask that covers the background

    # grab a list of local minima positions and a list of local maxima positions
    # the first local minima is the first peak, which is the covering label
    # the last local maxima is the last peak, which is the background

    # find the local minima
    local_minima = []
    for i in range(1, len(histogram)-1):

        if histogram[i-1] > histogram[i] < histogram[i+1]:
            local_minima.append(bin_midpoints[i])

    # find the local maxima
    local_maxima = []
    for i in range(0, len(histogram)-1):

        # if the index is the left most boundary, then no need to compare the left value
        if i == 0:
            if histogram[i] > histogram[i+1]:
                local_maxima.append(bin_midpoints[i])
        elif histogram[i-1] < histogram[i] > histogram[i+1]:
            local_maxima.append(bin_midpoints[i])

    if verbose:
        # plot the local minimum and maximum positions, minima are blue, maxima are red
        # plot the minimal maxima positions as vertical lines
        # make the line corresponding to first_min_after_first_max(local_minima, local_maxima) longer than the rest
        plt.figure()
        plt.title("Local Minima and Maxima")
        plt.xlabel("Bins")
        plt.ylabel("# of Pixels")
        plt.plot(bin_midpoints, histogram)
        plt.xlim([0, 256])
        plt.vlines(last_min_before_last_max(
            local_minima, local_maxima), 0, max(histogram), colors="g")
        plt.vlines(local_minima, 0, 1000, colors="b")
        plt.vlines(local_maxima, 0, 3000, colors="r")
        plt.show()

    # get a mask that contains all pixels with intensity smaller than the first local minimum right after the first peak
    mask = np.zeros(gray_image.shape, dtype="uint8")
    mask[gray_image > last_min_before_last_max(
        local_minima, local_maxima)] = 255

    if verbose:
        # display the mask
        plt.figure()
        plt.title("Mask")
        plt.imshow(mask, cmap="gray")
        plt.show()

    return mask


def get_background_mask(image, erosion_radius=35, median_blur_size=35, verbose=False):
    """ Returns a mask that covers the complement of the obstructor in the image. 
    The image is always assumed to be a PIL RGB image."""

    mask = get_white_mask(image, verbose=verbose)

    # Now we use the mask to mask the image.
    # Start by applying a median blur to the mask to get rid of salt and pepper noises
    mask = cv2.medianBlur(mask, median_blur_size)

    if verbose:
        # display the mask
        plt.figure()
        plt.title("Median Blurred Mask")
        plt.imshow(mask, cmap="gray")
        plt.show()

    # Then invert the mask
    mask = cv2.bitwise_not(mask)

    # Then thin the mask to get rid of the obstructor
    kernel = np.ones((erosion_radius, erosion_radius), np.uint8)
    mask = cv2.erode(mask, kernel, iterations=1)

    if verbose:
        # display the mask
        plt.figure()
        plt.title("Eroded Mask")
        plt.imshow(mask, cmap="gray")
        plt.show()

    # Remove all connected components in the black region of the mask that are smaller than 15000 pixels
    # This removes small holes in the mask

    # invert the mask
    mask = cv2.bitwise_not(mask)

    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
        mask, connectivity=8)
    for i in range(1, num_labels):
        if stats[i, cv2.CC_STAT_AREA] < 15000:
            mask[labels == i] = 0

    # invert the mask again
    mask = cv2.bitwise_not(mask)

    if verbose:
        # Display each connected component in the mask
        plt.figure()
        plt.title("Connected Components")
        plt.imshow(labels)
        plt.show()

        # display the mask
        plt.figure()
        plt.title("Mask")
        plt.imshow(mask, cmap="gray")
        plt.show()

    if verbose:
        # display the mask
        plt.figure()
        plt.title("Mask")
        plt.imshow(mask, cmap="gray")
        plt.show()

    return mask


def otsu_white_mask(image, verbose=False):
    """ Returns a mask that covers the whitest region of the image. 
    The image is always assumed to be a PIL RGB image. """

    image = np.array(image)
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    # Convert the image to grayscale
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Threshold using Otsu's method
    _, binary = cv2.threshold(
        gray_image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Invert the binary image to get the white mask
    white_mask = cv2.bitwise_not(binary)

    if verbose:
        # display the mask
        plt.figure()
        plt.title("White Mask")
        plt.imshow(white_mask, cmap="gray")
        plt.show()

    return white_mask


def get_top_view_mask(image,
                      obstructor_mask=None,
                      white_mask=None,
                      patch_size=64,
                      min_specimen_area_prop=0.25,
                      verbose=False):
    """ This will give you a top view mask that decides which are good regions to look at.
    The image is always assumed to be a PIL RGB image."""

    # get the obstructor mask
    if obstructor_mask is None:
        obstructor_mask = get_obstructor_mask(image, verbose=False)

    if verbose:
        # display the obstructor mask
        plt.imshow(obstructor_mask, cmap="gray")
        plt.show()

    # get the white mask
    if white_mask is None:
        white_mask = get_white_mask(image, verbose=False)

    if verbose:
        # display the white mask's complement
        plt.imshow(cv2.bitwise_not(white_mask), cmap="gray")
        plt.show()

    # display the white mask's complement intersected with the obstructor mask, only white if both white and obstructor are white
    mask = cv2.bitwise_and(cv2.bitwise_not(white_mask), obstructor_mask)

    if verbose:
        # display the mask
        plt.imshow(mask, cmap="gray")
        plt.show()

    # tile the image into 64x64 patches, if the patch is out of bound, disregard it
    # get a dictionary, which contains the patch coordinates of the top-left corner as keys and the patch images as values

    patch_dict = {}


    top_view_np = np.array(image)
    top_view_np = cv2.cvtColor(top_view_np, cv2.COLOR_RGB2BGR)
    
    # the padding should be equal on both sides, so that the patch is centered

    padding_x = (patch_size - top_view_np.shape[0] % patch_size) // 2
    padding_y = (patch_size - top_view_np.shape[1] % patch_size) // 2

    for x in range(padding_x, top_view_np.shape[1], patch_size):
        for y in range(padding_y, top_view_np.shape[0], patch_size):
            if x + patch_size <= top_view_np.shape[1] and y + patch_size <= top_view_np.shape[0]:
                patch_dict[(x, y)] = top_view_np[y:y +
                                                 patch_size, x:x+patch_size]

    min_specimen_area = patch_size * patch_size * min_specimen_area_prop

    # if more the min_specimen_area of the patch is covered by the mask, then keep it from the dictionary, otherwise, remove it
    for key in list(patch_dict.keys()):
        patch = patch_dict[key]
        patch_mask = mask[key[1]:key[1]+patch_size, key[0]:key[0]+patch_size]
        if cv2.countNonZero(patch_mask) < min_specimen_area:
            patch_dict.pop(key)

    # now the remaining patches, put em together into a big new mask
    new_mask = np.zeros(top_view_np.shape[:2], dtype="uint8")

    for key in patch_dict.keys():
        x, y = key
        new_mask[y:y+patch_size, x:x+patch_size] = 255

    if verbose:
        # display the new mask
        plt.imshow(new_mask, cmap="gray")
        plt.show()

    # take an intersection of the new mask with the obstructor mask
    new_mask = cv2.bitwise_and(new_mask, obstructor_mask)

    if verbose:
        # Assuming 'image' is your original image and 'new_mask' is your binary mask
        image_rgb = cv2.cvtColor(top_view_np, cv2.COLOR_BGR2RGB)

        # Create a fully green image of the same size as your original image
        green_image = np.zeros_like(image_rgb)
        green_image[..., 1] = 255  # Set the green channel to maximum

        # Overlay the green on places where the mask is white, using alpha blending
        overlay = np.where(new_mask[:, :, None].astype(bool), green_image, 0)
        final_image = cv2.addWeighted(image_rgb, 1, overlay, 0.2, 0)

        plt.imshow(final_image)
        plt.show()

        # show the new mask
        plt.imshow(new_mask, cmap="gray")
        plt.show()

    # make sure the new mask is binary with only value 0 and 255 if not raise a ValueError
    if not (np.unique(new_mask) == np.array([0, 255])).all():
        raise ValueError("new_mask is not binary")

    # check that image has the same dimensions as new_mask
    if top_view_np.shape[:2] != new_mask.shape:
        raise ValueError("image and new_mask have different dimensions")

    return new_mask
