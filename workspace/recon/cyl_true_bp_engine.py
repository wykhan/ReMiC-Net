from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import numpy as np

from workspace.common.protocol import PROTOCOL_V1
from workspace.recon.cyl_fast_reference_engine import load_sparse_echo
from workspace.sim.sim_utils import measurement_range


def _range_profiles(echo: np.ndarray, n_fft: int) -> tuple[np.ndarray, float]:
    protocol = PROTOCOL_V1
    dk = float(protocol.k_values[1] - protocol.k_values[0])
    dr = float(2.0 * np.pi / (n_fft * dk))
    profiles = np.fft.ifft(echo.astype(np.complex64), n=n_fft, axis=1).astype(np.complex64) * np.float32(n_fft)
    return profiles, dr


def true_backproject_sparse_echo(
    echo_path: Path,
    x_values: np.ndarray,
    y_values: np.ndarray,
    z_values: np.ndarray,
    *,
    voxel_chunk: int = 384,
    measurement_chunk: int = 512,
    n_fft: int = 4096,
) -> dict[str, Any]:
    """Direct voxel-wise cylindrical BP using active sparse echo cells.

    The forward simulator writes y(a,h,k)=sum_p amp(p)*exp(-j*k*R(a,h,p)).
    This BP evaluates sum_{a,h,k} y(a,h,k)*exp(+j*k*R(a,h,p)).
    A zero-padded inverse FFT over the uniformly spaced k samples is used only
    as range-profile interpolation of that same frequency summation.
    """

    protocol = PROTOCOL_V1
    started = time.perf_counter()
    sparse = load_sparse_echo(echo_path)
    echo = sparse["echo"].astype(np.complex64)
    azimuth = protocol.azimuth_values[sparse["azimuth_idx"]].astype(np.float64)
    height = protocol.height_values[sparse["height_idx"]].astype(np.float64)
    profiles, dr = _range_profiles(echo, n_fft=n_fft)

    xg, yg, zg = np.meshgrid(x_values.astype(np.float64), y_values.astype(np.float64), z_values.astype(np.float64), indexing="ij")
    xyz = np.stack([xg.ravel(), yg.ravel(), zg.ravel()], axis=1)
    rho = np.hypot(xyz[:, 0], xyz[:, 1])
    theta = np.arctan2(xyz[:, 1], xyz[:, 0])
    out = np.zeros(xyz.shape[0], dtype=np.complex64)
    k0 = float(protocol.k_values[0])

    for v_start in range(0, xyz.shape[0], voxel_chunk):
        v_stop = min(v_start + voxel_chunk, xyz.shape[0])
        rho_v = rho[v_start:v_stop]
        theta_v = theta[v_start:v_stop]
        z_v = xyz[v_start:v_stop, 2]
        accum = np.zeros(v_stop - v_start, dtype=np.complex64)

        for m_start in range(0, echo.shape[0], measurement_chunk):
            m_stop = min(m_start + measurement_chunk, echo.shape[0])
            ranges = measurement_range(
                rho_target=rho_v[None, :],
                theta_target=theta_v[None, :],
                z_target=z_v[None, :],
                azimuth=azimuth[m_start:m_stop, None],
                height=height[m_start:m_stop, None],
            )
            sample = ranges / dr
            i0 = np.floor(sample).astype(np.int64)
            frac = (sample - i0).astype(np.float32)
            i0 %= n_fft
            i1 = (i0 + 1) % n_fft
            rows = np.arange(m_stop - m_start)[:, None]
            profile_chunk = profiles[m_start:m_stop]
            interp = profile_chunk[rows, i0] * (1.0 - frac) + profile_chunk[rows, i1] * frac
            interp *= np.exp(1j * k0 * ranges).astype(np.complex64)
            accum += np.sum(interp, axis=0).astype(np.complex64)

        out[v_start:v_stop] = accum

    volume = np.abs(out.reshape((len(x_values), len(y_values), len(z_values)))).astype(np.float32)
    runtime = float(time.perf_counter() - started)
    estimated_peak_memory_bytes = int(
        profiles.nbytes
        + measurement_chunk * voxel_chunk * np.dtype(np.float64).itemsize * 3
        + measurement_chunk * voxel_chunk * np.dtype(np.complex64).itemsize * 3
    )
    return {
        "volume": volume,
        "x_values": x_values.astype(np.float64),
        "y_values": y_values.astype(np.float64),
        "z_values": z_values.astype(np.float64),
        "runtime_sec": runtime,
        "active_measurement_count": int(echo.shape[0]),
        "num_freq": int(echo.shape[1]),
        "reconstructed_voxels": int(volume.size),
        "voxel_chunk": int(voxel_chunk),
        "measurement_chunk": int(measurement_chunk),
        "n_fft": int(n_fft),
        "range_bin_spacing_m": dr,
        "estimated_peak_memory_mb": float(estimated_peak_memory_bytes / (1024.0 * 1024.0)),
        "phase_convention": "sum y(a,h,k) * exp(+j*k*R(a,h,p)); range-profile FFT interpolates the same k-domain sum",
    }


def simulate_single_voxel_echo(x_m: float, y_m: float, z_m: float, amplitude: float = 1.0) -> dict[str, np.ndarray]:
    from workspace.sim.sim_utils import visibility_indices

    protocol = PROTOCOL_V1
    rho = float(np.hypot(x_m, y_m))
    theta = float(np.arctan2(y_m, x_m))
    az_idx, h_idx = visibility_indices(theta_target=theta, rho_target=rho, z_target=z_m)
    az_grid, h_grid = np.meshgrid(protocol.azimuth_values[az_idx], protocol.height_values[h_idx], indexing="ij")
    ranges = measurement_range(rho_target=rho, theta_target=theta, z_target=z_m, azimuth=az_grid, height=h_grid)
    echo = amplitude * np.exp(-1j * ranges[..., None] * protocol.k_values[None, None, :])
    aa, hh = np.meshgrid(az_idx, h_idx, indexing="ij")
    return {
        "azimuth_idx": aa.ravel().astype(np.int32),
        "height_idx": hh.ravel().astype(np.int32),
        "echo": echo.reshape(-1, protocol.num_freq).astype(np.complex64),
    }


def write_sparse_echo_npz(path: Path, sparse: dict[str, np.ndarray]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    echo = sparse["echo"]
    np.savez_compressed(
        path,
        azimuth_idx=sparse["azimuth_idx"].astype(np.int32),
        height_idx=sparse["height_idx"].astype(np.int32),
        echo_real=echo.real.astype(np.float32),
        echo_imag=echo.imag.astype(np.float32),
        shape=np.array([PROTOCOL_V1.num_azimuth, PROTOCOL_V1.num_freq, PROTOCOL_V1.num_height], dtype=np.int32),
    )
