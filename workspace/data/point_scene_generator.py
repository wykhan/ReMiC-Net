from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from workspace.common.protocol import PROTOCOL_V1, wrap_angle


@dataclass(frozen=True)
class SampleConfig:
    sample_id: str
    split: str
    seed: int
    smoke: bool


def _pick_point_count(rng: np.random.Generator) -> int:
    return int(rng.choice([1, 2, 3, 4, 5], p=[0.30, 0.30, 0.20, 0.10, 0.10]))


def _sample_position(rng: np.random.Generator, edge_bias: bool) -> tuple[float, float, float]:
    protocol = PROTOCOL_V1
    if edge_bias:
        rho = float(rng.uniform(0.22, protocol.scene_radius - 0.01))
    else:
        rho = float(rng.uniform(0.03, 0.24))
    theta = float(rng.uniform(-np.pi, np.pi))
    z = float(rng.uniform(-0.85, 0.85))
    x = rho * np.cos(theta)
    y = rho * np.sin(theta)
    return x, y, z


def _sample_cluster_position(
    rng: np.random.Generator,
    anchor: tuple[float, float, float],
) -> tuple[float, float, float]:
    protocol = PROTOCOL_V1
    x0, y0, z0 = anchor
    for _ in range(128):
        dx = float(rng.integers(-5, 6)) * protocol.xy_spacing
        dy = float(rng.integers(-5, 6)) * protocol.xy_spacing
        dz = float(rng.integers(-4, 5)) * protocol.height_spacing
        x = float(np.clip(x0 + dx, -protocol.scene_radius + 0.01, protocol.scene_radius - 0.01))
        y = float(np.clip(y0 + dy, -protocol.scene_radius + 0.01, protocol.scene_radius - 0.01))
        z = float(np.clip(z0 + dz, -0.9, 0.9))
        rho = float(np.sqrt(x * x + y * y))
        if rho <= protocol.scene_radius - 0.005:
            return x, y, z
    return _sample_position(rng, edge_bias=False)


def _is_far_enough(points: list[dict[str, float]], candidate: tuple[float, float, float]) -> bool:
    if not points:
        return True
    xyz = np.array([[p["x_m"], p["y_m"], p["z_m"]] for p in points], dtype=np.float64)
    cand = np.array(candidate, dtype=np.float64)
    dists = np.linalg.norm(xyz - cand[None, :], axis=1)
    return bool(np.all(dists >= 0.025))


def generate_point_scene(config: SampleConfig) -> dict[str, Any]:
    rng = np.random.default_rng(config.seed)
    protocol = PROTOCOL_V1
    point_count = _pick_point_count(rng)
    edge_bias = bool(rng.random() < 0.35)
    points: list[dict[str, float]] = []
    anchor = _sample_position(rng, edge_bias=edge_bias)

    while len(points) < point_count:
        if len(points) == 0:
            candidate = anchor
        elif point_count == 1:
            candidate = _sample_position(rng, edge_bias=edge_bias)
        else:
            candidate = _sample_cluster_position(rng, anchor=anchor)
        if not _is_far_enough(points, candidate):
            continue
        x, y, z = candidate
        rho = float(np.sqrt(x * x + y * y))
        theta = float(wrap_angle(np.arctan2(y, x)))
        amplitude = float(rng.uniform(0.8, 1.2))
        points.append(
            {
                "x_m": round(x, 6),
                "y_m": round(y, 6),
                "z_m": round(z, 6),
                "rho_m": round(rho, 6),
                "theta_rad": round(theta, 6),
                "amplitude": round(amplitude, 6),
                "phase_rad": 0.0,
                "grid_x": protocol.world_to_grid_xy(x),
                "grid_y": protocol.world_to_grid_xy(y),
                "grid_z": protocol.world_to_grid_z(z),
            }
        )

    return {
        "sample_id": config.sample_id,
        "split": config.split,
        "seed": config.seed,
        "smoke": config.smoke,
        "scatter_rule": {"amplitude_range": [0.8, 1.2], "phase_randomized": False},
        "point_count": point_count,
        "points": points,
    }
