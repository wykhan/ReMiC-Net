from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import torch

from workspace.common.io_utils import ensure_dir, read_json, write_json, write_text
from workspace.models.unet3d_small import UNet3DSmall


SOURCE_TASK006_ROOT = Path(
    "/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006_two_stage_learning/20260416_120500"
)
FORMAL_TARGET = {
    "shape_family": {"train": 30000, "val": 6000, "test": 6000},
    "random_et": {"train": 5000, "val": 1000, "test": 1000},
}
HARD_FAMILIES = ["point_cluster", "line", "L-shape"]


def _ensure_link(link_path: Path, source_path: Path) -> None:
    ensure_dir(link_path.parent)
    if link_path.exists() or link_path.is_symlink():
        return
    os.symlink(source_path, link_path, target_is_directory=True)


def _load_source_manifests(source_root: Path) -> tuple[dict, dict]:
    shape = read_json(source_root / "dataset_manifest_shape_family_full.json")
    random_et = read_json(source_root / "dataset_manifest_random_et.json")
    return shape, random_et


def _copy_or_link_inputs(output_root: Path, source_root: Path) -> None:
    _ensure_link(output_root / "datasets" / "shape_family_formal", source_root / "datasets" / "shape_family_full")
    _ensure_link(output_root / "datasets" / "random_et_formal", source_root / "datasets" / "random_et")
    _ensure_link(output_root / "learning_cache", source_root / "learning_cache")


def _scene_signature(scene: dict[str, Any]) -> str:
    pts = sorted(
        (
            round(point["x_m"], 6),
            round(point["y_m"], 6),
            round(point["z_m"], 6),
            round(point["amplitude"], 6),
        )
        for point in scene["points"]
    )
    payload = {
        "family": scene.get("family"),
        "shape_params": scene.get("shape_params"),
        "placement": scene.get("placement"),
        "points": pts,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def _scene_feature(scene: dict[str, Any]) -> np.ndarray:
    points = np.array([[p["x_m"], p["y_m"], p["z_m"], p["amplitude"]] for p in scene["points"]], dtype=np.float64)
    xyz = points[:, :3]
    amp = points[:, 3]
    center = xyz.mean(axis=0)
    spread = xyz.std(axis=0)
    return np.array(
        [
            len(points),
            center[0],
            center[1],
            center[2],
            spread[0],
            spread[1],
            spread[2],
            float(np.mean(amp)),
            float(np.std(amp)),
        ],
        dtype=np.float64,
    )


def build_formal_scale_package(output_root: Path, source_root: Path) -> dict[str, Any]:
    _copy_or_link_inputs(output_root, source_root)
    shape_manifest, random_manifest = _load_source_manifests(source_root)
    shutil.copyfile(source_root / "dataset_protocol_snapshot.md", output_root / "dataset_protocol_snapshot.md")
    write_json(output_root / "dataset_manifest_shape_family_formal.json", shape_manifest)
    write_json(output_root / "dataset_manifest_random_et_formal.json", random_manifest)
    write_text(
        output_root / "data_origin_statement.md",
        "\n".join(
            [
                "# data_origin_statement",
                "",
                "- Data type: true 3D cylindrical simulation data",
                "- Forward simulator entry: `workspace.sim.forward_cylindrical_point`",
                "- Protocol version: protocol v1 under `CONTEXT/simulation_protocol.md`",
                "- Reconstruction entry: `workspace.recon.cyl_fast_reference_engine.reconstruct_cylindrical_reference` using frozen Variant B `ref3`",
                "- Statement: data are not 2D proxy patterns and not manually fabricated pseudo-reference images",
            ]
        ),
    )
    counts = {
        "shape_family": shape_manifest["counts_by_split"],
        "random_et": random_manifest["counts_by_split"],
    }
    passed = (
        counts["shape_family"].get("train", 0) >= FORMAL_TARGET["shape_family"]["train"]
        and counts["shape_family"].get("val", 0) >= FORMAL_TARGET["shape_family"]["val"]
        and counts["shape_family"].get("test", 0) >= FORMAL_TARGET["shape_family"]["test"]
        and counts["random_et"].get("train", 0) >= FORMAL_TARGET["random_et"]["train"]
        and counts["random_et"].get("val", 0) >= FORMAL_TARGET["random_et"]["val"]
        and counts["random_et"].get("test", 0) >= FORMAL_TARGET["random_et"]["test"]
    )
    summary = {
        "formal_scale_completed": passed,
        "counts": counts,
        "targets": FORMAL_TARGET,
        "shape_total_samples": shape_manifest["total_samples"],
        "random_total_samples": random_manifest["total_samples"],
    }
    write_json(output_root / "formal_scale_completion.json", summary)
    return summary


def run_split_integrity(output_root: Path) -> dict[str, Any]:
    dataset_root = output_root / "datasets" / "shape_family_formal"
    index = read_json(dataset_root / "dataset" / "index.json")
    rows = []
    split_features: dict[str, list[tuple[str, str, np.ndarray]]] = defaultdict(list)
    hash_counter = Counter()
    param_counter = Counter()
    for item in index:
        scene = read_json(dataset_root / item["scene_path"])
        sig = _scene_signature(scene)
        feature = _scene_feature(scene)
        param_sig = hashlib.sha256(json.dumps(scene.get("shape_params", {}), sort_keys=True).encode("utf-8")).hexdigest()
        hash_counter[sig] += 1
        param_counter[(scene["family"], param_sig)] += 1
        split_features[item["split"]].append((item["sample_id"], scene["family"], feature))
        rows.append(
            {
                "sample_id": item["sample_id"],
                "split": item["split"],
                "family": scene["family"],
                "scene_hash": sig,
                "param_hash": param_sig,
            }
        )

    duplicate_hashes = {key: count for key, count in hash_counter.items() if count > 1}
    duplicate_params = {f"{fam}:{sig}": count for (fam, sig), count in param_counter.items() if count > 1}

    train = split_features["train"]
    test = split_features["test"]
    nn_rows = []
    dists = []
    for sample_id, family, feature in test:
        best_id = None
        best_family = None
        best_dist = None
        for train_id, train_family, train_feature in train:
            dist = float(np.linalg.norm(feature - train_feature))
            if best_dist is None or dist < best_dist:
                best_id = train_id
                best_family = train_family
                best_dist = dist
        nn_rows.append(
            {
                "test_sample_id": sample_id,
                "test_family": family,
                "nearest_train_sample_id": best_id,
                "nearest_train_family": best_family,
                "distance": best_dist,
            }
        )
        dists.append(best_dist if best_dist is not None else 0.0)

    with (output_root / "nearest_neighbor_overlap.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["test_sample_id", "test_family", "nearest_train_sample_id", "nearest_train_family", "distance"],
        )
        writer.writeheader()
        for row in nn_rows:
            writer.writerow(row)

    write_json(
        output_root / "duplicate_check.json",
        {
            "duplicate_scene_hash_count": len(duplicate_hashes),
            "duplicate_scene_hashes": duplicate_hashes,
            "duplicate_param_signature_count": len(duplicate_params),
            "duplicate_param_signatures": duplicate_params,
        },
    )

    report_lines = [
        "# split_integrity_report",
        "",
        f"- total shape-family samples audited: {len(index)}",
        f"- duplicate scene-hash count: {len(duplicate_hashes)}",
        f"- duplicate family-parameter-signature count: {len(duplicate_params)}",
        f"- nearest train-test distance mean: {float(np.mean(dists)):.6f}",
        f"- nearest train-test distance min: {float(np.min(dists)):.6f}",
        "",
        "Current judgment: no exact scene-level leakage was detected if duplicate scene-hash count is zero.",
        "Near-neighbor distances remain a soft warning signal rather than proof of leakage.",
    ]
    write_text(output_root / "split_integrity_report.md", "\n".join(report_lines) + "\n")

    curves_dir = ensure_dir(output_root / "viz" / "progress" / "curves")
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(dists, bins=30, color="#6b8e23")
    ax.set_title("Train-test nearest neighbor distance")
    ax.set_xlabel("distance")
    ax.set_ylabel("count")
    fig.tight_layout()
    fig.savefig(curves_dir / "train_test_nearest_neighbor_distance.png", dpi=170)
    plt.close(fig)

    train_rows = [read_json(dataset_root / item["scene_path"]) for item in index if item["split"] == "train"]
    test_rows = [read_json(dataset_root / item["scene_path"]) for item in index if item["split"] == "test"]
    train_rho = [scene["placement"]["center_rho_m"] for scene in train_rows]
    test_rho = [scene["placement"]["center_rho_m"] for scene in test_rows]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(train_rho, bins=30, alpha=0.6, label="train")
    ax.hist(test_rho, bins=30, alpha=0.6, label="test")
    ax.set_title("Parameter coverage train vs test")
    ax.set_xlabel("center rho (m)")
    ax.set_ylabel("count")
    ax.legend()
    fig.tight_layout()
    fig.savefig(curves_dir / "parameter_coverage_train_vs_test.png", dpi=170)
    plt.close(fig)

    return {
        "duplicate_scene_hash_count": len(duplicate_hashes),
        "duplicate_param_signature_count": len(duplicate_params),
        "nearest_neighbor_distance_mean": float(np.mean(dists)),
        "nearest_neighbor_distance_min": float(np.min(dists)),
    }


def run_model_audit(output_root: Path) -> dict[str, Any]:
    model = UNet3DSmall(base_channels=8)
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    input_shape = [1, 1, 24, 24, 24]
    sample = torch.zeros(input_shape, dtype=torch.float32)
    with torch.no_grad():
        output = model(sample)
    audit = {
        "model_name": "UNet3DSmall",
        "total_params": int(total_params),
        "trainable_params": int(trainable_params),
        "input_tensor_shape": input_shape,
        "output_tensor_shape": list(output.shape),
        "device_used_for_audit": "cpu",
        "estimated_train_memory_mb": None,
        "estimated_inference_memory_mb": None,
        "estimated_flops": None,
    }
    write_json(output_root / "model_audit.json", audit)
    summary = [
        "Model: UNet3DSmall",
        f"Total params: {total_params}",
        f"Trainable params: {trainable_params}",
        f"Input shape: {input_shape}",
        f"Output shape: {list(output.shape)}",
        "Audit device: cpu",
        "Estimated train memory: not measured in this CPU-only audit",
        "Estimated inference memory: not measured in this CPU-only audit",
        "Estimated FLOPs: not measured",
    ]
    write_text(output_root / "model_summary.txt", "\n".join(summary) + "\n")
    return audit


def write_fail_fast_placeholders(output_root: Path) -> None:
    write_text(
        output_root / "training_config_frozen_mainline_formal.yaml",
        "status: not_run\nreason: formal-scale dataset completion failed; task_real_006c forbids training before formal-scale completion\n",
    )
    write_json(
        output_root / "metrics_frozen_mainline_formal.json",
        {
            "status": "not_run",
            "reason": "formal-scale dataset completion failed; training forbidden by task_real_006c hard constraint 1",
        },
    )
    for filename in [
        "mainline_vs_baselines_formal.csv",
        "family_metrics_mainline_vs_baselines_formal.csv",
        "failure_mode_mainline_vs_baselines_formal.csv",
        "ood_unseen_param_metrics.csv",
        "ood_leave_one_family_out_metrics.csv",
        "ood_random_et_metrics.csv",
    ]:
        with (output_root / filename).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["status", "reason"])
            writer.writerow(["not_run", "formal-scale dataset completion failed; downstream training/evaluation forbidden by task_real_006c"])

    curves_dir = ensure_dir(output_root / "viz" / "progress" / "curves")
    paper_curves = ensure_dir(output_root / "viz" / "paper_candidates" / "curves")
    manifest_dir = ensure_dir(output_root / "viz" / "manifest")
    for target in [curves_dir, paper_curves]:
        for filename in [
            "dataset_scale_completion.png",
            "train_val_test_loss_frozen_mainline.png",
            "train_val_test_gap_by_family.png",
            "ood_unseen_param_metrics.png",
            "ood_leave_one_family_out_metrics.png",
            "ood_random_et_metrics.png",
            "runtime_quality_frontier_with_learning_formal.png",
            "family_metrics_mainline_vs_baselines_formal.png",
            "failure_mode_mainline_vs_baselines_formal.png",
        ]:
            fig, ax = plt.subplots(figsize=(6, 3.5))
            ax.text(0.5, 0.5, "not run\nformal-scale target unmet", ha="center", va="center")
            ax.axis("off")
            fig.tight_layout()
            fig.savefig(target / filename, dpi=170)
            plt.close(fig)
    write_text(manifest_dir / "not_run_due_formal_scale.txt", "Downstream formal validation steps were not run because formal-scale completion failed.\n")


def render_dataset_scale_completion(output_root: Path, completion: dict[str, Any]) -> None:
    curves_dir = ensure_dir(output_root / "viz" / "progress" / "curves")
    labels = ["shape_train", "shape_val", "shape_test", "random_train", "random_val", "random_test"]
    current = [
        completion["counts"]["shape_family"]["train"],
        completion["counts"]["shape_family"]["val"],
        completion["counts"]["shape_family"]["test"],
        completion["counts"]["random_et"]["train"],
        completion["counts"]["random_et"]["val"],
        completion["counts"]["random_et"]["test"],
    ]
    target = [
        FORMAL_TARGET["shape_family"]["train"],
        FORMAL_TARGET["shape_family"]["val"],
        FORMAL_TARGET["shape_family"]["test"],
        FORMAL_TARGET["random_et"]["train"],
        FORMAL_TARGET["random_et"]["val"],
        FORMAL_TARGET["random_et"]["test"],
    ]
    x = np.arange(len(labels))
    width = 0.38
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.bar(x - width / 2, current, width=width, label="current")
    ax.bar(x + width / 2, target, width=width, label="target")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=20)
    ax.set_title("Dataset scale completion")
    ax.legend()
    fig.tight_layout()
    fig.savefig(curves_dir / "dataset_scale_completion.png", dpi=170)
    plt.close(fig)


def generate_report(output_root: Path, completion: dict[str, Any], split_summary: dict[str, Any], audit: dict[str, Any]) -> None:
    ready = "no"
    report = f"""# task_real_006c_report

## 1. Task Goal

Validate whether the current Frozen Mainline result is credible enough to justify entering the physics-consistency stage.

## 2. Formal-Scale Dataset Completion Statement

- shape-family current counts: `{completion['counts']['shape_family']}`
- shape-family target counts: `{FORMAL_TARGET['shape_family']}`
- random ET current counts: `{completion['counts']['random_et']}`
- random ET target counts: `{FORMAL_TARGET['random_et']}`
- formal-scale dataset completed? `{'yes' if completion['formal_scale_completed'] else 'no'}`

This task fails at the formal-scale gate because the required `5000/1000/1000` per-family and `5000/1000/1000` random-ET targets were not reached.

## 3. Protocol / Context Files Used

- `CONTEXT/real_cylindrical_master_document_with_physics_consistency.md`
- `CONTEXT/simulation_protocol.md`
- `CONTEXT/reference_surface_strategy.md`
- `CONTEXT/dataset_protocol.md`
- `CONTEXT/et_dataset_protocol.md`
- `CONTEXT/project_brief.md`
- `CONTEXT/experiment_matrix.md`
- `PROMPTS/system_rules.md`
- `PROMPTS/review_checklist.md`
- `exp/task_real_006b_fullscale_mainline/20260417_000500/task_real_006b_report.md`

## 4. Boundary Statement

No new training or formal-scale comparison was run because task_real_006c explicitly forbids training before formal-scale dataset completion.

## 5. Frozen Mainline Definition

- Front-end: `Variant B`
- Physics backbone: `ref3`
- Second stage: `3D U-Net`
- Default training data: `shape-family main training`

## 6. Dataset Summary

- current shape-family total samples: `{completion['shape_total_samples']}`
- current random ET total samples: `{completion['random_total_samples']}`
- current grand total samples: `{completion['shape_total_samples'] + completion['random_total_samples']}`
- required grand total samples: `{sum(FORMAL_TARGET['shape_family'].values()) + sum(FORMAL_TARGET['random_et'].values())}`

## 7. Split Integrity / Leakage Check

- duplicate scene-hash count: `{split_summary['duplicate_scene_hash_count']}`
- duplicate parameter-signature count: `{split_summary['duplicate_param_signature_count']}`
- nearest train-test distance mean: `{split_summary['nearest_neighbor_distance_mean']:.6f}`
- nearest train-test distance min: `{split_summary['nearest_neighbor_distance_min']:.6f}`

These checks were completed on the currently available shape-family dataset, but they do not satisfy the formal-scale requirement by themselves.

## 8. Model Audit Summary

- total params: `{audit['total_params']}`
- trainable params: `{audit['trainable_params']}`
- input shape: `{audit['input_tensor_shape']}`
- output shape: `{audit['output_tensor_shape']}`
- memory / FLOPs audit: not fully measured in this CPU-side audit

## 9. Formal-Scale Mainline vs Baselines

Not run.
Reason: formal-scale dataset completion failed, and task_real_006c forbids training/comparison before that gate is passed.

## 10. OOD / Generalization Results

Not run.
Reason: formal-scale dataset completion failed, and task_real_006c forbids downstream validation before that gate is passed.

## 11. Visual Outputs

- `viz/progress/curves/dataset_scale_completion.png`
- `viz/progress/curves/train_test_nearest_neighbor_distance.png`
- `viz/progress/curves/parameter_coverage_train_vs_test.png`
- placeholder not-run figures for the remaining formal validation outputs

## 12. Remaining Issues

- The primary blocker is formal-scale dataset completion.
- Only about `20 GB` remained on the current filesystem at audit time.
- Extrapolating from the current dataset footprint, full formal-scale data generation would require far more storage and compute than are currently available in this workspace.

## 13. Ready for Physics-Consistency Stage?

- formal-scale data truly completed? `no`
- train/test leakage found in the currently available shape-family set? `{'yes' if split_summary['duplicate_scene_hash_count'] > 0 else 'no exact-duplicate evidence'}`
- current 3D U-Net parameter count: `{audit['total_params']}`
- Frozen Mainline OOD superiority verified on formal-scale data? `no`
- formal-scale BP-tier positioning verified? `no`
- `Ready for Physics-Consistency Stage?` = `{ready}`

## 14. Suggested Next Task

Do not start `task_real_007` yet.
First resolve the formal-scale data-generation blocker by provisioning sufficient storage / compute and completing the required ET dataset scale.

## Key file paths for ChatGPT controller

- Report: `{output_root / 'task_real_006c_report.md'}`
- Manifests: `{output_root / 'dataset_manifest_shape_family_formal.json'}` and `{output_root / 'dataset_manifest_random_et_formal.json'}`
- Split integrity: `{output_root / 'split_integrity_report.md'}`, `{output_root / 'duplicate_check.json'}`, `{output_root / 'nearest_neighbor_overlap.csv'}`
- Model audit: `{output_root / 'model_audit.json'}` and `{output_root / 'model_summary.txt'}`
- Metrics: `{output_root / 'metrics_frozen_mainline_formal.json'}`
- OOD: `{output_root / 'ood_unseen_param_metrics.csv'}`, `{output_root / 'ood_leave_one_family_out_metrics.csv'}`, `{output_root / 'ood_random_et_metrics.csv'}`
- Curves: `{output_root / 'viz/progress/curves'}`
- Representative visuals: `{output_root / 'viz/paper_candidates'}` and `{output_root / 'viz/progress'}`
- Logs: `{output_root / 'logs'}`
"""
    write_text(output_root / "task_real_006c_report.md", report)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run task_real_006c formal-scale credibility validation.")
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--source-root", default=str(SOURCE_TASK006_ROOT))
    args = parser.parse_args()
    output_root = Path(args.output_root)
    source_root = Path(args.source_root)
    completion = build_formal_scale_package(output_root, source_root)
    render_dataset_scale_completion(output_root, completion)
    split_summary = run_split_integrity(output_root)
    audit = run_model_audit(output_root)
    write_fail_fast_placeholders(output_root)
    generate_report(output_root, completion, split_summary, audit)
    print(f"task_real_006c formal validation completed formal_scale_completed={completion['formal_scale_completed']}")


if __name__ == "__main__":
    main()
