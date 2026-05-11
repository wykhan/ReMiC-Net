from __future__ import annotations

import argparse
from pathlib import Path

from workspace.common.io_utils import read_json, write_json, write_text
from workspace.data.radial_control_dataset_builder import build_controlled_dataset


def build_accelerated_dataset(output_root: Path, project_root: Path) -> dict:
    summary = build_controlled_dataset(output_root=output_root, project_root=project_root)
    manifest = read_json(output_root / "dataset_manifest.json")
    manifest["dataset_name"] = "task_real_004_controlled_accelerated_point_set"
    write_json(output_root / "dataset_manifest.json", manifest)
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
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Build accelerated controlled radial mismatch point-target dataset.")
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()
    summary = build_accelerated_dataset(Path(args.output_root), Path(args.project_root))
    print(f"Built accelerated controlled dataset with {summary['total_samples']} samples")


if __name__ == "__main__":
    main()
