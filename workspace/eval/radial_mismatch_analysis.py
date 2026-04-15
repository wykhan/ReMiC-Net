from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from workspace.common.io_utils import ensure_dir, read_json, write_json


METHOD_ORDER = ["ref3", "ref5", "ref7", "ref9", "BP"]


def _group_curve(rows: list[dict], x_key: str, y_key: str) -> dict[str, list[list[float]]]:
    output: dict[str, list[list[float]]] = {}
    for method in METHOD_ORDER:
        selected = [row for row in rows if row["method"] == method]
        xs = sorted({float(row[x_key]) for row in selected})
        curve = []
        for x in xs:
            vals = [float(row[y_key]) for row in selected if float(row[x_key]) == x]
            curve.append([x, float(np.mean(vals))])
        output[method] = curve
    return output


def analyze(output_root: Path) -> dict:
    payload = read_json(output_root / "baseline_metrics_faithful.json")
    rows = payload["per_sample"]
    rho_rows = [row for row in rows if row["control_group"] == "rho_sweep"]
    mismatch_rows = [row for row in rows if row["control_group"] == "rho_sweep"]

    result = {
        "nmse_vs_rho_target": _group_curve(rho_rows, "rho_target_m", "nmse"),
        "psnr_vs_rho_target": _group_curve(rho_rows, "rho_target_m", "psnr"),
        "ssim_vs_rho_target": _group_curve(rho_rows, "rho_target_m", "ssim"),
        "error_vs_radial_mismatch": _group_curve(mismatch_rows, "radial_mismatch_m", "nmse"),
    }
    write_json(output_root / "radial_mismatch_metrics.json", result)
    return result


def plot_curves(output_root: Path, metrics: dict) -> None:
    curves_dir = ensure_dir(output_root / "viz" / "curves")

    def _plot(curve_key: str, filename: str, ylabel: str) -> None:
        fig, ax = plt.subplots(figsize=(6, 4))
        for method in METHOD_ORDER:
            pts = np.array(metrics[curve_key][method], dtype=np.float64)
            if pts.size == 0:
                continue
            ax.plot(pts[:, 0], pts[:, 1], marker="o", label=method)
        ax.set_xlabel(curve_key.split("_vs_")[-1].replace("_", " "))
        ax.set_ylabel(ylabel)
        ax.legend()
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        fig.savefig(curves_dir / filename, dpi=160)
        plt.close(fig)

    _plot("nmse_vs_rho_target", "nmse_vs_rho_target.png", "NMSE")
    _plot("psnr_vs_rho_target", "psnr_vs_rho_target.png", "PSNR")
    _plot("ssim_vs_rho_target", "ssim_vs_rho_target.png", "SSIM")
    _plot("error_vs_radial_mismatch", "error_vs_radial_mismatch.png", "NMSE")

    baseline = read_json(output_root / "baseline_metrics_faithful.json")["aggregate"]
    methods = METHOD_ORDER
    x = np.arange(len(methods))
    runtime = [baseline[m]["wall_time_mean_sec"] for m in methods]
    quality = [baseline[m]["nmse_mean"] for m in methods]

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(x, runtime)
    ax.set_xticks(x, methods)
    ax.set_ylabel("Wall Time Mean (sec)")
    ax.set_title("runtime_vs_method")
    fig.tight_layout()
    fig.savefig(curves_dir / "runtime_vs_method.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(x, quality)
    ax.set_xticks(x, methods)
    ax.set_ylabel("NMSE Mean")
    ax.set_title("quality_vs_method")
    fig.tight_layout()
    fig.savefig(curves_dir / "quality_vs_method.png", dpi=160)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze faithful radial mismatch curves.")
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()
    metrics = analyze(Path(args.output_root))
    plot_curves(Path(args.output_root), metrics)
    print("Radial mismatch analysis complete")


if __name__ == "__main__":
    main()
