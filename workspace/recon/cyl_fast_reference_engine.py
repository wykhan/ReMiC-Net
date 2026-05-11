from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import numpy as np
from scipy import fft

from workspace.common.io_utils import read_json
from workspace.common.protocol import PROTOCOL_V1
from workspace.eval.metrics_3d import nmse, psnr, ssim_global
from workspace.recon.geometry_correction import linear_geometry_correction, sinc_geometry_correction


def load_sparse_echo(echo_path: Path) -> dict[str, np.ndarray]:
    payload = np.load(echo_path)
    return {
        "azimuth_idx": payload["azimuth_idx"].astype(np.int32),
        "height_idx": payload["height_idx"].astype(np.int32),
        "echo": (payload["echo_real"] + 1j * payload["echo_imag"]).astype(np.complex64),
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


def _contiguous_azimuth_indices(az_unique: np.ndarray) -> np.ndarray:
    num_az = PROTOCOL_V1.num_azimuth
    ordered = np.sort(np.unique(az_unique.astype(np.int32)))
    if ordered.size == 0:
        return ordered
    diffs = np.diff(ordered)
    if np.all(diffs == 1):
        return ordered
    wrapped = ordered.copy()
    wrapped[wrapped > ordered.mean()] -= num_az
    wrapped = np.sort(wrapped)
    start = int(wrapped[0])
    stop = int(wrapped[-1])
    return (np.arange(start, stop + 1, dtype=np.int32) % num_az).astype(np.int32)


def _make_tensor_from_sparse(echo_sparse: dict[str, np.ndarray], tensor_mode: str) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    protocol = PROTOCOL_V1
    az_idx = echo_sparse["azimuth_idx"]
    h_idx = echo_sparse["height_idx"]
    active_count = len(np.unique(np.stack([az_idx, h_idx], axis=1), axis=0))
    if tensor_mode == "dense_global":
        az_window = np.arange(protocol.num_azimuth, dtype=np.int32)
        h_window = np.arange(protocol.num_height, dtype=np.int32)
    else:
        az_window = _contiguous_azimuth_indices(np.unique(az_idx))
        h_window = np.arange(int(h_idx.min()), int(h_idx.max()) + 1, dtype=np.int32)
    az_pos = {int(v): i for i, v in enumerate(az_window)}
    h_pos = {int(v): i for i, v in enumerate(h_window)}
    dense = np.zeros((len(az_window), protocol.num_freq, len(h_window)), dtype=np.complex64)
    for row_idx in range(len(az_idx)):
        dense[az_pos[int(az_idx[row_idx])], :, h_pos[int(h_idx[row_idx])]] = echo_sparse["echo"][row_idx]
    coverage_ratio = float(active_count / max(len(az_window) * len(h_window), 1))
    return dense, az_window, h_window, coverage_ratio


def _kwz_for_window(num_height: int) -> np.ndarray:
    d_kz = 2.0 * np.pi / (num_height * PROTOCOL_V1.height_spacing)
    return d_kz * np.arange(-(num_height // 2), -(num_height // 2) + num_height, dtype=np.float32)


def _fft_height_then_azimuth(dense_echo: np.ndarray) -> np.ndarray:
    stage_h = fft.fftshift(fft.fft(fft.fftshift(dense_echo, axes=2), axis=2), axes=2)
    return fft.fftshift(fft.fft(fft.fftshift(stage_h, axes=0), axis=0), axes=0).astype(np.complex64)


def _reference_surface_stack(
    fft_echo: np.ndarray,
    azimuth_rel_values: np.ndarray,
    height_values: np.ndarray,
    refs: np.ndarray,
) -> np.ndarray:
    protocol = PROTOCOL_V1
    k_values = protocol.k_values.astype(np.float32)
    kz_values = _kwz_for_window(len(height_values))
    kwz = np.sqrt(np.maximum(k_values[None, :] ** 2 - kz_values[:, None] ** 2, 0.0)).astype(np.float32)
    cos_u = np.cos(azimuth_rel_values).astype(np.float32)
    stack = np.zeros((len(azimuth_rel_values), len(refs), len(height_values)), dtype=np.complex64)
    rn_ref_all = np.sqrt(
        protocol.scan_radius**2
        + refs[:, None] ** 2
        - 2.0 * protocol.scan_radius * refs[:, None] * cos_u[None, :]
    ).astype(np.float32)
    for h_idx in range(len(height_values)):
        temp = fft_echo[:, :, h_idx]
        kernel = np.exp(1j * rn_ref_all[:, :, None] * kwz[h_idx][None, None, :]).astype(np.complex64)
        kernel *= (k_values[None, None, :] / 2.0).astype(np.float32)
        kernel_ft = fft.fftshift(fft.fft(fft.fftshift(kernel, axes=1), axis=1), axes=1)
        matched = np.sum(temp[None, :, :] * kernel_ft, axis=2)
        image = fft.fftshift(fft.ifft(fft.fftshift(matched, axes=1), axis=1), axes=1)
        stack[:, :, h_idx] = image.transpose(1, 0)
    return fft.fftshift(fft.ifft(fft.fftshift(stack, axes=2), axis=2), axes=2).astype(np.complex64)


def reconstruct_cylindrical_reference(
    scene_path: Path,
    echo_path: Path,
    method: str,
    tensor_mode: str = "active",
    geom_mode: str = "sinc",
) -> dict[str, Any]:
    scene = read_json(scene_path)
    gt = build_ground_truth(scene)
    echo_sparse = load_sparse_echo(echo_path)
    refs = PROTOCOL_V1.reference_sets[method].astype(np.float32)
    point_angles = np.array([point["theta_rad"] for point in scene["points"]], dtype=np.float64)
    azimuth_center = float(np.angle(np.mean(np.exp(1j * point_angles))))
    started = time.perf_counter()
    dense_echo, az_window, h_window, coverage_ratio = _make_tensor_from_sparse(echo_sparse, tensor_mode=tensor_mode)
    fft_echo = _fft_height_then_azimuth(dense_echo)
    azimuth_rel_values = PROTOCOL_V1.azimuth_values[az_window].astype(np.float64) - azimuth_center
    cylindrical_stack = _reference_surface_stack(
        fft_echo=fft_echo,
        azimuth_rel_values=azimuth_rel_values,
        height_values=PROTOCOL_V1.height_values[h_window],
        refs=refs,
    )
    if geom_mode == "sinc":
        correction = sinc_geometry_correction(
            cylindrical_stack=cylindrical_stack,
            refs=refs.astype(np.float64),
            azimuth_rel_values=azimuth_rel_values,
            height_values=PROTOCOL_V1.height_values[h_window],
            gt=gt,
            azimuth_center=azimuth_center,
            rho_limit=PROTOCOL_V1.scene_radius,
            rho_ref_full=PROTOCOL_V1.rho_ref_full.astype(np.float64),
        )
    else:
        correction = linear_geometry_correction(
            cylindrical_stack=cylindrical_stack,
            refs=refs.astype(np.float64),
            azimuth_rel_values=azimuth_rel_values,
            height_values=PROTOCOL_V1.height_values[h_window],
            gt=gt,
            azimuth_center=azimuth_center,
            rho_limit=PROTOCOL_V1.scene_radius,
        )
    volume = correction.volume.astype(np.float32)
    wall_time = time.perf_counter() - started
    estimated_peak_memory_bytes = int(dense_echo.nbytes + fft_echo.nbytes + cylindrical_stack.nbytes + correction.extra_memory_bytes)
    return {
        "sample_id": scene["sample_id"],
        "method": method,
        "tensor_mode": tensor_mode,
        "geom_mode": geom_mode,
        "volume": volume,
        "gt_volume": gt["volume"],
        "x_values": gt["x_values"],
        "y_values": gt["y_values"],
        "z_values": gt["z_values"],
        "wall_time_sec": wall_time,
        "tensor_shape": [int(len(az_window)), int(PROTOCOL_V1.num_freq), int(len(h_window))],
        "active_coverage_ratio": coverage_ratio,
        "reference_count": int(len(refs)),
        "estimated_peak_memory_mb": float(estimated_peak_memory_bytes / (1024.0 * 1024.0)),
        "quality": {
            "nmse": nmse(volume, gt["volume"]),
            "psnr": psnr(volume, gt["volume"]),
            "ssim": ssim_global(volume, gt["volume"]),
        },
    }
