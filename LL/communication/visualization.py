####################################################################################################
# Imports ##########################################################################################
####################################################################################################

# Outside imports ##################################################################################
from PIL import Image, ImageOps
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import cv2
import numpy as np


def annotate_focus_region(image, bboxes):
    """Return the image of the focus region annotated with the WBC candidates.
    bboxes is a list of tuples of the form (TL_x, TL_y, BR_x, BR_y).
    The input image is a PIL image.
    """

    # convert the image to numpy array
    image = np.array(image)

    # draw the bounding boxes in color red
    for bbox in bboxes:
        image = cv2.rectangle(
            image, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (255, 0, 0), 3
        )

    # convert the image back to PIL image
    image = Image.fromarray(image)

    return image


def save_hist_KDE_rug_plot(df, column_name, save_path, title, lines=[]):
    """
    This function takes a pandas DataFrame, the name of the column to plot,
    and a save path. It creates a histogram with a KDE overlay and rug plot for the specified
    column, with a dark, techno-futuristic, minimalistic, and medically professional theme,
    with the brightest elements for better visibility, saves the plot to the given path,
    and then closes the matplotlib figure.

    :param df: pandas DataFrame containing the data.
    :param column_name: string, the name of the column to plot.
    :param save_path: string, the file path where the plot will be saved.
    """
    # Set the dark theme with the brightest elements
    sns.set_theme(style="darkgrid")

    # Create the figure with techno theme
    plt.figure(figsize=(10, 6))

    # print("Diagnostics for column: ", column_name)
    # print(df[column_name])
    # print(df[column_name].isnull().any())
    # print(df[column_name].dtype)

    df_for_plot = df.copy()

    # Perform the rounding
    df_for_plot[column_name] = df_for_plot[column_name].round(3)

    # Create the histogram with KDE plot, changing 'stat' from 'density' to 'count' for mass
    sns.histplot(
        df_for_plot[column_name], kde=True, color="#606060", stat="count", edgecolor="none"
    )  # Even brighter grey

    # Add rug plot
    sns.rugplot(
        df_for_plot[column_name], color="#00FF00", height=0.05, alpha=0.5
    )  # Neon green for futuristic feel

    # Customize the plot to match a techno futuristic theme
    plt.title(title, fontsize=15, color="#00FF00")
    plt.xlabel(column_name, fontsize=12, color="#00FF00")
    plt.ylabel("Mass", fontsize=12, color="#00FF00")  # Change label to 'Mass'

    # Customize the KDE line color
    plt.setp(plt.gca().lines, color="#FFFFFF")  # Set the KDE line to white

    # Change the axis increment numbers to white
    plt.tick_params(axis="x", colors="white")
    plt.tick_params(axis="y", colors="white")

    # Plotting vertical red lines at specified positions
    for line in lines:
        if isinstance(line, (int, float)):  # Ensure the line position is a number
            plt.axvline(
                x=line, color="red", linestyle="--"
            )  # Add a dashed red line at each specified position

    # Set the spines to a bright color
    for spine in plt.gca().spines.values():
        spine.set_edgecolor("#00FF00")

    # Set the face color of the axes
    plt.gca().set_facecolor("#121212")  # Dark background for contrast

    # Set the grid to a brighter color
    plt.grid(color="#777777")  # Brighter grey for the grid

    # Save the plot with transparent background
    plt.savefig(save_path, transparent=True, facecolor="#121212")

    # Close the plot to free memory
    plt.close()


# def save_bar_chart(
#     data_dict,
#     save_path,
#     title,
#     xaxis_name,
#     yaxis_name,
#     color="green",
#     edge_color="white",
# ):
#     """
#     Plots a bar chart with a specific theme from a given dictionary.
#     The keys of the dictionary are used as labels, and the values are used as the heights of the bars.

#     Args:
#     data_dict (dict): A dictionary where the keys are strings and the values are numbers (int or float).
#     color (str): Color of the bars.
#     edge_color (str): Color of the edges of the bars.
#     """

#     # Extracting keys and values from the dictionary
#     keys = list(data_dict.keys())
#     values = list(data_dict.values())

#     # Creating the bar chart with a specific theme
#     plt.figure(figsize=(12, 7))
#     bars = plt.bar(keys, values, color=color, edgecolor=edge_color)

#     # Setting the background color
#     plt.gca().set_facecolor("black")
#     plt.gcf().set_facecolor("black")

#     # Changing the color of the axes and axes labels
#     plt.gca().spines["bottom"].set_color(edge_color)
#     plt.gca().spines["left"].set_color(edge_color)
#     plt.tick_params(axis="x", colors=edge_color)
#     plt.tick_params(axis="y", colors=edge_color)

#     # Setting the title and labels with a specific font color
#     plt.title(title, color=edge_color)
#     plt.xlabel(xaxis_name, color=edge_color)
#     plt.ylabel(yaxis_name, color=edge_color)

#     # save the plot to save_path
#     plt.savefig(save_path, transparent=True, facecolor="black")

#     # close the plot to free memory
#     plt.close()


def save_bar_chart(
    data_dict,
    save_path,
    title,
    xaxis_name,
    yaxis_name,
    color="green",
    edge_color="white",
):
    """
    Plots a bar chart with a specific theme from a given dictionary.
    The keys of the dictionary are used as labels, and the values are used as the heights of the bars.
    Replaces 'immature granulocyte' with 'Imm. Gran.' in x-axis labels.

    Args:
    data_dict (dict): A dictionary where the keys are strings and the values are numbers (int or float).
    color (str): Color of the bars.
    edge_color (str): Color of the edges of the bars.
    """

    # Extracting keys and values from the dictionary
    keys = [
        label.replace("Immature Granulocyte", "Imm. Gran.")
        for label in data_dict.keys()
    ]
    values = list(data_dict.values())

    # Creating the bar chart with a specific theme
    plt.figure(figsize=(12, 7))
    bars = plt.bar(keys, values, color=color, edgecolor=edge_color)

    # Setting the background color
    plt.gca().set_facecolor("black")
    plt.gcf().set_facecolor("black")

    # Changing the color of the axes and axes labels
    plt.gca().spines["bottom"].set_color(edge_color)
    plt.gca().spines["left"].set_color(edge_color)
    plt.tick_params(axis="x", colors=edge_color)
    plt.tick_params(axis="y", colors=edge_color)

    # Setting the title and labels with a specific font color
    plt.title(title, color=edge_color)
    plt.xlabel(xaxis_name, color=edge_color)
    plt.ylabel(yaxis_name, color=edge_color)

    # save the plot to save_path
    plt.savefig(save_path, transparent=True, facecolor="black")

    # close the plot to free memory
    plt.close()
