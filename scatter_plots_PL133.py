import os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# df = pd.read_csv('../data/jitter.csv')
def scatter_plot_temp(df,inpt,outpt, save_path=None, show=True):
    # 2. Forward fill the missing values and clean up temperature names
    # df["temp"] = df["temp"].ffill()
    # df["temp"] = df["temp"].str.extract(r"(-?\d+)")

    # 3. Explicitly define your custom colors for each group
    color_map = {"-40": "#377eb8","20": "#1ae482", "70": "#b83737", }  # Distinct red and blue hex colors

    # 4. Set up the plot
    fig, ax = plt.subplots(figsize=(8, 6))

    # 5. Group data by 'Temp' and plot each group separately
    # Matplotlib automatically extracts the group label to create a perfect native legend
    for temp_label, group in df.groupby("temp"):
        ax.scatter(
            group[f"{df.columns[inpt]}"],
            group[f"{df.columns[outpt]}"],  
            color=color_map.get(temp_label),  # Match label to our color map
            label=temp_label,  # Assign label explicitly to this plot group
            s=100,  # Size of markers
            alpha=0.8,
            edgecolors="none",
        )

    # 6. Customize plot details
    plt.title(f"{df.columns[outpt]} vs. {df.columns[inpt]}")
    plt.xlabel(f"{df.columns[inpt]}")
    plt.ylabel(f"{df.columns[outpt]}")
    plt.grid(True, linestyle="--", alpha=0.6)

    # 7. Render the legend (this will now correctly pair color icons + text labels)
    plt.legend(title="Temperature", loc="upper right")
    
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        

    # 8. Display the plot
    if show:
        plt.show()
    else: 
        
        plt.close(fig)
    return fig
### 

def data_ranges(df, outpt):
    min = np.min(df[f'{df.columns[outpt]}'])
    max = np.max(df[f'{df.columns[outpt]}'])
    range = max-min
    return min, max, range
