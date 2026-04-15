from __future__ import annotations

import numpy as np

from workspace.common.protocol import PROTOCOL_V1, wrap_angle


def dirichlet_phase_sum(delta_r: np.ndarray) -> np.ndarray:
    protocol = PROTOCOL_V1
    k_values = protocol.k_values
    delta_r = np.asarray(delta_r, dtype=np.float64)
    dk = (k_values[-1] - k_values[0]) / (len(k_values) - 1)
    phase_center = np.exp(1j * (k_values[0] + k_values[-1]) * 0.5 * delta_r)
    numerator = np.sin(0.5 * len(k_values) * dk * delta_r)
    denominator = np.sin(0.5 * dk * delta_r)
    ratio = np.where(np.abs(denominator) < 1e-10, len(k_values), numerator / denominator)
    return phase_center * ratio


def measurement_range(rho_target: float, theta_target: float, z_target: float, azimuth: np.ndarray, height: np.ndarray) -> np.ndarray:
    protocol = PROTOCOL_V1
    return np.sqrt(
        protocol.scan_radius**2
        + rho_target**2
        - 2.0 * protocol.scan_radius * rho_target * np.cos(theta_target - azimuth)
        + (z_target - height) ** 2
    )


def visibility_indices(theta_target: float, rho_target: float, z_target: float) -> tuple[np.ndarray, np.ndarray]:
    protocol = PROTOCOL_V1
    az = protocol.azimuth_values
    heights = protocol.height_values
    dtheta = np.abs(wrap_angle(az - theta_target))
    az_idx = np.where(dtheta <= protocol.theta_u_rad / 2.0)[0]
    height_span = (protocol.scan_radius - rho_target) * np.tan(protocol.theta_h_rad / 2.0)
    h_idx = np.where(np.abs(heights - z_target) <= height_span)[0]
    return az_idx.astype(np.int32), h_idx.astype(np.int32)
