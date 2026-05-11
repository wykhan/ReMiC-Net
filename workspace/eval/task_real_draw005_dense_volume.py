from __future__ import annotations

import argparse
import math
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from workspace.common.io_utils import ensure_dir, write_json, write_text
from workspace.common.protocol import PROTOCOL_V1, wrap_angle
from workspace.eval.metrics_3d import nmse, psnr, ssim_global
from workspace.eval.task_real_draw001_qualitative import (
    BASELINE_CKPT,
    METHOD_SLUG,
    METHODS,
    PROJECT_ROOT,
    TARGET_SHAPE,
    _fit_volume,
    _load_unet,
    _run_unet,
)
from workspace.recon.cyl_fast_reference_engine import build_ground_truth, reconstruct_cylindrical_reference
from workspace.sim.sim_utils import measurement_range, visibility_indices


TASK_NAME = "task_real_draw005"
RECON_METHODS = ["ref3", "ref9", "BP"]
LABELS = ["GT"] + METHODS
GRID_SHAPE = TARGET_SHAPE
ROTATION_DEG = {"x": 8.0, "y": -9.0, "z": 14.0}
TARGET_CENTER_M = np.array([0.205, 0.020, 0.000], dtype=np.float64)
TUBE_RADIUS_M = 0.008
FORWARD_THRESHOLD = 0.055
DB_FLOOR = -40.0


def _rotation_matrix() -> np.ndarray:
    ax, ay, az = [math.radians(ROTATION_DEG[key]) for key in ["x", "y", "z"]]
    rx = np.array(
        [[1.0, 0.0, 0.0], [0.0, math.cos(ax), -math.sin(ax)], [0.0, math.sin(ax), math.cos(ax)]],
        dtype=np.float64,
    )
    ry = np.array(
        [[math.cos(ay), 0.0, math.sin(ay)], [0.0, 1.0, 0.0], [-math.sin(ay), 0.0, math.cos(ay)]],
        dtype=np.float64,
    )
    rz = np.array(
        [[math.cos(az), -math.sin(az), 0.0], [math.sin(az), math.cos(az), 0.0], [0.0, 0.0, 1.0]],
        dtype=np.float64,
    )
    return rz @ ry @ rx


def _segment_distance(points: np.ndarray, start: np.ndarray, stop: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    direction = stop - start
    denom = max(float(np.dot(direction, direction)), 1.0e-12)
    alpha = np.clip(np.sum((points - start) * direction[None, :], axis=1) / denom, 0.0, 1.0)
    closest = start[None, :] + alpha[:, None] * direction[None, :]
    distance = np.linalg.norm(points - closest, axis=1)
    return distance, alpha


def build_dense_y_volume() -> dict[str, Any]:
    protocol = PROTOCOL_V1
    x_values = TARGET_CENTER_M[0] + (np.arange(GRID_SHAPE[0], dtype=np.float64) - (GRID_SHAPE[0] - 1) / 2.0) * protocol.xy_spacing
    y_values = TARGET_CENTER_M[1] + (np.arange(GRID_SHAPE[1], dtype=np.float64) - (GRID_SHAPE[1] - 1) / 2.0) * protocol.xy_spacing
    z_values = TARGET_CENTER_M[2] + (np.arange(GRID_SHAPE[2], dtype=np.float64) - (GRID_SHAPE[2] - 1) / 2.0) * protocol.height_spacing
    xg, yg, zg = np.meshgrid(x_values, y_values, z_values, indexing="ij")
    world = np.stack([xg.ravel(), yg.ravel(), zg.ravel()], axis=1)
    local = (world - TARGET_CENTER_M[None, :]) @ _rotation_matrix()

    trunk_start = np.array([0.000, 0.000, -0.030], dtype=np.float64)
    fork = np.array([0.000, 0.000, -0.001], dtype=np.float64)
    left_tip = np.array([-0.028, 0.000, 0.033], dtype=np.float64)
    right_tip = np.array([0.028, 0.000, 0.033], dtype=np.float64)
    segments = [(trunk_start, fork), (fork, left_tip), (fork, right_tip)]

    distance = np.full(local.shape[0], np.inf, dtype=np.float64)
    branch_coord = np.zeros(local.shape[0], dtype=np.float64)
    for seg_idx, (start, stop) in enumerate(segments):
        d_seg, alpha = _segment_distance(local, start, stop)
        update = d_seg < distance
        distance[update] = d_seg[update]
        branch_coord[update] = seg_idx + alpha[update]

    core = np.clip(1.0 - (distance / TUBE_RADIUS_M) ** 2, 0.0, 1.0)
    soft_edge = np.exp(-0.5 * (distance / (0.52 * TUBE_RADIUS_M)) ** 2)
    texture = 0.88 + 0.10 * np.cos(2.7 * branch_coord) + 0.04 * np.sin(5.0 * local[:, 2] / 0.033)
    volume = np.maximum(core, 0.45 * soft_edge) * texture
    volume[distance > 1.18 * TUBE_RADIUS_M] = 0.0
    volume = volume.reshape(GRID_SHAPE).astype(np.float32)
    volume[volume < FORWARD_THRESHOLD] = 0.0
    if float(volume.max()) > 0:
        volume /= float(volume.max())

    return {
        "volume": volume.astype(np.float32),
        "x_values": x_values.astype(np.float64),
        "y_values": y_values.astype(np.float64),
        "z_values": z_values.astype(np.float64),
        "control_points_local_m": {
            "trunk_start": [float(v) for v in trunk_start],
            "fork": [float(v) for v in fork],
            "left_tip": [float(v) for v in left_tip],
            "right_tip": [float(v) for v in right_tip],
        },
    }


def _make_point(x_m: float, y_m: float, z_m: float, amplitude: float) -> dict[str, Any]:
    protocol = PROTOCOL_V1
    rho_m = float(np.hypot(x_m, y_m))
    theta_rad = float(wrap_angle(np.arctan2(y_m, x_m)))
    return {
        "x_m": round(float(x_m), 6),
        "y_m": round(float(y_m), 6),
        "z_m": round(float(z_m), 6),
        "rho_m": round(rho_m, 6),
        "theta_rad": round(theta_rad, 6),
        "amplitude": round(float(amplitude), 6),
        "phase_rad": 0.0,
        "grid_x": protocol.world_to_grid_xy(float(x_m)),
        "grid_y": protocol.world_to_grid_xy(float(y_m)),
        "grid_z": protocol.world_to_grid_z(float(z_m)),
    }


def dense_volume_to_scene(dense: dict[str, Any]) -> dict[str, Any]:
    volume = dense["volume"]
    x_values = dense["x_values"]
    y_values = dense["y_values"]
    z_values = dense["z_values"]
    points = []
    for xi, yi, zi in np.argwhere(volume > 0.0):
        points.append(_make_point(x_values[xi], y_values[yi], z_values[zi], float(volume[xi, yi, zi])))
    return {
        "sample_id": "draw005_dense_manisali_y",
        "split": "draw",
        "seed": 20260511,
        "scene_type": "dense_volume_manisali_style_y",
        "family": "dense_volume_structured_y",
        "shape_params": {
            "primary_representation": "dense reflectivity volume on a 24^3 object grid",
            "compatibility_note": "points are derived from nonzero dense voxels only to reuse existing reconstruction patch metadata",
            "grid_shape": [int(v) for v in volume.shape],
            "tube_radius_m": TUBE_RADIUS_M,
            "rotation_deg": ROTATION_DEG,
            "center_xyz_m": [float(v) for v in TARGET_CENTER_M],
            "control_points_local_m": dense["control_points_local_m"],
            "forward_threshold": FORWARD_THRESHOLD,
        },
        "scatter_rule": {"amplitude": "dense continuous magnitude volume", "phase": "P0 same phase"},
        "point_count": len(points),
        "points": points,
    }


def simulate_dense_volume(dense: dict[str, Any], scene: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    protocol = PROTOCOL_V1
    volume = dense["volume"].astype(np.complex64)
    x_values = dense["x_values"]
    y_values = dense["y_values"]
    z_values = dense["z_values"]
    active_cells: dict[tuple[int, int], np.ndarray] = {}
    voxel_summaries = []
    nonzero = np.argwhere(np.abs(volume) > 0.0)
    started = time.perf_counter()

    for xi, yi, zi in nonzero:
        x_m = float(x_values[xi])
        y_m = float(y_values[yi])
        z_m = float(z_values[zi])
        rho_m = float(np.hypot(x_m, y_m))
        theta_rad = float(wrap_angle(np.arctan2(y_m, x_m)))
        az_idx, h_idx = visibility_indices(theta_target=theta_rad, rho_target=rho_m, z_target=z_m)
        az_sel = protocol.azimuth_values[az_idx]
        h_sel = protocol.height_values[h_idx]
        az_grid, h_grid = np.meshgrid(az_sel, h_sel, indexing="ij")
        ranges = measurement_range(rho_target=rho_m, theta_target=theta_rad, z_target=z_m, azimuth=az_grid, height=h_grid)
        amp = volume[xi, yi, zi]
        local_echo = amp * np.exp(-1j * ranges[..., None] * protocol.k_values[None, None, :])
        for i, a_idx in enumerate(az_idx):
            for j, h_index in enumerate(h_idx):
                key = (int(a_idx), int(h_index))
                if key not in active_cells:
                    active_cells[key] = np.zeros(protocol.num_freq, dtype=np.complex64)
                active_cells[key] += local_echo[i, j].astype(np.complex64)
        if len(voxel_summaries) < 12:
            voxel_summaries.append(
                {
                    "x_m": x_m,
                    "y_m": y_m,
                    "z_m": z_m,
                    "rho_m": rho_m,
                    "theta_rad": theta_rad,
                    "amplitude": float(np.abs(amp)),
                    "visible_azimuth_count": int(len(az_idx)),
                    "visible_height_count": int(len(h_idx)),
                }
            )

    ordered_keys = sorted(active_cells)
    azimuth_idx = np.array([item[0] for item in ordered_keys], dtype=np.int32)
    height_idx = np.array([item[1] for item in ordered_keys], dtype=np.int32)
    echo_matrix = np.stack([active_cells[item] for item in ordered_keys], axis=0) if ordered_keys else np.zeros((0, protocol.num_freq), dtype=np.complex64)
    output_path = output_dir / f"{scene['sample_id']}_echo_sparse.npz"
    np.savez_compressed(
        output_path,
        azimuth_idx=azimuth_idx,
        height_idx=height_idx,
        echo_real=echo_matrix.real.astype(np.float32),
        echo_imag=echo_matrix.imag.astype(np.float32),
        shape=np.array([protocol.num_azimuth, protocol.num_freq, protocol.num_height], dtype=np.int32),
    )
    metadata = {
        "sample_id": scene["sample_id"],
        "split": scene["split"],
        "operator": "dense_volume_forward_operator",
        "echo_path": str(output_path),
        "wall_time_sec": float(time.perf_counter() - started),
        "active_measurement_count": int(len(ordered_keys)),
        "dense_shape": [protocol.num_azimuth, protocol.num_freq, protocol.num_height],
        "nonzero_voxel_count": int(nonzero.shape[0]),
        "voxel_summary_preview": voxel_summaries,
    }
    write_json(output_dir / f"{scene['sample_id']}_echo_meta.json", metadata)
    return metadata


def _fit_preserves_support(raw: np.ndarray, fitted: np.ndarray) -> dict[str, Any]:
    return {
        "raw_shape": [int(v) for v in raw.shape],
        "fit_shape": [int(v) for v in fitted.shape],
        "raw_nonzero_voxels": int(np.count_nonzero(raw)),
        "fit_nonzero_voxels": int(np.count_nonzero(fitted)),
        "support_lost_voxels": int(np.count_nonzero(raw) - np.count_nonzero(fitted)),
        "fits_without_crop": bool(all(raw.shape[i] <= fitted.shape[i] for i in range(3))),
    }


def _db_image(image: np.ndarray) -> np.ndarray:
    image = np.maximum(image.astype(np.float64), 0.0)
    peak = max(float(image.max()), 1.0e-12)
    return np.maximum(20.0 * np.log10(np.maximum(image / peak, 1.0e-12)), DB_FLOOR)


def _draw_cube(ax: plt.Axes) -> None:
    n = np.array(GRID_SHAPE, dtype=np.float64) - 1.0
    faces = [
        [(0, 0, 0), (n[0], 0, 0), (n[0], n[1], 0), (0, n[1], 0)],
        [(0, 0, n[2]), (n[0], 0, n[2]), (n[0], n[1], n[2]), (0, n[1], n[2])],
        [(0, 0, 0), (n[0], 0, 0), (n[0], 0, n[2]), (0, 0, n[2])],
        [(0, n[1], 0), (n[0], n[1], 0), (n[0], n[1], n[2]), (0, n[1], n[2])],
        [(0, 0, 0), (0, n[1], 0), (0, n[1], n[2]), (0, 0, n[2])],
        [(n[0], 0, 0), (n[0], n[1], 0), (n[0], n[1], n[2]), (n[0], 0, n[2])],
    ]
    cube = Poly3DCollection(faces, facecolor=(0.48, 0.52, 0.86, 0.10), edgecolor=(0.45, 0.48, 0.72, 0.18), linewidth=0.45)
    ax.add_collection3d(cube)


def _plot_volume(ax: plt.Axes, volume: np.ndarray, title: str, vmax: float) -> None:
    _draw_cube(ax)
    cmap = mpl.colormaps["plasma"]
    local_peak = max(float(np.max(volume)), 1.0e-6)
    norm = mpl.colors.Normalize(vmin=0.0, vmax=max(local_peak, 1.0e-6))
    levels = [0.22 * local_peak, 0.46 * local_peak, 0.70 * local_peak]
    alphas = [0.12, 0.22, 0.42]
    for level, alpha in zip(levels, alphas):
        mask = volume >= level
        if not np.any(mask):
            continue
        colors = cmap(norm(volume))
        colors[..., 3] = alpha
        ax.voxels(mask, facecolors=colors, edgecolor=(0.22, 0.18, 0.45, 0.05), linewidth=0.05)
    ax.view_init(elev=20, azim=-58)
    ax.set_xlim(0, GRID_SHAPE[0])
    ax.set_ylim(0, GRID_SHAPE[1])
    ax.set_zlim(0, GRID_SHAPE[2])
    ax.set_box_aspect((1.0, 1.0, 1.25))
    ax.set_title(title, fontsize=11, fontweight="bold", pad=1)
    ax.set_xlabel("x", labelpad=-8, fontsize=8)
    ax.set_ylabel("y", labelpad=-8, fontsize=8)
    ax.set_zlabel("z", labelpad=-8, fontsize=8)
    ax.set_xticks([4, 12, 20])
    ax.set_yticks([4, 12, 20])
    ax.set_zticks([4, 12, 20])
    ax.tick_params(labelsize=6, pad=-3)
    ax.grid(True, alpha=0.18)


def _mip(volume: np.ndarray, view: str) -> np.ndarray:
    if view == "xy":
        return volume.max(axis=2)
    if view == "yz":
        return volume.max(axis=0).T
    raise ValueError(view)


def _plot_mip(ax: plt.Axes, volume: np.ndarray, view: str, title: str | None, colorbar: bool = False) -> None:
    image_db = _db_image(_mip(volume, view))
    im = ax.imshow(image_db, cmap="jet", origin="upper" if view == "xy" else "lower", vmin=DB_FLOOR, vmax=0.0, aspect="equal")
    if title:
        ax.text(0.5, 1.24 if colorbar else 1.04, title, transform=ax.transAxes, ha="center", va="bottom", fontsize=8.5)
    if view == "xy":
        ax.set_xlabel("y (m)", fontsize=8)
        ax.set_ylabel("x (m)", fontsize=8)
    else:
        ax.set_xlabel("y (m)", fontsize=8)
        ax.set_ylabel("z (m)", fontsize=8)
    ax.set_xticks([0, 12, 23])
    ax.set_yticks([0, 12, 23])
    ax.set_xticklabels(["-0.06", "0", "0.06"], fontsize=7)
    ax.set_yticklabels(["-0.06", "0", "0.06"], fontsize=7)
    if colorbar:
        cb = plt.colorbar(im, ax=ax, fraction=0.045, pad=0.035, orientation="horizontal", location="top")
        cb.set_ticks([-40, -30, -20, -10, 0])
        cb.ax.tick_params(labelsize=6, pad=1)


def render_manisali_style(volumes: dict[str, np.ndarray], metrics: list[dict[str, Any]], output_path: Path) -> None:
    metric_lookup = {row["method"]: row for row in metrics}
    vmax = max(float(np.max(volumes[label])) for label in LABELS)
    fig = plt.figure(figsize=(15.0, 8.9))
    gs = fig.add_gridspec(3, len(LABELS), height_ratios=[1.08, 1.0, 1.0], hspace=0.42, wspace=0.33)
    for col, label in enumerate(LABELS):
        ax3d = fig.add_subplot(gs[0, col], projection="3d")
        _plot_volume(ax3d, volumes[label], label, vmax)

        ax_xy = fig.add_subplot(gs[1, col])
        if label == "GT":
            title = ""
        else:
            row = metric_lookup[label]
            title = f"PSNR {row['psnr']:.2f} dB - SSIM {row['ssim']:.2f}"
        _plot_mip(ax_xy, volumes[label], "xy", title, colorbar=True)

        ax_yz = fig.add_subplot(gs[2, col])
        _plot_mip(ax_yz, volumes[label], "yz", None, colorbar=False)

    fig.suptitle("Dense-volume continuous Y target: Manisali-style 3D view and dB projections", fontsize=13)
    fig.subplots_adjust(left=0.055, right=0.985, top=0.90, bottom=0.065)
    fig.savefig(output_path, dpi=240)
    plt.close(fig)


def render_individuals(volumes: dict[str, np.ndarray], output_dir: Path) -> None:
    render3d = ensure_dir(output_dir / "single_3d")
    mips = ensure_dir(output_dir / "single_mip")
    vmax = max(float(np.max(volumes[label])) for label in LABELS)
    for label in LABELS:
        slug = "gt" if label == "GT" else METHOD_SLUG[label]
        fig = plt.figure(figsize=(4.6, 4.6))
        ax = fig.add_subplot(1, 1, 1, projection="3d")
        _plot_volume(ax, volumes[label], label, vmax)
        fig.tight_layout()
        fig.savefig(render3d / f"{slug}_volume.png", dpi=240)
        plt.close(fig)

        fig2, axes = plt.subplots(1, 2, figsize=(6.6, 3.2), squeeze=False)
        _plot_mip(axes[0, 0], volumes[label], "xy", "front x-y", colorbar=True)
        _plot_mip(axes[0, 1], volumes[label], "yz", "side y-z", colorbar=True)
        fig2.suptitle(label, fontsize=12)
        fig2.tight_layout(rect=[0, 0, 1, 0.92])
        fig2.savefig(mips / f"{slug}_mips_db.png", dpi=240)
        plt.close(fig2)


def reconstruct_dense_target(output_root: Path) -> dict[str, Any]:
    dataset_dir = ensure_dir(output_root / "dataset")
    scene_dir = ensure_dir(dataset_dir / "scenes")
    echo_dir = ensure_dir(dataset_dir / "echoes")
    dense_dir = ensure_dir(dataset_dir / "dense_volumes")
    gt_dir = ensure_dir(dataset_dir / "gt_volumes")
    recon_dir = ensure_dir(output_root / "recon_cache")

    dense = build_dense_y_volume()
    scene = dense_volume_to_scene(dense)
    scene_path = scene_dir / f"{scene['sample_id']}.json"
    write_json(scene_path, scene)
    dense_path = dense_dir / f"{scene['sample_id']}_dense_volume.npz"
    np.savez_compressed(dense_path, volume=dense["volume"], x_values=dense["x_values"], y_values=dense["y_values"], z_values=dense["z_values"])

    gt_payload = build_ground_truth(scene)
    gt_path = gt_dir / f"{scene['sample_id']}_gt_from_dense_voxels.npz"
    np.savez_compressed(gt_path, **gt_payload)
    simulate_meta = simulate_dense_volume(dense, scene, echo_dir)
    echo_path = Path(simulate_meta["echo_path"])

    raw_recons: dict[str, np.ndarray] = {}
    runtime_rows: list[dict[str, Any]] = []
    for method in RECON_METHODS:
        started = time.perf_counter()
        recon = reconstruct_cylindrical_reference(scene_path, echo_path, method)
        runtime = time.perf_counter() - started
        raw_recons[method] = recon["volume"].astype(np.float32)
        runtime_rows.append(
            {
                "method": method,
                "runtime_sec": float(runtime),
                "quality_raw": recon["quality"],
                "tensor_shape": recon["tensor_shape"],
                "active_coverage_ratio": recon["active_coverage_ratio"],
            }
        )
        np.savez_compressed(
            recon_dir / f"dense_y_{METHOD_SLUG[method]}.npz",
            volume=recon["volume"].astype(np.float32),
            gt_volume=recon["gt_volume"].astype(np.float32),
            x_values=recon["x_values"],
            y_values=recon["y_values"],
            z_values=recon["z_values"],
            runtime_sec=np.array(runtime, dtype=np.float32),
        )

    gt_fit = _fit_volume(gt_payload["volume"])
    fitted = {method: _fit_volume(raw_recons[method]) for method in RECON_METHODS}
    unet = _load_unet()
    fitted["U-Net"] = _run_unet(unet, fitted["ref3"], gt_fit)
    gt_peak = max(float(np.max(gt_fit)), 1.0e-6)
    volumes = {"GT": gt_fit.astype(np.float32) / gt_peak}
    volumes.update({method: np.maximum(fitted[method].astype(np.float32), 0.0) / gt_peak for method in METHODS})

    write_json(
        dataset_dir / "index.json",
        [
            {
                "target_key": "dense_manisali_y",
                "sample_id": scene["sample_id"],
                "dense_volume_path": str(dense_path.relative_to(output_root)),
                "scene_path": str(scene_path.relative_to(output_root)),
                "gt_path": str(gt_path.relative_to(output_root)),
                "echo_path": str(echo_path.relative_to(output_root)),
                "primary_representation": "dense reflectivity volume",
                "derived_nonzero_voxels": int(scene["point_count"]),
            }
        ],
    )
    for method in METHODS:
        np.savez_compressed(recon_dir / f"dense_y_{METHOD_SLUG[method]}_display.npz", volume=volumes[method].astype(np.float32))

    nonzero = np.argwhere(dense["volume"] > 0)
    rho_values = np.array([scene["points"][idx]["rho_m"] for idx in range(len(scene["points"]))], dtype=np.float64)
    theta_values = np.array([scene["points"][idx]["theta_rad"] for idx in range(len(scene["points"]))], dtype=np.float64)
    theta_center = float(np.angle(np.mean(np.exp(1j * theta_values))))
    theta_rel = np.angle(np.exp(1j * (theta_values - theta_center)))
    nearest_ref3 = np.min(np.abs(rho_values[:, None] - PROTOCOL_V1.reference_sets["ref3"][None, :]), axis=1)
    target_stats = {
        "dense_grid_shape": [int(v) for v in dense["volume"].shape],
        "nonzero_voxels": int(nonzero.shape[0]),
        "nonzero_fraction": float(nonzero.shape[0] / dense["volume"].size),
        "rho_min_m": float(rho_values.min()),
        "rho_max_m": float(rho_values.max()),
        "theta_span_deg": float(math.degrees(theta_rel.max() - theta_rel.min())),
        "nearest_ref3_distance_mean_m": float(nearest_ref3.mean()),
        "nearest_ref3_distance_max_m": float(nearest_ref3.max()),
        "forward_operator": "direct dense-voxel projection into protocol-v1 sparse cylindrical echoes",
        "fit_validation": _fit_preserves_support(gt_payload["volume"], gt_fit),
    }
    return {
        "scene": scene,
        "dense_volume_path": dense_path,
        "volumes": volumes,
        "target_stats": target_stats,
        "simulate_meta": simulate_meta,
        "runtime_rows": runtime_rows,
    }


def write_metrics(output_root: Path, payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    gt = payload["volumes"]["GT"]
    for method in METHODS:
        pred = payload["volumes"][method]
        rows.append(
            {
                "target": "dense_manisali_y",
                "method": method,
                "nmse": nmse(pred, gt),
                "psnr": psnr(pred, gt),
                "ssim": ssim_global(pred, gt),
                "peak_value": float(pred.max()),
                "support_voxels_ge_0p10": int(np.count_nonzero(pred >= 0.10)),
            }
        )
    write_json(output_root / "metrics_draw005.json", rows)
    return rows


def write_report(output_root: Path, payload: dict[str, Any], metrics: list[dict[str, Any]]) -> None:
    stats = payload["target_stats"]
    fit = stats["fit_validation"]
    lines = [
        "# task_real_draw005 report",
        "",
        "## Objective",
        "",
        "This task replaces the draw004 point-scatterer-looking rendering with a dense reflectivity-volume target and a Manisali-style 3D qualitative figure.",
        "",
        "## Manisali figure-9 rendering study",
        "",
        "- Paper source: `doc/（U1）Efficient physics-based learned reconstruction methods for real-time 3D near-field MIMO radar imaging.pdf`.",
        "- Source repository inspected: `wykhan/Efficient-Learned-3D-Near-Field-MIMO-Imaging`, especially `src/misc.py`.",
        "- Manisali Fig. 9 uses five method columns, a first-row 3D image-cube view in linear scale, then front/side max projections in dB scale.",
        "- Their public code renders the 3D cube with Plotly `go.Volume`, low opacity around `0.2`, and multiple translucent isosurfaces; max projections use `jet`, `20*log10(abs(x))`, and `[-40, 0]` dB color limits.",
        "- Plotly is not installed in this execution environment, so the static PNG uses a matplotlib multi-threshold translucent voxel-volume renderer with the same low-opacity cube and dB projection policy.",
        "- The 3D row uses per-panel relative isosurface thresholds so weak baseline outputs are still visible; absolute amplitude differences remain recorded in the metrics table.",
        "",
        "## Dense-volume forward operator",
        "",
        "- Implemented as `simulate_dense_volume` in `workspace/eval/task_real_draw005_dense_volume.py`.",
        "- The primary object is a 24^3 dense reflectivity array, not a hand-authored point list.",
        "- The forward model directly iterates over nonzero dense voxels and sums each voxel contribution into the protocol-v1 sparse cylindrical echo tensor.",
        "- A derived scene JSON is written only to reuse the existing ref3/ref9/BP reconstruction patch machinery.",
        f"- Dense volume path: `{payload['dense_volume_path']}`.",
        f"- Nonzero dense voxels after thresholding: `{stats['nonzero_voxels']}` (`{100.0 * stats['nonzero_fraction']:.2f}%` of the 24^3 grid).",
        f"- Echo active measurement cells: `{payload['simulate_meta']['active_measurement_count']}`.",
        f"- Dense forward wall time: `{payload['simulate_meta']['wall_time_sec']:.2f}` sec.",
        "",
        "## Target validation",
        "",
        f"- rho range: `{stats['rho_min_m']:.4f}` to `{stats['rho_max_m']:.4f}` m.",
        f"- theta span: `{stats['theta_span_deg']:.2f}` deg.",
        f"- Mean / max distance to nearest ref3 radius: `{stats['nearest_ref3_distance_mean_m']:.4f}` / `{stats['nearest_ref3_distance_max_m']:.4f}` m.",
        f"- Raw GT patch shape: `{fit['raw_shape']}`.",
        f"- Fitted display shape: `{fit['fit_shape']}`.",
        f"- Support lost during 24^3 fitting: `{fit['support_lost_voxels']}`.",
        f"- Fits without crop: `{fit['fits_without_crop']}`.",
        "",
        "## Outputs",
        "",
        f"- Main Manisali-style composite: `{output_root / 'viz/paper_candidates/manisali_style/dense_y_manisali_3x5.png'}`",
        f"- Individual 3D volume renders: `{output_root / 'viz/paper_candidates/manisali_style/single_3d'}`",
        f"- Individual dB MIP panels: `{output_root / 'viz/paper_candidates/manisali_style/single_mip'}`",
        f"- Manifest: `{output_root / 'draw005_manifest.json'}`",
        "",
        "## Metrics side check",
        "",
        "| Target | Method | NMSE | PSNR | SSIM | peak | support >=0.10 |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in metrics:
        lines.append(
            f"| {row['target']} | {row['method']} | {row['nmse']:.4f} | {row['psnr']:.4f} | "
            f"{row['ssim']:.4f} | {row['peak_value']:.4f} | {row['support_voxels_ge_0p10']} |"
        )
    lines += [
        "",
        "## Interpretation",
        "",
        "The GT panel is now a connected volumetric object rather than a scatter cloud. The first row follows the Manisali-style image-cube idea, while the second and third rows provide the same dB max-projection checks used in Fig. 9. The ordinary U-Net panel remains a baseline compensation result, not a ReMiC-Net / RSB-FiLM result.",
    ]
    write_text(output_root / "task_real_draw005_report.md", "\n".join(lines) + "\n")


def run(output_root: Path) -> dict[str, Any]:
    style_dir = ensure_dir(output_root / "viz" / "paper_candidates" / "manisali_style")
    progress_dir = ensure_dir(output_root / "viz" / "progress")
    manifest_dir = ensure_dir(output_root / "viz" / "manifest")
    payload = reconstruct_dense_target(output_root)
    metrics = write_metrics(output_root, payload)
    main_path = style_dir / "dense_y_manisali_3x5.png"
    render_manisali_style(payload["volumes"], metrics, main_path)
    render_individuals(payload["volumes"], style_dir)
    render_manisali_style(payload["volumes"], metrics, progress_dir / "dense_y_manisali_3x5.png")
    manifest = {
        "task": TASK_NAME,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "prompt": "PROMPTS/task_real_draw005.md",
        "paper": "doc/（U1）Efficient physics-based learned reconstruction methods for real-time 3D near-field MIMO radar imaging.pdf",
        "source_repo_studied": "git@github.com:wykhan/Efficient-Learned-3D-Near-Field-MIMO-Imaging.git",
        "source_files_studied": ["/tmp/Efficient-Learned-3D-Near-Field-MIMO-Imaging/src/misc.py"],
        "methods": METHODS,
        "unet_definition": "ordinary residual 3D U-Net baseline checkpoint from task_real_008; not RSB-FiLM/ReMiC-Net",
        "unet_checkpoint": str(BASELINE_CKPT),
        "dense_forward_operator": "workspace.eval.task_real_draw005_dense_volume.simulate_dense_volume",
        "target_stats": payload["target_stats"],
        "simulate_meta": payload["simulate_meta"],
        "runtime_rows": payload["runtime_rows"],
        "metrics": metrics,
        "main_composite": str(main_path.relative_to(output_root)),
        "individual_3d_dir": str((style_dir / "single_3d").relative_to(output_root)),
        "individual_mip_dir": str((style_dir / "single_mip").relative_to(output_root)),
    }
    write_json(output_root / "draw005_manifest.json", manifest)
    write_json(manifest_dir / "draw005_viz_manifest.json", manifest)
    write_report(output_root, payload, metrics)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate task_real_draw005 dense-volume Manisali-style figures.")
    parser.add_argument("--output-root", default=None)
    args = parser.parse_args()
    if args.output_root is None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_root = PROJECT_ROOT / "exp" / "task_real_draw005_dense_volume" / stamp
    else:
        output_root = Path(args.output_root)
    ensure_dir(output_root)
    manifest = run(output_root)
    print(f"Wrote draw005 dense-volume outputs to {output_root}")
    print(f"Main composite: {output_root / manifest['main_composite']}")


if __name__ == "__main__":
    main()
