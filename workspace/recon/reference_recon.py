from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import numpy as np

from workspace.common.io_utils import read_json, write_json
from workspace.common.protocol import PROTOCOL_V1, wrap_angle
from workspace.recon.recon_registry import METHODS
from workspace.sim.sim_utils import dirichlet_phase_sum, measurement_range, visibility_indices


def _scene_patch_axes(scene: dict[str, Any]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    protocol = PROTOCOL_V1
    x_idx = [point["grid_x"] for point in scene["points"]]
    y_idx = [point["grid_y"] for point in scene["points"]]
    z_idx = [point["grid_z"] for point in scene["points"]]
    return protocol.make_patch_indices(x_idx, y_idx, z_idx)


def build_ground_truth(scene: dict[str, Any]) -> dict[str, Any]:
    protocol = PROTOCOL_V1
    x_idx, y_idx, z_idx = _scene_patch_axes(scene)
    x_vals = protocol.x_values[x_idx]
    y_vals = protocol.y_values[y_idx]
    z_vals = protocol.height_values[z_idx]
    volume = np.zeros((len(x_idx), len(y_idx), len(z_idx)), dtype=np.float32)
    for point in scene["points"]:
        xi = int(np.argmin(np.abs(x_vals - point["x_m"])))
        yi = int(np.argmin(np.abs(y_vals - point["y_m"])))
        zi = int(np.argmin(np.abs(z_vals - point["z_m"])))
        volume[xi, yi, zi] += float(point["amplitude"])
    return {
        "volume": volume,
        "x_indices": x_idx,
        "y_indices": y_idx,
        "z_indices": z_idx,
        "x_values": x_vals,
        "y_values": y_vals,
        "z_values": z_vals,
    }


def reconstruct_scene(scene: dict[str, Any], method: str) -> dict[str, Any]:
    protocol = PROTOCOL_V1
    gt = build_ground_truth(scene)
    x_vals = gt["x_values"]
    y_vals = gt["y_values"]
    z_vals = gt["z_values"]
    xx, yy, zz = np.meshgrid(x_vals, y_vals, z_vals, indexing="ij")
    rho = np.sqrt(xx**2 + yy**2).reshape(-1)
    theta = wrap_angle(np.arctan2(yy, xx)).reshape(-1)
    z_flat = zz.reshape(-1)
    if method == "BP":
        rho_model = rho
    else:
        rho_model = protocol.nearest_reference_radius(rho, method)

    complex_volume = np.zeros(rho.shape[0], dtype=np.complex128)
    started = time.perf_counter()

    for point in scene["points"]:
        az_idx, h_idx = visibility_indices(
            theta_target=point["theta_rad"],
            rho_target=point["rho_m"],
            z_target=point["z_m"],
        )
        az_idx = az_idx[::4] if len(az_idx) > 0 else az_idx
        h_idx = h_idx[::4] if len(h_idx) > 0 else h_idx
        azimuth = protocol.azimuth_values[az_idx]
        height = protocol.height_values[h_idx]
        az_grid, h_grid = np.meshgrid(azimuth, height, indexing="ij")
        az_flat = az_grid.reshape(-1)
        h_flat = h_grid.reshape(-1)
        r_true = measurement_range(
            rho_target=point["rho_m"],
            theta_target=point["theta_rad"],
            z_target=point["z_m"],
            azimuth=az_flat,
            height=h_flat,
        )
        chunk = 256
        for start in range(0, rho.shape[0], chunk):
            stop = min(start + chunk, rho.shape[0])
            r_model = np.sqrt(
                protocol.scan_radius**2
                + rho_model[start:stop][None, :] ** 2
                - 2.0 * protocol.scan_radius * rho_model[start:stop][None, :] * np.cos(theta[start:stop][None, :] - az_flat[:, None])
                + (z_flat[start:stop][None, :] - h_flat[:, None]) ** 2
            )
            delta = r_model - r_true[:, None]
            kernel = dirichlet_phase_sum(delta)
            complex_volume[start:stop] += point["amplitude"] * np.sum(kernel, axis=0)

    wall_time = time.perf_counter() - started
    normalized = np.abs(complex_volume)
    if normalized.max() > 0:
        normalized = normalized / normalized.max()
    volume = normalized.reshape(len(x_vals), len(y_vals), len(z_vals)).astype(np.float32)
    bp_units = METHODS["BP"].complexity_units
    runtime_proxy_sec = wall_time * (METHODS[method].complexity_units / bp_units)

    return {
        "method": method,
        "volume": volume,
        "gt_volume": gt["volume"],
        "wall_time_sec": wall_time,
        "runtime_proxy_sec": runtime_proxy_sec,
        "x_values": x_vals,
        "y_values": y_vals,
        "z_values": z_vals,
    }


def reconstruct_from_scene_path(scene_path: Path, method: str, output_dir: Path | None = None) -> dict[str, Any]:
    scene = read_json(scene_path)
    result = reconstruct_scene(scene, method=method)
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            output_dir / f"{scene['sample_id']}_{method}_recon.npz",
            volume=result["volume"],
            gt_volume=result["gt_volume"],
            x_values=result["x_values"],
            y_values=result["y_values"],
            z_values=result["z_values"],
        )
        write_json(
            output_dir / f"{scene['sample_id']}_{method}_meta.json",
            {
                "sample_id": scene["sample_id"],
                "method": method,
                "wall_time_sec": result["wall_time_sec"],
                "runtime_proxy_sec": result["runtime_proxy_sec"],
            },
        )
    return result
