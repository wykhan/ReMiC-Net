from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from workspace.common.io_utils import read_json, write_json


def build_manifest(output_root: Path) -> dict:
    dataset_index = read_json(output_root / "dataset" / "index.json")
    baseline = read_json(output_root / "baseline_metrics_et.json")
    by_sample_ref3 = {
        row["sample_id"]: row
        for row in baseline["per_sample"]
        if row["method"] == "ref3"
    }
    family_nmse: dict[str, list[float]] = {}
    for sample_id, row in by_sample_ref3.items():
        family_nmse.setdefault(row["family"], [])
        family_nmse[row["family"]].append(float(row["nmse"]))

    family_priority = sorted(
        (
            {
                "family": family,
                "ref3_nmse_mean": float(np.mean(values)),
                "sample_count": len(values),
            }
            for family, values in family_nmse.items()
        ),
        key=lambda row: row["ref3_nmse_mean"],
        reverse=True,
    )
    recommended_families = [row["family"] for row in family_priority[:3]]

    samples = []
    split_index = {"train": [], "val": [], "test": []}
    for item in dataset_index:
        sample_id = item["sample_id"]
        sample_payload = {
            "sample_id": sample_id,
            "split": item["split"],
            "family": item["family"],
            "ref3_path": f"et_recon_cache/{sample_id}_ref3_et.npz",
            "gt_path": item["gt_volume_path"],
            "center_rho_m": item["center_rho_m"],
            "near_edge": item["near_edge"],
        }
        samples.append(sample_payload)
        split_index[item["split"]].append(sample_id)

    manifest = {
        "task": "task_real_005",
        "learning_interface": "RED_ref3 -> 3D U-Net -> GT amplitude",
        "input_representation": "ref3 coarse amplitude volume",
        "target_representation": "GT amplitude volume",
        "samples": samples,
        "split_index": split_index,
        "family_priority_for_learning": family_priority,
        "recommended_primary_families": recommended_families,
        "sampling_balance_note": (
            "The hardest ref3 families should be up-weighted first if ET-1 is expanded. "
            "Current ET-1 scale is already balanced by family count."
        ),
    }
    write_json(output_root / "learning_handoff_manifest.json", manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the ET learning handoff manifest.")
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()
    manifest = build_manifest(Path(args.output_root))
    print(f"Built learning handoff manifest families={len(manifest['family_priority_for_learning'])}")


if __name__ == "__main__":
    main()
