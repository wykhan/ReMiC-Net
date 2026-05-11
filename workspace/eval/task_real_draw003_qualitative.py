from __future__ import annotations

import argparse
import math
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import torch

from workspace.common.io_utils import ensure_dir, write_json, write_text
from workspace.common.protocol import PROTOCOL_V1, wrap_angle
from workspace.eval.metrics_3d import nmse, psnr, ssim_global
from workspace.eval.task_real_draw001_qualitative import (
    BASELINE_CKPT,
    METHOD_SLUG,
    PROJECT_ROOT,
    REF3_RADII,
    TARGET_SHAPE,
    _fit_volume,
    _load_unet,
    _normalize_pair,
    _resample_axis,
    _rho_z_projection,
    _run_unet,
)
from workspace.recon.cyl_fast_reference_engine import build_ground_truth, reconstruct_cylindrical_reference
from workspace.sim.forward_cylindrical_point import simulate_sample


TASK_NAME = "task_real_draw003"
METHODS = ["ref3", "ref9", "BP", "ref3 + U-Net"]
RECON_METHODS = ["ref3", "ref9", "BP"]
ROI = {"rho_min": 0.170, "rho_max": 0.265, "z_min": -0.055, "z_max": 0.105}
ROTATION_DEG = {"x": 18.0, "y": -22.0, "z": 28.0}


def _log_image(image: np.ndarray) -> np.ndarray:
    return np.log10(1.0 + np.maximum(image, 0.0))


def _rotation_matrix() -> np.ndarray:
    ax, ay, az = [math.radians(ROTATION_DEG[k]) for k in ["x", "y", "z"]]
    rx = np.array([[1, 0, 0], [0, math.cos(ax), -math.sin(ax)], [0, math.sin(ax), math.cos(ax)]], dtype=np.float64)
    ry = np.array([[math.cos(ay), 0, math.sin(ay)], [0, 1, 0], [-math.sin(ay), 0, math.cos(ay)]], dtype=np.float64)
    rz = np.array([[math.cos(az), -math.sin(az), 0], [math.sin(az), math.cos(az), 0], [0, 0, 1]], dtype=np.float64)
    return rz @ ry @ rx


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


def _orthonormal_frame(direction: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    direction = direction / max(float(np.linalg.norm(direction)), 1.0e-9)
    ref = np.array([0.0, 0.0, 1.0], dtype=np.float64)
    if abs(float(np.dot(direction, ref))) > 0.9:
        ref = np.array([0.0, 1.0, 0.0], dtype=np.float64)
    n1 = np.cross(direction, ref)
    n1 /= max(float(np.linalg.norm(n1)), 1.0e-9)
    n2 = np.cross(direction, n1)
    n2 /= max(float(np.linalg.norm(n2)), 1.0e-9)
    return n1, n2


def _segment_solid_points(start: np.ndarray, stop: np.ndarray, samples: int, radius: float) -> list[np.ndarray]:
    direction = stop - start
    n1, n2 = _orthonormal_frame(direction)
    offsets = [
        np.zeros(3),
        radius * n1,
        -radius * n1,
        radius * n2,
        -radius * n2,
        0.72 * radius * (n1 + n2),
        0.72 * radius * (-n1 + n2),
        0.72 * radius * (n1 - n2),
        0.72 * radius * (-n1 - n2),
    ]
    pts = []
    for alpha in np.linspace(0.0, 1.0, samples):
        center = (1.0 - alpha) * start + alpha * stop
        pts.extend(center + offset for offset in offsets)
    return pts


def build_thick_y_scene() -> dict[str, Any]:
    # Local coordinates are in meters. z is the main trunk direction before rotation.
    trunk_start = np.array([0.0, 0.0, -0.090], dtype=np.float64)
    fork = np.array([0.0, 0.0, 0.020], dtype=np.float64)
    left_tip = np.array([-0.050, 0.0, 0.115], dtype=np.float64)
    right_tip = np.array([0.052, 0.0, 0.118], dtype=np.float64)
    radius = 0.010
    local_points = []
    local_points += _segment_solid_points(trunk_start, fork, samples=12, radius=radius)
    local_points += _segment_solid_points(fork, left_tip, samples=11, radius=radius)
    local_points += _segment_solid_points(fork, right_tip, samples=11, radius=radius)
    rotation = _rotation_matrix()
    center = np.array([0.205, 0.035, 0.000], dtype=np.float64)
    merged: dict[tuple[int, int, int], dict[str, Any]] = {}
    rng = np.random.default_rng(20260511)
    for local in local_points:
        world = center + rotation @ local
        rho = float(np.hypot(world[0], world[1]))
        if rho >= PROTOCOL_V1.scene_radius - 0.01 or not (-0.85 <= world[2] <= 0.85):
            continue
        amp = float(np.clip(0.86 + 0.10 * rng.normal(), 0.68, 1.08))
        point = _make_point(float(world[0]), float(world[1]), float(world[2]), amp)
        key = (point["grid_x"], point["grid_y"], point["grid_z"])
        if key not in merged or point["amplitude"] > merged[key]["amplitude"]:
            merged[key] = point
    points = list(merged.values())
    return {
        "sample_id": "draw003_thick_rotated_y",
        "split": "draw",
        "seed": 20260511,
        "scene_type": "thick_rotated_y_target",
        "family": "thick_rotated_y",
        "shape_params": {
            "construction": "three cylindrical branch primitives represented by finite-thickness scatterer samples",
            "branch_radius_m": radius,
            "rotation_deg": ROTATION_DEG,
            "center_xyz_m": [float(v) for v in center],
            "point_count": len(points),
        },
        "scatter_rule": {"amplitude": "mildly varying around 0.86 to 1.08", "phase_randomized": False},
        "point_count": len(points),
        "points": points,
    }


def _roi_to_indices(rho_axis: np.ndarray, z_axis: np.ndarray, roi: dict[str, float]) -> tuple[slice, slice]:
    rmask = np.where((rho_axis >= roi["rho_min"]) & (rho_axis <= roi["rho_max"]))[0]
    zmask = np.where((z_axis >= roi["z_min"]) & (z_axis <= roi["z_max"]))[0]
    if len(rmask) == 0 or len(zmask) == 0:
        return slice(0, len(rho_axis)), slice(0, len(z_axis))
    return slice(int(rmask[0]), int(rmask[-1]) + 1), slice(int(zmask[0]), int(zmask[-1]) + 1)


def _plot_3d_support(ax: plt.Axes, volume: np.ndarray, title: str, threshold_fraction: float = 0.42) -> None:
    vmax = max(float(volume.max()), 1.0e-6)
    threshold = threshold_fraction * vmax
    coords = np.argwhere(volume >= threshold)
    if coords.shape[0] > 550:
        values = volume[tuple(coords.T)]
        keep = np.argsort(values)[-550:]
        coords = coords[keep]
    vals = volume[tuple(coords.T)] if coords.size else np.array([0.0])
    ax.scatter(coords[:, 0], coords[:, 1], coords[:, 2], c=vals, cmap="viridis", s=18, alpha=0.82, depthshade=False)
    ax.view_init(elev=22, azim=-58)
    ax.set_title(title, fontsize=11)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_zticks([])
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_zlabel("z")
    ax.set_box_aspect((1, 1, 1))


def _plot_mip(ax: plt.Axes, volume: np.ndarray, view: str, vmax: float, title: str | None = None) -> None:
    if view == "xy":
        image = volume.max(axis=2).T
        xlabel, ylabel = "x", "y"
    elif view == "xz":
        image = volume.max(axis=1).T
        xlabel, ylabel = "x", "z"
    elif view == "yz":
        image = volume.max(axis=0).T
        xlabel, ylabel = "y", "z"
    else:
        raise ValueError(view)
    ax.imshow(_log_image(image), origin="lower", cmap="viridis", vmin=0.0, vmax=max(np.log10(1.0 + vmax), 1.0e-6))
    if title:
        ax.set_title(title, fontsize=11)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_xticks([])
    ax.set_yticks([])


def render_family_a(volumes: dict[str, np.ndarray], output_dir: Path) -> None:
    labels = ["GT"] + METHODS
    fig = plt.figure(figsize=(16.0, 3.6))
    for idx, label in enumerate(labels):
        ax = fig.add_subplot(1, len(labels), idx + 1, projection="3d")
        _plot_3d_support(ax, volumes[label], label, threshold_fraction=0.35 if label == "GT" else 0.50)
    fig.suptitle("Thick rotated Y target: perspective support view", fontsize=14)
    fig.tight_layout()
    fig.savefig(output_dir / "familyA_primary_thickY_perspective.png", dpi=220)
    plt.close(fig)

    vmax = max(float(np.percentile(volumes[label], 99.5)) for label in labels)
    fig2, axes = plt.subplots(3, len(labels), figsize=(16.0, 8.2), squeeze=False)
    for col, label in enumerate(labels):
        for row, view in enumerate(["xy", "xz", "yz"]):
            _plot_mip(axes[row, col], volumes[label], view, vmax, label if row == 0 else None)
            if col == 0:
                axes[row, col].set_ylabel(f"{view.upper()} MIP")
    fig2.suptitle("Thick rotated Y target: multi-view MIP comparison", fontsize=14)
    fig2.tight_layout(rect=[0, 0, 1, 0.95])
    fig2.savefig(output_dir / "familyA_primary_thickY_multiview.png", dpi=220)
    plt.close(fig2)


def _render_rhoz_panel(
    ax: plt.Axes,
    image: np.ndarray,
    gt: np.ndarray,
    rho_axis: np.ndarray,
    z_axis: np.ndarray,
    vmax: float,
    title: str,
    roi: dict[str, float] | None,
) -> None:
    ax.imshow(
        _log_image(image).T,
        origin="lower",
        aspect="auto",
        cmap="viridis",
        vmin=0.0,
        vmax=max(np.log10(1.0 + vmax), 1.0e-6),
        extent=[float(rho_axis.min()), float(rho_axis.max()), float(z_axis.min()), float(z_axis.max())],
    )
    if np.any(gt > 0):
        ax.contour(rho_axis, z_axis, gt.T, levels=[float(np.percentile(gt[gt > 0], 55))], colors="white", linewidths=1.0)
    for radius in REF3_RADII:
        ax.axvline(radius, color="white", linestyle="--", linewidth=0.8, alpha=0.72)
    if roi is not None:
        ax.add_patch(
            patches.Rectangle(
                (roi["rho_min"], roi["z_min"]),
                roi["rho_max"] - roi["rho_min"],
                roi["z_max"] - roi["z_min"],
                fill=False,
                edgecolor="cyan",
                linewidth=1.4,
            )
        )
    ax.set_title(title, fontsize=11)
    ax.set_xlabel("rho (m)")
    ax.set_ylabel("z (m)")


def render_family_b(projections: dict[str, np.ndarray], rho_axis: np.ndarray, z_axis: np.ndarray, output_dir: Path) -> None:
    labels = ["GT"] + METHODS
    vmax = max(float(np.percentile(projections[label], 99.5)) for label in labels)
    fig, axes = plt.subplots(1, len(labels), figsize=(16.2, 3.7), squeeze=False)
    for col, label in enumerate(labels):
        _render_rhoz_panel(axes[0, col], projections[label], projections["GT"], rho_axis, z_axis, vmax, label, ROI)
        if col > 0:
            axes[0, col].set_ylabel("")
            axes[0, col].set_yticklabels([])
    fig.suptitle("Thick rotated Y: rho-z mechanism view with GT contour, ref3 surfaces, and ROI", fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.92])
    fig.savefig(output_dir / "familyB_mechanism_thickY_rhoz.png", dpi=220)
    plt.close(fig)


def render_family_c(projections: dict[str, np.ndarray], rho_axis: np.ndarray, z_axis: np.ndarray, output_dir: Path) -> None:
    labels = ["GT"] + METHODS
    rs, zs = _roi_to_indices(rho_axis, z_axis, ROI)
    rr = rho_axis[rs]
    zz = z_axis[zs]
    recon_vmax = max(float(np.percentile(projections[label][rs, zs], 99.5)) for label in labels)
    err_maps = {label: np.abs(projections[label] - projections["GT"]) for label in METHODS}
    corr_maps = {label: np.abs(projections[label] - projections["ref3"]) for label in ["ref9", "BP", "ref3 + U-Net"]}
    err_vmax = max(float(np.percentile(err_maps[label][rs, zs], 99.0)) for label in METHODS)
    corr_vmax = max(float(np.percentile(corr_maps[label][rs, zs], 99.0)) for label in corr_maps)
    fig, axes = plt.subplots(3, len(labels), figsize=(16.2, 8.4), squeeze=False)
    for col, label in enumerate(labels):
        ax = axes[0, col]
        ax.imshow(
            _log_image(projections[label][rs, zs]).T,
            origin="lower",
            aspect="auto",
            cmap="viridis",
            vmin=0.0,
            vmax=max(np.log10(1.0 + recon_vmax), 1.0e-6),
            extent=[float(rr.min()), float(rr.max()), float(zz.min()), float(zz.max())],
        )
        gt_roi = projections["GT"][rs, zs]
        if np.any(gt_roi > 0):
            ax.contour(rr, zz, gt_roi.T, levels=[float(np.percentile(gt_roi[gt_roi > 0], 55))], colors="white", linewidths=1.0)
        ax.set_title(label, fontsize=11)
        ax.set_xlabel("rho (m)")
        ax.set_ylabel("ROI recon\nz (m)" if col == 0 else "")
        if col > 0:
            ax.set_yticklabels([])

        ax = axes[1, col]
        if label == "GT":
            ax.axis("off")
            ax.text(0.5, 0.5, "GT reference", ha="center", va="center", transform=ax.transAxes)
        else:
            ax.imshow(
                err_maps[label][rs, zs].T,
                origin="lower",
                aspect="auto",
                cmap="inferno",
                vmin=0.0,
                vmax=max(err_vmax, 1.0e-6),
                extent=[float(rr.min()), float(rr.max()), float(zz.min()), float(zz.max())],
            )
            ax.set_xlabel("rho (m)")
            ax.set_ylabel("|method-GT|\nz (m)" if col == 0 else "")
            if col > 0:
                ax.set_yticklabels([])

        ax = axes[2, col]
        if label in ["GT", "ref3"]:
            ax.axis("off")
            ax.text(0.5, 0.5, "GT" if label == "GT" else "ref3 baseline", ha="center", va="center", transform=ax.transAxes)
        else:
            ax.imshow(
                corr_maps[label][rs, zs].T,
                origin="lower",
                aspect="auto",
                cmap="magma",
                vmin=0.0,
                vmax=max(corr_vmax, 1.0e-6),
                extent=[float(rr.min()), float(rr.max()), float(zz.min()), float(zz.max())],
            )
            ax.set_xlabel("rho (m)")
            ax.set_ylabel("|method-ref3|\nz (m)" if col == 0 else "")
            if col > 0:
                ax.set_yticklabels([])
    fig.suptitle("Thick rotated Y: ROI zoom, absolute error, and change relative to ref3", fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(output_dir / "familyC_zoom_error_thickY.png", dpi=220)
    plt.close(fig)


def reconstruct_target(output_root: Path) -> dict[str, Any]:
    dataset_dir = ensure_dir(output_root / "dataset")
    scene_dir = ensure_dir(dataset_dir / "scenes")
    echo_dir = ensure_dir(dataset_dir / "echoes")
    gt_dir = ensure_dir(dataset_dir / "gt_volumes")
    recon_dir = ensure_dir(output_root / "recon_cache")
    scene = build_thick_y_scene()
    scene_path = scene_dir / f"{scene['sample_id']}.json"
    write_json(scene_path, scene)
    gt_payload = build_ground_truth(scene)
    gt_path = gt_dir / f"{scene['sample_id']}_gt.npz"
    np.savez_compressed(gt_path, **gt_payload)
    simulate_meta = simulate_sample(scene, echo_dir)
    echo_path = Path(simulate_meta["echo_path"])

    raw_recons: dict[str, np.ndarray] = {}
    raw_axes: dict[str, np.ndarray] = {}
    for method in RECON_METHODS:
        started = time.perf_counter()
        recon = reconstruct_cylindrical_reference(scene_path, echo_path, method)
        runtime = time.perf_counter() - started
        raw_recons[method] = recon["volume"].astype(np.float32)
        raw_axes = {"x": recon["x_values"], "y": recon["y_values"], "z": recon["z_values"]}
        np.savez_compressed(
            recon_dir / f"thickY_{METHOD_SLUG[method]}.npz",
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
    fitted["ref3 + U-Net"] = _run_unet(unet, fitted["ref3"], gt_fit)
    _, gt_norm, scale = _normalize_pair(gt_fit, gt_fit)
    volumes = {"GT": gt_norm}
    volumes.update({method: fitted[method].astype(np.float32) / max(scale, 1.0e-6) for method in METHODS})

    x_axis = _resample_axis(raw_axes["x"], TARGET_SHAPE[0])
    y_axis = _resample_axis(raw_axes["y"], TARGET_SHAPE[1])
    z_axis = _resample_axis(raw_axes["z"], TARGET_SHAPE[2])
    projections: dict[str, np.ndarray] = {}
    rho_axis = None
    z_proj_axis = None
    for label, volume in volumes.items():
        proj, rho_axis, z_proj_axis = _rho_z_projection(volume, x_axis, y_axis, z_axis)
        projections[label] = proj
    assert rho_axis is not None and z_proj_axis is not None
    for method in METHODS:
        slug = "unet_comp" if method == "ref3 + U-Net" else METHOD_SLUG[method]
        np.savez_compressed(
            recon_dir / f"thickY_{slug}_display.npz",
            volume=volumes[method].astype(np.float32),
            rho_z_projection=projections[method].astype(np.float32),
            rho_axis=rho_axis,
            z_axis=z_proj_axis,
        )
    write_json(
        dataset_dir / "index.json",
        [
            {
                "target_key": "thickY",
                "sample_id": scene["sample_id"],
                "scene_path": str(scene_path.relative_to(output_root)),
                "gt_path": str(gt_path.relative_to(output_root)),
                "echo_path": str(echo_path.relative_to(output_root)),
                "point_count": len(scene["points"]),
                "rotation_deg": ROTATION_DEG,
            }
        ],
    )
    return {"scene": scene, "volumes": volumes, "projections": projections, "rho_axis": rho_axis, "z_axis": z_proj_axis}


def write_metrics(output_root: Path, payload: dict[str, Any]) -> list[dict[str, Any]]:
    gt = payload["volumes"]["GT"]
    rows = []
    for method in METHODS:
        pred = payload["volumes"][method]
        rows.append({"target": "thickY", "method": method, "nmse": nmse(pred, gt), "psnr": psnr(pred, gt), "ssim": ssim_global(pred, gt)})
    write_json(output_root / "metrics_draw003.json", rows)
    return rows


def write_report(output_root: Path, payload: dict[str, Any], metrics: list[dict[str, Any]]) -> None:
    scene = payload["scene"]
    lines = [
        "# task_real_draw003 report",
        "",
        "## 1. Task objective",
        "",
        "Draw003 upgrades the target itself to a thick, rotated, recognizable 3D Y object while keeping the method comparison fixed to ref3, ref9, BP, and the ordinary residual U-Net compensation on ref3.",
        "",
        "## 2. Why draw002 was not yet sufficient",
        "",
        "Draw002 improved rendering and annotation, but the Y target was still a thin point-built skeleton. That made the reader-facing figures less like a true 3D imaging object.",
        "",
        "## 3. Thick-Y target design",
        "",
        f"- Construction: {scene['shape_params']['construction']}.",
        f"- Thickness: branch radius `{scene['shape_params']['branch_radius_m']:.3f} m`, sampled with cross-section offsets.",
        f"- Rotation: x={ROTATION_DEG['x']} deg, y={ROTATION_DEG['y']} deg, z={ROTATION_DEG['z']} deg.",
        f"- Placement center: `{scene['shape_params']['center_xyz_m']}` m; object spans near and between ref3 reference radii.",
        f"- Scatterer count after grid deduplication: `{scene['point_count']}`.",
        "",
        "## 4. Figure families implemented",
        "",
        f"- Family A: `{output_root / 'viz/paper_candidates/familyA'}`",
        f"- Family B: `{output_root / 'viz/paper_candidates/familyB'}`",
        f"- Family C: `{output_root / 'viz/paper_candidates/familyC'}`",
        "",
        "## 5. Visualization choices",
        "",
        "- Family A includes a perspective support rendering and a three-view MIP comparison.",
        "- Family B uses rho-z max-over-theta projection with GT contour, ref3 reference-surface markers, and an ROI box.",
        "- Family C uses the same ROI for reconstruction zoom, absolute error to GT, and correction/change relative to ref3.",
        "- The learning panel is always the final compensated result `ref3 + U-Net`, not the residual alone.",
        "- Reconstruction/MIP views use shared normalization and `log10(1 + A)` display. Error maps use shared absolute-error scaling within the figure.",
        "",
        "## 6. Reader-interpretability assessment",
        "",
        "The thick target is more object-like than the draw002 skeleton. The perspective view helps communicate that the object is rotated in 3D, while the MIP figure remains useful for method-by-method comparison. Family B and C are still needed because the object-readable views alone do not explain radial reference-surface mismatch.",
        "",
        "## 7. Scientific interpretation",
        "",
        "ref3 shows broad smeared support around the thick Y, while ref9 and BP are more localized. The ordinary `ref3 + U-Net` compensation visibly changes the ref3 output, but it should still be interpreted as a baseline compensation result rather than a ReMiC-Net claim. Object thickness helps expose shape distortion because blur and continuity loss are easier to see than on a one-voxel skeleton.",
        "",
        "## 8. Recommendation for manuscript use",
        "",
        "Use Family A as the main paper qualitative candidate if the paper needs an immediately recognizable object. Use Family B or C as the mechanism companion. A draw004 should replace ordinary `ref3 + U-Net` with the true ReMiC-Net / RSB-FiLM branch if the manuscript claim is structured mismatch compensation by ReMiC-Net.",
        "",
        "## Metrics side check",
        "",
        "| Target | Method | NMSE | PSNR | SSIM |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for row in metrics:
        lines.append(f"| {row['target']} | {row['method']} | {row['nmse']:.4f} | {row['psnr']:.4f} | {row['ssim']:.4f} |")
    write_text(output_root / "task_real_draw003_report.md", "\n".join(lines) + "\n")


def run(output_root: Path) -> dict[str, Any]:
    family_a = ensure_dir(output_root / "viz" / "paper_candidates" / "familyA")
    family_b = ensure_dir(output_root / "viz" / "paper_candidates" / "familyB")
    family_c = ensure_dir(output_root / "viz" / "paper_candidates" / "familyC")
    progress = ensure_dir(output_root / "viz" / "progress")
    manifest_dir = ensure_dir(output_root / "viz" / "manifest")
    payload = reconstruct_target(output_root)
    render_family_a(payload["volumes"], family_a)
    render_family_b(payload["projections"], payload["rho_axis"], payload["z_axis"], family_b)
    render_family_c(payload["projections"], payload["rho_axis"], payload["z_axis"], family_c)
    render_family_a(payload["volumes"], progress)
    metrics = write_metrics(output_root, payload)
    manifest = {
        "task": TASK_NAME,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "prompt": "PROMPTS/task_real_draw003.md",
        "source_draw002": "exp/task_real_draw002_qualitative/20260511_000001",
        "methods": METHODS,
        "unet_definition": "ordinary residual 3D U-Net baseline applied as final ref3 + U-Net compensation; not RSB-FiLM/ReMiC-Net",
        "unet_checkpoint": str(BASELINE_CKPT),
        "target": "thick_rotated_y",
        "rotation_deg": ROTATION_DEG,
        "roi": ROI,
        "familyA": str(family_a.relative_to(output_root)),
        "familyB": str(family_b.relative_to(output_root)),
        "familyC": str(family_c.relative_to(output_root)),
    }
    write_json(output_root / "draw003_manifest.json", manifest)
    write_json(manifest_dir / "draw003_viz_manifest.json", manifest)
    write_report(output_root, payload, metrics)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate task_real_draw003 thick rotated Y qualitative figures.")
    parser.add_argument("--output-root", default=None)
    args = parser.parse_args()
    if args.output_root is None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_root = PROJECT_ROOT / "exp" / "task_real_draw003_qualitative" / stamp
    else:
        output_root = Path(args.output_root)
    ensure_dir(output_root)
    manifest = run(output_root)
    print(f"Wrote draw003 qualitative figure outputs to {output_root}")
    print(f"Family A dir: {output_root / manifest['familyA']}")


if __name__ == "__main__":
    main()
