from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn.functional as F

from workspace.common.protocol import PROTOCOL_V1


@dataclass
class EchoSubsetConfig:
    active_cells_per_sample: int = 12
    frequencies_per_cell: int = 24
    fixed_subset: bool = True
    subset_seed: int = 20260419


@dataclass
class GeometryAwareConfig:
    support_threshold_ratio: float = 0.18
    support_weight: float = 2.0
    boundary_weight: float = 1.35
    dilation_radius: int = 1
    use_boundary: bool = False


def _stable_seed(sample_id: str, base_seed: int) -> int:
    digest = hashlib.sha256(f"{sample_id}:{base_seed}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], byteorder="little", signed=False) % (2**32)


def load_sparse_echo_subset(
    echo_path: Path,
    sample_id: str,
    config: EchoSubsetConfig,
) -> dict[str, np.ndarray]:
    payload = np.load(echo_path)
    azimuth_idx = payload["azimuth_idx"].astype(np.int64)
    height_idx = payload["height_idx"].astype(np.int64)
    echo = (payload["echo_real"] + 1j * payload["echo_imag"]).astype(np.complex64)
    rng = np.random.default_rng(_stable_seed(sample_id, config.subset_seed))
    total_cells = len(azimuth_idx)
    if total_cells == 0:
        raise RuntimeError(f"Empty sparse echo for sample_id={sample_id}")
    chosen_cells = np.arange(total_cells)
    if total_cells > config.active_cells_per_sample:
        chosen_cells = np.sort(rng.choice(total_cells, size=config.active_cells_per_sample, replace=False))
    freq_idx = np.arange(PROTOCOL_V1.num_freq)
    if PROTOCOL_V1.num_freq > config.frequencies_per_cell:
        freq_idx = np.sort(rng.choice(PROTOCOL_V1.num_freq, size=config.frequencies_per_cell, replace=False))
    target = echo[chosen_cells][:, freq_idx]
    return {
        "azimuth_idx": azimuth_idx[chosen_cells],
        "height_idx": height_idx[chosen_cells],
        "freq_idx": freq_idx.astype(np.int64),
        "target_echo": target,
    }


def _torch_complex_exp(phase: torch.Tensor) -> torch.Tensor:
    return torch.complex(torch.cos(phase), torch.sin(phase))


def forward_echo_from_volume(
    volume: torch.Tensor,
    x_values: np.ndarray,
    y_values: np.ndarray,
    z_values: np.ndarray,
    subset: dict[str, np.ndarray],
    device: torch.device,
) -> torch.Tensor:
    protocol = PROTOCOL_V1
    amp = volume.to(device=device, dtype=torch.float32)
    xx, yy, zz = torch.meshgrid(
        torch.as_tensor(x_values, dtype=torch.float32, device=device),
        torch.as_tensor(y_values, dtype=torch.float32, device=device),
        torch.as_tensor(z_values, dtype=torch.float32, device=device),
        indexing="ij",
    )
    rho = torch.sqrt(xx * xx + yy * yy + 1.0e-12)
    theta = torch.atan2(yy, xx)
    amp_flat = amp.reshape(-1)
    rho_flat = rho.reshape(-1)
    theta_flat = theta.reshape(-1)
    z_flat = zz.reshape(-1)

    azimuth = torch.as_tensor(protocol.azimuth_values[subset["azimuth_idx"]], dtype=torch.float32, device=device)
    height = torch.as_tensor(protocol.height_values[subset["height_idx"]], dtype=torch.float32, device=device)
    k_values = torch.as_tensor(protocol.k_values[subset["freq_idx"]], dtype=torch.float32, device=device)
    ranges = torch.sqrt(
        protocol.scan_radius**2
        + rho_flat[None, :] ** 2
        - 2.0 * protocol.scan_radius * rho_flat[None, :] * torch.cos(theta_flat[None, :] - azimuth[:, None])
        + (z_flat[None, :] - height[:, None]) ** 2
    )
    phase = -ranges[:, :, None] * k_values[None, None, :]
    kernel = _torch_complex_exp(phase)
    pred_echo = torch.sum(amp_flat[None, :, None].to(torch.complex64) * kernel, dim=1)
    return pred_echo


def _dilate_mask(mask: torch.Tensor, dilation_radius: int) -> torch.Tensor:
    if dilation_radius <= 0:
        return mask
    pooled = F.max_pool3d(mask[None, None, ...], kernel_size=2 * dilation_radius + 1, stride=1, padding=dilation_radius)
    return (pooled[0, 0] > 0).to(mask.dtype)


def build_support_weight_volume(
    pred_volume: torch.Tensor,
    config: GeometryAwareConfig,
) -> tuple[torch.Tensor, dict[str, float]]:
    amp = torch.abs(pred_volume.to(torch.float32))
    peak = torch.max(amp)
    threshold = peak * float(config.support_threshold_ratio)
    support = (amp >= threshold).to(torch.float32)
    dilated = _dilate_mask(support, config.dilation_radius)
    boundary = torch.clamp(dilated - support, min=0.0, max=1.0)
    weights = torch.ones_like(amp)
    weights = weights + support * float(max(config.support_weight - 1.0, 0.0))
    if config.use_boundary:
        weights = weights + boundary * float(max(config.boundary_weight - 1.0, 0.0))
    summary = {
        "support_threshold": float(threshold.item()),
        "support_fraction": float(torch.mean(support).item()),
        "boundary_fraction": float(torch.mean(boundary).item()),
    }
    return weights, summary


def measurement_weights_from_volume(
    pred_volume: torch.Tensor,
    x_values: np.ndarray,
    y_values: np.ndarray,
    z_values: np.ndarray,
    subset: dict[str, np.ndarray],
    geo_config: GeometryAwareConfig,
    device: torch.device,
) -> tuple[torch.Tensor, dict[str, float]]:
    amp = pred_volume.to(device=device, dtype=torch.float32)
    weight_volume, summary = build_support_weight_volume(amp, geo_config)
    xx, yy, zz = torch.meshgrid(
        torch.as_tensor(x_values, dtype=torch.float32, device=device),
        torch.as_tensor(y_values, dtype=torch.float32, device=device),
        torch.as_tensor(z_values, dtype=torch.float32, device=device),
        indexing="ij",
    )
    rho = torch.sqrt(xx * xx + yy * yy + 1.0e-12)
    theta = torch.atan2(yy, xx)
    amp_flat = torch.abs(amp).reshape(-1)
    rho_flat = rho.reshape(-1)
    theta_flat = theta.reshape(-1)
    z_flat = zz.reshape(-1)
    weight_flat = weight_volume.reshape(-1)

    protocol = PROTOCOL_V1
    azimuth = torch.as_tensor(protocol.azimuth_values[subset["azimuth_idx"]], dtype=torch.float32, device=device)
    height = torch.as_tensor(protocol.height_values[subset["height_idx"]], dtype=torch.float32, device=device)
    ranges = torch.sqrt(
        protocol.scan_radius**2
        + rho_flat[None, :] ** 2
        - 2.0 * protocol.scan_radius * rho_flat[None, :] * torch.cos(theta_flat[None, :] - azimuth[:, None])
        + (z_flat[None, :] - height[:, None]) ** 2
    )
    support_energy = torch.sum((amp_flat[None, :] * weight_flat[None, :]) / (ranges + 1.0e-6), dim=1)
    base_energy = torch.sum(amp_flat[None, :] / (ranges + 1.0e-6), dim=1) + 1.0e-6
    measurement_weight = torch.clamp(support_energy / base_energy, min=1.0, max=max(float(geo_config.support_weight), float(geo_config.boundary_weight), 1.0))
    summary["measurement_weight_mean"] = float(measurement_weight.mean().item())
    summary["measurement_weight_max"] = float(measurement_weight.max().item())
    return measurement_weight[:, None], summary


def echo_nmse_loss(
    pred_volume: torch.Tensor,
    x_values: np.ndarray,
    y_values: np.ndarray,
    z_values: np.ndarray,
    subset: dict[str, np.ndarray],
    scale: float,
    device: torch.device,
) -> torch.Tensor:
    pred_echo = forward_echo_from_volume(pred_volume * float(scale), x_values, y_values, z_values, subset, device)
    target_echo = torch.as_tensor(subset["target_echo"], dtype=torch.complex64, device=device)
    diff = pred_echo - target_echo
    numerator = torch.mean(torch.abs(diff) ** 2)
    denominator = torch.mean(torch.abs(target_echo) ** 2) + 1.0e-8
    return numerator / denominator


def echo_geo_nmse_loss(
    pred_volume: torch.Tensor,
    x_values: np.ndarray,
    y_values: np.ndarray,
    z_values: np.ndarray,
    subset: dict[str, np.ndarray],
    scale: float,
    device: torch.device,
    geo_config: GeometryAwareConfig,
) -> tuple[torch.Tensor, dict[str, float]]:
    pred_echo = forward_echo_from_volume(pred_volume * float(scale), x_values, y_values, z_values, subset, device)
    target_echo = torch.as_tensor(subset["target_echo"], dtype=torch.complex64, device=device)
    measurement_weight, summary = measurement_weights_from_volume(pred_volume, x_values, y_values, z_values, subset, geo_config, device)
    diff2 = torch.abs(pred_echo - target_echo) ** 2
    target2 = torch.abs(target_echo) ** 2
    numerator = torch.sum(measurement_weight * diff2)
    denominator = torch.sum(measurement_weight * target2) + 1.0e-8
    return numerator / denominator, summary


def extract_center_patch(volume: torch.Tensor, raw_shape: tuple[int, int, int]) -> torch.Tensor:
    target_shape = volume.shape[-3:]
    starts = [max((target_shape[i] - raw_shape[i]) // 2, 0) for i in range(3)]
    return volume[
        ...,
        starts[0] : starts[0] + raw_shape[0],
        starts[1] : starts[1] + raw_shape[1],
        starts[2] : starts[2] + raw_shape[2],
    ]


def summarize_config(config: EchoSubsetConfig, lambda_pc: float) -> dict[str, Any]:
    return {
        "lambda_pc": lambda_pc,
        "subset_sampling": {
            "active_cells_per_sample": config.active_cells_per_sample,
            "frequencies_per_cell": config.frequencies_per_cell,
            "fixed_subset": config.fixed_subset,
            "subset_seed": config.subset_seed,
        },
        "physics_consistency": "sampled forward echo consistency on sparse measurement subset",
    }


def summarize_geometry_config(config: GeometryAwareConfig) -> dict[str, Any]:
    return {
        "support_threshold_ratio": config.support_threshold_ratio,
        "support_weight": config.support_weight,
        "boundary_weight": config.boundary_weight,
        "dilation_radius": config.dilation_radius,
        "use_boundary": config.use_boundary,
        "mask_mode": "dynamic_prediction_support",
    }
