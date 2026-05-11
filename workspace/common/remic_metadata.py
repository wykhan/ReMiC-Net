from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np


REF3_RADII_M = np.array([0.0, 0.15, 0.30], dtype=np.float32)
FC_HZ = 34.5e9
LAMBDA_C_M = 3.0e8 / FC_HZ
K2W_C_RAD_PER_M = np.float32(4.0 * math.pi * FC_HZ / 3.0e8)
EPSILON_M = np.float32(0.05)


def fit_volume_to_shape(volume: np.ndarray, target_shape: tuple[int, int, int]) -> np.ndarray:
    output = np.zeros(target_shape, dtype=np.float32)
    src_shape = volume.shape
    copy_shape = tuple(min(src_shape[i], target_shape[i]) for i in range(3))
    src_start = tuple(max((src_shape[i] - copy_shape[i]) // 2, 0) for i in range(3))
    dst_start = tuple(max((target_shape[i] - copy_shape[i]) // 2, 0) for i in range(3))
    output[
        dst_start[0] : dst_start[0] + copy_shape[0],
        dst_start[1] : dst_start[1] + copy_shape[1],
        dst_start[2] : dst_start[2] + copy_shape[2],
    ] = volume[
        src_start[0] : src_start[0] + copy_shape[0],
        src_start[1] : src_start[1] + copy_shape[1],
        src_start[2] : src_start[2] + copy_shape[2],
    ]
    return output


def fit_volume_to_shape_with_fill(volume: np.ndarray, target_shape: tuple[int, int, int], fill_value: float) -> np.ndarray:
    output = np.full(target_shape, fill_value, dtype=np.float32)
    src_shape = volume.shape
    copy_shape = tuple(min(src_shape[i], target_shape[i]) for i in range(3))
    src_start = tuple(max((src_shape[i] - copy_shape[i]) // 2, 0) for i in range(3))
    dst_start = tuple(max((target_shape[i] - copy_shape[i]) // 2, 0) for i in range(3))
    output[
        dst_start[0] : dst_start[0] + copy_shape[0],
        dst_start[1] : dst_start[1] + copy_shape[1],
        dst_start[2] : dst_start[2] + copy_shape[2],
    ] = volume[
        src_start[0] : src_start[0] + copy_shape[0],
        src_start[1] : src_start[1] + copy_shape[1],
        src_start[2] : src_start[2] + copy_shape[2],
    ]
    return output


def wrap_to_pi(values: np.ndarray) -> np.ndarray:
    wrapped = (values + math.pi) % (2.0 * math.pi) - math.pi
    wrapped[np.isclose(wrapped, -math.pi)] = math.pi
    return wrapped.astype(np.float32)


def build_remic_metadata(
    x_values: np.ndarray,
    y_values: np.ndarray,
    z_values: np.ndarray,
    target_shape: tuple[int, int, int],
) -> dict[str, np.ndarray]:
    zz, yy, xx = np.meshgrid(z_values, y_values, x_values, indexing="ij")
    rho = np.sqrt(xx**2 + yy**2, dtype=np.float32)
    shell_dist = np.abs(rho[..., None] - REF3_RADII_M[None, None, None, :])
    shell_idx = np.argmin(shell_dist, axis=-1)
    rho_ref_star = REF3_RADII_M[shell_idx]
    delta_rho_raw = (rho - rho_ref_star).astype(np.float32)
    phi_wrap = wrap_to_pi(K2W_C_RAD_PER_M * delta_rho_raw)
    pcyc = (phi_wrap / math.pi).astype(np.float32)
    mshell = np.stack([(shell_idx == i).astype(np.float32) for i in range(len(REF3_RADII_M))], axis=0)
    m_rsb = (EPSILON_M + (1.0 - EPSILON_M) * np.abs(pcyc)).astype(np.float32)
    return {
        "mshell": np.stack([fit_volume_to_shape(channel, target_shape) for channel in mshell], axis=0),
        "delta_rho_raw": fit_volume_to_shape(delta_rho_raw, target_shape)[None, ...],
        "pcyc": fit_volume_to_shape(pcyc, target_shape)[None, ...],
        "m_rsb": fit_volume_to_shape_with_fill(m_rsb, target_shape, float(EPSILON_M))[None, ...],
        "rho": fit_volume_to_shape(rho.astype(np.float32), target_shape)[None, ...],
    }


def write_metadata_npz(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, **payload)
