from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from workspace.common.io_utils import ensure_dir, read_json, write_json
from workspace.eval.metrics_3d import nmse, psnr, ssim_global
from workspace.recon.recon_registry import ordered_methods
from workspace.recon.reference_recon import reconstruct_from_scene_path


def _save_visual(output_dir: Path, sample_id: str, method: str, volume: np.ndarray, gt_volume: np.ndarray) -> None:
    pred_mip = volume.max(axis=2)
    gt_mip = gt_volume.max(axis=2)
    fig, axes = plt.subplots(1, 2, figsize=(8, 4))
    axes[0].imshow(gt_mip, cmap="viridis")
    axes[0].set_title("GT MIP")
    axes[1].imshow(pred_mip, cmap="viridis")
    axes[1].set_title(f"{method} MIP")
    for ax in axes:
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(output_dir / f"{sample_id}_{method}.png", dpi=160)
    plt.close(fig)


def evaluate(output_root: Path, split: str, max_samples: int | None = None) -> dict:
    index = read_json(output_root / "dataset" / "index.json")
    sample_visuals = ensure_dir(output_root / "sample_visuals")
    recon_dir = ensure_dir(output_root / "recon_cache")
    selected = [item for item in index if item["split"] == split]
    if max_samples is not None:
        selected = selected[:max_samples]
    per_sample: list[dict] = []
    aggregate: dict[str, dict] = {}

    for method in ordered_methods():
        method_rows: list[dict] = []
        for idx, item in enumerate(selected):
            scene_path = output_root / item["scene_path"]
            result = reconstruct_from_scene_path(scene_path, method.name, recon_dir)
            metrics = {
                "sample_id": item["sample_id"],
                "method": method.name,
                "nmse": nmse(result["volume"], result["gt_volume"]),
                "psnr": psnr(result["volume"], result["gt_volume"]),
                "ssim": ssim_global(result["volume"], result["gt_volume"]),
                "wall_time_sec": result["wall_time_sec"],
                "runtime_proxy_sec": result["runtime_proxy_sec"],
            }
            method_rows.append(metrics)
            per_sample.append(metrics)
            if idx < 2:
                _save_visual(sample_visuals, item["sample_id"], method.name, result["volume"], result["gt_volume"])

        aggregate[method.name] = {
            "split": split,
            "num_samples": len(method_rows),
            "nmse_mean": float(np.mean([row["nmse"] for row in method_rows])),
            "psnr_mean": float(np.mean([row["psnr"] for row in method_rows])),
            "ssim_mean": float(np.mean([row["ssim"] for row in method_rows])),
            "wall_time_mean_sec": float(np.mean([row["wall_time_sec"] for row in method_rows])),
            "runtime_proxy_mean_sec": float(np.mean([row["runtime_proxy_sec"] for row in method_rows])),
        }

    bp_runtime = aggregate["BP"]["runtime_proxy_mean_sec"]
    for method_name, stats in aggregate.items():
        stats["speedup_vs_bp"] = float(bp_runtime / stats["runtime_proxy_mean_sec"]) if stats["runtime_proxy_mean_sec"] > 0 else 0.0

    with (output_root / "runtime_table.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["method", "runtime_proxy_mean_sec", "wall_time_mean_sec", "speedup_vs_bp"],
        )
        writer.writeheader()
        for method_name in ["ref3", "ref5", "ref7", "ref9", "BP"]:
            row = aggregate[method_name]
            writer.writerow(
                {
                    "method": method_name,
                    "runtime_proxy_mean_sec": row["runtime_proxy_mean_sec"],
                    "wall_time_mean_sec": row["wall_time_mean_sec"],
                    "speedup_vs_bp": row["speedup_vs_bp"],
                }
            )

    with (output_root / "quality_table.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["method", "nmse_mean", "psnr_mean", "ssim_mean"])
        writer.writeheader()
        for method_name in ["ref3", "ref5", "ref7", "ref9", "BP"]:
            row = aggregate[method_name]
            writer.writerow(
                {
                    "method": method_name,
                    "nmse_mean": row["nmse_mean"],
                    "psnr_mean": row["psnr_mean"],
                    "ssim_mean": row["ssim_mean"],
                }
            )

    payload = {"split": split, "aggregate": aggregate, "per_sample": per_sample}
    write_json(output_root / "baseline_metrics.json", payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate point-target baselines.")
    parser.add_argument("--output-root", required=True, help="Task artifact root.")
    parser.add_argument("--split", default="test", choices=["train", "val", "test"])
    parser.add_argument("--max-samples", type=int, default=None)
    args = parser.parse_args()
    payload = evaluate(Path(args.output_root), split=args.split, max_samples=args.max_samples)
    print(f"Evaluated {len(payload['per_sample'])} method-sample rows")


if __name__ == "__main__":
    main()
