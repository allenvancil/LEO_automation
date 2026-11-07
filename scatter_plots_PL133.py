import io
import matplotlib.pyplot as plt
import pandas as pd


# df = pd.read_csv('../data/jitter.csv')
def scatter_plot_temp(df, outpt):
    # 2. Forward fill the missing values and clean up temperature names
    # df["temp"] = df["temp"].ffill()
    # df["temp"] = df["temp"].str.extract(r"(-?\d+)")

    # 3. Explicitly define your custom colors for each group
    color_map = {"-40": "#377eb8","20": "#1ae482", "70": "#b83737", }  # Distinct red and blue hex colors

    # 4. Set up the plot
    plt.figure(figsize=(8, 6))

    # 5. Group data by 'Temp' and plot each group separately
    # Matplotlib automatically extracts the group label to create a perfect native legend
    for temp_label, group in df.groupby("temp"):
        plt.scatter(
            group[f"{df.columns[1]}"],
            group[f"{df.columns[outpt]}"],
            color=color_map.get(temp_label, "black"),  # Match label to our color map
            label=temp_label,  # Assign label explicitly to this plot group
            s=100,  # Size of markers
            alpha=0.8,
            edgecolors="none",
        )

    # 6. Customize plot details
    plt.title(f"{df.columns[outpt]} vs. {df.columns[1]}")
    plt.xlabel(f"{df.columns[1]}")
    plt.ylabel(f"{df.columns[outpt]}")
    plt.grid(True, linestyle="--", alpha=0.6)

    # 7. Render the legend (this will now correctly pair color icons + text labels)
    plt.legend(title="Temperature", loc="upper right")

    # 8. Display the plot
    plt.show()

