import os
import matplotlib.pyplot as plt

def scatter_plot_temp(df, outpt, save_path=None, show=True):
    color_map = {"-40": "#377eb8", "20": "#1ae482", "70": "#b83737"}

    fig, ax = plt.subplots(figsize=(8, 6))

    for temp_label, group in df.groupby("temp"):
        ax.scatter(
            group[df.columns[1]],
            group[df.columns[outpt]],
            color=color_map.get(str(temp_label)),
            label=temp_label,
            s=100,
            alpha=0.8,
            edgecolors="none",
        )

    ax.set_title(f"{df.columns[outpt]} vs. {df.columns[1]}")
    ax.set_xlabel(df.columns[1])
    ax.set_ylabel(df.columns[outpt])
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend(title="Temperature", loc="upper right")

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")

    if show:
        plt.show()
    else:
        plt.close(fig)

    return fig