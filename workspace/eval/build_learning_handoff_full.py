from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from typing import Any

import numpy as np

from workspace.common.io_utils import ensure_dir, read_json, write_json, write_text
from workspace.recon.cyl_fast_reference_engine import reconstruct_cylindrical_reference


def _save_ref3_cache(output_path: Path, result: dict[str, Any]) -> None:
    np.savez_compressed(
        output_path,
        volume=result["volume"],
        gt_volume=result["gt_volume"],
        x_values=result["x_values"],
        y_values=result["y_values"],
        z_values=result["z_values"],
    )


def build_handoff(output_root: Path) -> dict[str, Any]:
    shape_root = output_root / "datasets" / "shape_family_full"
    random_root = output_root / "datasets" / "random_et"
    shape_manifest = read_json(shape_root / "dataset_manifest.json")
    random_manifest = read_json(random_root / "dataset_manifest.json")
    shape_index = read_json(shape_root / "dataset" / "index.json")
    random_index = read_json(random_root / "dataset" / "index.json")
    cache_root = ensure_dir(output_root / "learning_cache")
    split_index = {"train": [], "val": [], "test": []}
    samples: list[dict[str, Any]] = []
    summary_by_source = {
        "shape_family_full": {split: 0 for split in split_index},
        "random_et": {split: 0 for split in split_index},
    }
    hardest_families = {"point_cluster", "line", "L-shape"}

    for dataset_source, dataset_root, rows in [
        ("shape_family_full", shape_root, shape_index),
        ("random_et", random_root, random_index),
    ]:
        dataset_cache = ensure_dir(cache_root / dataset_source)
        for item in rows:
            sample_id = item["sample_id"]
            ref3_path = dataset_cache / f"{sample_id}_ref3_full.npz"
            if not ref3_path.exists():
                result = reconstruct_cylindrical_reference(
                    scene_path=dataset_root / item["scene_path"],
                    echo_path=dataset_root / "dataset" / "echoes" / f"{sample_id}_echo_sparse.npz",
                    method="ref3",
                )
                _save_ref3_cache(ref3_path, result)
            rel_ref3_path = str(ref3_path.relative_to(output_root))
            rel_gt_path = str((dataset_root / item["gt_volume_path"]).relative_to(output_root))
            sample = {
                "sample_id": sample_id,
                "dataset_source": dataset_source,
                "split": item["split"],
                "family": item["family"],
                "is_random_et": dataset_source == "random_et",
                "is_hard_family": item["family"] in hardest_families,
                "ref3_path": rel_ref3_path,
                "gt_path": rel_gt_path,
                "scene_path": str((dataset_root / item["scene_path"]).relative_to(output_root)),
                "echo_path": str((dataset_root / "dataset" / "echoes" / f"{sample_id}_echo_sparse.npz").relative_to(output_root)),
                "center_rho_m": item["center_rho_m"],
                "near_edge": item["near_edge"],
            }
            samples.append(sample)
            split_index[item["split"]].append(sample_id)
            summary_by_source[dataset_source][item["split"]] += 1

    samples.sort(key=lambda row: (row["split"], row["dataset_source"], row["sample_id"]))
    manifest = {
        "task": "task_real_006",
        "learning_interface": "Variant B ref3 coarse volume -> 3D U-Net -> GT amplitude",
        "input_representation": "ref3 coarse amplitude volume",
        "target_representation": "GT amplitude volume",
        "frozen_backbone": "Variant B ref3",
        "samples": samples,
        "split_index": split_index,
        "summary_by_source": summary_by_source,
        "hardest_family_priority": ["point_cluster", "line", "L-shape"],
    }
    write_json(output_root / "learning_handoff_manifest_full.json", manifest)

    shutil.copyfile(shape_root / "dataset_manifest.json", output_root / "dataset_manifest_shape_family_full.json")
    shutil.copyfile(random_root / "dataset_manifest.json", output_root / "dataset_manifest_random_et.json")
    shutil.copyfile(shape_root / "dataset_protocol_snapshot.md", output_root / "dataset_protocol_snapshot.md")
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
                "- Included sources: shape-family ET full dataset and Manisali-style random ET supplement",
            ]
        ),
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the task_real_006 full learning handoff manifest.")
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()
    manifest = build_handoff(Path(args.output_root))
    print(f"Built learning handoff manifest full samples={len(manifest['samples'])}")


if __name__ == "__main__":
    main()
