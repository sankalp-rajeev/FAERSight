"""Exactly three deterministic charts, rendered by the separately pinned Matplotlib."""

import argparse
import importlib.metadata
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def render(data_path, output):
    data = json.loads(data_path.read_text())
    output.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 11,
            "svg.hashsalt": "FAERSight-metric-study-v1",
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )
    metrics = data["metrics"]
    source = "Frozen A3 common pool | 586 rules | support 0.002 | lift >=1.2 | WEKA 3.8.6"
    footer = "Average ranks for ties. Descriptive, dependent rules; lift range restricted."
    files = []

    def save(fig, name):
        for extension in ("png", "svg"):
            path = output / f"{name}.{extension}"
            metadata = (
                {"Software": "FAERSight metric study"}
                if extension == "png"
                else {"Date": None, "Creator": "FAERSight metric study"}
            )
            fig.savefig(path, dpi=180, metadata=metadata, facecolor="white")
            files.append(path.name)
        plt.close(fig)

    by_pair = {
        tuple(sorted([r["metric_a"], r["metric_b"]])): r["spearman"] for r in data["correlations"]
    }
    matrix = [[1.0 if a == b else by_pair[tuple(sorted([a, b]))] for b in metrics] for a in metrics]
    fig, ax = plt.subplots(figsize=(8.8, 7.2))
    fig.subplots_adjust(bottom=0.21, top=0.81, left=0.16, right=0.88)
    im = ax.imshow(matrix, vmin=-1, vmax=1, cmap="RdBu_r")
    ax.set_xticks(range(4), metrics)
    ax.set_yticks(range(4), metrics)
    ax.set_xlabel("WEKA rule metric")
    ax.set_ylabel("WEKA rule metric")
    for i in range(4):
        for j in range(4):
            ax.text(
                j,
                i,
                f"{matrix[i][j]:.3f}",
                ha="center",
                va="center",
                color="white" if abs(matrix[i][j]) > 0.7 else "black",
                fontsize=13,
            )
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.05, label="Spearman rho")
    fig.suptitle("Metric-ranking agreement within the lift-qualified pool", y=0.96, fontsize=14)
    fig.text(0.5, 0.065, source + "\n" + footer, ha="center", fontsize=9)
    save(fig, "spearman_matrix")
    for selected in data["scatter_pairs"]:
        a, b = selected["metric_a"], selected["metric_b"]
        fig, ax = plt.subplots(figsize=(8.8, 7.2))
        fig.subplots_adjust(bottom=0.22, top=0.83, left=0.13, right=0.95)
        xs = [r["average_ranks"][a] for r in data["rules"]]
        ys = [r["average_ranks"][b] for r in data["rules"]]
        ax.scatter(xs, ys, s=17, color="#21627b", alpha=0.6, linewidths=0)
        ax.set_xlim(0, 587)
        ax.set_ylim(0, 587)
        ax.set_xlabel(f"{a}: average descending rank (1 = highest)")
        ax.set_ylabel(f"{b}: average descending rank (1 = highest)")
        ax.grid(alpha=0.15)
        ax.set_axisbelow(True)
        fig.suptitle(
            f"{selected['selection'].capitalize()} agreement: {a} vs {b}", y=0.96, fontsize=14
        )
        ax.set_title(f"Spearman rho = {selected['spearman']:.6f}; pair chosen mechanically")
        fig.text(0.5, 0.065, source + "\n" + footer, ha="center", fontsize=9)
        save(fig, "rank_scatter_" + selected["selection"])
    versions = {p: importlib.metadata.version(p) for p in ("matplotlib", "numpy", "pillow")}
    (output / "plot_versions.json").write_text(
        json.dumps({"versions": versions, "chart_files": files}, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    render(args.data, args.output)
