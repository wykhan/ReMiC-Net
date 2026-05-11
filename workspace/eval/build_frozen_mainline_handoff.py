from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

from workspace.common.io_utils import ensure_dir, read_json, write_json, write_text


SOURCE_TASK006_ROOT = Path(
    "/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006_two_stage_learning/20260416_120500"
)


def _link_dataset(target_root: Path, link_name: str, source_path: Path) -> None:
    link_path = target_root / "datasets" / link_name
    ensure_dir(link_path.parent)
    if link_path.exists() or link_path.is_symlink():
        return
    os.symlink(source_path, link_path, target_is_directory=True)


def build_handoff(output_root: Path, source_root: Path) -> dict:
    _link_dataset(output_root, "shape_family_full", source_root / "datasets" / "shape_family_full")
    _link_dataset(output_root, "random_et", source_root / "datasets" / "random_et")
    learning_cache_link = output_root / "learning_cache"
    if not learning_cache_link.exists() and not learning_cache_link.is_symlink():
        os.symlink(source_root / "learning_cache", learning_cache_link, target_is_directory=True)

    full_handoff = read_json(source_root / "learning_handoff_manifest_full.json")
    samples = [row for row in full_handoff["samples"] if row["dataset_source"] == "shape_family_full"]
    split_index = {"train": [], "val": [], "test": []}
    for row in samples:
        split_index[row["split"]].append(row["sample_id"])
    manifest = {
        "task": "task_real_006b",
        "learning_interface": "Frozen Mainline = Variant B ref3 coarse volume -> 3D U-Net -> GT amplitude",
        "input_representation": "ref3 coarse amplitude volume",
        "target_representation": "GT amplitude volume",
        "frozen_mainline_definition": {
            "frontend": "Variant B",
            "physics_backbone": "ref3",
            "second_stage": "3D U-Net",
            "training_data": "shape_family_full only",
        },
        "samples": samples,
        "split_index": split_index,
        "hardest_family_priority": ["point_cluster", "line", "L-shape"],
    }
    write_json(output_root / "learning_handoff_manifest_frozen_mainline.json", manifest)
    write_json(output_root / "learning_handoff_manifest_full.json", manifest)
    shutil.copyfile(source_root / "dataset_manifest_shape_family_full.json", output_root / "dataset_manifest_shape_family_full.json")
    shutil.copyfile(source_root / "dataset_manifest_random_et.json", output_root / "dataset_manifest_random_et.json")
    shutil.copyfile(source_root / "dataset_protocol_snapshot.md", output_root / "dataset_protocol_snapshot.md")
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
                "- Frozen Mainline training data: shape-family full-scale only",
                "- Random ET supplement is still linked and preserved as a formal resource for add-on experiments",
            ]
        ),
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the task_real_006b frozen-mainline handoff manifest.")
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--source-root", default=str(SOURCE_TASK006_ROOT))
    args = parser.parse_args()
    manifest = build_handoff(Path(args.output_root), Path(args.source_root))
    print(f"Built frozen mainline handoff samples={len(manifest['samples'])}")


if __name__ == "__main__":
    main()
