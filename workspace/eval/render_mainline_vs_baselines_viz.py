from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from workspace.common.io_utils import ensure_dir, read_json


METHODS = ["ref3", "ref5", "ref7", "ref9", "BP", "ref3+learning"]
HARD_FAMILIES = ["point_cluster", "line", "L-shape"]


def render(output_root: Path) -> None:
    curves_dir = ensure_dir(output_root / "viz" / "curves")
    metrics = read_json(output_root / "mainline_vs_baselines_metrics.json")
    overall = metrics["overall"]

    runtimes = [overall[method]["wall_time_mean_sec"] for method in METHODS]
    nmse_vals = [overall[method]["nmse_mean"] for method in METHODS]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(runtimes, nmse_vals, s=80)
    for method, x, y in zip(METHODS, runtimes, nmse_vals):
        ax.annotate(method, (x, y))
    ax.set_xlabel("Runtime (s)")
    ax.set_ylabel("NMSE mean")
    ax.set_title("Runtime-quality frontier with learning")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(curves_dir / "runtime_quality_frontier_with_learning.png", dpi=170)
    plt.close(fig)

    rows = list(csv.DictReader((output_root / "family_metrics_mainline_vs_baselines.csv").open("r", encoding="utf-8")))
    families = sorted({row["family"] for row in rows})
    x = np.arange(len(families))
    width = 0.12
    fig, ax = plt.subplots(figsize=(13, 5))
    for idx, method in enumerate(METHODS):
        vals = [float(next(row["nmse_mean"] for row in rows if row["family"] == family and row["method"] == method)) for family in families]
        ax.bar(x + (idx - 2.5) * width, vals, width=width, label=method)
    ax.set_xticks(x)
    ax.set_xticklabels(families, rotation=20)
    ax.set_ylabel("NMSE mean")
    ax.set_title("Family metrics mainline vs baselines")
    ax.legend(ncol=3, fontsize=8)
    fig.tight_layout()
    fig.savefig(curves_dir / "family_metrics_mainline_vs_baselines.png", dpi=170)
    plt.close(fig)

    failure_rows = list(csv.DictReader((output_root / "failure_mode_mainline_vs_baselines.csv").open("r", encoding="utf-8")))
    labels = ["F2", "F3", "F4"]
    fig, ax = plt.subplots(figsize=(10, 4.8))
    x = np.arange(len(labels))
    width = 0.12
    for idx, method in enumerate(METHODS):
        vals = [int(next(row["count"] for row in failure_rows if row["method"] == method and row["failure_label"] == label)) for label in labels]
        ax.bar(x + (idx - 2.5) * width, vals, width=width, label=method)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("count")
    ax.set_title("Failure mode mainline vs baselines")
    ax.legend(ncol=3, fontsize=8)
    fig.tight_layout()
    fig.savefig(curves_dir / "failure_mode_mainline_vs_baselines.png", dpi=170)
    plt.close(fig)

    hardest = read_json(output_root / "hardest_family_summary.json")
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    for ax, family in zip(axes, HARD_FAMILIES):
        methods = [method for method in METHODS if method in hardest[family]]
        vals = [hardest[family][method]["nmse_mean"] for method in methods]
        ax.bar(methods, vals)
        ax.set_title(family)
        ax.tick_params(axis="x", rotation=20)
    fig.suptitle("Hardest family case gallery")
    fig.tight_layout()
    fig.savefig(curves_dir / "hardest_family_case_gallery.png", dpi=170)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render task_real_006b mainline-vs-baselines visualizations.")
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()
    render(Path(args.output_root))
    print("Rendered task_real_006b visualizations")


if __name__ == "__main__":
    main()
