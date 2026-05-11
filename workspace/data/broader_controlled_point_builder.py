from __future__ import annotations

import argparse
import math
import shutil
from pathlib import Path

import numpy as np

from workspace.common.io_utils import ensure_dir, write_json, write_text
from workspace.common.protocol import PROTOCOL_V1
from workspace.data.point_scene_generator import SampleConfig, generate_point_scene


def _base_scene(sample_id: str, split: str, seed: int) -> dict:
    return generate_point_scene(SampleConfig(sample_id=sample_id, split=split, seed=seed, smoke=True))


def _make_point(rho_m: float, theta_rad: float, z_m: float, amplitude: float = 1.0) -> dict:
    protocol = PROTOCOL_V1
    x_m = float(rho_m * math.cos(theta_rad))
    y_m = float(rho_m * math.sin(theta_rad))
    return {
        "x_m": round(x_m, 6),
        "y_m": round(y_m, 6),
        "z_m": round(z_m, 6),
        "rho_m": round(rho_m, 6),
        "theta_rad": round(theta_rad, 6),
        "amplitude": float(amplitude),
        "phase_rad": 0.0,
        "grid_x": protocol.world_to_grid_xy(x_m),
        "grid_y": protocol.world_to_grid_xy(y_m),
        "grid_z": protocol.world_to_grid_z(z_m),
    }


def _single_point_scene(sample_id: str, split: str, seed: int, rho_m: float, theta_rad: float, z_m: float, amplitude: float = 1.0) -> dict:
    scene = _base_scene(sample_id=sample_id, split=split, seed=seed)
    scene.update(
        {
            "point_count": 1,
            "points": [_make_point(rho_m=rho_m, theta_rad=theta_rad, z_m=z_m, amplitude=amplitude)],
        }
    )
    return scene


def _double_point_scene(sample_id: str, split: str, seed: int, points: list[tuple[float, float, float, float]]) -> dict:
    scene = _base_scene(sample_id=sample_id, split=split, seed=seed)
    point_dicts = [_make_point(rho_m=rho, theta_rad=theta, z_m=z, amplitude=amp) for rho, theta, z, amp in points]
    scene.update({"point_count": len(point_dicts), "points": point_dicts})
    return scene


def build_broader_controlled_point_suite(output_root: Path, project_root: Path) -> dict:
    protocol = PROTOCOL_V1
    du = float(protocol.azimuth_values[1] - protocol.azimuth_values[0])
    scene_root = ensure_dir(output_root / "dataset" / "scenes" / "controlled_broader")
    manifest_rows: list[dict] = []
    seed = 5100
    sample_index = 0

    def add_scene(scene: dict, metadata: dict) -> None:
        nonlocal sample_index
        path = scene_root / f"{scene['sample_id']}.json"
        write_json(path, scene)
        row = {
            "sample_id": scene["sample_id"],
            "split": "controlled_broader",
            "scene_path": str(path.relative_to(output_root)),
            "du_rad": du,
        }
        row.update(metadata)
        manifest_rows.append(row)
        sample_index += 1

    # 31 samples
    for idx in range(31):
        rho = idx * 0.01
        sample_id = f"rho_{idx:03d}"
        scene = _single_point_scene(sample_id=sample_id, split="controlled_broader", seed=seed + sample_index, rho_m=rho, theta_rad=0.0, z_m=0.0)
        add_scene(
            scene,
            {
                "control_group": "rho_sweep",
                "rho_target_m": rho,
                "theta_target_rad": 0.0,
                "z_target_m": 0.0,
                "point_count_group": "single_point",
                "seam_subset": False,
                "non_seam_subset": True,
                "inner_radius_subset": rho <= 0.10,
                "outer_radius_subset": rho >= 0.24,
                "height_edge_subset": False,
                "double_point_subset": False,
            },
        )

    # 21 samples
    azimuth_specs = [
        ("inner", 0.10, -np.pi),
        ("inner", 0.10, -np.pi + du),
        ("inner", 0.10, -np.pi + 2.0 * du),
        ("inner", 0.10, np.pi - 2.0 * du),
        ("inner", 0.10, np.pi - du),
        ("inner", 0.10, np.pi),
        ("inner", 0.10, 0.0),
        ("mid", 0.20, -np.pi),
        ("mid", 0.20, -np.pi + du),
        ("mid", 0.20, -np.pi + 2.0 * du),
        ("mid", 0.20, np.pi - 2.0 * du),
        ("mid", 0.20, np.pi - du),
        ("mid", 0.20, np.pi),
        ("mid", 0.20, 0.0),
        ("outer", 0.28, -np.pi),
        ("outer", 0.28, -np.pi + du),
        ("outer", 0.28, -np.pi + 2.0 * du),
        ("outer", 0.28, np.pi - 2.0 * du),
        ("outer", 0.28, np.pi - du),
        ("outer", 0.28, np.pi),
        ("outer", 0.28, 0.0),
    ]
    for radius_name, rho, theta in azimuth_specs:
        offset_name = (
            "negpi_exact" if abs(theta + np.pi) < 1.0e-12 else
            "negpi_p1" if abs(theta - (-np.pi + du)) < 1.0e-12 else
            "negpi_p2" if abs(theta - (-np.pi + 2.0 * du)) < 1.0e-12 else
            "pi_m2" if abs(theta - (np.pi - 2.0 * du)) < 1.0e-12 else
            "pi_m1" if abs(theta - (np.pi - du)) < 1.0e-12 else
            "pi_exact" if abs(theta - np.pi) < 1.0e-12 else
            "center_zero"
        )
        sample_id = f"az_{radius_name}_{offset_name}"
        scene = _single_point_scene(sample_id=sample_id, split="controlled_broader", seed=seed + sample_index, rho_m=rho, theta_rad=float(theta), z_m=0.0)
        add_scene(
            scene,
            {
                "control_group": "azimuth_control",
                "rho_target_m": rho,
                "theta_target_rad": float(theta),
                "z_target_m": 0.0,
                "point_count_group": "single_point",
                "seam_subset": offset_name.startswith("negpi") or offset_name.startswith("pi_"),
                "non_seam_subset": not (offset_name.startswith("negpi") or offset_name.startswith("pi_")),
                "inner_radius_subset": rho <= 0.10,
                "outer_radius_subset": rho >= 0.24,
                "height_edge_subset": False,
                "double_point_subset": False,
            },
        )

    # 10 samples
    for radius_name, rho in [("inner", 0.10), ("outer", 0.28)]:
        for z_name, z_val in [("low", -0.72), ("midlow", -0.36), ("mid", 0.0), ("midhigh", 0.36), ("high", 0.72)]:
            sample_id = f"z_{radius_name}_{z_name}"
            scene = _single_point_scene(sample_id=sample_id, split="controlled_broader", seed=seed + sample_index, rho_m=rho, theta_rad=0.0, z_m=z_val)
            add_scene(
                scene,
                {
                    "control_group": "height_control",
                    "rho_target_m": rho,
                    "theta_target_rad": 0.0,
                    "z_target_m": z_val,
                    "point_count_group": "single_point",
                    "seam_subset": False,
                    "non_seam_subset": True,
                    "inner_radius_subset": rho <= 0.10,
                    "outer_radius_subset": rho >= 0.24,
                    "height_edge_subset": abs(z_val) >= 0.72,
                    "double_point_subset": False,
                },
            )

    # 8 samples
    double_specs = [
        ("double_inner_center", [(0.08, 0.0, 0.0, 1.0), (0.11, 0.10, 0.0, 0.9)]),
        ("double_inner_seam", [(0.08, -np.pi + du, 0.0, 1.0), (0.12, -np.pi + 2.0 * du, 0.0, 0.9)]),
        ("double_mid_center", [(0.18, 0.0, 0.0, 1.0), (0.22, 0.25, 0.0, 0.9)]),
        ("double_mid_height", [(0.18, 0.0, -0.20, 1.0), (0.22, 0.0, 0.20, 0.9)]),
        ("double_outer_center", [(0.25, 0.0, 0.0, 1.0), (0.28, 0.30, 0.0, 0.9)]),
        ("double_outer_seam", [(0.25, -np.pi + du, 0.0, 1.0), (0.28, -np.pi + 2.0 * du, 0.0, 0.9)]),
        ("double_outer_height", [(0.25, 0.0, -0.72, 1.0), (0.28, 0.0, 0.72, 0.9)]),
        ("double_mixed_diag", [(0.10, np.pi / 2.0, -0.36, 1.0), (0.26, 0.0, 0.36, 0.9)]),
    ]
    for sample_id, points in double_specs:
        scene = _double_point_scene(sample_id=sample_id, split="controlled_broader", seed=seed + sample_index, points=points)
        rho_values = [pt[0] for pt in points]
        z_values = [pt[2] for pt in points]
        theta_values = [pt[1] for pt in points]
        add_scene(
            scene,
            {
                "control_group": "double_point_control",
                "rho_target_m": float(np.mean(rho_values)),
                "theta_target_rad": float(np.mean(theta_values)),
                "z_target_m": float(np.mean(z_values)),
                "point_count_group": "double_point",
                "seam_subset": any(abs(theta + np.pi) < 3.0 * du for theta in theta_values),
                "non_seam_subset": not any(abs(theta + np.pi) < 3.0 * du for theta in theta_values),
                "inner_radius_subset": max(rho_values) <= 0.12,
                "outer_radius_subset": max(rho_values) >= 0.24,
                "height_edge_subset": any(abs(z) >= 0.72 for z in z_values),
                "double_point_subset": True,
            },
        )

    write_json(output_root / "dataset" / "index.json", manifest_rows)
    write_json(
        output_root / "dataset_manifest.json",
        {
            "dataset_name": "task_real_004c_broader_controlled_point_suite",
            "split_names": ["controlled_broader"],
            "counts_by_group": {
                "rho_sweep": 31,
                "azimuth_control": 21,
                "height_control": 10,
                "double_point_control": 8,
            },
            "total_samples": len(manifest_rows),
            "index_path": "dataset/index.json",
            "default_frontend_variant": "Variant B",
        },
    )
    shutil.copyfile(project_root / "CONTEXT" / "dataset_protocol.md", output_root / "dataset_protocol_snapshot.md")
    write_text(
        output_root / "data_origin_statement.md",
        "\n".join(
            [
                "# data_origin_statement",
                "",
                "- Data type: true 3D cylindrical simulation data",
                "- Forward simulator entry: `workspace.sim.forward_cylindrical_point`",
                "- Geometry protocol version: protocol v1 from `CONTEXT/simulation_protocol.md`",
                "- Reconstruction entry: default Variant B via `workspace.recon.cyl_fast_reference_engine.reconstruct_cylindrical_reference`",
                "- Default front-end: `tensor_mode=active`, `geom_mode=sinc`",
                "- Statement: data are not 2D proxy patterns and not manually fabricated pseudo-reference images",
            ]
        ),
    )
    return {"total_samples": len(manifest_rows)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build broader controlled point suite for Variant B confirmation.")
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()
    summary = build_broader_controlled_point_suite(Path(args.output_root), Path(args.project_root))
    print(f"Built broader controlled point suite with {summary['total_samples']} samples")


if __name__ == "__main__":
    main()
