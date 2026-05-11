from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from workspace.common.io_utils import ensure_dir, read_json, write_json


VARIANT_ORDER = ["A", "B", "C", "D"]
METHOD_ORDER = ["ref7", "ref9", "BP"]


def _pair_key(row: dict) -> tuple[str, str]:
    return row["stress_pair_group"], str(row["stress_offset_steps"])


def analyze_wrap_metrics(output_root: Path) -> dict:
    payload = read_json(output_root / "wrap_variant_metrics.json")
    rows = payload["per_sample"]

    monotonicity_rows: list[dict] = []
    wrap_symmetry: dict[str, dict[str, list[list[float]]]] = {variant: {method: [] for method in METHOD_ORDER} for variant in VARIANT_ORDER}
    edge_metrics: dict[str, dict[str, dict[str, float]]] = {variant: {} for variant in VARIANT_ORDER}
    mismatch_curves: dict[str, dict[str, list[list[float]]]] = {variant: {method: [] for method in METHOD_ORDER} for variant in VARIANT_ORDER}

    for variant in VARIANT_ORDER:
        variant_rows = [row for row in rows if row["variant"] == variant]
        for method in METHOD_ORDER:
            method_rows = [row for row in variant_rows if row["method"] == method]
            edge_metrics[variant][method] = {
                "nmse_mean": float(np.mean([row["nmse"] for row in method_rows])),
                "psnr_mean": float(np.mean([row["psnr"] for row in method_rows])),
                "ssim_mean": float(np.mean([row["ssim"] for row in method_rows])),
            }
            mismatch_groups = sorted({float(row["radial_mismatch_m"]) for row in method_rows})
            mismatch_curves[variant][method] = [
                [
                    mismatch,
                    float(np.mean([row["nmse"] for row in method_rows if float(row["radial_mismatch_m"]) == mismatch])),
                ]
                for mismatch in mismatch_groups
            ]

        ref7_rows = {row["sample_id"]: row for row in variant_rows if row["method"] == "ref7"}
        ref9_rows = {row["sample_id"]: row for row in variant_rows if row["method"] == "ref9"}
        nmse_violations = 0
        psnr_violations = 0
        for sample_id in sorted(ref7_rows):
            if ref9_rows[sample_id]["nmse"] > ref7_rows[sample_id]["nmse"]:
                nmse_violations += 1
            if ref9_rows[sample_id]["psnr"] < ref7_rows[sample_id]["psnr"]:
                psnr_violations += 1
        monotonicity_rows.append(
            {
                "variant": variant,
                "nmse_violation_count": nmse_violations,
                "psnr_violation_count": psnr_violations,
                "total_samples": len(ref7_rows),
            }
        )

        for method in METHOD_ORDER:
            method_rows = [row for row in variant_rows if row["method"] == method]
            neg_rows = {(row["stress_pair_group"], row["stress_offset_steps"]): row for row in method_rows if row["stress_offset_name"].startswith("negpi")}
            pos_rows = {(row["stress_pair_group"], row["stress_offset_steps"]): row for row in method_rows if row["stress_offset_name"].startswith("pi")}
            for key in sorted(set(neg_rows) & set(pos_rows), key=lambda item: (item[0], int(item[1]))):
                left = neg_rows[key]
                right = pos_rows[key]
                wrap_symmetry[variant][method].append(
                    [float(key[1]), abs(float(left["nmse"]) - float(right["nmse"]))]
                )

    with (output_root / "monotonicity_violations.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["variant", "nmse_violation_count", "psnr_violation_count", "total_samples"])
        writer.writeheader()
        writer.writerows(monotonicity_rows)

    result = {
        "variant_definition": payload["variants"],
        "edge_metrics": edge_metrics,
        "wrap_symmetry_error": wrap_symmetry,
        "monotonicity": monotonicity_rows,
        "error_vs_radial_mismatch_edge_subset": mismatch_curves,
    }
    write_json(output_root / "wrap_stability_metrics.json", result)
    return result


def plot_wrap_metrics(output_root: Path, metrics: dict) -> None:
    curves_dir = ensure_dir(output_root / "viz" / "curves")
    runtime_rows = read_json(output_root / "wrap_variant_metrics.json")["aggregate"]
    monotonicity_rows = metrics["monotonicity"]

    fig, ax = plt.subplots(figsize=(6, 4))
    x = np.arange(len(VARIANT_ORDER))
    nmse_vals = [next(row["nmse_violation_count"] for row in monotonicity_rows if row["variant"] == variant) for variant in VARIANT_ORDER]
    psnr_vals = [next(row["psnr_violation_count"] for row in monotonicity_rows if row["variant"] == variant) for variant in VARIANT_ORDER]
    ax.bar(x - 0.15, nmse_vals, width=0.3, label="NMSE")
    ax.bar(x + 0.15, psnr_vals, width=0.3, label="PSNR")
    ax.set_xticks(x, VARIANT_ORDER)
    ax.set_ylabel("Violation Count")
    ax.legend()
    fig.tight_layout()
    fig.savefig(curves_dir / "monotonicity_violations_by_variant.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 4))
    for variant in VARIANT_ORDER:
        pts = np.array(metrics["wrap_symmetry_error"][variant]["ref9"], dtype=np.float64)
        if pts.size == 0:
            continue
        order = np.argsort(pts[:, 0])
        ax.plot(pts[order, 0], pts[order, 1], marker="o", label=variant)
    ax.set_xlabel("Offset steps from seam")
    ax.set_ylabel("Wrap symmetry error (|NMSE_left-NMSE_right|)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(curves_dir / "wrap_symmetry_error_by_variant.png", dpi=160)
    plt.close(fig)

    for metric_name, filename, ylabel in [
        ("nmse_mean", "edge_nmse_by_variant.png", "NMSE"),
        ("psnr_mean", "edge_psnr_by_variant.png", "PSNR"),
    ]:
        fig, ax = plt.subplots(figsize=(6, 4))
        values = [metrics["edge_metrics"][variant]["ref9"][metric_name] for variant in VARIANT_ORDER]
        ax.bar(np.arange(len(VARIANT_ORDER)), values)
        ax.set_xticks(np.arange(len(VARIANT_ORDER)), VARIANT_ORDER)
        ax.set_ylabel(ylabel)
        fig.tight_layout()
        fig.savefig(curves_dir / filename, dpi=160)
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 4))
    values = [runtime_rows[variant]["ref9"]["wall_time_mean_sec"] for variant in VARIANT_ORDER]
    ax.bar(np.arange(len(VARIANT_ORDER)), values)
    ax.set_xticks(np.arange(len(VARIANT_ORDER)), VARIANT_ORDER)
    ax.set_ylabel("Wall Time Mean (sec)")
    fig.tight_layout()
    fig.savefig(curves_dir / "runtime_by_variant.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 4))
    values = [runtime_rows[variant]["ref9"]["estimated_peak_memory_mb"] for variant in VARIANT_ORDER]
    ax.bar(np.arange(len(VARIANT_ORDER)), values)
    ax.set_xticks(np.arange(len(VARIANT_ORDER)), VARIANT_ORDER)
    ax.set_ylabel("Estimated Peak Memory (MB)")
    fig.tight_layout()
    fig.savefig(curves_dir / "memory_by_variant.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 4))
    for variant in VARIANT_ORDER:
        pts = np.array(metrics["error_vs_radial_mismatch_edge_subset"][variant]["ref9"], dtype=np.float64)
        if pts.size == 0:
            continue
        order = np.argsort(pts[:, 0])
        ax.plot(pts[order, 0], pts[order, 1], marker="o", label=variant)
    ax.set_xlabel("Radial mismatch (m)")
    ax.set_ylabel("NMSE")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(curves_dir / "error_vs_radial_mismatch_edge_subset.png", dpi=160)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze wrap-stability metrics.")
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()
    metrics = analyze_wrap_metrics(Path(args.output_root))
    plot_wrap_metrics(Path(args.output_root), metrics)
    print("Wrap stability analysis complete")


if __name__ == "__main__":
    main()
