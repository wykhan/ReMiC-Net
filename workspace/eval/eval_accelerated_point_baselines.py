from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np

from workspace.common.io_utils import ensure_dir, read_json, write_json
from workspace.common.protocol import PROTOCOL_V1
from workspace.recon.cyl_fast_reference_engine import reconstruct_cylindrical_reference


METHOD_ORDER = ["ref3", "ref5", "ref7", "ref9", "BP"]


def evaluate_accelerated(output_root: Path, repeats: int = 3) -> dict:
    index = read_json(output_root / "dataset" / "index.json")
    echo_dir = output_root / "dataset" / "echoes"
    recon_dir = ensure_dir(output_root / "accelerated_recon_cache")
    per_sample: list[dict] = []
    runtime_repeats: dict[str, dict[str, list[float]]] = {method: {} for method in METHOD_ORDER}
    aggregate: dict[str, dict] = {}

    for method in METHOD_ORDER:
        rows: list[dict] = []
        for item in index:
            sample_id = item["sample_id"]
            echo_path = echo_dir / f"{sample_id}_echo_sparse.npz"
            best_result = None
            run_times: list[float] = []
            for repeat_idx in range(repeats):
                result = reconstruct_cylindrical_reference(output_root / item["scene_path"], echo_path, method)
                run_times.append(float(result["wall_time_sec"]))
                if best_result is None:
                    best_result = result
            assert best_result is not None
            nearest_ref = float(PROTOCOL_V1.nearest_reference_radius(np.array([item["rho_target_m"]]), method)[0]) if method != "BP" else float(item["rho_target_m"])
            np.savez_compressed(
                recon_dir / f"{sample_id}_{method}_accelerated.npz",
                volume=best_result["volume"],
                gt_volume=best_result["gt_volume"],
                x_values=best_result["x_values"],
                y_values=best_result["y_values"],
                z_values=best_result["z_values"],
            )
            write_json(
                recon_dir / f"{sample_id}_{method}_accelerated_meta.json",
                {
                    "sample_id": sample_id,
                    "method": method,
                    "wall_time_sec": best_result["wall_time_sec"],
                    "window_shape": best_result["window_shape"],
                    "reference_count": best_result["reference_count"],
                    "runtime_repeats_sec": run_times,
                    "quality": best_result["quality"],
                },
            )
            row = {
                "sample_id": sample_id,
                "method": method,
                "control_group": item["control_group"],
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
                "wall_time_median_sec": float(np.median(run_times)),
            }
            rows.append(row)
            per_sample.append(row)
            runtime_repeats[method][sample_id] = run_times
        aggregate[method] = {
            "nmse_mean": float(np.mean([row["nmse"] for row in rows])),
            "psnr_mean": float(np.mean([row["psnr"] for row in rows])),
            "ssim_mean": float(np.mean([row["ssim"] for row in rows])),
            "wall_time_mean_sec": float(np.mean([row["wall_time_mean_sec"] for row in rows])),
            "wall_time_std_sec": float(np.mean([row["wall_time_std_sec"] for row in rows])),
            "wall_time_median_sec": float(np.median([row["wall_time_median_sec"] for row in rows])),
            "num_samples": len(rows),
            "reference_count": int(len(PROTOCOL_V1.reference_sets[method])),
        }

    bp_time = aggregate["BP"]["wall_time_mean_sec"]
    for method in METHOD_ORDER:
        aggregate[method]["speedup_vs_bp"] = float(bp_time / aggregate[method]["wall_time_mean_sec"]) if aggregate[method]["wall_time_mean_sec"] > 0 else 0.0

    payload = {"aggregate": aggregate, "per_sample": per_sample}
    write_json(output_root / "baseline_metrics_accelerated.json", payload)
    write_json(output_root / "runtime_repeats.json", runtime_repeats)

    with (output_root / "runtime_table_accelerated.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["method", "reference_count", "wall_time_mean_sec", "wall_time_std_sec", "wall_time_median_sec", "speedup_vs_bp"],
        )
        writer.writeheader()
        for method in METHOD_ORDER:
            writer.writerow(
                {
                    "method": method,
                    "reference_count": aggregate[method]["reference_count"],
                    "wall_time_mean_sec": aggregate[method]["wall_time_mean_sec"],
                    "wall_time_std_sec": aggregate[method]["wall_time_std_sec"],
                    "wall_time_median_sec": aggregate[method]["wall_time_median_sec"],
                    "speedup_vs_bp": aggregate[method]["speedup_vs_bp"],
                }
            )

    with (output_root / "quality_table_accelerated.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["method", "nmse_mean", "psnr_mean", "ssim_mean"])
        writer.writeheader()
        for method in METHOD_ORDER:
            writer.writerow(
                {
                    "method": method,
                    "nmse_mean": aggregate[method]["nmse_mean"],
                    "psnr_mean": aggregate[method]["psnr_mean"],
                    "ssim_mean": aggregate[method]["ssim_mean"],
                }
            )
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Run accelerated point baseline evaluation.")
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    payload = evaluate_accelerated(Path(args.output_root), repeats=args.repeats)
    print(f"Accelerated evaluation rows={len(payload['per_sample'])}")


if __name__ == "__main__":
    main()
