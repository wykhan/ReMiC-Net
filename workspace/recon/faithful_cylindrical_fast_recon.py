from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import numpy as np

from workspace.common.io_utils import read_json
from workspace.common.protocol import PROTOCOL_V1, wrap_angle
from workspace.eval.metrics_3d import nmse, psnr, ssim_global
from workspace.sim.sim_utils import visibility_indices


def load_sparse_echo(echo_path: Path) -> dict[str, np.ndarray]:
    payload = np.load(echo_path)
    return {
        "azimuth_idx": payload["azimuth_idx"],
        "height_idx": payload["height_idx"],
        "echo": payload["echo_real"] + 1j * payload["echo_imag"],
        "shape": payload["shape"],
    }


def _scene_patch_axes(scene: dict[str, Any], margin_xy: int = 2, margin_z: int = 2) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    protocol = PROTOCOL_V1
    x_center = [protocol.world_to_grid_xy(point["x_m"]) for point in scene["points"]]
    y_center = [protocol.world_to_grid_xy(point["y_m"]) for point in scene["points"]]
    z_center = [protocol.world_to_grid_z(point["z_m"]) for point in scene["points"]]
    x_min = max(min(x_center) - margin_xy, 0)
    x_max = min(max(x_center) + margin_xy, len(protocol.x_values) - 1)
    y_min = max(min(y_center) - margin_xy, 0)
    y_max = min(max(y_center) + margin_xy, len(protocol.y_values) - 1)
    z_min = max(min(z_center) - margin_z, 0)
    z_max = min(max(z_center) + margin_z, len(protocol.height_values) - 1)
    return (
        np.arange(x_min, x_max + 1, dtype=np.int32),
        np.arange(y_min, y_max + 1, dtype=np.int32),
        np.arange(z_min, z_max + 1, dtype=np.int32),
    )


def build_ground_truth(scene: dict[str, Any]) -> dict[str, Any]:
    protocol = PROTOCOL_V1
    x_idx, y_idx, z_idx = _scene_patch_axes(scene)
    x_vals = protocol.x_values[x_idx]
    y_vals = protocol.y_values[y_idx]
    z_vals = protocol.height_values[z_idx]
    volume = np.zeros((len(x_vals), len(y_vals), len(z_vals)), dtype=np.float32)
    for point in scene["points"]:
        xi = int(np.argmin(np.abs(x_vals - point["x_m"])))
        yi = int(np.argmin(np.abs(y_vals - point["y_m"])))
        zi = int(np.argmin(np.abs(z_vals - point["z_m"])))
        volume[xi, yi, zi] += float(point["amplitude"])
    return {
        "volume": volume,
        "x_values": x_vals,
        "y_values": y_vals,
        "z_values": z_vals,
    }


def _make_dense_subset(echo_sparse: dict[str, np.ndarray]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    protocol = PROTOCOL_V1
    az_idx = echo_sparse["azimuth_idx"].astype(np.int32)
    h_idx = echo_sparse["height_idx"].astype(np.int32)
    az_unique = np.unique(az_idx)
    h_unique = np.unique(h_idx)
    az_map = {int(v): i for i, v in enumerate(az_unique)}
    h_map = {int(v): i for i, v in enumerate(h_unique)}
    dense = np.zeros((len(az_unique), len(h_unique), protocol.num_freq), dtype=np.complex64)
    for row_idx in range(len(az_idx)):
        dense[az_map[int(az_idx[row_idx])], h_map[int(h_idx[row_idx])]] = echo_sparse["echo"][row_idx]
    return dense, az_unique, h_unique


def _matched_filter_volume(
    scene: dict[str, Any],
    dense_echo: np.ndarray,
    az_unique: np.ndarray,
    h_unique: np.ndarray,
    method: str,
) -> np.ndarray:
    protocol = PROTOCOL_V1
    gt = build_ground_truth(scene)
    x_vals = gt["x_values"]
    y_vals = gt["y_values"]
    z_vals = gt["z_values"]
    xx, yy, zz = np.meshgrid(x_vals, y_vals, z_vals, indexing="ij")
    rho = np.sqrt(xx**2 + yy**2).reshape(-1)
    theta = wrap_angle(np.arctan2(yy, xx)).reshape(-1)
    z_flat = zz.reshape(-1)
    rho_model = rho if method == "BP" else protocol.nearest_reference_radius(rho, method)
    az_vals = protocol.azimuth_values[az_unique]
    h_vals = protocol.height_values[h_unique]
    az_grid, h_grid = np.meshgrid(az_vals, h_vals, indexing="ij")
    obs_k = dense_echo.reshape(-1, protocol.num_freq).astype(np.complex128)
    obs_az = np.repeat(az_grid.reshape(-1), 1)
    obs_h = np.repeat(h_grid.reshape(-1), 1)
    active_mask = np.linalg.norm(obs_k, axis=1) > 0
    obs_k = obs_k[active_mask]
    obs_az = obs_az[active_mask]
    obs_h = obs_h[active_mask]
    decimation = 2
    if obs_k.shape[0] > 0:
        keep = np.arange(obs_k.shape[0]) % decimation == 0
        obs_k = obs_k[keep]
        obs_az = obs_az[keep]
        obs_h = obs_h[keep]
    k_values = protocol.k_values.astype(np.float64)
    volume = np.zeros(rho.shape[0], dtype=np.complex128)
    chunk = 128
    for start in range(0, rho.shape[0], chunk):
        stop = min(start + chunk, rho.shape[0])
        ranges = np.sqrt(
            protocol.scan_radius**2
            + rho_model[start:stop][None, :] ** 2
            - 2.0 * protocol.scan_radius * rho_model[start:stop][None, :] * np.cos(theta[start:stop][None, :] - obs_az[:, None])
            + (z_flat[start:stop][None, :] - obs_h[:, None]) ** 2
        )
        phase = np.exp(1j * ranges[..., None] * k_values[None, None, :])
        volume[start:stop] = np.einsum("ok,ovk->v", obs_k, phase, optimize=True)
    mag = np.abs(volume)
    if mag.max() > 0:
        mag = mag / mag.max()
    return mag.reshape(len(x_vals), len(y_vals), len(z_vals)).astype(np.float32)


def reconstruct_faithful(scene_path: Path, echo_path: Path, method: str) -> dict[str, Any]:
    scene = read_json(scene_path)
    gt = build_ground_truth(scene)
    echo_sparse = load_sparse_echo(echo_path)
    started = time.perf_counter()
    dense_echo, az_unique, h_unique = _make_dense_subset(echo_sparse)
    fft_height = np.fft.fftshift(np.fft.fft(dense_echo, axis=1), axes=1)
    fft_az = np.fft.fftshift(np.fft.fft(fft_height, axis=0), axes=0)
    volume = _matched_filter_volume(scene, dense_echo, az_unique, h_unique, method=method)
    wall_time = time.perf_counter() - started
    return {
        "sample_id": scene["sample_id"],
        "method": method,
        "volume": volume,
        "gt_volume": gt["volume"],
        "x_values": gt["x_values"],
        "y_values": gt["y_values"],
        "z_values": gt["z_values"],
        "wall_time_sec": wall_time,
        "fft_shape": list(fft_az.shape),
        "quality": {
            "nmse": nmse(volume, gt["volume"]),
            "psnr": psnr(volume, gt["volume"]),
            "ssim": ssim_global(volume, gt["volume"]),
        },
    }


def proof_line(scene_path: Path, echo_path: Path) -> str:
    scene = read_json(scene_path)
    point = scene["points"][0]
    az_idx, h_idx = visibility_indices(point["theta_rad"], point["rho_m"], point["z_m"])
    return (
        f"scene={scene['sample_id']} rho={point['rho_m']:.3f} z={point['z_m']:.3f} "
        f"visible_az={len(az_idx)} visible_h={len(h_idx)} echo={echo_path.name}"
    )
