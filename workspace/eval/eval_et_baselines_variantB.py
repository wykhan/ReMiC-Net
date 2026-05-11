from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from scipy import ndimage

from workspace.common.io_utils import ensure_dir, read_json, write_json, write_text
from workspace.recon.cyl_fast_reference_engine import reconstruct_cylindrical_reference


METHOD_ORDER = ["ref3", "ref5", "ref7", "ref9", "BP"]
FAILURE_LABELS = ["F1", "F2", "F3", "F4", "F5", "F6"]
THIN_FAMILIES = {"line", "cross", "L-shape", "double-line", "small_rect_edge"}


def _connected_components(mask: np.ndarray) -> int:
    if not np.any(mask):
        return 0
    structure = np.ones((3, 3, 3), dtype=np.int8)
    _labels, count = ndimage.label(mask.astype(np.int8), structure=structure)
    return int(count)


def _center_of_mass(mask: np.ndarray) -> np.ndarray:
    if not np.any(mask):
        return np.array(mask.shape, dtype=np.float64) * 0.5
    return np.array(ndimage.center_of_mass(mask.astype(np.float64)), dtype=np.float64)


def _failure_tags(volume: np.ndarray, gt: np.ndarray, family: str, nmse_value: float) -> dict[str, Any]:
    recon = volume.astype(np.float32)
    gt = gt.astype(np.float32)
    recon_norm = recon / max(float(recon.max()), 1.0e-8)
    gt_norm = gt / max(float(gt.max()), 1.0e-8)
    gt_support = gt_norm > 0.05
    recon_support = recon_norm > 0.30
    gt_recall = float(np.mean(recon_norm[gt_support] > 0.22)) if np.any(gt_support) else 0.0
    recon_precision = float(np.mean(gt_support[recon_support])) if np.any(recon_support) else 0.0
    support_ratio = float(recon_support.sum() / max(int(gt_support.sum()), 1))
    comp_gt = _connected_components(gt_support)
    comp_recon = _connected_components(recon_support)
    center_shift = float(np.linalg.norm(_center_of_mass(recon_support) - _center_of_mass(gt_support)))
    weak_mask = (gt > 0.0) & (gt <= np.percentile(gt[gt > 0.0], 40)) if np.any(gt > 0.0) else np.zeros_like(gt, dtype=bool)
    weak_recall = float(np.mean(recon_norm[weak_mask] > 0.18)) if np.any(weak_mask) else 1.0

    tags: list[str] = []
    if (support_ratio > 15.0 and recon_precision < 0.08) or (nmse_value > 10.0 and recon_precision < 0.05):
        tags.append("F1")
    if family in THIN_FAMILIES and recon_precision < 0.55 and 0.20 <= gt_recall <= 0.80:
        tags.append("F2")
    if family in THIN_FAMILIES and gt_recall < 0.45:
        tags.append("F3")
    if comp_recon >= max(3, comp_gt + 2):
        tags.append("F4")
    if center_shift > 2.5:
        tags.append("F5")
    if weak_recall < 0.35:
        tags.append("F6")

    return {
        "tags": tags,
        "diagnostics": {
            "gt_recall": gt_recall,
            "recon_precision": recon_precision,
            "support_ratio": support_ratio,
            "components_gt": comp_gt,
            "components_recon": comp_recon,
            "center_shift_vox": center_shift,
            "weak_recall": weak_recall,
        },
    }


def _aggregate_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "nmse_mean": float(np.mean([row["nmse"] for row in rows])),
        "psnr_mean": float(np.mean([row["psnr"] for row in rows])),
        "ssim_mean": float(np.mean([row["ssim"] for row in rows])),
        "wall_time_mean_sec": float(np.mean([row["wall_time_sec"] for row in rows])),
        "estimated_peak_memory_mb": float(np.mean([row["estimated_peak_memory_mb"] for row in rows])),
        "num_samples": len(rows),
    }


def evaluate_et_variantB(output_root: Path) -> dict[str, Any]:
    index = read_json(output_root / "dataset" / "index.json")
    echo_dir = output_root / "dataset" / "echoes"
    recon_dir = ensure_dir(output_root / "et_recon_cache")
    per_sample: list[dict[str, Any]] = []
    aggregate: dict[str, dict[str, Any]] = {}
    by_family: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    failure_cases: list[dict[str, Any]] = []
    method_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    family_method_rows: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    failure_counts_by_method = {method: {label: 0 for label in FAILURE_LABELS} for method in METHOD_ORDER}
    failure_counts_by_family_method = {
        family: {method: {label: 0 for label in FAILURE_LABELS} for method in METHOD_ORDER}
        for family in sorted({item["family"] for item in index})
    }

    for method in METHOD_ORDER:
        for item in index:
            sample_id = item["sample_id"]
            result = reconstruct_cylindrical_reference(
                scene_path=output_root / item["scene_path"],
                echo_path=echo_dir / f"{sample_id}_echo_sparse.npz",
                method=method,
            )
            np.savez_compressed(
                recon_dir / f"{sample_id}_{method}_et.npz",
                volume=result["volume"],
                gt_volume=result["gt_volume"],
                x_values=result["x_values"],
                y_values=result["y_values"],
                z_values=result["z_values"],
            )
            failure = _failure_tags(result["volume"], result["gt_volume"], family=item["family"], nmse_value=result["quality"]["nmse"])
            case = {
                "sample_id": sample_id,
                "family": item["family"],
                "split": item["split"],
                "method": method,
                "tags": failure["tags"],
                "diagnostics": failure["diagnostics"],
            }
            failure_cases.append(case)
            for label in failure["tags"]:
                failure_counts_by_method[method][label] += 1
                failure_counts_by_family_method[item["family"]][method][label] += 1
            row = dict(item)
            row.update(
                {
                    "method": method,
                    "nmse": result["quality"]["nmse"],
                    "psnr": result["quality"]["psnr"],
                    "ssim": result["quality"]["ssim"],
                    "wall_time_sec": result["wall_time_sec"],
                    "estimated_peak_memory_mb": result["estimated_peak_memory_mb"],
                    "failure_tags": failure["tags"],
                }
            )
            per_sample.append(row)
            method_rows[method].append(row)
            family_method_rows[(item["family"], method)].append(row)
            write_json(
                recon_dir / f"{sample_id}_{method}_et_meta.json",
                {
                    "sample_id": sample_id,
                    "family": item["family"],
                    "method": method,
                    "tensor_mode": result["tensor_mode"],
                    "geom_mode": result["geom_mode"],
                    "tensor_shape": result["tensor_shape"],
                    "active_coverage_ratio": result["active_coverage_ratio"],
                    "estimated_peak_memory_mb": result["estimated_peak_memory_mb"],
                    "quality": result["quality"],
                    "wall_time_sec": result["wall_time_sec"],
                    "failure_tags": failure["tags"],
                    "failure_diagnostics": failure["diagnostics"],
                },
            )

    for method in METHOD_ORDER:
        aggregate[method] = _aggregate_rows(method_rows[method])

    bp_time = aggregate["BP"]["wall_time_mean_sec"]
    for method in METHOD_ORDER:
        aggregate[method]["speedup_vs_bp"] = float(bp_time / aggregate[method]["wall_time_mean_sec"]) if aggregate[method]["wall_time_mean_sec"] > 0 else 0.0

    families = sorted({item["family"] for item in index})
    for family in families:
        for method in METHOD_ORDER:
            by_family[family][method] = _aggregate_rows(family_method_rows[(family, method)])
        bp_family_time = by_family[family]["BP"]["wall_time_mean_sec"]
        for method in METHOD_ORDER:
            by_family[family][method]["speedup_vs_bp"] = float(
                bp_family_time / by_family[family][method]["wall_time_mean_sec"]
            ) if by_family[family][method]["wall_time_mean_sec"] > 0 else 0.0

    payload = {
        "aggregate": aggregate,
        "by_family": by_family,
        "per_sample": per_sample,
        "failure_summary": {
            "labels": FAILURE_LABELS,
            "counts_by_method": failure_counts_by_method,
            "counts_by_family_method": failure_counts_by_family_method,
        },
    }
    write_json(output_root / "baseline_metrics_et.json", payload)
    write_json(output_root / "failure_case_index.json", failure_cases)

    with (output_root / "runtime_table_et.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["method", "wall_time_mean_sec", "estimated_peak_memory_mb", "speedup_vs_bp"])
        writer.writeheader()
        for method in METHOD_ORDER:
            writer.writerow(
                {
                    "method": method,
                    "wall_time_mean_sec": aggregate[method]["wall_time_mean_sec"],
                    "estimated_peak_memory_mb": aggregate[method]["estimated_peak_memory_mb"],
                    "speedup_vs_bp": aggregate[method]["speedup_vs_bp"],
                }
            )

    with (output_root / "quality_table_et.csv").open("w", encoding="utf-8", newline="") as handle:
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

    lines = [
        "# failure_taxonomy",
        "",
        "This file summarizes ET failure modes using review-style heuristic tagging on the reconstructed amplitude volumes.",
        "",
        "## Labels",
        "",
        "- `F1`: overall blur / global smearing",
        "- `F2`: edge break / contour fracture",
        "- `F3`: thin-structure disappearance",
        "- `F4`: support fragmentation",
        "- `F5`: local geometric shift",
        "- `F6`: weak-return region suppression",
        "",
        "## Counts By Method",
        "",
    ]
    for method in METHOD_ORDER:
        counts = failure_counts_by_method[method]
        lines.append(
            f"- `{method}`: " + ", ".join([f"{label}={counts[label]}" for label in FAILURE_LABELS])
        )
    lines.extend(["", "## Counts By Family And Method", ""])
    for family in families:
        lines.append(f"### {family}")
        lines.append("")
        for method in METHOD_ORDER:
            counts = failure_counts_by_family_method[family][method]
            lines.append(f"- `{method}`: " + ", ".join([f"{label}={counts[label]}" for label in FAILURE_LABELS]))
        lines.append("")
    write_text(output_root / "failure_taxonomy.md", "\n".join(lines))
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Variant B ET baselines and build ET failure taxonomy.")
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()
    payload = evaluate_et_variantB(Path(args.output_root))
    print(f"ET Variant B evaluation rows={len(payload['per_sample'])}")


if __name__ == "__main__":
    main()
