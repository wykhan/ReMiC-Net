from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def wrap_angle(angle: np.ndarray | float) -> np.ndarray | float:
    return (np.asarray(angle) + np.pi) % (2.0 * np.pi) - np.pi


@dataclass(frozen=True)
class ProtocolV1:
    c: float = 3.0e8
    scan_radius: float = 0.600
    scene_radius: float = 0.300
    scene_height: float = 2.000
    theta_u_deg: float = 30.0
    theta_h_deg: float = 30.0
    fmin_hz: float = 30.0e9
    fmax_hz: float = 39.0e9
    num_freq: int = 181
    num_azimuth: int = 1101
    num_height: int = 501
    height_spacing: float = 0.004
    xy_spacing: float = 0.005
    rho_ref_spacing: float = 0.01
    patch_xy_size: int = 12
    patch_z_size: int = 12

    @property
    def theta_u_rad(self) -> float:
        return np.deg2rad(self.theta_u_deg)

    @property
    def theta_h_rad(self) -> float:
        return np.deg2rad(self.theta_h_deg)

    @property
    def k_values(self) -> np.ndarray:
        kmin = 4.0 * np.pi * self.fmin_hz / self.c
        kmax = 4.0 * np.pi * self.fmax_hz / self.c
        return np.linspace(kmin, kmax, self.num_freq, dtype=np.float64)

    @property
    def azimuth_values(self) -> np.ndarray:
        return np.linspace(-np.pi, np.pi, self.num_azimuth, dtype=np.float64)

    @property
    def height_values(self) -> np.ndarray:
        half = self.scene_height / 2.0
        return np.linspace(-half, half, self.num_height, dtype=np.float64)

    @property
    def x_values(self) -> np.ndarray:
        return np.linspace(
            -self.scene_radius,
            self.scene_radius,
            int(round(2.0 * self.scene_radius / self.xy_spacing)) + 1,
            dtype=np.float64,
        )

    @property
    def y_values(self) -> np.ndarray:
        return self.x_values.copy()

    @property
    def rho_ref_full(self) -> np.ndarray:
        return np.linspace(
            0.0,
            self.scene_radius,
            int(round(self.scene_radius / self.rho_ref_spacing)) + 1,
            dtype=np.float64,
        )

    @property
    def reference_sets(self) -> dict[str, np.ndarray]:
        return {
            "ref3": np.array([0.00, 0.15, 0.30], dtype=np.float64),
            "ref5": np.array([0.00, 0.08, 0.15, 0.22, 0.30], dtype=np.float64),
            "ref7": np.array([0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30], dtype=np.float64),
            "ref9": np.array([0.00, 0.04, 0.08, 0.11, 0.15, 0.19, 0.22, 0.26, 0.30], dtype=np.float64),
            "BP": self.rho_ref_full,
        }

    @property
    def method_complexity_units(self) -> dict[str, int]:
        return {"ref3": 3, "ref5": 5, "ref7": 7, "ref9": 9, "BP": 31}

    def nearest_reference_radius(self, rho_values: np.ndarray, method: str) -> np.ndarray:
        refs = self.reference_sets[method]
        diff = np.abs(rho_values[:, None] - refs[None, :])
        return refs[np.argmin(diff, axis=1)]

    def world_to_grid_xy(self, value: float) -> int:
        return int(round((value + self.scene_radius) / self.xy_spacing))

    def world_to_grid_z(self, value: float) -> int:
        return int(round((value + self.scene_height / 2.0) / self.height_spacing))

    def grid_to_world_xy(self, index: int) -> float:
        return -self.scene_radius + index * self.xy_spacing

    def grid_to_world_z(self, index: int) -> float:
        return -self.scene_height / 2.0 + index * self.height_spacing

    def clip_xy_index(self, index: int) -> int:
        return int(np.clip(index, 0, len(self.x_values) - 1))

    def clip_z_index(self, index: int) -> int:
        return int(np.clip(index, 0, len(self.height_values) - 1))

    def make_patch_indices(
        self,
        x_indices: Iterable[int],
        y_indices: Iterable[int],
        z_indices: Iterable[int],
        pad_xy: int = 4,
        pad_z: int = 4,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        x_list = list(x_indices)
        y_list = list(y_indices)
        z_list = list(z_indices)
        x_half = self.patch_xy_size // 2
        y_half = self.patch_xy_size // 2
        z_half = self.patch_z_size // 2
        x_start = self.clip_xy_index(min(x_list) - x_half - pad_xy)
        y_start = self.clip_xy_index(min(y_list) - y_half - pad_xy)
        z_start = self.clip_z_index(min(z_list) - z_half - pad_z)
        x_stop = self.clip_xy_index(max(x_list) + x_half + pad_xy)
        y_stop = self.clip_xy_index(max(y_list) + y_half + pad_xy)
        z_stop = self.clip_z_index(max(z_list) + z_half + pad_z)
        return (
            np.arange(x_start, x_stop + 1, dtype=np.int32),
            np.arange(y_start, y_stop + 1, dtype=np.int32),
            np.arange(z_start, z_stop + 1, dtype=np.int32),
        )


PROTOCOL_V1 = ProtocolV1()
