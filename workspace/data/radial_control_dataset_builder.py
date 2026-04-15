from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from workspace.common.io_utils import ensure_dir, write_json, write_text
from workspace.data.point_scene_generator import SampleConfig, generate_point_scene


def _single_point_scene(sample_id: str, split: str, seed: int, x_m: float, y_m: float, z_m: float, amplitude: float, tag: str) -> dict:
    base = generate_point_scene(SampleConfig(sample_id=sample_id, split=split, seed=seed, smoke=True))
    rho = (x_m**2 + y_m**2) ** 0.5
    theta = 0.0 if rho == 0 else float(__import__("math").atan2(y_m, x_m))
    base.update(
        {
            "point_count": 1,
            "controlled_tag": tag,
            "points": [
                {
                    "x_m": round(x_m, 6),
                    "y_m": round(y_m, 6),
                    "z_m": round(z_m, 6),
                    "rho_m": round(rho, 6),
                    "theta_rad": round(theta, 6),
                    "amplitude": amplitude,
                    "phase_rad": 0.0,
                }
            ],
        }
    )
    return base


def build_controlled_dataset(output_root: Path, project_root: Path) -> dict:
    scenes_root = ensure_dir(output_root / "dataset" / "scenes")
    split_dir = ensure_dir(scenes_root / "controlled")
    manifest_rows: list[dict] = []
    seed = 3100

    # Rho sweep: 0.00 to 0.30 inclusive with 0.01 m step.
    for idx in range(31):
        rho = idx * 0.01
        sample_id = f"rho_{idx:03d}"
        scene = _single_point_scene(
            sample_id=sample_id,
            split="controlled",
            seed=seed + idx,
            x_m=rho,
            y_m=0.0,
            z_m=0.0,
            amplitude=1.0,
            tag="rho_sweep",
        )
        path = split_dir / f"{sample_id}.json"
        write_json(path, scene)
        manifest_rows.append(
            {
                "sample_id": sample_id,
                "split": "controlled",
                "scene_path": str(path.relative_to(output_root)),
                "control_group": "rho_sweep",
                "rho_target_m": rho,
                "theta_target_rad": 0.0,
                "z_target_m": 0.0,
            }
        )

    azimuth_specs = [
        ("az_inner_negpi", 0.10, -3.05),
        ("az_inner_zero", 0.10, 0.0),
        ("az_inner_halfpi", 0.10, 1.57),
        ("az_mid_negpi", 0.20, -3.05),
        ("az_mid_zero", 0.20, 0.0),
        ("az_mid_halfpi", 0.20, 1.57),
        ("az_outer_negpi", 0.28, -3.05),
        ("az_outer_zero", 0.28, 0.0),
        ("az_outer_halfpi", 0.28, 1.57),
    ]
    for idx, (sample_id, rho, theta) in enumerate(azimuth_specs, start=len(manifest_rows)):
        import math

        scene = _single_point_scene(
            sample_id=sample_id,
            split="controlled",
            seed=seed + idx,
            x_m=rho * math.cos(theta),
            y_m=rho * math.sin(theta),
            z_m=0.0,
            amplitude=1.0,
            tag="azimuth_control",
        )
        path = split_dir / f"{sample_id}.json"
        write_json(path, scene)
        manifest_rows.append(
            {
                "sample_id": sample_id,
                "split": "controlled",
                "scene_path": str(path.relative_to(output_root)),
                "control_group": "azimuth_control",
                "rho_target_m": rho,
                "theta_target_rad": theta,
                "z_target_m": 0.0,
            }
        )

    height_specs = [
        ("z_inner_low", 0.10, -0.72),
        ("z_inner_mid", 0.10, 0.0),
        ("z_inner_high", 0.10, 0.72),
        ("z_outer_low", 0.28, -0.72),
        ("z_outer_mid", 0.28, 0.0),
        ("z_outer_high", 0.28, 0.72),
    ]
    for idx, (sample_id, rho, z_val) in enumerate(height_specs, start=len(manifest_rows)):
        scene = _single_point_scene(
            sample_id=sample_id,
            split="controlled",
            seed=seed + idx,
            x_m=rho,
            y_m=0.0,
            z_m=z_val,
            amplitude=1.0,
            tag="height_control",
        )
        path = split_dir / f"{sample_id}.json"
        write_json(path, scene)
        manifest_rows.append(
            {
                "sample_id": sample_id,
                "split": "controlled",
                "scene_path": str(path.relative_to(output_root)),
                "control_group": "height_control",
                "rho_target_m": rho,
                "theta_target_rad": 0.0,
                "z_target_m": z_val,
            }
        )

    write_json(output_root / "dataset" / "index.json", manifest_rows)
    write_json(
        output_root / "dataset_manifest.json",
        {
            "dataset_name": "task_real_003_controlled_radial_point_set",
            "split_names": ["controlled"],
            "counts_by_group": {
                "rho_sweep": 31,
                "azimuth_control": 9,
                "height_control": 6,
            },
            "total_samples": len(manifest_rows),
            "index_path": "dataset/index.json",
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
                "- Geometry protocol version: protocol v1 from `CONTEXT/simulation_protocol.md`",
                "- Forward simulator entry: `workspace.sim.forward_cylindrical_point`",
                "- Reconstruction chain: true cylindrical `ref3/ref5/ref7/ref9/BP` faithful echo-driven chain",
                "- Statement: data are not 2D proxy patterns and not manually fabricated pseudo-reference images",
            ]
        ),
    )
    return {"total_samples": len(manifest_rows)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build controlled radial mismatch point-target dataset.")
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()
    summary = build_controlled_dataset(Path(args.output_root), Path(args.project_root))
    print(f"Built controlled dataset with {summary['total_samples']} samples")


if __name__ == "__main__":
    main()
