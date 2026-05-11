from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from workspace.common.io_utils import ensure_dir, read_json, write_json


METHOD_ORDER = ["ref3", "ref5", "ref7", "ref9", "BP"]
SUBSET_KEYS = [
    ("all_samples", None),
    ("seam_subset", "seam_subset"),
    ("non_seam_subset", "non_seam_subset"),
    ("inner_radius_subset", "inner_radius_subset"),
    ("outer_radius_subset", "outer_radius_subset"),
    ("height_edge_subset", "height_edge_subset"),
    ("double_point_subset", "double_point_subset"),
]


def _group_curve(rows: list[dict], x_key: str, y_key: str) -> dict[str, list[list[float]]]:
    output: dict[str, list[list[float]]] = {}
    for method in METHOD_ORDER:
        selected = [row for row in rows if row["method"] == method]
        xs = sorted({float(row[x_key]) for row in selected})
        output[method] = [
            [x, float(np.mean([float(row[y_key]) for row in selected if float(row[x_key]) == x]))]
            for x in xs
        ]
    return output


def analyze_variantB(output_root: Path) -> dict:
    payload = read_json(output_root / "baseline_metrics_variantB.json")
    rows = payload["per_sample"]
    ref7_rows = {row["sample_id"]: row for row in rows if row["method"] == "ref7"}
    ref9_rows = {row["sample_id"]: row for row in rows if row["method"] == "ref9"}

    monotonicity_rows: list[dict] = []
    gap_distribution: list[dict] = []
    wrap_symmetry_error: list[list[float]] = []

    for subset_name, subset_key in SUBSET_KEYS:
        sample_ids = [
            sample_id
            for sample_id, row in ref7_rows.items()
            if subset_key is None or bool(row.get(subset_key, False))
        ]
        nmse_violations = 0
        psnr_violations = 0
        for sample_id in sample_ids:
            if ref9_rows[sample_id]["nmse"] > ref7_rows[sample_id]["nmse"]:
                nmse_violations += 1
            if ref9_rows[sample_id]["psnr"] < ref7_rows[sample_id]["psnr"]:
                psnr_violations += 1
            gap_distribution.append(
                {
                    "subset": subset_name,
                    "sample_id": sample_id,
                    "nmse_gap_ref9_minus_ref7": float(ref9_rows[sample_id]["nmse"] - ref7_rows[sample_id]["nmse"]),
                    "psnr_gap_ref9_minus_ref7": float(ref9_rows[sample_id]["psnr"] - ref7_rows[sample_id]["psnr"]),
                }
            )
        monotonicity_rows.append(
            {
                "subset": subset_name,
                "nmse_violation_count": nmse_violations,
                "psnr_violation_count": psnr_violations,
                "total_samples": len(sample_ids),
            }
        )

    seam_rows = [row for row in rows if row["method"] == "ref9" and row["control_group"] == "azimuth_control" and row["seam_subset"]]
    seam_pairs: dict[tuple[float, float], dict[str, float]] = {}
    for row in seam_rows:
        key = (float(row["rho_target_m"]), float(row["z_target_m"]))
        if row["theta_target_rad"] < 0:
            seam_pairs.setdefault(key, {})["left_nmse"] = float(row["nmse"])
        else:
            seam_pairs.setdefault(key, {})["right_nmse"] = float(row["nmse"])
    for key, value in seam_pairs.items():
        if "left_nmse" in value and "right_nmse" in value:
            wrap_symmetry_error.append([key[0], abs(value["left_nmse"] - value["right_nmse"])])

    rho_rows = [row for row in rows if row["control_group"] == "rho_sweep"]
    result = {
        "monotonicity_by_subset": monotonicity_rows,
        "wrap_symmetry_error_variantB": wrap_symmetry_error,
        "ref7_ref9_gap_distribution": gap_distribution,
        "nmse_vs_rho_target": _group_curve(rho_rows, "rho_target_m", "nmse"),
        "error_vs_radial_mismatch": _group_curve(rho_rows, "radial_mismatch_m", "nmse"),
    }
    write_json(output_root / "stability_metrics_variantB.json", result)

    with (output_root / "monotonicity_violations_variantB.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["subset", "nmse_violation_count", "psnr_violation_count", "total_samples"])
        writer.writeheader()
        writer.writerows(monotonicity_rows)
    return result


def plot_variantB(output_root: Path, metrics: dict) -> None:
    curves_dir = ensure_dir(output_root / "viz" / "curves")
    baseline = read_json(output_root / "baseline_metrics_variantB.json")["aggregate"]

    methods = METHOD_ORDER
    x = np.arange(len(methods))

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(x, [baseline[m]["wall_time_mean_sec"] for m in methods])
    ax.set_xticks(x, methods)
    ax.set_ylabel("Wall Time Mean (sec)")
    fig.tight_layout()
    fig.savefig(curves_dir / "runtime_vs_method_variantB.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(x, [baseline[m]["speedup_vs_bp"] for m in methods])
    ax.set_xticks(x, methods)
    ax.set_ylabel("Speedup vs BP")
    fig.tight_layout()
    fig.savefig(curves_dir / "speedup_vs_bp_variantB.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(x, [baseline[m]["nmse_mean"] for m in methods])
    ax.set_xticks(x, methods)
    ax.set_ylabel("NMSE Mean")
    fig.tight_layout()
    fig.savefig(curves_dir / "quality_vs_method_variantB.png", dpi=160)
    plt.close(fig)

    monotonicity = metrics["monotonicity_by_subset"]
    fig, ax = plt.subplots(figsize=(8, 4))
    xs = np.arange(len(monotonicity))
    ax.bar(xs - 0.15, [row["nmse_violation_count"] for row in monotonicity], width=0.3, label="NMSE")
    ax.bar(xs + 0.15, [row["psnr_violation_count"] for row in monotonicity], width=0.3, label="PSNR")
    ax.set_xticks(xs, [row["subset"] for row in monotonicity], rotation=25, ha="right")
    ax.set_ylabel("Violation Count")
    ax.legend()
    fig.tight_layout()
    fig.savefig(curves_dir / "monotonicity_violations_by_subset.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 4))
    pts = np.array(metrics["wrap_symmetry_error_variantB"], dtype=np.float64)
    if pts.size > 0:
        ax.plot(pts[:, 0], pts[:, 1], marker="o")
    ax.set_xlabel("rho target")
    ax.set_ylabel("Wrap symmetry error")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(curves_dir / "wrap_symmetry_error_variantB.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 4))
    gaps = [row["nmse_gap_ref9_minus_ref7"] for row in metrics["ref7_ref9_gap_distribution"] if row["subset"] == "all_samples"]
    ax.hist(gaps, bins=16)
    ax.set_xlabel("NMSE gap ref9-ref7")
    ax.set_ylabel("Count")
    fig.tight_layout()
    fig.savefig(curves_dir / "ref7_ref9_gap_distribution.png", dpi=160)
    plt.close(fig)

    for key, filename in [
        ("nmse_vs_rho_target", "nmse_vs_rho_target_variantB.png"),
        ("error_vs_radial_mismatch", "error_vs_radial_mismatch_variantB.png"),
    ]:
        fig, ax = plt.subplots(figsize=(6, 4))
        for method in METHOD_ORDER:
            pts = np.array(metrics[key][method], dtype=np.float64)
            if pts.size == 0:
                continue
            ax.plot(pts[:, 0], pts[:, 1], marker="o", label=method)
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_xlabel(key.split("_vs_")[-1].replace("_", " "))
        ax.set_ylabel("NMSE")
        fig.tight_layout()
        fig.savefig(curves_dir / filename, dpi=160)
        plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze Variant B broader controlled suite stability.")
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()
    metrics = analyze_variantB(Path(args.output_root))
    plot_variantB(Path(args.output_root), metrics)
    print("Variant B stability analysis complete")


if __name__ == "__main__":
    main()
