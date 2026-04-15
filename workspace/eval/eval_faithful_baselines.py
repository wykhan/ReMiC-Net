from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np

from workspace.common.io_utils import ensure_dir, read_json, write_json
from workspace.common.protocol import PROTOCOL_V1
from workspace.recon.faithful_reference_recon import reconstruct_from_paths


METHOD_ORDER = ["ref3", "ref5", "ref7", "ref9", "BP"]


def evaluate_faithful(output_root: Path) -> dict:
    index = read_json(output_root / "dataset" / "index.json")
    echo_dir = output_root / "dataset" / "echoes"
    recon_dir = ensure_dir(output_root / "faithful_recon_cache")
    per_sample: list[dict] = []
    aggregate: dict[str, dict] = {}

    for method in METHOD_ORDER:
        rows: list[dict] = []
        for item in index:
            sample_id = item["sample_id"]
            echo_path = echo_dir / f"{sample_id}_echo_sparse.npz"
            result = reconstruct_from_paths(output_root / item["scene_path"], echo_path, method, recon_dir)
            nearest_ref = float(PROTOCOL_V1.nearest_reference_radius(np.array([item["rho_target_m"]]), method)[0]) if method != "BP" else float(item["rho_target_m"])
            row = {
                "sample_id": sample_id,
                "method": method,
                "control_group": item["control_group"],
                "rho_target_m": item["rho_target_m"],
                "theta_target_rad": item["theta_target_rad"],
                "z_target_m": item["z_target_m"],
                "nearest_reference_m": nearest_ref,
                "radial_mismatch_m": abs(item["rho_target_m"] - nearest_ref),
                "nmse": result["quality"]["nmse"],
                "psnr": result["quality"]["psnr"],
                "ssim": result["quality"]["ssim"],
                "wall_time_sec": result["wall_time_sec"],
            }
            rows.append(row)
            per_sample.append(row)
        aggregate[method] = {
            "nmse_mean": float(np.mean([row["nmse"] for row in rows])),
            "psnr_mean": float(np.mean([row["psnr"] for row in rows])),
            "ssim_mean": float(np.mean([row["ssim"] for row in rows])),
            "wall_time_mean_sec": float(np.mean([row["wall_time_sec"] for row in rows])),
            "num_samples": len(rows),
        }

    bp_time = aggregate["BP"]["wall_time_mean_sec"]
    for method in METHOD_ORDER:
        aggregate[method]["speedup_vs_bp"] = float(bp_time / aggregate[method]["wall_time_mean_sec"]) if aggregate[method]["wall_time_mean_sec"] > 0 else 0.0

    payload = {"aggregate": aggregate, "per_sample": per_sample}
    write_json(output_root / "baseline_metrics_faithful.json", payload)

    with (output_root / "runtime_table_faithful.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["method", "wall_time_mean_sec", "speedup_vs_bp"])
        writer.writeheader()
        for method in METHOD_ORDER:
            writer.writerow(
                {
                    "method": method,
                    "wall_time_mean_sec": aggregate[method]["wall_time_mean_sec"],
                    "speedup_vs_bp": aggregate[method]["speedup_vs_bp"],
                }
            )

    with (output_root / "quality_table_faithful.csv").open("w", encoding="utf-8", newline="") as handle:
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
    parser = argparse.ArgumentParser(description="Run faithful point baseline evaluation.")
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()
    payload = evaluate_faithful(Path(args.output_root))
    print(f"Faithful evaluation rows={len(payload['per_sample'])}")


if __name__ == "__main__":
    main()
