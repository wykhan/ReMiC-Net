from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from workspace.common.io_utils import ensure_dir, read_json


def _load_metrics(output_root: Path, mode: str) -> dict | None:
    path = output_root / f"metrics_{mode}.json"
    return read_json(path) if path.exists() else None


def render(output_root: Path) -> None:
    curves_dir = ensure_dir(output_root / "viz" / "curves")
    metrics = {mode: _load_metrics(output_root, mode) for mode in ["M1", "M2", "M3"]}
    available = {key: value for key, value in metrics.items() if value is not None}

    fig, ax = plt.subplots(figsize=(7, 4))
    modes = list(available.keys())
    gains = [available[mode]["overall"]["nmse_gain_vs_ref3"] for mode in modes]
    ax.bar(modes, gains, color=["#588157", "#a3b18a", "#dda15e"][: len(modes)])
    ax.set_title("Quality gain vs ref3")
    ax.set_ylabel("NMSE gain")
    fig.tight_layout()
    fig.savefig(curves_dir / "quality_gain_vs_ref3.png", dpi=170)
    plt.close(fig)

    if (output_root / "family_metrics.csv").exists():
        import csv

        rows = list(csv.DictReader((output_root / "family_metrics.csv").open("r", encoding="utf-8")))
        families = sorted({row["family"] for row in rows if row["mode"] == modes[0]})
        fig, ax = plt.subplots(figsize=(12, 5))
        x = np.arange(len(families))
        width = 0.2
        baseline = [float(next(row["ref3_nmse_mean"] for row in rows if row["mode"] == modes[0] and row["family"] == family)) for family in families]
        ax.bar(x - width, baseline, width=width, label="ref3")
        for idx, mode in enumerate(modes):
            values = []
            for family in families:
                match = next((row for row in rows if row["mode"] == mode and row["family"] == family), None)
                values.append(float(match["learned_nmse_mean"]) if match is not None else np.nan)
            ax.bar(x + idx * width, values, width=width, label=mode)
        ax.set_xticks(x)
        ax.set_xticklabels(families, rotation=20)
        ax.set_ylabel("NMSE mean")
        ax.set_title("Family metrics learning")
        ax.legend()
        fig.tight_layout()
        fig.savefig(curves_dir / "family_metrics_learning.png", dpi=170)
        plt.close(fig)

    if (output_root / "failure_mode_improvement.csv").exists():
        import csv

        rows = list(csv.DictReader((output_root / "failure_mode_improvement.csv").open("r", encoding="utf-8")))
        labels = ["F2", "F3", "F4"]
        fig, ax = plt.subplots(figsize=(9, 4.5))
        x = np.arange(len(labels))
        width = 0.22
        for idx, mode in enumerate(modes):
            vals = [int(next(row["improvement_count"] for row in rows if row["mode"] == mode and row["failure_label"] == label)) for label in labels]
            ax.bar(x + idx * width, vals, width=width, label=mode)
        ax.set_xticks(x + width)
        ax.set_xticklabels(labels)
        ax.set_ylabel("count decrease vs ref3")
        ax.set_title("Failure mode improvement")
        ax.legend()
        fig.tight_layout()
        fig.savefig(curves_dir / "failure_mode_improvement.png", dpi=170)
        plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render aggregate learning curves for task_real_006.")
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()
    render(Path(args.output_root))
    print("Rendered learning visualizations")


if __name__ == "__main__":
    main()
