"""Shared figure style: quiet grey for context, one blue accent for the point."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

BLUE = "#2f7bd9"
GREY = "#8a8a8a"
DARK = "#333333"
LIGHT = "#f0f0f0"
RED = "#c4553a"


def setup(figsize=(10, 5.4)):
    fig, ax = plt.subplots(figsize=figsize, dpi=150)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(colors="#555555", length=0)
    ax.grid(axis="y", color="#e6e6e6")
    ax.set_axisbelow(True)
    return fig, ax


def titles(fig, title, subtitle=None, source=None):
    fig.text(0.02, 0.965, title, ha="left", va="top", fontsize=13.5, fontweight="bold", color="#111111")
    if subtitle:
        fig.text(0.02, 0.915, subtitle, ha="left", va="top", fontsize=9.5, color="#555555")
    if source:
        fig.text(0.02, 0.012, source, ha="left", va="bottom", fontsize=7.5, color="#777777")


def shade_episodes(ax, episodes, ymax_text=None, labels=True):
    for i, (a, b, lab) in enumerate(episodes):
        if i % 2 == 1:
            ax.axvspan(a - 0.5, b + 0.5, color=LIGHT, zorder=0)
        if labels and ymax_text is not None:
            ax.text((a + b) / 2, ymax_text, lab, ha="center", va="top", fontsize=8.5, color="#555555")


def save(fig, path, rect=(0, 0.04, 1, 0.88)):
    fig.tight_layout(rect=rect)
    fig.savefig(path)
    plt.close(fig)
