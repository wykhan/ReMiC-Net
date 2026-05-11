from __future__ import annotations

import argparse
import math
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from workspace.common.io_utils import ensure_dir, write_json, write_text
from workspace.common.protocol import PROTOCOL_V1, wrap_angle
from workspace.recon.cyl_fast_reference_engine import build_ground_truth


FAMILIES = ["line", "cross", "L-shape", "double-line", "small_rect_edge", "point_cluster"]
DEFAULT_SPLIT_SIZES = {"train": 16, "val": 4, "test": 4}


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


def _within_scene(x_m: float, y_m: float, z_m: float, radial_margin: float = 0.01) -> bool:
    protocol = PROTOCOL_V1
    rho_m = float(np.hypot(x_m, y_m))
    return (
        rho_m <= protocol.scene_radius - radial_margin
        and -0.9 <= z_m <= 0.9
    )


def _dedupe_points(points: list[tuple[float, float, float, float]]) -> list[tuple[float, float, float, float]]:
    deduped: dict[tuple[float, float, float], float] = {}
    for x_m, y_m, z_m, amp in points:
        key = (round(x_m, 6), round(y_m, 6), round(z_m, 6))
        deduped[key] = max(deduped.get(key, 0.0), float(amp))
    return [(key[0], key[1], key[2], amp) for key, amp in deduped.items()]


def _transform_local_points(
    local_points: list[tuple[float, float, float, float]],
    center_xy: tuple[float, float],
    center_z: float,
    angle_rad: float,
) -> list[tuple[float, float, float, float]] | None:
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    transformed: list[tuple[float, float, float, float]] = []
    for x_l, y_l, z_l, amp in local_points:
        x_m = _snap_xy(center_xy[0] + x_l * cos_a - y_l * sin_a)
        y_m = _snap_xy(center_xy[1] + x_l * sin_a + y_l * cos_a)
        z_m = _snap_z(center_z + z_l)
        if not _within_scene(x_m, y_m, z_m):
            return None
        transformed.append((x_m, y_m, z_m, amp))
    return _dedupe_points(transformed)


def _sample_center(rng: np.random.Generator, prefer_edge: bool) -> tuple[tuple[float, float], float, float]:
    protocol = PROTOCOL_V1
    if prefer_edge:
        rho_m = float(rng.uniform(0.20, protocol.scene_radius - 0.03))
    else:
        rho_m = float(rng.uniform(0.05, 0.22))
    theta_rad = float(rng.uniform(-np.pi, np.pi))
    z_m = _snap_z(float(rng.uniform(-0.65, 0.65)))
    center_xy = (_snap_xy(rho_m * math.cos(theta_rad)), _snap_xy(rho_m * math.sin(theta_rad)))
    return center_xy, z_m, theta_rad


def _amp_profile(rng: np.random.Generator, num_points: int, base_low: float = 0.65, base_high: float = 1.20) -> np.ndarray:
    start = float(rng.uniform(base_low, 0.95))
    stop = float(rng.uniform(0.95, base_high))
    profile = np.linspace(start, stop, max(num_points, 1), dtype=np.float64)
    jitter = rng.uniform(-0.06, 0.06, size=profile.shape)
    return np.clip(profile + jitter, 0.55, 1.25).astype(np.float32)


def _local_line_points(
    rng: np.random.Generator,
    length_vox: int,
    width_vox: int,
    z_layers: int,
    allow_gap: bool,
) -> tuple[list[tuple[float, float, float, float]], dict[str, Any]]:
    protocol = PROTOCOL_V1
    s_coords = np.arange(-(length_vox // 2), length_vox // 2 + 1, dtype=np.int32)
    if allow_gap and len(s_coords) >= 7 and rng.random() < 0.55:
        gap_center = int(rng.integers(-1, 2))
        gap_half = int(rng.integers(0, 2))
        mask = np.abs(s_coords - gap_center) > gap_half
        s_coords = s_coords[mask]
    t_coords = np.arange(-(width_vox // 2), width_vox // 2 + 1, dtype=np.int32)
    z_offsets = [0] if z_layers == 1 else [-1, 0]
    amps = _amp_profile(rng, len(s_coords))
    points: list[tuple[float, float, float, float]] = []
    for s_idx, s_val in enumerate(s_coords):
        for t_val in t_coords:
            for z_off in z_offsets:
                points.append(
                    (
                        float(s_val * protocol.xy_spacing),
                        float(t_val * protocol.xy_spacing),
                        float(z_off * protocol.height_spacing),
                        float(amps[s_idx]),
                    )
                )
    params = {
        "length_vox": int(length_vox),
        "width_vox": int(width_vox),
        "z_layers": int(z_layers),
        "gap_enabled": bool(allow_gap and len(s_coords) < length_vox + 1),
    }
    return points, params


def _build_line(rng: np.random.Generator) -> tuple[list[tuple[float, float, float, float]], dict[str, Any]]:
    points, params = _local_line_points(
        rng=rng,
        length_vox=int(rng.integers(6, 14)),
        width_vox=int(rng.integers(1, 3)),
        z_layers=int(rng.choice([1, 2], p=[0.75, 0.25])),
        allow_gap=True,
    )
    params["family"] = "line"
    return points, params


def _build_cross(rng: np.random.Generator) -> tuple[list[tuple[float, float, float, float]], dict[str, Any]]:
    protocol = PROTOCOL_V1
    arm_a = int(rng.integers(5, 11))
    arm_b = int(rng.integers(5, 11))
    width = int(rng.integers(1, 3))
    base_a, params_a = _local_line_points(rng, arm_a, width, 1, allow_gap=False)
    base_b, params_b = _local_line_points(rng, arm_b, width, 1, allow_gap=False)
    points = base_a[:]
    for x_l, y_l, z_l, amp in base_b:
        points.append((-y_l, x_l, z_l + float(protocol.height_spacing * int(rng.choice([0, 1]))), amp))
    params = {
        "family": "cross",
        "arm_a_vox": params_a["length_vox"],
        "arm_b_vox": params_b["length_vox"],
        "width_vox": width,
    }
    return _dedupe_points(points), params


def _build_l_shape(rng: np.random.Generator) -> tuple[list[tuple[float, float, float, float]], dict[str, Any]]:
    protocol = PROTOCOL_V1
    length_a = int(rng.integers(5, 11))
    length_b = int(rng.integers(4, 10))
    width = int(rng.integers(1, 3))
    amps_a = _amp_profile(rng, length_a + 1)
    amps_b = _amp_profile(rng, length_b + 1)
    t_coords = np.arange(-(width // 2), width // 2 + 1, dtype=np.int32)
    points: list[tuple[float, float, float, float]] = []
    for idx, s_val in enumerate(range(0, length_a + 1)):
        for t_val in t_coords:
            points.append((float(s_val * protocol.xy_spacing), float(t_val * protocol.xy_spacing), 0.0, float(amps_a[idx])))
    for idx, s_val in enumerate(range(0, length_b + 1)):
        for t_val in t_coords:
            points.append((float(t_val * protocol.xy_spacing), float(s_val * protocol.xy_spacing), 0.0, float(amps_b[idx])))
    params = {"family": "L-shape", "arm_x_vox": length_a, "arm_y_vox": length_b, "width_vox": width}
    return _dedupe_points(points), params


def _build_double_line(rng: np.random.Generator) -> tuple[list[tuple[float, float, float, float]], dict[str, Any]]:
    protocol = PROTOCOL_V1
    length_vox = int(rng.integers(6, 13))
    gap_vox = int(rng.integers(2, 6))
    width_vox = int(rng.integers(1, 3))
    z_shift = int(rng.choice([0, 1]))
    base, _params = _local_line_points(rng, length_vox, width_vox, 1, allow_gap=False)
    points = []
    amp_scale = float(rng.uniform(0.70, 1.00))
    for x_l, y_l, z_l, amp in base:
        points.append((x_l, y_l - gap_vox * protocol.xy_spacing * 0.5, z_l, amp))
        points.append((x_l, y_l + gap_vox * protocol.xy_spacing * 0.5, z_l + z_shift * protocol.height_spacing, amp * amp_scale))
    params = {
        "family": "double-line",
        "length_vox": length_vox,
        "width_vox": width_vox,
        "gap_vox": gap_vox,
        "secondary_amp_scale": round(amp_scale, 4),
    }
    return _dedupe_points(points), params


def _build_small_rect_edge(rng: np.random.Generator) -> tuple[list[tuple[float, float, float, float]], dict[str, Any]]:
    protocol = PROTOCOL_V1
    width_vox = int(rng.integers(5, 9))
    height_vox = int(rng.integers(4, 8))
    open_edge = str(rng.choice(["none", "top", "right"]))
    amps = _amp_profile(rng, 4)
    points: list[tuple[float, float, float, float]] = []
    x_range = np.arange(-(width_vox // 2), width_vox // 2 + 1, dtype=np.int32)
    y_range = np.arange(-(height_vox // 2), height_vox // 2 + 1, dtype=np.int32)
    for x_idx in x_range:
        if open_edge != "top":
            points.append((float(x_idx * protocol.xy_spacing), float(y_range[-1] * protocol.xy_spacing), 0.0, float(amps[0])))
        points.append((float(x_idx * protocol.xy_spacing), float(y_range[0] * protocol.xy_spacing), 0.0, float(amps[1])))
    for y_idx in y_range:
        if open_edge != "right":
            points.append((float(x_range[-1] * protocol.xy_spacing), float(y_idx * protocol.xy_spacing), 0.0, float(amps[2])))
        points.append((float(x_range[0] * protocol.xy_spacing), float(y_idx * protocol.xy_spacing), 0.0, float(amps[3])))
    params = {
        "family": "small_rect_edge",
        "rect_width_vox": width_vox,
        "rect_height_vox": height_vox,
        "open_edge": open_edge,
    }
    return _dedupe_points(points), params


def _build_point_cluster(rng: np.random.Generator) -> tuple[list[tuple[float, float, float, float]], dict[str, Any]]:
    protocol = PROTOCOL_V1
    cluster_count = int(rng.choice([1, 2], p=[0.7, 0.3]))
    points: list[tuple[float, float, float, float]] = []
    cluster_specs = []
    for cluster_idx in range(cluster_count):
        center_x = float(rng.integers(-3, 4)) * protocol.xy_spacing * (1.5 if cluster_idx == 1 else 1.0)
        center_y = float(rng.integers(-3, 4)) * protocol.xy_spacing * (1.5 if cluster_idx == 1 else 1.0)
        center_z = float(rng.integers(-2, 3)) * protocol.height_spacing
        count = int(rng.integers(5, 11))
        amp_scale = float(rng.uniform(0.75, 1.10))
        cluster_specs.append(
            {
                "count": count,
                "center_offset_xy": [round(center_x, 4), round(center_y, 4)],
                "center_offset_z": round(center_z, 4),
                "amp_scale": round(amp_scale, 4),
            }
        )
        for _ in range(count):
            x_m = center_x + float(rng.integers(-2, 3)) * protocol.xy_spacing
            y_m = center_y + float(rng.integers(-2, 3)) * protocol.xy_spacing
            z_m = center_z + float(rng.integers(-1, 2)) * protocol.height_spacing
            amp = float(rng.uniform(0.60, 1.20) * amp_scale)
            points.append((x_m, y_m, z_m, min(1.25, amp)))
    params = {"family": "point_cluster", "cluster_count": cluster_count, "cluster_specs": cluster_specs}
    return _dedupe_points(points), params


FAMILY_BUILDERS = {
    "line": _build_line,
    "cross": _build_cross,
    "L-shape": _build_l_shape,
    "double-line": _build_double_line,
    "small_rect_edge": _build_small_rect_edge,
    "point_cluster": _build_point_cluster,
}


def _build_family_scene(sample_id: str, split: str, seed: int, family: str) -> tuple[dict[str, Any], dict[str, Any]]:
    rng = np.random.default_rng(seed)
    prefer_edge = family == "small_rect_edge" or bool(rng.random() < 0.35)
    local_points, family_params = FAMILY_BUILDERS[family](rng)
    for _ in range(256):
        center_xy, center_z, theta_center = _sample_center(rng, prefer_edge=prefer_edge)
        angle_rad = float(rng.choice([0.0, np.pi / 6.0, np.pi / 4.0, np.pi / 3.0, np.pi / 2.0, 3.0 * np.pi / 4.0]))
        transformed = _transform_local_points(local_points, center_xy=center_xy, center_z=center_z, angle_rad=angle_rad)
        if transformed is None or len(transformed) < 4:
            continue
        points = [_make_point(x_m, y_m, z_m, amp) for x_m, y_m, z_m, amp in transformed]
        center_rho = float(np.hypot(center_xy[0], center_xy[1]))
        scene = {
            "sample_id": sample_id,
            "split": split,
            "seed": seed,
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
            },
            "scatter_rule": {"amplitude_range": [0.55, 1.25], "phase_randomized": False},
            "point_count": len(points),
            "points": points,
        }
        metadata = {
            "family": family,
            "shape_params": family_params,
            "split": split,
            "seed": seed,
            "point_count": len(points),
            "center_rho_m": round(center_rho, 6),
            "center_theta_rad": round(theta_center, 6),
            "center_z_m": round(center_z, 6),
            "orientation_rad": round(angle_rad, 6),
            "near_edge": bool(center_rho >= 0.22 or family == "small_rect_edge"),
        }
        return scene, metadata
    raise RuntimeError(f"Failed to place ET family sample family={family} sample_id={sample_id}")


def build_et_shape_family_dataset(
    output_root: Path,
    project_root: Path,
    split_sizes: dict[str, int],
    base_seed: int,
) -> dict[str, Any]:
    dataset_dir = ensure_dir(output_root / "dataset")
    scenes_root = ensure_dir(dataset_dir / "scenes")
    gt_root = ensure_dir(dataset_dir / "gt_volumes")
    index: list[dict[str, Any]] = []
    family_counts = Counter()
    split_counts = Counter()
    family_split_counts: dict[str, dict[str, int]] = defaultdict(dict)
    sample_counter = 0

    for family in FAMILIES:
        for split, split_count in split_sizes.items():
            split_dir = ensure_dir(scenes_root / split / family)
            for offset in range(split_count):
                seed = base_seed + sample_counter
                sample_id = f"{family.replace('-', '_')}_{split}_{offset:04d}"
                scene, metadata = _build_family_scene(sample_id=sample_id, split=split, seed=seed, family=family)
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
                row = {
                    "sample_id": sample_id,
                    "split": split,
                    "seed": seed,
                    "family": family,
                    "scene_path": str(scene_path.relative_to(output_root)),
                    "gt_volume_path": str(gt_path.relative_to(output_root)),
                    "point_count": metadata["point_count"],
                    "center_rho_m": metadata["center_rho_m"],
                    "center_theta_rad": metadata["center_theta_rad"],
                    "center_z_m": metadata["center_z_m"],
                    "orientation_rad": metadata["orientation_rad"],
                    "near_edge": metadata["near_edge"],
                    "shape_params": metadata["shape_params"],
                }
                index.append(row)
                family_counts[family] += 1
                split_counts[split] += 1
                family_split_counts[family][split] = family_split_counts[family].get(split, 0) + 1
                sample_counter += 1

    write_json(dataset_dir / "index.json", index)
    dataset_manifest = {
        "dataset_name": "task_real_005_shape_family_et_phase1",
        "dataset_type": "shape_family_extended_target",
        "protocol_snapshot_source": "CONTEXT/et_dataset_protocol.md",
        "family_names": FAMILIES,
        "split_sizes_per_family": split_sizes,
        "counts_by_family": {family: int(family_counts[family]) for family in FAMILIES},
        "counts_by_split": {split: int(split_counts[split]) for split in split_sizes},
        "counts_by_family_split": {family: family_split_counts[family] for family in FAMILIES},
        "total_samples": len(index),
        "gt_definition": "voxel truth amplitude volume",
        "forward_simulator_entry": "workspace.sim.forward_cylindrical_point",
        "reconstruction_entries": {
            "variantB": "workspace.recon.cyl_fast_reference_engine.reconstruct_cylindrical_reference",
            "bp": "workspace.recon.cyl_fast_reference_engine.reconstruct_cylindrical_reference(method='BP')",
        },
        "baseline_methods": ["ref3", "ref5", "ref7", "ref9", "BP"],
        "scale_statement": "Reduced ET-1 executed scale frozen for task_real_005 to keep the first full true-cylindrical ET baseline pass tractable.",
        "index_path": "dataset/index.json",
    }
    write_json(output_root / "dataset_manifest.json", dataset_manifest)
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
                "- ET protocol freeze: `CONTEXT/et_dataset_protocol.md`",
                "- Reconstruction entry: `workspace.recon.cyl_fast_reference_engine.reconstruct_cylindrical_reference`",
                "- Frozen accelerated front-end: `Variant B = active windows + full-library sinc geometry correction`",
                "- BP role: high-quality traditional baseline only",
                "- Statement: these samples are not 2D proxy family patterns and not manually fabricated pseudo-reference images",
            ]
        ),
    )
    return dataset_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Phase ET-1 shape-family extended-target dataset.")
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--train-per-family", type=int, default=DEFAULT_SPLIT_SIZES["train"])
    parser.add_argument("--val-per-family", type=int, default=DEFAULT_SPLIT_SIZES["val"])
    parser.add_argument("--test-per-family", type=int, default=DEFAULT_SPLIT_SIZES["test"])
    parser.add_argument("--base-seed", type=int, default=20260416)
    args = parser.parse_args()
    split_sizes = {
        "train": int(args.train_per_family),
        "val": int(args.val_per_family),
        "test": int(args.test_per_family),
    }
    manifest = build_et_shape_family_dataset(
        output_root=Path(args.output_root),
        project_root=Path(args.project_root),
        split_sizes=split_sizes,
        base_seed=args.base_seed,
    )
    print(f"Built ET shape-family dataset total_samples={manifest['total_samples']}")


if __name__ == "__main__":
    main()
