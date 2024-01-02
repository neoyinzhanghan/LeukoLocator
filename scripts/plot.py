import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

# Read the CSV file
df = pd.read_csv(
    "/Users/neo/Documents/Research/DeepHeme/LLData/LabelledCartridges/accuracy.csv"
)

# Replace NaN/NA values with 0
df['accuracy'] = df['accuracy'].fillna(0)

# Sort the data by accuracy
df_sorted = df.sort_values(by='accuracy', ascending=False)

# Create the bar plot with enhanced styling
plt.figure(figsize=(10, 6))

# Create a list of colors from light pink to dark magenta
n_bars = len(df_sorted)
colors = plt.cm.magma(np.linspace(0.3, 0.8, n_bars))

# Create bars with individual colors
bars = plt.bar(df_sorted['cellname'], df_sorted['accuracy'], color=colors)

# Adding heart symbols on top of the bars
for bar in bars:
    plt.text(bar.get_x() + bar.get_width() / 2, 
             bar.get_height(), 
             '❤️',  
             ha='center', color='purple', fontsize=12)

# Styling the plot
plt.title('❤️ Accuracy Comparison ❤️', fontsize=16, color='purple', fontweight='bold')
plt.xlabel('Cell Name', fontsize=14, color='purple', fontweight='bold')
plt.ylabel('Accuracy', fontsize=14, color='purple', fontweight='bold')
plt.xticks(rotation=45, fontsize=12, color='purple')
plt.yticks(fontsize=12, color='purple')
plt.gca().spines['top'].set_color('none')
plt.gca().spines['right'].set_color('none')
plt.gca().spines['left'].set_color('pink')
plt.gca().spines['bottom'].set_color('pink')
plt.gca().set_facecolor('#FFF0F5')  # Light pink background
plt.grid(color='lavender', linestyle='--', linewidth=0.5)

# Show the plot
plt.tight_layout()
plt.show()

# Sort the data by num_cells
df_sorted = df.sort_values(by='num_cells', ascending=False)

# Create the bar plot with enhanced styling
plt.figure(figsize=(12, 6))

# Define the number of bars and color scale
n_bars = len(df_sorted) * 2  # Two bars (num_cells and correct_num_cells) per cell
colors = plt.cm.magma(np.linspace(0.3, 0.8, n_bars))

# Create side by side bars for num_cells and correct_num_cells
bar_width = 0.35
index = np.arange(len(df_sorted))
bars1 = plt.bar(index, df_sorted['num_cells'], bar_width, color=colors[:len(df_sorted)])
bars2 = plt.bar(index + bar_width, df_sorted['correct_num_cells'], bar_width, color=colors[len(df_sorted):])

# Adding heart symbols on top of the bars
for bars in [bars1, bars2]:
    for bar in bars:
        plt.text(bar.get_x() + bar.get_width() / 2, 
                 bar.get_height(), 
                 '❤️',  
                 ha='center', color='purple', fontsize=12)

# Styling the plot
plt.title('❤️ Cell Count Comparison ❤️', fontsize=16, color='purple', fontweight='bold')
plt.xlabel('Cell Name', fontsize=14, color='purple', fontweight='bold')
plt.ylabel('Number of Cells', fontsize=14, color='purple', fontweight='bold')
plt.xticks(index + bar_width / 2, df_sorted['cellname'], rotation=45, fontsize=12, color='purple')
plt.yticks(fontsize=12, color='purple')
plt.gca().spines['top'].set_color('none')
plt.gca().spines['right'].set_color('none')
plt.gca().spines['left'].set_color('pink')
plt.gca().spines['bottom'].set_color('pink')
plt.gca().set_facecolor('#FFF0F5')  # Light pink background
plt.grid(color='lavender', linestyle='--', linewidth=0.5)
plt.legend(['Total Cells', 'Correct Cells'], loc='upper right')

# Show the plot
plt.tight_layout()
plt.show()

