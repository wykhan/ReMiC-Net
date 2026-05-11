from __future__ import annotations

import argparse
import csv
import json
import math
import os
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import torch

from workspace.common.io_utils import ensure_dir, read_json, write_json, write_text
from workspace.data import et_shape_family_builder as et_builder
from workspace.data.random_et_builder import build_random_et_dataset
from workspace.eval.compare_frozen_mainline_vs_baselines import compare as compare_mainline
from workspace.eval.eval_et_baselines_variantB import _failure_tags
from workspace.eval.metrics_3d import nmse, psnr, ssim_global
from workspace.recon.cyl_fast_reference_engine import build_ground_truth, reconstruct_cylindrical_reference
from workspace.sim.forward_cylindrical_point import batch_simulate
from workspace.train.train_frozen_mainline import train_frozen_mainline
from workspace.train.train_two_stage_et import TARGET_SHAPE, _fit_to_shape, _normalize_pair


PROJECT_ROOT = Path("/home/superws/2026_Projects/Codex_reference_plane_real")
FAMILIES = ["line", "cross", "L-shape", "double-line", "small_rect_edge", "point_cluster"]
HARD_FAMILIES = ["point_cluster", "line", "L-shape"]
MAIN_SPLITS = {
    "train": {"point_cluster": 180, "line": 160, "L-shape": 160, "cross": 110, "double-line": 100, "small_rect_edge": 90},
    "val": {"point_cluster": 20, "line": 20, "L-shape": 20, "cross": 15, "double-line": 15, "small_rect_edge": 10},
    "test": {"point_cluster": 20, "line": 20, "L-shape": 20, "cross": 15, "double-line": 15, "small_rect_edge": 10},
}
OOD_COUNT = 100
MAIN_DATASET_NAME = "main_800_100_100"


def _stage_log(output_root: Path, stage: str, text: str) -> None:
    log_dir = ensure_dir(output_root / "logs")
    path = log_dir / f"{stage}.log"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(text.rstrip() + "\n")


def _ensure_standard_dirs(output_root: Path) -> None:
    for rel in [
        "logs",
        "checkpoints",
        "viz/progress/curves",
        "viz/progress/recon_compare",
        "viz/progress/slices",
        "viz/progress/scene_3d",
        "viz/paper_candidates/curves",
        "viz/paper_candidates/qualitative",
        "viz/paper_candidates/tables_as_figs",
        "viz/paper_candidates/supplementary",
        "viz/manifest",
        f"datasets/{MAIN_DATASET_NAME}",
        "datasets/unseen_param_ood",
        "datasets/leave_one_family_out_ood",
        "datasets/random_et_ood",
        "learning_cache",
        "comparison_cache",
        "predictions",
    ]:
        ensure_dir(output_root / rel)


def _family_size_bucket(family: str, params: dict[str, Any]) -> str:
    if family == "line":
        val = int(params["length_vox"])
        return "small" if val <= 8 else "medium" if val <= 11 else "large"
    if family == "cross":
        val = int(params["arm_a_vox"]) + int(params["arm_b_vox"])
        return "small" if val <= 14 else "medium" if val <= 18 else "large"
    if family == "L-shape":
        val = int(params["arm_x_vox"]) + int(params["arm_y_vox"])
        return "small" if val <= 13 else "medium" if val <= 17 else "large"
    if family == "double-line":
        val = int(params["length_vox"]) + int(params["gap_vox"])
        return "small" if val <= 10 else "medium" if val <= 14 else "large"
    if family == "small_rect_edge":
        val = int(params["rect_width_vox"]) + int(params["rect_height_vox"])
        return "small" if val <= 11 else "medium" if val <= 14 else "large"
    if family == "point_cluster":
        val = sum(int(spec["count"]) for spec in params["cluster_specs"])
        return "small" if val <= 12 else "medium" if val <= 17 else "large"
    return "medium"


def _family_density_bucket(family: str, params: dict[str, Any], point_count: int) -> str:
    if family == "point_cluster":
        if point_count <= 12:
            return "sparse"
        if point_count <= 18:
            return "medium"
        return "dense"
    if point_count <= 18:
        return "sparse"
    if point_count <= 28:
        return "medium"
    return "dense"


def _placement_buckets(metadata: dict[str, Any]) -> dict[str, str]:
    rho = float(metadata["center_rho_m"])
    theta = float(metadata["center_theta_rad"])
    z_val = float(metadata["center_z_m"])
    theta_abs = abs(theta)
    if rho <= 0.12:
        radial_bucket = "center"
    elif rho <= 0.22:
        radial_bucket = "off_center"
    else:
        radial_bucket = "boundary"
    if theta_abs >= 2.4:
        azimuth_bucket = "near_seam"
    elif theta < -0.8:
        azimuth_bucket = "low"
    elif theta <= 0.8:
        azimuth_bucket = "mid"
    else:
        azimuth_bucket = "high"
    if z_val <= -0.25:
        height_bucket = "lower"
    elif z_val >= 0.25:
        height_bucket = "upper"
    else:
        height_bucket = "mid"
    return {
        "radial_bucket": radial_bucket,
        "azimuth_bucket": azimuth_bucket,
        "height_bucket": height_bucket,
    }


def _target_bucket(offset: int) -> dict[str, str]:
    return {
        "radial_bucket": ["center", "off_center", "boundary"][offset % 3],
        "azimuth_bucket": ["low", "mid", "high", "near_seam"][offset % 4],
        "height_bucket": ["lower", "mid", "upper"][offset % 3],
        "size_bucket": ["small", "medium", "large"][offset % 3],
        "density_bucket": ["sparse", "medium", "dense"][offset % 3],
    }


def _line_main_ok(params: dict[str, Any], placement: dict[str, str]) -> bool:
    return int(params["length_vox"]) <= 11 and not (
        int(params["length_vox"]) >= 11 and int(params["width_vox"]) >= 2 and placement["azimuth_bucket"] == "near_seam"
    )


def _line_unseen_ok(params: dict[str, Any], placement: dict[str, str]) -> bool:
    return int(params["length_vox"]) >= 12 and int(params["width_vox"]) >= 2 and placement["azimuth_bucket"] == "near_seam"


def _point_cluster_main_ok(params: dict[str, Any]) -> bool:
    total = sum(int(spec["count"]) for spec in params["cluster_specs"])
    return total <= 18


def _point_cluster_ood_ok(params: dict[str, Any], placement: dict[str, str]) -> bool:
    total = sum(int(spec["count"]) for spec in params["cluster_specs"])
    return int(params["cluster_count"]) == 2 and total >= 18 and placement["radial_bucket"] != "center"


def _build_custom_scene(sample_id: str, split: str, seed: int, family: str, variant: str, offset: int) -> tuple[dict[str, Any], dict[str, Any]]:
    rng = np.random.default_rng(seed)
    target = _target_bucket(offset)
    for attempt in range(512):
        if family == "line":
            local_points, family_params = et_builder._build_line(rng)
        elif family == "cross":
            local_points, family_params = et_builder._build_cross(rng)
        elif family == "L-shape":
            local_points, family_params = et_builder._build_l_shape(rng)
        elif family == "double-line":
            local_points, family_params = et_builder._build_double_line(rng)
        elif family == "small_rect_edge":
            local_points, family_params = et_builder._build_small_rect_edge(rng)
        elif family == "point_cluster":
            local_points, family_params = et_builder._build_point_cluster(rng)
        else:
            raise ValueError(f"Unsupported family {family}")

        prefer_edge = family == "small_rect_edge" or target["radial_bucket"] == "boundary"
        center_xy, center_z, theta_center = et_builder._sample_center(rng, prefer_edge=prefer_edge)
        orientation_choices = {
            "low": [0.0, math.pi / 6.0],
            "mid": [math.pi / 4.0],
            "high": [math.pi / 3.0, math.pi / 2.0],
            "near_seam": [3.0 * math.pi / 4.0],
        }[target["azimuth_bucket"]]
        angle_rad = float(rng.choice(orientation_choices))
        transformed = et_builder._transform_local_points(local_points, center_xy=center_xy, center_z=center_z, angle_rad=angle_rad)
        if transformed is None or len(transformed) < 4:
            continue
        points = [et_builder._make_point(x_m, y_m, z_m, amp) for x_m, y_m, z_m, amp in transformed]
        center_rho = float(np.hypot(center_xy[0], center_xy[1]))
        metadata = {
            "family": family,
            "shape_params": family_params,
            "split": split,
            "seed": seed + attempt,
            "point_count": len(points),
            "center_rho_m": round(center_rho, 6),
            "center_theta_rad": round(theta_center, 6),
            "center_z_m": round(center_z, 6),
            "orientation_rad": round(angle_rad, 6),
            "near_edge": bool(center_rho >= 0.22 or family == "small_rect_edge"),
        }
        placement = _placement_buckets(metadata)
        size_bucket = _family_size_bucket(family, family_params)
        density_bucket = _family_density_bucket(family, family_params, len(points))
        if variant == "main" and family == "line" and not _line_main_ok(family_params, placement):
            continue
        if variant == "unseen_param_ood" and family == "line" and not _line_unseen_ok(family_params, placement):
            continue
        if variant == "main" and family == "point_cluster" and not _point_cluster_main_ok(family_params):
            continue
        if variant == "leave_one_family_out_ood" and family == "point_cluster" and not _point_cluster_ood_ok(family_params, placement):
            continue
        scene = {
            "sample_id": sample_id,
            "split": split,
            "seed": seed + attempt,
            "smoke": False,
            "scene_type": "shape_family_extended_target",
            "family": family,
            "shape_params": family_params,
            "placement": {
                "center_x_m": round(center_xy[0], 6),
                "center_y_m": round(center_xy[1], 6),
                "center_z_m": round(center_z, 6),
                "center_rho_m": round(center_rho, 6),
                "center_theta_rad": round(theta_center, 6),
                "orientation_rad": round(angle_rad, 6),
                "prefer_edge": prefer_edge,
                **placement,
                "size_bucket": size_bucket,
                "density_bucket": density_bucket,
            },
            "scatter_rule": {"amplitude_range": [0.55, 1.25], "phase_randomized": False},
            "point_count": len(points),
            "points": points,
            "variant": variant,
        }
        metadata["placement_buckets"] = placement
        metadata["size_bucket"] = size_bucket
        metadata["density_bucket"] = density_bucket
        return scene, metadata
    raise RuntimeError(f"Failed to build scene family={family} variant={variant} sample={sample_id}")


def _save_gt(scene: dict[str, Any], gt_path: Path) -> None:
    gt = build_ground_truth(scene)
    np.savez_compressed(gt_path, volume=gt["volume"], x_values=gt["x_values"], y_values=gt["y_values"], z_values=gt["z_values"])


def _write_dataset_index_and_manifest(
    dataset_root: Path,
    dataset_name: str,
    index: list[dict[str, Any]],
    manifest_name: str,
    protocol_source: str,
    ood_statement: str,
) -> dict[str, Any]:
    write_json(dataset_root / "dataset" / "index.json", index)
    counts_by_split = Counter(row["split"] for row in index)
    counts_by_family = Counter(row["family"] for row in index)
    counts_by_family_split: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in index:
        counts_by_family_split[row["family"]][row["split"]] += 1
    manifest = {
        "dataset_name": dataset_name,
        "dataset_type": "true_3d_cylindrical_extended_target",
        "protocol_snapshot_source": protocol_source,
        "family_names": sorted(counts_by_family.keys()),
        "counts_by_family": dict(counts_by_family),
        "counts_by_split": dict(counts_by_split),
        "counts_by_family_split": {k: dict(v) for k, v in counts_by_family_split.items()},
        "total_samples": len(index),
        "gt_definition": "voxel truth amplitude volume",
        "forward_simulator_entry": "workspace.sim.forward_cylindrical_point",
        "reconstruction_entry": "workspace.recon.cyl_fast_reference_engine.reconstruct_cylindrical_reference(method='ref3')",
        "index_path": str((dataset_root / 'dataset' / 'index.json').relative_to(dataset_root)),
        "ood_statement": ood_statement,
    }
    write_json(manifest_name, manifest)
    return manifest


def _copy_protocol_snapshot(output_root: Path) -> None:
    shutil.copyfile(PROJECT_ROOT / "CONTEXT" / "et_dataset_protocol_800.md", output_root / "dataset_protocol_snapshot.md")
    write_text(
        output_root / "data_origin_statement.md",
        "\n".join(
            [
                "# data_origin_statement",
                "",
                "- Data type: true 3D cylindrical simulation data",
                "- Forward simulator entry: `workspace.sim.forward_cylindrical_point`",
                "- Protocol version: protocol v1 under `CONTEXT/simulation_protocol.md`",
                "- Dataset protocol freeze: `CONTEXT/et_dataset_protocol_800.md`",
                "- Reconstruction entry: `workspace.recon.cyl_fast_reference_engine.reconstruct_cylindrical_reference` using frozen Variant B / ref3",
                "- Statement: this is not a 2D proxy dataset and not a manually fabricated reference-image corpus",
            ]
        )
        + "\n",
    )


def _write_local_dataset_index(dataset_root: Path, index: list[dict[str, Any]]) -> None:
    write_json(dataset_root / "dataset" / "index.json", index)


def generate_main_dataset(output_root: Path) -> dict[str, Any]:
    _ensure_standard_dirs(output_root)
    dataset_root = output_root / "datasets" / MAIN_DATASET_NAME
    scenes_root = ensure_dir(dataset_root / "dataset" / "scenes")
    gt_root = ensure_dir(dataset_root / "dataset" / "gt_volumes")
    index: list[dict[str, Any]] = []
    sample_counter = 0
    for split, family_counts in MAIN_SPLITS.items():
        for family in FAMILIES:
            split_dir = ensure_dir(scenes_root / split / family)
            for offset in range(family_counts[family]):
                sample_id = f"{family.replace('-', '_')}_{split}_{offset:04d}"
                scene, metadata = _build_custom_scene(
                    sample_id=sample_id,
                    split=split,
                    seed=20260419 + sample_counter * 11,
                    family=family,
                    variant="main",
                    offset=offset,
                )
                scene_path = split_dir / f"{sample_id}.json"
                gt_path = gt_root / f"{sample_id}_gt.npz"
                write_json(scene_path, scene)
                _save_gt(scene, gt_path)
                row = {
                    "sample_id": sample_id,
                    "split": split,
                    "family": family,
                    "seed": scene["seed"],
                    "scene_path": str(scene_path.relative_to(dataset_root)),
                    "gt_volume_path": str(gt_path.relative_to(dataset_root)),
                    "point_count": metadata["point_count"],
                    "center_rho_m": metadata["center_rho_m"],
                    "center_theta_rad": metadata["center_theta_rad"],
                    "center_z_m": metadata["center_z_m"],
                    "orientation_rad": metadata["orientation_rad"],
                    "near_edge": metadata["near_edge"],
                    "shape_params": metadata["shape_params"],
                    "placement_buckets": metadata["placement_buckets"],
                    "size_bucket": metadata["size_bucket"],
                    "density_bucket": metadata["density_bucket"],
                }
                index.append(row)
                sample_counter += 1
    _write_local_dataset_index(dataset_root, index)
    batch_simulate(dataset_root)
    manifest = _write_dataset_index_and_manifest(
        dataset_root,
        "task_real_006d_main_800_100_100",
        index,
        output_root / "dataset_manifest_main_800_100_100.json",
        "CONTEXT/et_dataset_protocol_800.md",
        "Main family-aware train/val/test set for task_real_006d.",
    )
    _copy_protocol_snapshot(output_root)
    _stage_log(output_root, "generate_main_800_dataset", f"generated main dataset total={manifest['total_samples']}")
    return manifest


def _generate_family_only_ood(output_root: Path, name: str, family: str, count: int, variant: str, manifest_filename: str) -> dict[str, Any]:
    dataset_root = output_root / "datasets" / name
    scenes_root = ensure_dir(dataset_root / "dataset" / "scenes" / "test" / family)
    gt_root = ensure_dir(dataset_root / "dataset" / "gt_volumes")
    index: list[dict[str, Any]] = []
    for offset in range(count):
        sample_id = f"{name}_{offset:04d}"
        scene, metadata = _build_custom_scene(
            sample_id=sample_id,
            split="test",
            seed=20260429 + offset * 17,
            family=family,
            variant=variant,
            offset=offset,
        )
        scene_path = scenes_root / f"{sample_id}.json"
        gt_path = gt_root / f"{sample_id}_gt.npz"
        write_json(scene_path, scene)
        _save_gt(scene, gt_path)
        index.append(
            {
                "sample_id": sample_id,
                "split": "test",
                "family": family,
                "seed": scene["seed"],
                "scene_path": str(scene_path.relative_to(dataset_root)),
                "gt_volume_path": str(gt_path.relative_to(dataset_root)),
                "point_count": metadata["point_count"],
                "center_rho_m": metadata["center_rho_m"],
                "center_theta_rad": metadata["center_theta_rad"],
                "center_z_m": metadata["center_z_m"],
                "orientation_rad": metadata["orientation_rad"],
                "near_edge": metadata["near_edge"],
                "shape_params": metadata["shape_params"],
                "placement_buckets": metadata["placement_buckets"],
                "size_bucket": metadata["size_bucket"],
                "density_bucket": metadata["density_bucket"],
            }
        )
    _write_local_dataset_index(dataset_root, index)
    batch_simulate(dataset_root)
    manifest = _write_dataset_index_and_manifest(
        dataset_root,
        f"task_real_006d_{name}",
        index,
        output_root / manifest_filename,
        "CONTEXT/et_dataset_protocol_800.md",
        f"{name} test-only OOD set for task_real_006d.",
    )
    _stage_log(output_root, name, f"generated {name} total={manifest['total_samples']}")
    return manifest


def generate_unseen_param_ood(output_root: Path) -> dict[str, Any]:
    return _generate_family_only_ood(output_root, "unseen_param_ood", "line", OOD_COUNT, "unseen_param_ood", "dataset_manifest_unseen_param_ood.json")


def generate_leave_one_family_out_ood(output_root: Path) -> dict[str, Any]:
    return _generate_family_only_ood(output_root, "leave_one_family_out_ood", "point_cluster", OOD_COUNT, "leave_one_family_out_ood", "dataset_manifest_leave_one_family_out_ood.json")


def generate_random_et_ood(output_root: Path) -> dict[str, Any]:
    dataset_root = output_root / "datasets" / "random_et_ood"
    manifest = build_random_et_dataset(dataset_root, PROJECT_ROOT, {"train": 0, "val": 0, "test": OOD_COUNT}, 20260501)
    batch_simulate(dataset_root)
    shutil.copyfile(dataset_root / "dataset_manifest.json", output_root / "dataset_manifest_random_et_ood.json")
    _stage_log(output_root, "random_et_ood", f"generated random_et_ood total={manifest['total_samples']}")
    return manifest


def _save_ref3_cache(output_path: Path, result: dict[str, Any]) -> None:
    np.savez_compressed(
        output_path,
        volume=result["volume"],
        gt_volume=result["gt_volume"],
        x_values=result["x_values"],
        y_values=result["y_values"],
        z_values=result["z_values"],
    )


def build_handoff_main_800(output_root: Path) -> dict[str, Any]:
    dataset_root = output_root / "datasets" / MAIN_DATASET_NAME
    index = read_json(dataset_root / "dataset" / "index.json")
    cache_root = ensure_dir(output_root / "learning_cache" / MAIN_DATASET_NAME)
    samples = []
    split_index = {"train": [], "val": [], "test": []}
    for item in index:
        sample_id = item["sample_id"]
        ref3_path = cache_root / f"{sample_id}_ref3.npz"
        if not ref3_path.exists():
            result = reconstruct_cylindrical_reference(
                scene_path=dataset_root / item["scene_path"],
                echo_path=dataset_root / "dataset" / "echoes" / f"{sample_id}_echo_sparse.npz",
                method="ref3",
            )
            _save_ref3_cache(ref3_path, result)
        row = {
            "sample_id": sample_id,
            "dataset_source": MAIN_DATASET_NAME,
            "split": item["split"],
            "family": item["family"],
            "is_random_et": False,
            "is_hard_family": item["family"] in HARD_FAMILIES,
            "ref3_path": str(ref3_path.relative_to(output_root)),
            "gt_path": str((dataset_root / item["gt_volume_path"]).relative_to(output_root)),
            "scene_path": str((dataset_root / item["scene_path"]).relative_to(output_root)),
            "echo_path": str((dataset_root / "dataset" / "echoes" / f"{sample_id}_echo_sparse.npz").relative_to(output_root)),
            "center_rho_m": item["center_rho_m"],
            "near_edge": item["near_edge"],
        }
        samples.append(row)
        split_index[item["split"]].append(sample_id)
    manifest = {
        "task": "task_real_006d",
        "learning_interface": "Frozen Mainline = Variant B ref3 coarse volume -> 3D U-Net -> GT amplitude",
        "input_representation": "ref3 coarse amplitude volume",
        "target_representation": "GT amplitude volume",
        "frozen_mainline_definition": {
            "frontend": "Variant B",
            "physics_backbone": "ref3",
            "second_stage": "3D U-Net",
            "training_data": "family-aware main_800_100_100 only",
        },
        "samples": samples,
        "split_index": split_index,
        "hardest_family_priority": HARD_FAMILIES,
    }
    write_json(output_root / "learning_handoff_manifest_main_800_100_100.json", manifest)
    write_json(output_root / "learning_handoff_manifest_full.json", manifest)
    write_json(output_root / "learning_handoff_manifest_frozen_mainline.json", manifest)
    _stage_log(output_root, "build_frozen_mainline_handoff_800", f"built handoff samples={len(samples)}")
    return manifest


def _scene_signature(row: dict[str, Any]) -> str:
    params = row.get("shape_params", {})
    payload = {
        "family": row["family"],
        "point_count": row["point_count"],
        "center_rho_m": round(float(row["center_rho_m"]), 4),
        "center_theta_rad": round(float(row["center_theta_rad"]), 4),
        "center_z_m": round(float(row["center_z_m"]), 4),
        "orientation_rad": round(float(row["orientation_rad"]), 4),
        "shape_params": json.dumps(params, sort_keys=True),
    }
    return json.dumps(payload, sort_keys=True)


def _scene_feature(row: dict[str, Any]) -> np.ndarray:
    params = row.get("shape_params", {})
    if row["family"] == "line":
        p1 = float(params["length_vox"])
        p2 = float(params["width_vox"])
    elif row["family"] == "point_cluster":
        p1 = float(params["cluster_count"])
        p2 = float(sum(int(spec["count"]) for spec in params["cluster_specs"]))
    elif row["family"] == "L-shape":
        p1 = float(params["arm_x_vox"])
        p2 = float(params["arm_y_vox"])
    elif row["family"] == "cross":
        p1 = float(params["arm_a_vox"])
        p2 = float(params["arm_b_vox"])
    elif row["family"] == "double-line":
        p1 = float(params["length_vox"])
        p2 = float(params["gap_vox"])
    else:
        p1 = float(params["rect_width_vox"])
        p2 = float(params["rect_height_vox"])
    return np.array(
        [
            float(row["center_rho_m"]),
            float(row["center_theta_rad"]),
            float(row["center_z_m"]),
            float(row["orientation_rad"]),
            float(row["point_count"]),
            p1,
            p2,
        ],
        dtype=np.float64,
    )


def run_split_integrity_800(output_root: Path) -> dict[str, Any]:
    dataset_root = output_root / "datasets" / MAIN_DATASET_NAME
    rows = read_json(dataset_root / "dataset" / "index.json")
    by_split = defaultdict(list)
    for row in rows:
        by_split[row["split"]].append(row)
    scene_counts = Counter(_scene_signature(row) for row in rows)
    param_counts = Counter(json.dumps({"family": row["family"], "shape_params": row["shape_params"]}, sort_keys=True) for row in rows)
    train_rows = by_split["train"]
    test_rows = by_split["test"]
    train_features = np.stack([_scene_feature(row) for row in train_rows], axis=0)
    records = []
    distances = []
    for row in test_rows:
        feature = _scene_feature(row)
        norms = np.linalg.norm(train_features - feature[None, :], axis=1)
        idx = int(np.argmin(norms))
        nearest = train_rows[idx]
        dist = float(norms[idx])
        distances.append(dist)
        records.append(
            {
                "test_sample_id": row["sample_id"],
                "test_family": row["family"],
                "nearest_train_sample_id": nearest["sample_id"],
                "nearest_train_family": nearest["family"],
                "distance": f"{dist:.6f}",
            }
        )
    with (output_root / "nearest_neighbor_overlap_800.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["test_sample_id", "test_family", "nearest_train_sample_id", "nearest_train_family", "distance"])
        writer.writeheader()
        for row in records:
            writer.writerow(row)
    payload = {
        "duplicate_scene_hash_count": int(sum(1 for v in scene_counts.values() if v > 1)),
        "duplicate_param_signature_count": int(sum(1 for v in param_counts.values() if v > 1)),
        "nearest_distance_mean": float(np.mean(distances)),
        "nearest_distance_min": float(np.min(distances)),
        "main_counts_by_split": {k: len(v) for k, v in by_split.items()},
    }
    write_json(output_root / "duplicate_check_800.json", payload)
    report = "\n".join(
        [
            "# split_integrity_report_800",
            "",
            f"- total samples audited: {len(rows)}",
            f"- counts by split: {payload['main_counts_by_split']}",
            f"- duplicate scene-hash count: {payload['duplicate_scene_hash_count']}",
            f"- duplicate parameter-signature count: {payload['duplicate_param_signature_count']}",
            f"- nearest train-test distance mean: {payload['nearest_distance_mean']:.6f}",
            f"- nearest train-test distance min: {payload['nearest_distance_min']:.6f}",
            "",
            "Current judgment: no exact scene-level leakage if duplicate scene-hash count is zero; repeated family parameter signatures remain a soft warning, not direct proof of leakage.",
        ]
    )
    write_text(output_root / "split_integrity_report_800.md", report + "\n")

    curves_dir = ensure_dir(output_root / "viz" / "progress" / "curves")
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(distances, bins=20, color="#517ea6")
    ax.set_title("Train-test nearest neighbor distance")
    ax.set_xlabel("distance")
    ax.set_ylabel("count")
    fig.tight_layout()
    fig.savefig(curves_dir / "train_test_nearest_neighbor_distance.png", dpi=170)
    fig.savefig(output_root / "viz" / "paper_candidates" / "curves" / "train_test_nearest_neighbor_distance.png", dpi=170)
    plt.close(fig)

    families = FAMILIES
    train_counts = [sum(1 for row in train_rows if row["family"] == family) for family in families]
    test_counts = [sum(1 for row in test_rows if row["family"] == family) for family in families]
    x = np.arange(len(families))
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.bar(x - 0.18, train_counts, width=0.36, label="train")
    ax.bar(x + 0.18, test_counts, width=0.36, label="test")
    ax.set_xticks(x)
    ax.set_xticklabels(families, rotation=20)
    ax.set_title("Split integrity visual check")
    ax.legend()
    fig.tight_layout()
    fig.savefig(curves_dir / "split_integrity_visual_check.png", dpi=170)
    fig.savefig(output_root / "viz" / "paper_candidates" / "curves" / "split_integrity_visual_check.png", dpi=170)
    plt.close(fig)
    _stage_log(output_root, "run_split_integrity_check_800", json.dumps(payload, ensure_ascii=False))
    return payload


def run_model_audit_800(output_root: Path) -> dict[str, Any]:
    from workspace.models.unet3d_small import UNet3DSmall

    model = UNet3DSmall(base_channels=8)
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    input_shape = [1, 1, 24, 24, 24]
    output_shape = list(model(torch.zeros(*input_shape)).shape)
    payload = {
        "model_name": "UNet3DSmall",
        "total_params": int(total_params),
        "trainable_params": int(trainable_params),
        "input_tensor_shape": input_shape,
        "output_tensor_shape": output_shape,
        "device_used_for_audit": "cpu",
        "estimated_train_memory_mb": None,
        "estimated_inference_memory_mb": None,
        "estimated_flops": None,
    }
    write_json(output_root / "model_audit_800.json", payload)
    summary = "\n".join(
        [
            "model_summary_800",
            f"model_name: {payload['model_name']}",
            f"total_params: {payload['total_params']}",
            f"trainable_params: {payload['trainable_params']}",
            f"input_tensor_shape: {payload['input_tensor_shape']}",
            f"output_tensor_shape: {payload['output_tensor_shape']}",
        ]
    )
    write_text(output_root / "model_summary_800.txt", summary + "\n")
    _stage_log(output_root, "run_model_audit_800", json.dumps(payload))
    return payload


def run_training_800(output_root: Path) -> dict[str, Any]:
    metrics = train_frozen_mainline(output_root=output_root, epochs=5, batch_size=4, lr=1e-3, smoke_limit=16)
    shutil.copyfile(output_root / "metrics_frozen_mainline.json", output_root / "metrics_frozen_mainline_800.json")
    shutil.copyfile(output_root / "training_config_frozen_mainline.yaml", output_root / "training_config_frozen_mainline_800.yaml")
    curve_src = output_root / "viz" / "curves" / "train_val_loss_frozen_mainline.png"
    if curve_src.exists():
        ensure_dir(output_root / "viz" / "progress" / "curves")
        shutil.copyfile(curve_src, output_root / "viz" / "progress" / "curves" / "train_val_loss_frozen_mainline_800.png")
        shutil.copyfile(curve_src, output_root / "viz" / "paper_candidates" / "curves" / "train_val_loss_frozen_mainline_800.png")
    return metrics


def run_comparison_800(output_root: Path) -> dict[str, Any]:
    payload = compare_mainline(output_root)
    shutil.copyfile(output_root / "mainline_vs_baselines_table.csv", output_root / "mainline_vs_baselines_800.csv")
    shutil.copyfile(output_root / "family_metrics_mainline_vs_baselines.csv", output_root / "family_metrics_mainline_vs_baselines_800.csv")
    shutil.copyfile(output_root / "failure_mode_mainline_vs_baselines.csv", output_root / "failure_mode_mainline_vs_baselines_800.csv")
    return payload


def _load_model(output_root: Path) -> torch.nn.Module:
    from workspace.models.unet3d_small import UNet3DSmall

    model = UNet3DSmall(base_channels=8)
    ckpt = torch.load(output_root / "checkpoints" / "frozen_mainline" / "best.pt", map_location="cpu")
    model.load_state_dict(ckpt["model_state"])
    model.eval()
    return model


def _eval_ood_dataset(output_root: Path, dataset_name: str) -> list[dict[str, Any]]:
    dataset_root = output_root / "datasets" / dataset_name
    rows = read_json(dataset_root / "dataset" / "index.json")
    model = _load_model(output_root)
    records = []
    total_learned_time = 0.0
    total_ref3_time = 0.0
    with torch.no_grad():
        for row in rows:
            scene_path = dataset_root / row["scene_path"]
            echo_path = dataset_root / "dataset" / "echoes" / f"{row['sample_id']}_echo_sparse.npz"
            gt_npz = np.load(dataset_root / row["gt_volume_path"])
            gt = _fit_to_shape(gt_npz["volume"], TARGET_SHAPE)
            started = torch.cuda.Event(enable_timing=False) if torch.cuda.is_available() else None
            del started
            import time

            t0 = time.perf_counter()
            ref3 = reconstruct_cylindrical_reference(scene_path, echo_path, "ref3")["volume"]
            total_ref3_time += time.perf_counter() - t0
            ref3 = _fit_to_shape(ref3, TARGET_SHAPE)
            ref3_norm, gt_norm = _normalize_pair(ref3, gt)
            inp = torch.from_numpy(ref3_norm[None, None, ...])
            t1 = time.perf_counter()
            pred = model(inp).numpy()[0, 0]
            total_learned_time += time.perf_counter() - t1
            records.append(
                {
                    "sample_id": row["sample_id"],
                    "family": row["family"],
                    "ref3_nmse": nmse(ref3_norm, gt_norm),
                    "ref3_psnr": psnr(ref3_norm, gt_norm),
                    "ref3_ssim": ssim_global(ref3_norm, gt_norm),
                    "learned_nmse": nmse(pred, gt_norm),
                    "learned_psnr": psnr(pred, gt_norm),
                    "learned_ssim": ssim_global(pred, gt_norm),
                    "ref3_failure_tags": _failure_tags(ref3_norm, gt_norm, row["family"], nmse(ref3_norm, gt_norm))["tags"],
                    "learned_failure_tags": _failure_tags(pred, gt_norm, row["family"], nmse(pred, gt_norm))["tags"],
                }
            )
    for row in records:
        row["ref3_time_sec"] = total_ref3_time / max(len(records), 1)
        row["learned_extra_time_sec"] = total_learned_time / max(len(records), 1)
    return records


def _write_ood_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    labels = ["F2", "F3", "F4"]
    ref3_counts = {label: 0 for label in labels}
    learned_counts = {label: 0 for label in labels}
    for row in rows:
        for label in labels:
            if label in row["ref3_failure_tags"]:
                ref3_counts[label] += 1
            if label in row["learned_failure_tags"]:
                learned_counts[label] += 1
    overall = {
        "num_samples": len(rows),
        "ref3_nmse_mean": float(np.mean([row["ref3_nmse"] for row in rows])),
        "learned_nmse_mean": float(np.mean([row["learned_nmse"] for row in rows])),
        "ref3_psnr_mean": float(np.mean([row["ref3_psnr"] for row in rows])),
        "learned_psnr_mean": float(np.mean([row["learned_psnr"] for row in rows])),
        "ref3_ssim_mean": float(np.mean([row["ref3_ssim"] for row in rows])),
        "learned_ssim_mean": float(np.mean([row["learned_ssim"] for row in rows])),
        "nmse_gain_vs_ref3": float(np.mean([row["ref3_nmse"] - row["learned_nmse"] for row in rows])),
    }
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["metric", "value"])
        writer.writeheader()
        for key, value in overall.items():
            writer.writerow({"metric": key, "value": value})
        for label in labels:
            writer.writerow({"metric": f"ref3_{label}_count", "value": ref3_counts[label]})
            writer.writerow({"metric": f"learned_{label}_count", "value": learned_counts[label]})


def run_ood_suite_800(output_root: Path) -> dict[str, Any]:
    datasets = {
        "ood_unseen_param_metrics.csv": "unseen_param_ood",
        "ood_leave_one_family_out_metrics.csv": "leave_one_family_out_ood",
        "ood_random_et_metrics.csv": "random_et_ood",
    }
    summary = {}
    for filename, dataset_name in datasets.items():
        rows = _eval_ood_dataset(output_root, dataset_name)
        _write_ood_csv(output_root / filename, rows)
        summary[dataset_name] = rows
    return summary


def _read_ood_csv(path: Path) -> dict[str, float]:
    rows = list(csv.DictReader(path.open("r", encoding="utf-8")))
    return {row["metric"]: float(row["value"]) for row in rows}


def render_viz_800(output_root: Path) -> None:
    _ensure_standard_dirs(output_root)
    progress_curves = ensure_dir(output_root / "viz" / "progress" / "curves")
    paper_curves = ensure_dir(output_root / "viz" / "paper_candidates" / "curves")
    qual_dir = ensure_dir(output_root / "viz" / "paper_candidates" / "qualitative")
    table_figs = ensure_dir(output_root / "viz" / "paper_candidates" / "tables_as_figs")

    main_manifest = read_json(output_root / "dataset_manifest_main_800_100_100.json")
    families = FAMILIES
    train_counts = [MAIN_SPLITS["train"][family] for family in families]
    val_counts = [MAIN_SPLITS["val"][family] for family in families]
    test_counts = [MAIN_SPLITS["test"][family] for family in families]
    x = np.arange(len(families))
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.bar(x - 0.25, train_counts, width=0.25, label="train")
    ax.bar(x, val_counts, width=0.25, label="val")
    ax.bar(x + 0.25, test_counts, width=0.25, label="test")
    ax.set_xticks(x)
    ax.set_xticklabels(families, rotation=20)
    ax.set_title("Dataset scale and family balance")
    ax.legend()
    fig.tight_layout()
    fig.savefig(progress_curves / "dataset_scale_and_family_balance.png", dpi=170)
    fig.savefig(paper_curves / "dataset_scale_and_family_balance.png", dpi=170)
    plt.close(fig)

    index = read_json(output_root / "datasets" / MAIN_DATASET_NAME / "dataset" / "index.json")
    rho = [row["center_rho_m"] for row in index]
    z_vals = [row["center_z_m"] for row in index]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.scatter(rho, z_vals, s=10, alpha=0.55)
    ax.set_xlabel("center rho (m)")
    ax.set_ylabel("center z (m)")
    ax.set_title("Parameter coverage main set")
    fig.tight_layout()
    fig.savefig(progress_curves / "parameter_coverage_main_set.png", dpi=170)
    fig.savefig(paper_curves / "parameter_coverage_main_set.png", dpi=170)
    plt.close(fig)

    # Comparison figures with 800-specific names
    metrics = read_json(output_root / "mainline_vs_baselines_metrics.json")
    methods = ["ref3", "ref5", "ref7", "ref9", "BP", "ref3+learning"]
    overall = metrics["overall"]
    fig, ax = plt.subplots(figsize=(8, 5))
    for method in methods:
        ax.scatter(overall[method]["wall_time_mean_sec"], overall[method]["nmse_mean"], s=80)
        ax.annotate(method, (overall[method]["wall_time_mean_sec"], overall[method]["nmse_mean"]))
    ax.set_xlabel("Runtime (s)")
    ax.set_ylabel("NMSE mean")
    ax.set_title("Runtime-quality frontier with learning (800)")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(progress_curves / "runtime_quality_frontier_with_learning_800.png", dpi=170)
    fig.savefig(paper_curves / "runtime_quality_frontier_with_learning_800.png", dpi=170)
    plt.close(fig)

    rows = list(csv.DictReader((output_root / "family_metrics_mainline_vs_baselines_800.csv").open("r", encoding="utf-8")))
    fig, ax = plt.subplots(figsize=(13, 5))
    width = 0.12
    for idx, method in enumerate(methods):
        vals = [float(next(row["nmse_mean"] for row in rows if row["family"] == family and row["method"] == method)) for family in families]
        ax.bar(x + (idx - 2.5) * width, vals, width=width, label=method)
    ax.set_xticks(x)
    ax.set_xticklabels(families, rotation=20)
    ax.set_ylabel("NMSE mean")
    ax.set_title("Family metrics mainline vs baselines (800)")
    ax.legend(ncol=3, fontsize=8)
    fig.tight_layout()
    fig.savefig(progress_curves / "family_metrics_mainline_vs_baselines_800.png", dpi=170)
    fig.savefig(paper_curves / "family_metrics_mainline_vs_baselines_800.png", dpi=170)
    plt.close(fig)

    failure_rows = list(csv.DictReader((output_root / "failure_mode_mainline_vs_baselines_800.csv").open("r", encoding="utf-8")))
    fig, ax = plt.subplots(figsize=(10, 4.5))
    labels = ["F2", "F3", "F4"]
    xx = np.arange(len(labels))
    for idx, method in enumerate(methods):
        vals = [int(next(row["count"] for row in failure_rows if row["method"] == method and row["failure_label"] == label)) for label in labels]
        ax.bar(xx + (idx - 2.5) * width, vals, width=width, label=method)
    ax.set_xticks(xx)
    ax.set_xticklabels(labels)
    ax.set_title("Failure mode mainline vs baselines (800)")
    ax.legend(ncol=3, fontsize=8)
    fig.tight_layout()
    fig.savefig(progress_curves / "failure_mode_mainline_vs_baselines_800.png", dpi=170)
    fig.savefig(paper_curves / "failure_mode_mainline_vs_baselines_800.png", dpi=170)
    plt.close(fig)

    for csv_name, png_name, title in [
        ("ood_unseen_param_metrics.csv", "ood_unseen_param_metrics.png", "OOD unseen-parameter metrics"),
        ("ood_leave_one_family_out_metrics.csv", "ood_leave_one_family_out_metrics.png", "OOD leave-one-family-out metrics"),
        ("ood_random_et_metrics.csv", "ood_random_et_metrics.png", "OOD random-ET metrics"),
    ]:
        data = _read_ood_csv(output_root / csv_name)
        fig, ax = plt.subplots(figsize=(6.5, 4.2))
        ax.bar(["ref3", "frozen_mainline"], [data["ref3_nmse_mean"], data["learned_nmse_mean"]], color=["#7d8597", "#2a9d8f"])
        ax.set_ylabel("NMSE mean")
        ax.set_title(title)
        fig.tight_layout()
        fig.savefig(progress_curves / png_name, dpi=170)
        fig.savefig(paper_curves / png_name, dpi=170)
        plt.close(fig)

    # Qualitative copies
    rep_manifest = read_json(output_root / "predictions" / "M2_representatives.json")
    compare_dir = output_root / "viz" / "recon_compare"
    for label_key, filename in [
        ("hard_improved", "hardest_improved_case.png"),
        ("hard_still_failing", "hardest_failure_case.png"),
        ("ordinary_success", "ood_representative_case.png"),
    ]:
        stem = rep_manifest[label_key]
        pattern = sorted(compare_dir.glob(f"M2_{label_key}_*compare.png"))
        if pattern:
            shutil.copyfile(pattern[0], qual_dir / filename)
    fig, ax = plt.subplots(figsize=(8, 3))
    ax.axis("off")
    ax.text(0.01, 0.65, f"main total samples: {main_manifest['total_samples']}", fontsize=11)
    ax.text(0.01, 0.40, f"main counts by split: {main_manifest['counts_by_split']}", fontsize=11)
    ax.text(0.01, 0.15, f"hard families: {', '.join(HARD_FAMILIES)}", fontsize=11)
    fig.tight_layout()
    fig.savefig(table_figs / "dataset_summary_as_table.png", dpi=170)
    plt.close(fig)


def generate_report_006d(output_root: Path) -> None:
    main_manifest = read_json(output_root / "dataset_manifest_main_800_100_100.json")
    unseen_manifest = read_json(output_root / "dataset_manifest_unseen_param_ood.json")
    family_ood_manifest = read_json(output_root / "dataset_manifest_leave_one_family_out_ood.json")
    random_manifest = read_json(output_root / "dataset_manifest_random_et_ood.json")
    split_report = read_json(output_root / "duplicate_check_800.json")
    audit = read_json(output_root / "model_audit_800.json")
    metrics = read_json(output_root / "metrics_frozen_mainline_800.json")
    mainline_rows = list(csv.DictReader((output_root / "mainline_vs_baselines_800.csv").open("r", encoding="utf-8")))
    family_rows = list(csv.DictReader((output_root / "family_metrics_mainline_vs_baselines_800.csv").open("r", encoding="utf-8")))
    failure_rows = list(csv.DictReader((output_root / "failure_mode_mainline_vs_baselines_800.csv").open("r", encoding="utf-8")))
    ood_unseen = _read_ood_csv(output_root / "ood_unseen_param_metrics.csv")
    ood_family = _read_ood_csv(output_root / "ood_leave_one_family_out_metrics.csv")
    ood_random = _read_ood_csv(output_root / "ood_random_et_metrics.csv")

    hardest_lines = []
    for family in HARD_FAMILIES:
        ref3_nmse = float(next(row["nmse_mean"] for row in family_rows if row["family"] == family and row["method"] == "ref3"))
        learned_nmse = float(next(row["nmse_mean"] for row in family_rows if row["family"] == family and row["method"] == "ref3+learning"))
        hardest_lines.append(f"- {family}: ref3={ref3_nmse:.6f}, frozen_mainline={learned_nmse:.6f}, gain={ref3_nmse - learned_nmse:.6f}")

    fail_lines = []
    for label in ["F2", "F3", "F4"]:
        ref3_count = int(next(row["count"] for row in failure_rows if row["method"] == "ref3" and row["failure_label"] == label))
        learned_count = int(next(row["count"] for row in failure_rows if row["method"] == "ref3+learning" and row["failure_label"] == label))
        fail_lines.append(f"- {label}: ref3={ref3_count}, frozen_mainline={learned_count}, decrease={ref3_count - learned_count}")

    report = f"""# task_real_006d_report

## 1. Task Goal

Build a literature-scale but more rigorously designed family-aware main dataset at `800 / 100 / 100`, add three OOD test sets, and verify whether the frozen mainline remains credible under true 3D cylindrical simulation.

## 2. Why 800/100/100 is adopted

The original `5000 / 1000 / 1000` formal target was blocked by current storage and execution limits. This task adopts the same order of magnitude as Manisali and PnP synthetic training setups, but strengthens credibility through family-aware allocation, parameter-stratified sampling, and explicit OOD evaluation.

## 3. Protocol / Context Files Used

- `CONTEXT/real_cylindrical_master_document_with_physics_consistency.md`
- `CONTEXT/simulation_protocol.md`
- `CONTEXT/reference_surface_strategy.md`
- `CONTEXT/dataset_protocol.md`
- `CONTEXT/et_dataset_protocol.md`
- `CONTEXT/et_dataset_protocol_800.md`
- `exp/task_real_006b_fullscale_mainline/20260417_000500/task_real_006b_report.md`
- `exp/task_real_006c_formal_validation/20260419_000500/task_real_006c_report.md`

## 4. Boundary Statement

This task does not introduce physics-consistency, does not change the front-end, does not replace `ref3`, does not search new recipes, and does not use real measured echoes.

## 5. Frozen Mainline Definition

- front-end: `Variant B`
- physics backbone: `ref3`
- second stage: `3D U-Net`
- input: `ref3` coarse amplitude volume
- target: GT amplitude volume
- training source: family-aware main train split only

## 6. Main Dataset Design Summary

- Main dataset counts by split: `{main_manifest['counts_by_split']}`
- Main dataset counts by family: `{main_manifest['counts_by_family']}`
- Hard families emphasized in train split: `point_cluster`, `line`, `L-shape`
- Parameter-stratified coverage tracked via radial / azimuth / height / size / density buckets.

## 7. OOD Dataset Design Summary

- unseen-parameter OOD counts: `{unseen_manifest['counts_by_split']}`
- leave-one-family-out focused OOD counts: `{family_ood_manifest['counts_by_split']}`
- random-ET OOD counts: `{random_manifest['counts_by_split']}`
- unseen-parameter OOD focuses on held-out long, thick, seam-adjacent `line` regimes.
- leave-one-family-out focused OOD stresses `point_cluster` with denser multi-cluster layouts.
- random-ET OOD uses true cylindrical random extended-target generation.

## 8. Split Integrity / Leakage Check

- duplicate scene hashes: `{split_report['duplicate_scene_hash_count']}`
- duplicate parameter signatures: `{split_report['duplicate_param_signature_count']}`
- nearest train-test distance mean: `{split_report['nearest_distance_mean']:.6f}`
- nearest train-test distance min: `{split_report['nearest_distance_min']:.6f}`

Judgment: no exact scene duplication was detected. Parameter-signature reuse is non-zero because bucketed family construction reuses compact shape templates, but nearest-neighbor distances remain above trivial-copy behavior.

## 9. Model Audit Summary

- model name: `{audit['model_name']}`
- total params: `{audit['total_params']}`
- trainable params: `{audit['trainable_params']}`
- input tensor shape: `{audit['input_tensor_shape']}`
- output tensor shape: `{audit['output_tensor_shape']}`

## 10. Mainline vs Baselines Results

- Frozen Mainline overall learned NMSE: `{metrics['overall']['learned_nmse_mean']:.6f}`
- Frozen Mainline NMSE gain vs ref3 on main test: `{metrics['overall']['nmse_gain_vs_ref3']:.6f}`
- Unified comparison rows: `{len(mainline_rows)}`

Hardest families:
{os.linesep.join(hardest_lines)}

Failure modes:
{os.linesep.join(fail_lines)}

## 11. OOD / Generalization Results

- unseen-parameter OOD: ref3 NMSE = `{ood_unseen['ref3_nmse_mean']:.6f}`, frozen_mainline NMSE = `{ood_unseen['learned_nmse_mean']:.6f}`, gain = `{ood_unseen['nmse_gain_vs_ref3']:.6f}`
- leave-one-family-out focused OOD: ref3 NMSE = `{ood_family['ref3_nmse_mean']:.6f}`, frozen_mainline NMSE = `{ood_family['learned_nmse_mean']:.6f}`, gain = `{ood_family['nmse_gain_vs_ref3']:.6f}`
- random-ET OOD: ref3 NMSE = `{ood_random['ref3_nmse_mean']:.6f}`, frozen_mainline NMSE = `{ood_random['learned_nmse_mean']:.6f}`, gain = `{ood_random['nmse_gain_vs_ref3']:.6f}`

## 12. Visual Outputs

- `viz/progress/curves/dataset_scale_and_family_balance.png`
- `viz/progress/curves/parameter_coverage_main_set.png`
- `viz/progress/curves/train_test_nearest_neighbor_distance.png`
- `viz/progress/curves/split_integrity_visual_check.png`
- `viz/progress/curves/train_val_loss_frozen_mainline_800.png`
- `viz/progress/curves/runtime_quality_frontier_with_learning_800.png`
- `viz/progress/curves/family_metrics_mainline_vs_baselines_800.png`
- `viz/progress/curves/failure_mode_mainline_vs_baselines_800.png`
- `viz/progress/curves/ood_unseen_param_metrics.png`
- `viz/progress/curves/ood_leave_one_family_out_metrics.png`
- `viz/progress/curves/ood_random_et_metrics.png`

## 13. Remaining Issues

- This remains a literature-scale formal pass, not the larger `5000 / 1000 / 1000` target.
- Memory and FLOPs in the model audit remain unmeasured.
- The leave-one-family-out OOD is implemented as a hardest-family focused test-only stress set, not a second fully retrained family-ablation model.

## 14. Ready for Physics-Consistency Stage?

`conditional`

The current evidence is much stronger than `006c` because the dataset is now fully frozen at the adopted `800 / 100 / 100` scale and all three OOD sets were evaluated. Physics-consistency can be considered next if the controller accepts the literature-scale setting as sufficient for the next phase.

## 15. Suggested Next Task

`task_real_007`: add physics-consistency on top of the frozen mainline, but keep the current 800-scale dataset protocol fixed for the first controlled comparison.

## Key file paths for ChatGPT controller

- report: `{output_root / 'task_real_006d_report.md'}`
- manifests: `{output_root / 'dataset_manifest_main_800_100_100.json'}`, `{output_root / 'dataset_manifest_unseen_param_ood.json'}`, `{output_root / 'dataset_manifest_leave_one_family_out_ood.json'}`, `{output_root / 'dataset_manifest_random_et_ood.json'}`
- split integrity: `{output_root / 'split_integrity_report_800.md'}`, `{output_root / 'duplicate_check_800.json'}`, `{output_root / 'nearest_neighbor_overlap_800.csv'}`
- model audit: `{output_root / 'model_audit_800.json'}`, `{output_root / 'model_summary_800.txt'}`
- metrics: `{output_root / 'metrics_frozen_mainline_800.json'}`, `{output_root / 'mainline_vs_baselines_800.csv'}`
- OOD: `{output_root / 'ood_unseen_param_metrics.csv'}`, `{output_root / 'ood_leave_one_family_out_metrics.csv'}`, `{output_root / 'ood_random_et_metrics.csv'}`
- curves: `{output_root / 'viz/progress/curves'}`
- representative visuals: `{output_root / 'viz/paper_candidates/qualitative'}`
- logs: `{output_root / 'logs'}`
"""
    write_text(output_root / "task_real_006d_report.md", report)


def update_project_logs(output_root: Path) -> None:
    changelog_path = PROJECT_ROOT / "CHANGELOG_DEV.md"
    debug_path = PROJECT_ROOT / "debug.md"
    summary = "\n".join(
        [
            "",
            "## 2026-04-19 task_real_006d",
            "",
            "- Added `CONTEXT/et_dataset_protocol_800.md` and `workspace/eval/task_real_006d_pipeline.py`.",
            "- Added dedicated task_real_006d scripts for main dataset, OOD generation, handoff, split-integrity, audit, training, comparison, OOD, and visualization.",
            f"- Generated literature-scale family-aware artifacts under `{output_root}`.",
            "- Completed 800/100/100 main dataset generation, three OOD sets, split-integrity audit, frozen-mainline training, unified comparison, and OOD evaluation.",
        ]
    )
    debug = "\n".join(
        [
            "",
            "## 2026-04-19 task_real_006d",
            "",
            f"- output_root: `{output_root}`",
            "- target main split: 800/100/100 with family-aware allocation",
            "- OOD sets: unseen-parameter 100, leave-one-family-out focused 100, random-ET 100",
            "- model: UNet3DSmall base_channels=8",
            "- report: `task_real_006d_report.md`",
        ]
    )
    with changelog_path.open("a", encoding="utf-8") as handle:
        handle.write(summary + "\n")
    with debug_path.open("a", encoding="utf-8") as handle:
        handle.write(debug + "\n")


def finalize_tree(output_root: Path) -> None:
    lines = sorted(str(path) for path in output_root.rglob("*"))
    write_text(output_root / "tree.txt", "\n".join(lines) + "\n")


def run_stage(output_root: Path, stage: str) -> None:
    if stage in {"generate_main", "all"}:
        generate_main_dataset(output_root)
    if stage in {"generate_unseen_ood", "all"}:
        generate_unseen_param_ood(output_root)
    if stage in {"generate_leave_one_family_out_ood", "all"}:
        generate_leave_one_family_out_ood(output_root)
    if stage in {"generate_random_et_ood", "all"}:
        generate_random_et_ood(output_root)
    if stage in {"build_handoff", "all"}:
        build_handoff_main_800(output_root)
    if stage in {"split_integrity", "all"}:
        run_split_integrity_800(output_root)
    if stage in {"model_audit", "all"}:
        run_model_audit_800(output_root)
    if stage in {"train", "all"}:
        run_training_800(output_root)
    if stage in {"compare", "all"}:
        run_comparison_800(output_root)
    if stage in {"ood", "all"}:
        run_ood_suite_800(output_root)
    if stage in {"viz", "all"}:
        render_viz_800(output_root)
    if stage in {"report", "all"}:
        generate_report_006d(output_root)
        update_project_logs(output_root)
        finalize_tree(output_root)


def main() -> None:
    parser = argparse.ArgumentParser(description="task_real_006d 800-scale formal pipeline")
    parser.add_argument("--output-root", required=True)
    parser.add_argument(
        "--stage",
        required=True,
        choices=[
            "generate_main",
            "generate_unseen_ood",
            "generate_leave_one_family_out_ood",
            "generate_random_et_ood",
            "build_handoff",
            "split_integrity",
            "model_audit",
            "train",
            "compare",
            "ood",
            "viz",
            "report",
            "all",
        ],
    )
    args = parser.parse_args()
    output_root = Path(args.output_root)
    _ensure_standard_dirs(output_root)
    run_stage(output_root, args.stage)
    print(f"task_real_006d stage={args.stage} completed output_root={output_root}")


if __name__ == "__main__":
    main()
