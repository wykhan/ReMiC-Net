from __future__ import annotations

import argparse
import csv
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from workspace.common.io_utils import ensure_dir, read_json, write_json
from workspace.eval.eval_et_baselines_variantB import _failure_tags
from workspace.eval.metrics_3d import nmse, psnr, ssim_global
from workspace.recon.cyl_fast_reference_engine import reconstruct_cylindrical_reference
from workspace.train.train_two_stage_et import TARGET_SHAPE, _fit_to_shape, _normalize_pair


METHODS = ["ref3", "ref5", "ref7", "ref9", "BP", "ref3+learning"]
HARD_FAMILIES = {"point_cluster", "line", "L-shape"}


def _evaluate_baselines(output_root: Path, handoff: dict) -> tuple[list[dict], dict[str, list[dict]]]:
    test_rows = [row for row in handoff["samples"] if row["split"] == "test"]
    cache_dir = ensure_dir(output_root / "comparison_cache" / "baselines")
    sample_records: list[dict[str, Any]] = []
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in test_rows:
        gt_npz = np.load(output_root / item["gt_path"])
        gt = _fit_to_shape(gt_npz["volume"], TARGET_SHAPE)
        scene_path = output_root / item["scene_path"]
        echo_path = output_root / item["echo_path"]
        for method in ["ref3", "ref5", "ref7", "ref9", "BP"]:
            started = time.perf_counter()
            result = reconstruct_cylindrical_reference(scene_path, echo_path, method)
            measured = time.perf_counter() - started
            volume = _fit_to_shape(result["volume"], TARGET_SHAPE)
            volume, gt_norm = _normalize_pair(volume, gt)
            failure = _failure_tags(volume, gt_norm, item["family"], nmse(volume, gt_norm))
            payload = {
                "sample_id": item["sample_id"],
                "family": item["family"],
                "method": method,
                "nmse": nmse(volume, gt_norm),
                "psnr": psnr(volume, gt_norm),
                "ssim": ssim_global(volume, gt_norm),
                "wall_time_sec": measured,
                "failure_tags": failure["tags"],
            }
            sample_records.append(payload)
            grouped[method].append(payload)
            np.savez_compressed(cache_dir / f"{item['sample_id']}_{method}.npz", volume=volume, gt=gt_norm)
    return sample_records, grouped


def _evaluate_learned(output_root: Path, handoff: dict, frozen_metrics: dict, baseline_records: list[dict[str, Any]]) -> list[dict]:
    rows = [row for row in handoff["samples"] if row["split"] == "test"]
    ref3_runtime_by_sample = {row["sample_id"]: row["wall_time_sec"] for row in baseline_records if row["method"] == "ref3"}
    records = []
    pred_dir = output_root / "predictions" / "frozen_mainline"
    for row in rows:
        pred = np.load(pred_dir / f"{row['sample_id']}_M2_pred.npz")
        gt = pred["gt"]
        learned = pred["pred"]
        failure = _failure_tags(learned, gt, row["family"], nmse(learned, gt))
        records.append(
            {
                "sample_id": row["sample_id"],
                "family": row["family"],
                "method": "ref3+learning",
                "nmse": nmse(learned, gt),
                "psnr": psnr(learned, gt),
                "ssim": ssim_global(learned, gt),
                "wall_time_sec": ref3_runtime_by_sample[row["sample_id"]] + frozen_metrics["overall"]["avg_inference_time_sec"],
                "failure_tags": failure["tags"],
            }
        )
    return records


def _aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "nmse_mean": float(np.mean([row["nmse"] for row in rows])),
        "psnr_mean": float(np.mean([row["psnr"] for row in rows])),
        "ssim_mean": float(np.mean([row["ssim"] for row in rows])),
        "wall_time_mean_sec": float(np.mean([row["wall_time_sec"] for row in rows])),
        "num_samples": len(rows),
    }


def compare(output_root: Path) -> dict:
    handoff = read_json(output_root / "learning_handoff_manifest_frozen_mainline.json")
    frozen_metrics = read_json(output_root / "metrics_frozen_mainline.json")
    baseline_records, baseline_grouped = _evaluate_baselines(output_root, handoff)
    learned_records = _evaluate_learned(output_root, handoff, frozen_metrics, baseline_records)
    all_records = baseline_records + learned_records
    by_method = defaultdict(list)
    for row in all_records:
        by_method[row["method"]].append(row)
    overall = {method: _aggregate(rows) for method, rows in by_method.items()}
    bp_time = overall["BP"]["wall_time_mean_sec"]
    for method in METHODS:
        overall[method]["speedup_vs_bp"] = bp_time / overall[method]["wall_time_mean_sec"] if overall[method]["wall_time_mean_sec"] > 0 else 0.0

    family_table = []
    by_family_method = defaultdict(list)
    for row in all_records:
        by_family_method[(row["family"], row["method"])].append(row)
    family_metrics = {}
    for family in sorted({row["family"] for row in all_records}):
        family_metrics[family] = {}
        for method in METHODS:
            rows = by_family_method[(family, method)]
            if not rows:
                continue
            stats = _aggregate(rows)
            stats["speedup_vs_bp"] = _aggregate(by_family_method[(family, "BP")])["wall_time_mean_sec"] / stats["wall_time_mean_sec"] if stats["wall_time_mean_sec"] > 0 else 0.0
            family_metrics[family][method] = stats
            family_table.append({"family": family, "method": method, **stats})

    failure_rows = []
    hardest = {}
    for method in METHODS:
        counts = {label: 0 for label in ["F2", "F3", "F4"]}
        for row in by_method[method]:
            for label in counts:
                if label in row["failure_tags"]:
                    counts[label] += 1
        for label, count in counts.items():
            failure_rows.append({"method": method, "failure_label": label, "count": count})
    for family in HARD_FAMILIES:
        hardest[family] = {}
        for method in METHODS:
            rows = by_family_method[(family, method)]
            if rows:
                hardest[family][method] = _aggregate(rows)

    payload = {"overall": overall, "family_metrics": family_metrics, "hardest_family_summary": hardest, "per_sample": all_records}
    write_json(output_root / "mainline_vs_baselines_metrics.json", payload)
    write_json(output_root / "hardest_family_summary.json", hardest)

    with (output_root / "mainline_vs_baselines_table.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["method", "nmse_mean", "psnr_mean", "ssim_mean", "wall_time_mean_sec", "speedup_vs_bp", "num_samples"])
        writer.writeheader()
        for method in METHODS:
            writer.writerow({"method": method, **overall[method]})

    with (output_root / "family_metrics_mainline_vs_baselines.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["family", "method", "nmse_mean", "psnr_mean", "ssim_mean", "wall_time_mean_sec", "speedup_vs_bp", "num_samples"])
        writer.writeheader()
        for row in family_table:
            writer.writerow(row)

    with (output_root / "failure_mode_mainline_vs_baselines.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["method", "failure_label", "count"])
        writer.writeheader()
        for row in failure_rows:
            writer.writerow(row)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare frozen mainline against traditional baselines.")
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()
    payload = compare(Path(args.output_root))
    print(f"Compared frozen mainline against baselines rows={len(payload['per_sample'])}")


if __name__ == "__main__":
    main()
