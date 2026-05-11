from __future__ import annotations

from dataclasses import dataclass

import numpy as np


STENCIL_OFFSETS = np.arange(-7, 9, dtype=np.int32)


@dataclass(frozen=True)
class GeometryCorrectionResult:
    volume: np.ndarray
    extra_memory_bytes: int


def _dedupe_azimuth_axis(azimuth_values: np.ndarray, cylindrical_stack: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    azimuth_unwrapped = np.unwrap(azimuth_values.astype(np.float64))
    keep_mask = np.ones(len(azimuth_unwrapped), dtype=bool)
    keep_mask[1:] = np.diff(azimuth_unwrapped) > 1.0e-9
    return azimuth_unwrapped[keep_mask], cylindrical_stack[keep_mask]


def _adjust_query_angles(angle_query: np.ndarray, azimuth_unwrapped: np.ndarray) -> np.ndarray:
    center = float(azimuth_unwrapped[len(azimuth_unwrapped) // 2])
    return angle_query + 2.0 * np.pi * np.round((center - angle_query) / (2.0 * np.pi))


def _complex_linear_interp(x_values: np.ndarray, y_values: np.ndarray, targets: np.ndarray) -> np.ndarray:
    real = np.interp(targets, x_values, y_values.real)
    imag = np.interp(targets, x_values, y_values.imag)
    return real + 1j * imag


def _expand_rho_to_full_library(cylindrical_stack: np.ndarray, refs: np.ndarray, rho_ref_full: np.ndarray) -> np.ndarray:
    if len(refs) == len(rho_ref_full) and np.allclose(refs, rho_ref_full):
        return cylindrical_stack
    expanded = np.zeros((cylindrical_stack.shape[0], len(rho_ref_full), cylindrical_stack.shape[2]), dtype=np.complex64)
    for az_idx in range(cylindrical_stack.shape[0]):
        for h_idx in range(cylindrical_stack.shape[2]):
            expanded[az_idx, :, h_idx] = _complex_linear_interp(refs, cylindrical_stack[az_idx, :, h_idx], rho_ref_full).astype(np.complex64)
    return expanded


def _rho_indices_with_clamp(center_index: int, count: int) -> np.ndarray:
    return np.clip(center_index + STENCIL_OFFSETS, 0, count - 1).astype(np.int32)


def _azimuth_indices_with_wrap(center_index: int, count: int) -> np.ndarray:
    return (center_index + STENCIL_OFFSETS) % count


def linear_geometry_correction(
    cylindrical_stack: np.ndarray,
    refs: np.ndarray,
    azimuth_rel_values: np.ndarray,
    height_values: np.ndarray,
    gt: dict[str, np.ndarray],
    azimuth_center: float,
    rho_limit: float,
) -> GeometryCorrectionResult:
    azimuth_unwrapped, cylindrical_stack = _dedupe_azimuth_axis(azimuth_rel_values, cylindrical_stack)
    xx, yy, zz = np.meshgrid(gt["x_values"], gt["y_values"], gt["z_values"], indexing="ij")
    rho = np.sqrt(xx**2 + yy**2).reshape(-1)
    theta = np.arctan2(yy, xx).reshape(-1) - azimuth_center
    theta = _adjust_query_angles(theta, azimuth_unwrapped)
    z_flat = zz.reshape(-1)
    volume = np.zeros(rho.shape[0], dtype=np.float32)
    valid = rho <= rho_limit
    ref_values = refs.astype(np.float64)
    for idx in np.where(valid)[0]:
        theta_q = theta[idx]
        rho_q = float(rho[idx])
        z_q = float(z_flat[idx])
        az_hi = int(np.searchsorted(azimuth_unwrapped, theta_q, side="left"))
        az_hi = min(max(az_hi, 1), len(azimuth_unwrapped) - 1)
        az_lo = az_hi - 1
        az0 = azimuth_unwrapped[az_lo]
        az1 = azimuth_unwrapped[az_hi]
        az_alpha = 0.0 if abs(az1 - az0) < 1.0e-12 else (theta_q - az0) / (az1 - az0)

        ref_hi = int(np.searchsorted(ref_values, rho_q, side="left"))
        ref_hi = min(max(ref_hi, 1), len(ref_values) - 1)
        ref_lo = ref_hi - 1
        r0 = ref_values[ref_lo]
        r1 = ref_values[ref_hi]
        rho_alpha = 0.0 if abs(r1 - r0) < 1.0e-12 else (rho_q - r0) / (r1 - r0)

        h_pos = int(np.argmin(np.abs(height_values - z_q)))
        v00 = cylindrical_stack[az_lo, ref_lo, h_pos]
        v01 = cylindrical_stack[az_lo, ref_hi, h_pos]
        v10 = cylindrical_stack[az_hi, ref_lo, h_pos]
        v11 = cylindrical_stack[az_hi, ref_hi, h_pos]
        interp = (
            (1.0 - az_alpha) * (1.0 - rho_alpha) * v00
            + (1.0 - az_alpha) * rho_alpha * v01
            + az_alpha * (1.0 - rho_alpha) * v10
            + az_alpha * rho_alpha * v11
        )
        volume[idx] = abs(interp)
    if volume.max() > 0:
        volume /= volume.max()
    return GeometryCorrectionResult(
        volume=volume.reshape(len(gt["x_values"]), len(gt["y_values"]), len(gt["z_values"])),
        extra_memory_bytes=0,
    )


def sinc_geometry_correction(
    cylindrical_stack: np.ndarray,
    refs: np.ndarray,
    azimuth_rel_values: np.ndarray,
    height_values: np.ndarray,
    gt: dict[str, np.ndarray],
    azimuth_center: float,
    rho_limit: float,
    rho_ref_full: np.ndarray,
) -> GeometryCorrectionResult:
    azimuth_unwrapped, cylindrical_stack = _dedupe_azimuth_axis(azimuth_rel_values, cylindrical_stack)
    full_stack = _expand_rho_to_full_library(cylindrical_stack, refs.astype(np.float64), rho_ref_full.astype(np.float64))
    du = float(np.mean(np.diff(azimuth_unwrapped)))
    rho_step = float(np.mean(np.diff(rho_ref_full)))
    xx, yy, zz = np.meshgrid(gt["x_values"], gt["y_values"], gt["z_values"], indexing="ij")
    rho = np.sqrt(xx**2 + yy**2).reshape(-1)
    theta = np.arctan2(yy, xx).reshape(-1) - azimuth_center
    theta = _adjust_query_angles(theta, azimuth_unwrapped)
    z_flat = zz.reshape(-1)
    volume = np.zeros(rho.shape[0], dtype=np.float32)
    valid = rho <= rho_limit
    for idx in np.where(valid)[0]:
        theta_q = float(theta[idx])
        rho_q = float(rho[idx])
        z_q = float(z_flat[idx])
        h_pos = int(np.argmin(np.abs(height_values - z_q)))
        az_center_idx = int(np.argmin(np.abs(azimuth_unwrapped - theta_q)))
        rho_center_idx = int(np.argmin(np.abs(rho_ref_full - rho_q)))
        az_indices = _azimuth_indices_with_wrap(az_center_idx, len(azimuth_unwrapped))
        rho_indices = _rho_indices_with_clamp(rho_center_idx, len(rho_ref_full))
        az_kernel = np.sinc((azimuth_unwrapped[az_indices] - theta_q) / du)
        rho_kernel = np.sinc((rho_ref_full[rho_indices] - rho_q) / rho_step)
        weights = az_kernel[:, None] * rho_kernel[None, :]
        patch = full_stack[np.ix_(az_indices, rho_indices, np.array([h_pos]))][:, :, 0]
        volume[idx] = abs(np.sum(patch * weights))
    if volume.max() > 0:
        volume /= volume.max()
    return GeometryCorrectionResult(
        volume=volume.reshape(len(gt["x_values"]), len(gt["y_values"]), len(gt["z_values"])),
        extra_memory_bytes=int(full_stack.nbytes),
    )
