from __future__ import annotations

import argparse
import math
import shutil
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

from workspace.common.io_utils import ensure_dir, write_json, write_text
from workspace.common.protocol import PROTOCOL_V1, wrap_angle
from workspace.recon.cyl_fast_reference_engine import build_ground_truth


DEFAULT_SPLITS = {"train": 192, "val": 48, "test": 48}


def _make_point(x_m: float, y_m: float, z_m: float, amplitude: float) -> dict[str, float]:
    protocol = PROTOCOL_V1
    rho_m = float(np.hypot(x_m, y_m))
    theta_rad = float(wrap_angle(np.arctan2(y_m, x_m)))
    return {
        "x_m": round(float(x_m), 6),
        "y_m": round(float(y_m), 6),
        "z_m": round(float(z_m), 6),
        "rho_m": round(rho_m, 6),
        "theta_rad": round(theta_rad, 6),
        "amplitude": round(float(amplitude), 6),
        "phase_rad": 0.0,
        "grid_x": protocol.world_to_grid_xy(float(x_m)),
        "grid_y": protocol.world_to_grid_xy(float(y_m)),
        "grid_z": protocol.world_to_grid_z(float(z_m)),
    }


def _snap_xy(value: float) -> float:
    protocol = PROTOCOL_V1
    idx = protocol.clip_xy_index(protocol.world_to_grid_xy(value))
    return float(protocol.grid_to_world_xy(idx))


def _snap_z(value: float) -> float:
    protocol = PROTOCOL_V1
    idx = protocol.clip_z_index(protocol.world_to_grid_z(value))
    return float(protocol.grid_to_world_z(idx))


def _within_scene(x_m: float, y_m: float, z_m: float) -> bool:
    protocol = PROTOCOL_V1
    return float(np.hypot(x_m, y_m)) <= protocol.scene_radius - 0.01 and -0.9 <= z_m <= 0.9


def _dedupe(points: list[tuple[float, float, float, float]]) -> list[tuple[float, float, float, float]]:
    merged: dict[tuple[float, float, float], float] = {}
    for x_m, y_m, z_m, amp in points:
        key = (round(x_m, 6), round(y_m, 6), round(z_m, 6))
        merged[key] = max(merged.get(key, 0.0), float(amp))
    return [(key[0], key[1], key[2], amp) for key, amp in merged.items()]


def _sample_global_center(rng: np.random.Generator) -> tuple[float, float, float]:
    protocol = PROTOCOL_V1
    rho_m = float(rng.uniform(0.05, protocol.scene_radius - 0.05))
    theta_rad = float(rng.uniform(-np.pi, np.pi))
    z_m = float(rng.uniform(-0.55, 0.55))
    return _snap_xy(rho_m * math.cos(theta_rad)), _snap_xy(rho_m * math.sin(theta_rad)), _snap_z(z_m)


def _build_random_et_scene(sample_id: str, split: str, seed: int) -> tuple[dict[str, Any], dict[str, Any]]:
    protocol = PROTOCOL_V1
    rng = np.random.default_rng(seed)
    center_x, center_y, center_z = _sample_global_center(rng)
    local_center_count = int(rng.integers(2, 5))
    all_points: list[tuple[float, float, float, float]] = []
    local_centers = []
    for idx in range(local_center_count):
        offset_r = float(rng.uniform(0.0, 0.05))
        offset_theta = float(rng.uniform(-np.pi, np.pi))
        offset_z = float(rng.uniform(-0.06, 0.06))
        cx = center_x + offset_r * math.cos(offset_theta)
        cy = center_y + offset_r * math.sin(offset_theta)
        cz = center_z + offset_z
        cx = _snap_xy(cx)
        cy = _snap_xy(cy)
        cz = _snap_z(cz)
        local_centers.append((cx, cy, cz))
        cloud_points = int(rng.integers(6, 18))
        spatial_sigma_xy = float(rng.uniform(0.006, 0.018))
        spatial_sigma_z = float(rng.uniform(0.004, 0.020))
        for _ in range(cloud_points):
            x_m = _snap_xy(cx + float(rng.normal(0.0, spatial_sigma_xy)))
            y_m = _snap_xy(cy + float(rng.normal(0.0, spatial_sigma_xy)))
            z_m = _snap_z(cz + float(rng.normal(0.0, spatial_sigma_z)))
            if not _within_scene(x_m, y_m, z_m):
                continue
            amp = float(np.clip(rng.uniform(0.55, 1.25), 0.55, 1.25))
            all_points.append((x_m, y_m, z_m, amp))
        if idx > 0 and rng.random() < 0.65:
            px, py, pz = local_centers[idx - 1]
            qx, qy, qz = local_centers[idx]
            steps = int(rng.integers(3, 7))
            for alpha in np.linspace(0.0, 1.0, steps):
                x_m = _snap_xy((1.0 - alpha) * px + alpha * qx)
                y_m = _snap_xy((1.0 - alpha) * py + alpha * qy)
                z_m = _snap_z((1.0 - alpha) * pz + alpha * qz)
                if _within_scene(x_m, y_m, z_m):
                    all_points.append((x_m, y_m, z_m, float(rng.uniform(0.60, 1.00))))
    all_points = _dedupe(all_points)
    points = [_make_point(x_m, y_m, z_m, amp) for x_m, y_m, z_m, amp in all_points]
    scene = {
        "sample_id": sample_id,
        "split": split,
        "seed": seed,
        "smoke": False,
        "scene_type": "manisali_style_random_extended_target",
        "family": "random_et",
        "shape_params": {
            "local_center_count": local_center_count,
            "point_count": len(points),
            "generation_style": "local_centers + clustered points + sparse bridges",
        },
        "placement": {
            "center_x_m": round(center_x, 6),
            "center_y_m": round(center_y, 6),
            "center_z_m": round(center_z, 6),
        },
        "scatter_rule": {"amplitude_range": [0.55, 1.25], "phase_randomized": False},
        "point_count": len(points),
        "points": points,
    }
    metadata = {
        "local_center_count": local_center_count,
        "point_count": len(points),
        "center_rho_m": round(float(np.hypot(center_x, center_y)), 6),
        "near_edge": bool(float(np.hypot(center_x, center_y)) >= 0.22),
    }
    return scene, metadata


def build_random_et_dataset(
    output_root: Path,
    project_root: Path,
    split_sizes: dict[str, int],
    base_seed: int,
) -> dict[str, Any]:
    dataset_dir = ensure_dir(output_root / "dataset")
    scene_root = ensure_dir(dataset_dir / "scenes")
    gt_root = ensure_dir(dataset_dir / "gt_volumes")
    index: list[dict[str, Any]] = []
    split_counts = Counter()
    sample_counter = 0
    for split, count in split_sizes.items():
        split_dir = ensure_dir(scene_root / split)
        for offset in range(count):
            seed = base_seed + sample_counter
            sample_id = f"random_et_{split}_{offset:05d}"
            scene, metadata = _build_random_et_scene(sample_id=sample_id, split=split, seed=seed)
            scene_path = split_dir / f"{sample_id}.json"
            write_json(scene_path, scene)
            gt = build_ground_truth(scene)
            gt_path = gt_root / f"{sample_id}_gt.npz"
            np.savez_compressed(
                gt_path,
                volume=gt["volume"],
                x_values=gt["x_values"],
                y_values=gt["y_values"],
                z_values=gt["z_values"],
            )
            index.append(
                {
                    "sample_id": sample_id,
                    "split": split,
                    "seed": seed,
                    "family": "random_et",
                    "scene_path": str(scene_path.relative_to(output_root)),
                    "gt_volume_path": str(gt_path.relative_to(output_root)),
                    "point_count": metadata["point_count"],
                    "center_rho_m": metadata["center_rho_m"],
                    "near_edge": metadata["near_edge"],
                    "shape_params": scene["shape_params"],
                }
            )
            split_counts[split] += 1
            sample_counter += 1
    write_json(dataset_dir / "index.json", index)
    manifest = {
        "dataset_name": "task_real_006_random_et_supplement",
        "dataset_type": "manisali_style_random_extended_target",
        "split_sizes": split_sizes,
        "counts_by_split": {split: int(split_counts[split]) for split in split_sizes},
        "total_samples": len(index),
        "index_path": "dataset/index.json",
        "gt_definition": "voxel truth amplitude volume",
        "forward_simulator_entry": "workspace.sim.forward_cylindrical_point",
        "reconstruction_entry": "workspace.recon.cyl_fast_reference_engine.reconstruct_cylindrical_reference(method='ref3')",
    }
    write_json(output_root / "dataset_manifest.json", manifest)
    shutil.copyfile(project_root / "CONTEXT" / "et_dataset_protocol.md", output_root / "dataset_protocol_snapshot.md")
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
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the task_real_006 random extended-target supplement dataset.")
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--train-count", type=int, default=DEFAULT_SPLITS["train"])
    parser.add_argument("--val-count", type=int, default=DEFAULT_SPLITS["val"])
    parser.add_argument("--test-count", type=int, default=DEFAULT_SPLITS["test"])
    parser.add_argument("--base-seed", type=int, default=20260417)
    args = parser.parse_args()
    manifest = build_random_et_dataset(
        output_root=Path(args.output_root),
        project_root=Path(args.project_root),
        split_sizes={"train": args.train_count, "val": args.val_count, "test": args.test_count},
        base_seed=args.base_seed,
    )
    print(f"Built random ET dataset total_samples={manifest['total_samples']}")


if __name__ == "__main__":
    main()
