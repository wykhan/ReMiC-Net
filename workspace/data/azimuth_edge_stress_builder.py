from __future__ import annotations

import argparse
import math
import shutil
from pathlib import Path

import numpy as np

from workspace.common.io_utils import ensure_dir, write_json, write_text
from workspace.common.protocol import PROTOCOL_V1
from workspace.data.point_scene_generator import SampleConfig, generate_point_scene


def _single_point_scene(sample_id: str, split: str, seed: int, rho_m: float, theta_rad: float, z_m: float, tag: str) -> dict:
    base = generate_point_scene(SampleConfig(sample_id=sample_id, split=split, seed=seed, smoke=True))
    base.update(
        {
            "point_count": 1,
            "controlled_tag": tag,
            "points": [
                {
                    "x_m": round(rho_m * math.cos(theta_rad), 6),
                    "y_m": round(rho_m * math.sin(theta_rad), 6),
                    "z_m": round(z_m, 6),
                    "rho_m": round(rho_m, 6),
                    "theta_rad": round(theta_rad, 6),
                    "amplitude": 1.0,
                    "phase_rad": 0.0,
                }
            ],
        }
    )
    return base


def build_azimuth_edge_stress_dataset(output_root: Path, project_root: Path) -> dict:
    protocol = PROTOCOL_V1
    du = float(protocol.azimuth_values[1] - protocol.azimuth_values[0])
    scene_root = ensure_dir(output_root / "dataset" / "scenes" / "edge_stress")
    manifest_rows: list[dict] = []
    seed = 4100
    sample_specs = [
        ("inner", "mid", 0.05, 0.0, "negpi_exact", -np.pi),
        ("inner", "mid", 0.05, 0.0, "pi_exact", np.pi),
        ("mid", "high", 0.15, 0.72, "negpi_p1", -np.pi + du),
        ("mid", "high", 0.15, 0.72, "pi_m1", np.pi - du),
        ("outer", "low", 0.28, -0.72, "negpi_p2", -np.pi + 2.0 * du),
        ("outer", "low", 0.28, -0.72, "pi_m2", np.pi - 2.0 * du),
    ]

    sample_index = 0
    offset_steps = {
        "negpi_exact": 0,
        "negpi_p1": 1,
        "negpi_p2": 2,
        "pi_m2": 2,
        "pi_m1": 1,
        "pi_exact": 0,
    }
    for radius_name, height_name, rho_m, z_m, offset_name, theta_rad in sample_specs:
        pair_group = f"{radius_name}_{height_name}"
        sample_id = f"{pair_group}_{offset_name}"
        scene = _single_point_scene(
            sample_id=sample_id,
            split="edge_stress",
            seed=seed + sample_index,
            rho_m=rho_m,
            theta_rad=float(theta_rad),
            z_m=z_m,
            tag="azimuth_edge_stress",
        )
        path = scene_root / f"{sample_id}.json"
        write_json(path, scene)
        manifest_rows.append(
            {
                "sample_id": sample_id,
                "split": "edge_stress",
                "scene_path": str(path.relative_to(output_root)),
                "control_group": "azimuth_edge_stress",
                "stress_radius_group": radius_name,
                "stress_height_group": height_name,
                "stress_pair_group": pair_group,
                "stress_offset_name": offset_name,
                "stress_offset_steps": offset_steps[offset_name],
                "rho_target_m": rho_m,
                "theta_target_rad": float(theta_rad),
                "z_target_m": z_m,
                "du_rad": du,
                "is_edge_subset": True,
            }
        )
        sample_index += 1

    write_json(output_root / "dataset" / "index.json", manifest_rows)
    write_json(
        output_root / "dataset_manifest.json",
        {
            "dataset_name": "task_real_004b_azimuth_edge_stress_set",
            "split_names": ["edge_stress"],
            "counts_by_group": {"azimuth_edge_stress": len(manifest_rows)},
            "total_samples": len(manifest_rows),
            "index_path": "dataset/index.json",
            "radius_groups": ["inner", "mid", "outer"],
            "height_groups": ["mid", "high", "low"],
            "offsets": [item[4] for item in sample_specs],
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
                "- Reconstruction entry: `workspace.recon.cyl_fast_reference_engine.reconstruct_cylindrical_reference`",
                "- Statement: data are not 2D proxy patterns and not manually fabricated pseudo-reference images",
            ]
        ),
    )
    return {"total_samples": len(manifest_rows)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build azimuth-wrap edge stress dataset.")
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()
    summary = build_azimuth_edge_stress_dataset(Path(args.output_root), Path(args.project_root))
    print(f"Built azimuth edge stress dataset with {summary['total_samples']} samples")


if __name__ == "__main__":
    main()
