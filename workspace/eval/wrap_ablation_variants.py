from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np

from workspace.common.io_utils import ensure_dir, read_json, write_json
from workspace.common.protocol import PROTOCOL_V1
from workspace.recon.cyl_fast_reference_engine import reconstruct_cylindrical_reference


VARIANTS = {
    "A": {"tensor_mode": "active", "geom_mode": "linear"},
    "B": {"tensor_mode": "active", "geom_mode": "sinc"},
    "C": {"tensor_mode": "dense_global", "geom_mode": "linear"},
    "D": {"tensor_mode": "dense_global", "geom_mode": "sinc"},
}
METHOD_ORDER = ["ref7", "ref9", "BP"]


def evaluate_wrap_variants(output_root: Path, repeats: int = 1) -> dict:
    index = read_json(output_root / "dataset" / "index.json")
    echo_dir = output_root / "dataset" / "echoes"
    recon_dir = ensure_dir(output_root / "wrap_variant_cache")
    per_sample: list[dict] = []
    aggregate: dict[str, dict[str, dict]] = {variant: {} for variant in VARIANTS}

    for variant_name, variant_cfg in VARIANTS.items():
        for method in METHOD_ORDER:
            rows: list[dict] = []
            for item in index:
                sample_id = item["sample_id"]
                echo_path = echo_dir / f"{sample_id}_echo_sparse.npz"
                best_result = None
                run_times: list[float] = []
                memories: list[float] = []
                for _ in range(repeats):
                    result = reconstruct_cylindrical_reference(
                        output_root / item["scene_path"],
                        echo_path,
                        method,
                        tensor_mode=variant_cfg["tensor_mode"],
                        geom_mode=variant_cfg["geom_mode"],
                    )
                    run_times.append(float(result["wall_time_sec"]))
                    memories.append(float(result["estimated_peak_memory_mb"]))
                    if best_result is None:
                        best_result = result
                assert best_result is not None
                nearest_ref = float(PROTOCOL_V1.nearest_reference_radius(np.array([item["rho_target_m"]]), method)[0]) if method != "BP" else float(item["rho_target_m"])
                np.savez_compressed(
                    recon_dir / f"{sample_id}_{method}_{variant_name}.npz",
                    volume=best_result["volume"],
                    gt_volume=best_result["gt_volume"],
                    x_values=best_result["x_values"],
                    y_values=best_result["y_values"],
                    z_values=best_result["z_values"],
                )
                write_json(
                    recon_dir / f"{sample_id}_{method}_{variant_name}_meta.json",
                    {
                        "sample_id": sample_id,
                        "method": method,
                        "variant": variant_name,
                        "tensor_mode": variant_cfg["tensor_mode"],
                        "geom_mode": variant_cfg["geom_mode"],
                        "tensor_shape": best_result["tensor_shape"],
                        "active_coverage_ratio": best_result["active_coverage_ratio"],
                        "estimated_peak_memory_mb": best_result["estimated_peak_memory_mb"],
                        "reference_count": best_result["reference_count"],
                        "runtime_repeats_sec": run_times,
                        "quality": best_result["quality"],
                    },
                )
                row = {
                    "sample_id": sample_id,
                    "variant": variant_name,
                    "tensor_mode": variant_cfg["tensor_mode"],
                    "geom_mode": variant_cfg["geom_mode"],
                    "method": method,
                    "stress_pair_group": item["stress_pair_group"],
                    "stress_radius_group": item["stress_radius_group"],
                    "stress_height_group": item["stress_height_group"],
                    "stress_offset_name": item["stress_offset_name"],
                    "stress_offset_steps": item["stress_offset_steps"],
                    "rho_target_m": item["rho_target_m"],
                    "theta_target_rad": item["theta_target_rad"],
                    "z_target_m": item["z_target_m"],
                    "nearest_reference_m": nearest_ref,
                    "radial_mismatch_m": abs(item["rho_target_m"] - nearest_ref),
                    "nmse": best_result["quality"]["nmse"],
                    "psnr": best_result["quality"]["psnr"],
                    "ssim": best_result["quality"]["ssim"],
                    "wall_time_mean_sec": float(np.mean(run_times)),
                    "wall_time_std_sec": float(np.std(run_times)),
                    "estimated_peak_memory_mb": float(np.max(memories)),
                    "active_coverage_ratio": best_result["active_coverage_ratio"],
                    "tensor_shape": "x".join(str(v) for v in best_result["tensor_shape"]),
                }
                rows.append(row)
                per_sample.append(row)
            aggregate[variant_name][method] = {
                "nmse_mean": float(np.mean([row["nmse"] for row in rows])),
                "psnr_mean": float(np.mean([row["psnr"] for row in rows])),
                "ssim_mean": float(np.mean([row["ssim"] for row in rows])),
                "wall_time_mean_sec": float(np.mean([row["wall_time_mean_sec"] for row in rows])),
                "estimated_peak_memory_mb": float(np.mean([row["estimated_peak_memory_mb"] for row in rows])),
                "active_coverage_ratio": float(np.mean([row["active_coverage_ratio"] for row in rows])),
                "num_samples": len(rows),
            }

    payload = {"variants": VARIANTS, "aggregate": aggregate, "per_sample": per_sample}
    write_json(output_root / "wrap_variant_metrics.json", payload)

    with (output_root / "runtime_memory_by_variant.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "variant",
                "method",
                "tensor_mode",
                "geom_mode",
                "wall_time_mean_sec",
                "estimated_peak_memory_mb",
                "active_coverage_ratio",
            ],
        )
        writer.writeheader()
        for variant_name, method_dict in aggregate.items():
            for method in METHOD_ORDER:
                writer.writerow(
                    {
                        "variant": variant_name,
                        "method": method,
                        "tensor_mode": VARIANTS[variant_name]["tensor_mode"],
                        "geom_mode": VARIANTS[variant_name]["geom_mode"],
                        "wall_time_mean_sec": method_dict[method]["wall_time_mean_sec"],
                        "estimated_peak_memory_mb": method_dict[method]["estimated_peak_memory_mb"],
                        "active_coverage_ratio": method_dict[method]["active_coverage_ratio"],
                    }
                )
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Run wrap ablation A/B/C/D variants.")
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--repeats", type=int, default=1)
    args = parser.parse_args()
    payload = evaluate_wrap_variants(Path(args.output_root), repeats=args.repeats)
    print(f"Wrap ablation rows={len(payload['per_sample'])}")


if __name__ == "__main__":
    main()
