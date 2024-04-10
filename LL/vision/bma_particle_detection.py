import cv2
import numpy as np
import matplotlib.pyplot as plt
import sys
import os


def last_min_before_last_max(local_minima, local_maxima, last_n=1):
    """Returns the last local minimum before the last local maximum"""

    if len(local_minima) == 0:
        raise ValueError("There are no local minima")

    for i in range(len(local_minima) - 1, -1, -1):
        if local_minima[i] < local_maxima[-last_n]:
            return local_minima[i]


def get_white_mask(image, verbose=False):
    """Return a mask covering the whitest region of the image."""

    # Convert the image to grayscale
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Create a histogram of the pixel intensities of the image
    bins = 64
    histogram = cv2.calcHist([gray_image], [0], None, [bins], [0, 256])

    # Calculate the bin midpoints
    bin_midpoints = np.linspace(0, 256, bins + 1)[1:] - (256 / bins / 2)

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
    for i in range(1, len(histogram) - 1):

        if histogram[i - 1] > histogram[i] < histogram[i + 1]:
            local_minima.append(bin_midpoints[i])

    # find the local maxima
    local_maxima = []
    for i in range(0, len(histogram) - 1):

        # if the index is the left most boundary, then no need to compare the left value
        if i == 0:
            if histogram[i] > histogram[i + 1]:
                local_maxima.append(bin_midpoints[i])
        elif histogram[i - 1] < histogram[i] > histogram[i + 1]:
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
        plt.vlines(
            last_min_before_last_max(local_minima, local_maxima),
            0,
            max(histogram),
            colors="g",
        )
        plt.vlines(local_minima, 0, 1000, colors="b")
        plt.vlines(local_maxima, 0, 3000, colors="r")
        plt.show()

    # get a mask that contains all pixels with intensity smaller than the first local minimum right after the first peak
    mask = np.zeros(gray_image.shape, dtype="uint8")
    mask[gray_image > last_min_before_last_max(local_minima, local_maxima)] = 255

    if verbose:
        # display the mask
        plt.figure()
        plt.title("Mask")
        plt.imshow(mask, cmap="gray")
        plt.show()

    return mask


def get_background_mask(image, erosion_radius=35, median_blur_size=35, verbose=False):
    """Returns a mask that covers the complement of the obstructor in the image."""

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
        mask, connectivity=8
    )
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


def get_threshold(img, prop_black=0.3, bins=1024):
    # tally up the histogram of the image's greyscale values
    histogram = np.zeros(bins)
    for pixel in img:
        histogram[pixel] += 1
    # choose the most generous threshold that gives a proportion of black pixels greater than prop_black
    threshold = 0
    for i in range(bins):
        if np.sum(histogram[:i]) / np.sum(histogram) >= prop_black:
            threshold = i
            break
    return threshold


""" Apply a number of cv2 filters to the image specified in image_path. If verbose is True, the image will be displayed after each filter is applied, and the user will be prompted to continue. If verbose is False, the image will not be displayed, and the user will not be prompted to continue. """


def get_high_blue_signal_mask(
    image,
    prop_black=0.75,
    bins=1024,
    median_blur_size=3,
    dilation_kernel_size=9,
    verbose=False,
):
    """
    Return a mask that covers the high blue signal in the image.
    """

    # # Apply pyramid mean shift filtering to image
    # image = cv2.pyrMeanShiftFiltering(image, 21, 51)
    # if verbose:
    #     try:
    #         # display the image and pause the execution until the user presses a key
    #         cv2.imshow("PMSF", image)
    #         cv2.waitKey(0)
    #         # close all windows
    #         cv2.destroyAllWindows()
    #     except KeyboardInterrupt:
    #         print("KeyboardInterrupt")
    #         # end the program
    #         sys.exit()

    # # Apply a blur filter to image
    # image = cv2.blur(image, (5,5))
    # if verbose:
    #     try:
    #         # display the image and pause the execution until the user presses a key
    #         cv2.imshow("Blur", image)
    #         cv2.waitKey(0)
    #         # close all windows
    #         cv2.destroyAllWindows()
    #     except KeyboardInterrupt:
    #         print("KeyboardInterrupt")
    #         # end the program
    #         sys.exit()

    # Convert to float32 to prevent overflow during division
    image = image.astype(np.float32)

    # Compute the sum over the color channels
    sum_channels = np.sum(image, axis=2, keepdims=True)

    # To avoid division by zero, we can add a small constant
    sum_channels = sum_channels + 1e-7

    # Normalize the blue channel by the sum
    image[:, :, 0] = image[:, :, 0] / sum_channels[:, :, 0]

    # Now, image has the normalized blue channel, and all other channels as they were.
    # If you want to zero out the other channels, you can do it now
    image[:, :, 1] = 0  # zero out green channel
    image[:, :, 2] = 0  # zero out red channel

    # Before saving, convert back to uint8
    image = np.clip(image, 0, 1) * 255
    image = image.astype(np.uint8)

    if verbose:
        try:
            # display the image and pause the execution until the user presses a key
            cv2.imshow("Blue Channel", image)
            cv2.waitKey(0)
            # close all windows
            cv2.destroyAllWindows()
        except KeyboardInterrupt:
            print("KeyboardInterrupt")
            # end the program
            sys.exit()

    # convert image to grayscale
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    if verbose:
        try:
            # display the image and pause the execution until the user presses a key
            cv2.imshow("Grayscale", image)
            cv2.waitKey(0)
            # close all windows
            cv2.destroyAllWindows()
        except KeyboardInterrupt:
            print("KeyboardInterrupt")
            # end the program
            sys.exit()

    # # Apply a laplacian filter to image
    # image = cv2.Laplacian(image, cv2.CV_64F)
    # image = np.absolute(image)  # Absolute value
    # image = np.uint8(255 * (image / np.max(image)))  # Normalize to 0-255
    # if verbose:
    #     try:
    #         # display the image and pause the execution until the user presses a key
    #         cv2.imshow("Laplacian", image)
    #         cv2.waitKey(0)
    #         # close all windows
    #         cv2.destroyAllWindows()
    #     except KeyboardInterrupt:
    #         print("KeyboardInterrupt")
    #         # end the program
    #         sys.exit()

    # apply a median blur to the image to get rid of salt and pepper noise
    image = cv2.medianBlur(image, median_blur_size)
    if verbose:
        try:
            # display the image and pause the execution until the user presses a key
            cv2.imshow("Median Blur", image)
            cv2.waitKey(0)
            # close all windows
            cv2.destroyAllWindows()
        except KeyboardInterrupt:
            print("KeyboardInterrupt")
            # end the program
            sys.exit()

    # dilate the image to get rid of small holes
    kernel = np.ones((dilation_kernel_size, dilation_kernel_size), np.uint8)
    image = cv2.dilate(image, kernel, iterations=1)
    if verbose:
        try:
            # display the image and pause the execution until the user presses a key
            cv2.imshow("Dilate", image)
            cv2.waitKey(0)
            # close all windows
            cv2.destroyAllWindows()
        except KeyboardInterrupt:
            print("KeyboardInterrupt")
            # end the program
            sys.exit()

    # # erode the image to get rid of small protrusions
    # kernel = np.ones((5,5),np.uint8)
    # image = cv2.erode(image, kernel, iterations = 1)
    # if verbose:
    #     try:
    #         # display the image and pause the execution until the user presses a key
    #         cv2.imshow("Erode", image)
    #         cv2.waitKey(0)
    #         # close all windows
    #         cv2.destroyAllWindows()
    #     except KeyboardInterrupt:
    #         print("KeyboardInterrupt")
    #         # end the program
    #         sys.exit()

    # threshold the image to get a black and white image with solid white areas, be generous with the threshold
    # tally up the histogram of the image's greyscale values, and choose the threshold just before the peak
    threshold = get_threshold(image, prop_black=prop_black, bins=bins)
    image = cv2.threshold(image, threshold, 255, cv2.THRESH_BINARY)[1]
    if verbose:
        try:
            # display the image and pause the execution until the user presses a key
            cv2.imshow("Threshold", image)
            cv2.waitKey(0)
            # close all windows
            cv2.destroyAllWindows()
        except KeyboardInterrupt:
            print("KeyboardInterrupt")
            # end the program
            sys.exit()

    return image


def first_min_after_first_max(local_minima, local_maxima, first_n=2):
    """Returns the first local minimum after the first local maximum"""
    for i in range(len(local_minima)):
        if local_minima[i] > local_maxima[first_n - 1]:
            return local_minima[i]


def get_obstructor_mask(
    image,
    erosion_radius=25,
    median_blur_size=25,
    verbose=False,
    first_n=2,
    apply_blur=False,
):
    """Returns a mask that covers the complement of the obstructor in the image."""

    # Convert the image to grayscale
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Create a histogram of the pixel intensities of the image
    bins = 64
    histogram = cv2.calcHist([gray_image], [0], None, [bins], [0, 256])

    # Calculate the bin midpoints
    bin_midpoints = np.linspace(0, 256, bins + 1)[1:] - (256 / bins / 2)

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
    for i in range(1, len(histogram) - 1):

        if histogram[i - 1] > histogram[i] < histogram[i + 1]:
            local_minima.append(bin_midpoints[i])

    # find the local maxima
    local_maxima = []
    for i in range(0, len(histogram) - 1):

        # if the index is the left most boundary, then no need to compare the left value
        if i == 0:
            if histogram[i] > histogram[i + 1]:
                local_maxima.append(bin_midpoints[i])
        elif histogram[i - 1] < histogram[i] > histogram[i + 1]:
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
        plt.vlines(
            first_min_after_first_max(local_minima, local_maxima, first_n=first_n),
            0,
            max(histogram),
            colors="g",
        )
        plt.vlines(local_minima, 0, 1000, colors="b")
        plt.vlines(local_maxima, 0, 3000, colors="r")
        plt.show()

    # get a mask that contains all pixels with intensity smaller than the first local minimum right after the first peak
    mask = np.zeros(gray_image.shape, dtype="uint8")
    mask[
        gray_image
        < first_min_after_first_max(local_minima, local_maxima, first_n=first_n)
    ] = 255

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


def marrow_boxing(
    mask, image, background_mask=None, box_ratio=0.1, output_dir=None, verbose=False
):
    """Put boxes based on mask from mask_path on image from image_path. If output_path is not None, save the image to output_path.
    Else, save to working directory. If verbose is True, display the image.
    The mask from background path is to remove the background from the marrow mask."""

    # create a new mask, this new mask is constructed by added a box around each pixel in the original mask
    # the box is 2*box_radius+1 pixels wide centered at each pixel
    # the radius is a center proprotion of the minimum of the image width and height

    box_radius = int(box_ratio * min(image.shape[:2]))

    # create a new mask
    new_mask = np.zeros_like(mask, dtype="uint8")

    # get the coordinates of all the white pixels in the mask
    white_pixels = np.where(mask == 255)

    # for each white pixel, add a box around it
    for i in range(len(white_pixels[0])):
        # get the coordinates of the current white pixel
        row = white_pixels[0][i]
        col = white_pixels[1][i]

        # add a box around the current white pixel, if the box is out of bounds, crop the part that is out of bounds
        # the box is 2*box_radius+1 pixels wide centered at the current white pixel
        # the radius is a center proprotion of the minimum of the image width and height
        # the box is added to the new mask
        new_mask[
            max(0, row - box_radius) : min(new_mask.shape[0], row + box_radius + 1),
            max(0, col - box_radius) : min(new_mask.shape[1], col + box_radius + 1),
        ] = 255

    if verbose:
        # display the original mask and the new mask side by side
        plt.figure()
        plt.subplot(1, 2, 1)
        plt.title("Original Mask")
        plt.imshow(mask, cmap="gray")
        plt.subplot(1, 2, 2)
        plt.title("New Mask")
        plt.imshow(new_mask, cmap="gray")
        plt.show()

    # now display the original image, the mask, and then the new_mask layed on top of the original image in color green, with transparency 0.5
    # open the image using OpenCV

    # convert the image to RGB format for matplotlib
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # get the coordinates of all the black pixels in the background mask
    if background_mask is not None:
        background_black_pixels = np.where(background_mask == 0)
    else:
        background_black_pixels = (np.array([]), np.array([]))

    # for each white pixel, set the corresponding pixel in the new mask to 0
    for i in range(len(background_black_pixels[0])):
        # get the coordinates of the current white pixel
        row = background_black_pixels[0][i]
        col = background_black_pixels[1][i]

        # set the corresponding pixel in the new mask to 0
        new_mask[row, col] = 0

    # display the original image, the mask, and the new_mask layed on top of the original image in color green, with transparency 0.3
    # the original image should have transparency 1.0, and the mask should have transparency 0.3
    # the original and the mask should be displayed side by side
    # the new_mask should be displayed below the other two

    # convert the single channel mask to a 3-channel mask
    new_mask_colored = cv2.cvtColor(new_mask, cv2.COLOR_GRAY2BGR)

    # change the color of the mask to green
    new_mask_colored[:, :, 0] = 0  # Zero out the blue channel
    new_mask_colored[:, :, 2] = 0  # Zero out the red channel

    # now display the original image, the mask, and then the new_mask_colored layed on top of the original image in color green, with transparency 0.5
    # Make sure the mask is put on the original image in the correct order
    overlayed_image = cv2.addWeighted(image, 1.0, new_mask_colored, 0.2, 0.0)

    if verbose:
        plt.figure()
        plt.subplot(1, 3, 1)
        plt.title("Original Image")
        plt.imshow(image)
        plt.subplot(1, 3, 2)
        plt.title("Mask")
        plt.imshow(mask, cmap="gray")
        plt.subplot(1, 3, 3)
        plt.title("New Mask on Original Image")
        plt.imshow(overlayed_image)
        plt.show()

    # Save the new mask on the original image

    # Convert the overlayed image to BGR format for OpenCV
    overlayed_image = cv2.cvtColor(overlayed_image, cv2.COLOR_RGB2BGR)

    return new_mask, overlayed_image


def get_top_view_preselection_mask(image, verbose=False):
    """The input is a cv2 image which is a np array in BGR format. Output a binary mask used to region preselection."""

    high_blue = get_high_blue_signal_mask(
        image,
        prop_black=0.75,
        median_blur_size=3,
        dilation_kernel_size=9,
        verbose=verbose,
    )

    # get the obstructor mask
    obstructor_mask = get_obstructor_mask(image, verbose=verbose)

    # get the background mask
    background_mask = None
    # background_mask = get_background_mask(image, verbose=verbose)

    # combine the two masks
    final_blue_mask = cv2.bitwise_and(high_blue, obstructor_mask)

    final_mask, overlayed_image = marrow_boxing(
        final_blue_mask, image, background_mask, box_ratio=0.12, verbose=verbose
    )

    return final_mask, overlayed_image, final_blue_mask


def get_grid_rep(image, mask, overlayed_image, final_blue_mask):
    # construct the 2x2 grid
    grid = np.zeros((2 * image.shape[0], 2 * image.shape[1], 3), dtype="uint8")
    grid[: image.shape[0], : image.shape[1]] = image
    grid[: image.shape[0], image.shape[1] :] = cv2.cvtColor(
        final_blue_mask, cv2.COLOR_GRAY2BGR
    )
    grid[image.shape[0] :, : image.shape[1]] = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    grid[image.shape[0] :, image.shape[1] :] = overlayed_image

    return grid


if __name__ == "__main__":

    from tqdm import tqdm

    image_rel_path = "/Users/neo/Documents/Research/results/ppt_BMA_pics/H18-841_S10_MSK6_2023-06-01_02.png"
    image = cv2.imread(image_rel_path)

    # get the top view preselection mask
    mask, overlayed_image, final_blue_mask = get_top_view_preselection_mask(
        image, verbose=True
    )

    # display the mask
    plt.figure()
    plt.title("Mask")
    plt.imshow(mask, cmap="gray")
    plt.show()

    ############################################################################################################
    # # get the top view preselection masks and save them
    image_dir = "/Users/neo/Documents/Research/DeepHeme/LLData/topviews_1k/BMA"
    save_dir = "/Users/neo/Documents/Research/DeepHeme/LLData/topviews_1k_bma_particles_no_bg_removal"
    error_images = []
    for image_name in tqdm(os.listdir(image_dir)):

        try:
            image_path = os.path.join(image_dir, image_name)
            image = cv2.imread(image_path)
            mask, overlayed_image, final_blue_mask = get_top_view_preselection_mask(
                image, verbose=False
            )
            mask_path = os.path.join(save_dir, image_name)

            # save the image, final_blue_mask, mask, and overlayed_image in a 2x2 grid as a single image
            # the image should be in the top left, the final_blue_mask should be in the top right
            # the mask should be in the bottom left, and the overlayed_image should be in the bottom right
            # the image should be displayed in color, the final_blue_mask and the mask should be displayed in grayscale
            # the overlayed_image should be displayed in color

            # construct the 2x2 grid
            grid = np.zeros((2 * image.shape[0], 2 * image.shape[1], 3), dtype="uint8")
            grid[: image.shape[0], : image.shape[1]] = image
            grid[: image.shape[0], image.shape[1] :] = cv2.cvtColor(
                final_blue_mask, cv2.COLOR_GRAY2BGR
            )
            grid[image.shape[0] :, : image.shape[1]] = cv2.cvtColor(
                mask, cv2.COLOR_GRAY2BGR
            )
            grid[image.shape[0] :, image.shape[1] :] = overlayed_image

            # save the grid
            cv2.imwrite(mask_path, grid)

        except Exception as e:
            print(e)
            print(image_name)
            error_images.append(image_name)
            continue

    print(error_images)
