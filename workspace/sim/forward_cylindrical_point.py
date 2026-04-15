from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from workspace.common.io_utils import ensure_dir, read_json, write_json
from workspace.common.protocol import PROTOCOL_V1
from workspace.sim.sim_utils import measurement_range, visibility_indices


def simulate_sample(scene: dict, output_dir: Path) -> dict:
    protocol = PROTOCOL_V1
    az = protocol.azimuth_values
    heights = protocol.height_values
    k_values = protocol.k_values
    active_cells: dict[tuple[int, int], np.ndarray] = {}
    point_summaries: list[dict] = []

    for point in scene["points"]:
        az_idx, h_idx = visibility_indices(
            theta_target=point["theta_rad"],
            rho_target=point["rho_m"],
            z_target=point["z_m"],
        )
        az_sel = az[az_idx]
        h_sel = heights[h_idx]
        az_grid, h_grid = np.meshgrid(az_sel, h_sel, indexing="ij")
        ranges = measurement_range(
            rho_target=point["rho_m"],
            theta_target=point["theta_rad"],
            z_target=point["z_m"],
            azimuth=az_grid,
            height=h_grid,
        )
        local_echo = point["amplitude"] * np.exp(-1j * ranges[..., None] * k_values[None, None, :])
        for i, a_idx in enumerate(az_idx):
            for j, z_idx in enumerate(h_idx):
                key = (int(a_idx), int(z_idx))
                if key not in active_cells:
                    active_cells[key] = np.zeros(protocol.num_freq, dtype=np.complex64)
                active_cells[key] += local_echo[i, j].astype(np.complex64)
        point_summaries.append(
            {
                "point_theta_rad": point["theta_rad"],
                "point_rho_m": point["rho_m"],
                "point_z_m": point["z_m"],
                "visible_azimuth_count": int(len(az_idx)),
                "visible_height_count": int(len(h_idx)),
            }
        )

    ordered_keys = sorted(active_cells)
    az_idx = np.array([item[0] for item in ordered_keys], dtype=np.int32)
    h_idx = np.array([item[1] for item in ordered_keys], dtype=np.int32)
    echo_matrix = np.stack([active_cells[item] for item in ordered_keys], axis=0) if ordered_keys else np.zeros((0, protocol.num_freq), dtype=np.complex64)
    output_path = output_dir / f"{scene['sample_id']}_echo_sparse.npz"
    np.savez_compressed(
        output_path,
        azimuth_idx=az_idx,
        height_idx=h_idx,
        echo_real=echo_matrix.real.astype(np.float32),
        echo_imag=echo_matrix.imag.astype(np.float32),
        shape=np.array([protocol.num_azimuth, protocol.num_freq, protocol.num_height], dtype=np.int32),
    )
    metadata = {
        "sample_id": scene["sample_id"],
        "split": scene["split"],
        "echo_path": str(output_path),
        "active_measurement_count": int(len(ordered_keys)),
        "dense_shape": [protocol.num_azimuth, protocol.num_freq, protocol.num_height],
        "points": point_summaries,
    }
    write_json(output_dir / f"{scene['sample_id']}_echo_meta.json", metadata)
    return metadata


def batch_simulate(output_root: Path) -> dict:
    dataset_index = read_json(output_root / "dataset" / "index.json")
    echo_dir = ensure_dir(output_root / "dataset" / "echoes")
    by_split: dict[str, list[dict]] = {}
    for item in dataset_index:
        scene = read_json(output_root / item["scene_path"])
        meta = simulate_sample(scene, echo_dir)
        by_split.setdefault(item["split"], [])
        by_split[item["split"]].append(meta)
    summary = {
        "total_samples": len(dataset_index),
        "splits": {key: len(value) for key, value in by_split.items()},
        "average_active_measurements": {
            key: float(np.mean([entry["active_measurement_count"] for entry in value])) if value else 0.0
            for key, value in by_split.items()
        },
    }
    write_json(output_root / "dataset" / "echo_summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run protocol-v1 point forward simulation.")
    parser.add_argument("--output-root", required=True, help="Task artifact root.")
    args = parser.parse_args()
    summary = batch_simulate(Path(args.output_root))
    print(f"Simulated echoes for {summary['total_samples']} samples")


if __name__ == "__main__":
    main()
