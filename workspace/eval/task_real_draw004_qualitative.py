from __future__ import annotations

import argparse
import math
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

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
    _normalize_pair,
    _run_unet,
)
from workspace.recon.cyl_fast_reference_engine import build_ground_truth, reconstruct_cylindrical_reference
from workspace.sim.forward_cylindrical_point import simulate_sample


TASK_NAME = "task_real_draw004"
RECON_METHODS = ["ref3", "ref9", "BP"]
LABELS = ["GT"] + METHODS
ROTATION_DEG = {"x": 6.0, "y": -8.0, "z": 12.0}
TARGET_CENTER_M = np.array([0.205, 0.020, 0.000], dtype=np.float64)
TUBE_RADIUS_M = 0.006
SUPPORT_THRESHOLD = 0.035


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


def _segment_tube_points(start: np.ndarray, stop: np.ndarray, samples: int, radius: float) -> list[np.ndarray]:
    direction = stop - start
    n1, n2 = _orthonormal_frame(direction)
    offsets = [
        np.zeros(3, dtype=np.float64),
        radius * n1,
        -radius * n1,
        radius * n2,
        -radius * n2,
        0.70 * radius * (n1 + n2),
        0.70 * radius * (-n1 + n2),
        0.70 * radius * (n1 - n2),
        0.70 * radius * (-n1 - n2),
    ]
    points = []
    for alpha in np.linspace(0.0, 1.0, samples):
        center = (1.0 - alpha) * start + alpha * stop
        points.extend(center + offset for offset in offsets)
    return points


def build_manisali_inspired_y_scene() -> dict[str, Any]:
    trunk_start = np.array([0.000, 0.000, -0.026], dtype=np.float64)
    fork = np.array([0.000, 0.000, 0.002], dtype=np.float64)
    left_tip = np.array([-0.024, 0.000, 0.032], dtype=np.float64)
    right_tip = np.array([0.024, 0.000, 0.032], dtype=np.float64)

    local_points: list[np.ndarray] = []
    local_points += _segment_tube_points(trunk_start, fork, samples=9, radius=TUBE_RADIUS_M)
    local_points += _segment_tube_points(fork, left_tip, samples=9, radius=TUBE_RADIUS_M)
    local_points += _segment_tube_points(fork, right_tip, samples=9, radius=TUBE_RADIUS_M)

    rotation = _rotation_matrix()
    rng = np.random.default_rng(20260511)
    merged: dict[tuple[int, int, int], dict[str, Any]] = {}
    for local in local_points:
        world = TARGET_CENTER_M + rotation @ local
        rho = float(np.hypot(world[0], world[1]))
        if rho >= PROTOCOL_V1.scene_radius - 0.015:
            continue
        # Mild deterministic magnitude texture only; phase remains P0.
        amp = float(np.clip(0.92 + 0.06 * rng.normal(), 0.78, 1.04))
        point = _make_point(float(world[0]), float(world[1]), float(world[2]), amp)
        key = (point["grid_x"], point["grid_y"], point["grid_z"])
        if key not in merged or point["amplitude"] > merged[key]["amplitude"]:
            merged[key] = point

    points = list(merged.values())
    return {
        "sample_id": "draw004_manisali_inspired_y",
        "split": "draw",
        "seed": 20260511,
        "scene_type": "manisali_inspired_volumetric_y",
        "family": "structured_shape_y",
        "shape_params": {
            "construction": "three finite-thickness tube primitives sampled as a compact connected Y",
            "branch_radius_m": TUBE_RADIUS_M,
            "rotation_deg": ROTATION_DEG,
            "center_xyz_m": [float(v) for v in TARGET_CENTER_M],
            "local_control_points_m": {
                "trunk_start": [float(v) for v in trunk_start],
                "fork": [float(v) for v in fork],
                "left_tip": [float(v) for v in left_tip],
                "right_tip": [float(v) for v in right_tip],
            },
            "design_note": "compact enough for 24^3 U-Net display volume without support crop",
        },
        "scatter_rule": {"amplitude": "M1 mild deterministic variation", "phase": "P0 same phase"},
        "point_count": len(points),
        "points": points,
    }


def _angle_span_rad(theta_values: np.ndarray) -> float:
    center = float(np.angle(np.mean(np.exp(1j * theta_values))))
    rel = np.angle(np.exp(1j * (theta_values - center)))
    return float(rel.max() - rel.min())


def _target_stats(scene: dict[str, Any], gt_volume: np.ndarray, gt_fit: np.ndarray) -> dict[str, Any]:
    points = scene["points"]
    rho_values = np.array([point["rho_m"] for point in points], dtype=np.float64)
    theta_values = np.array([point["theta_rad"] for point in points], dtype=np.float64)
    z_values = np.array([point["z_m"] for point in points], dtype=np.float64)
    ref3 = PROTOCOL_V1.reference_sets["ref3"].astype(np.float64)
    nearest_ref3 = np.min(np.abs(rho_values[:, None] - ref3[None, :]), axis=1)
    return {
        "point_count": int(len(points)),
        "rho_min_m": float(rho_values.min()),
        "rho_max_m": float(rho_values.max()),
        "z_min_m": float(z_values.min()),
        "z_max_m": float(z_values.max()),
        "theta_span_deg": float(math.degrees(_angle_span_rad(theta_values))),
        "nearest_ref3_distance_mean_m": float(nearest_ref3.mean()),
        "nearest_ref3_distance_max_m": float(nearest_ref3.max()),
        "raw_gt_shape": [int(v) for v in gt_volume.shape],
        "target_shape_for_unet": [int(v) for v in TARGET_SHAPE],
        "raw_gt_nonzero_voxels": int(np.count_nonzero(gt_volume)),
        "fit_gt_nonzero_voxels": int(np.count_nonzero(gt_fit)),
        "fit_support_lost_voxels": int(np.count_nonzero(gt_volume) - np.count_nonzero(gt_fit)),
        "fits_24_cube_without_crop": bool(all(gt_volume.shape[idx] <= TARGET_SHAPE[idx] for idx in range(3))),
    }


def _log_image(image: np.ndarray) -> np.ndarray:
    return np.log10(1.0 + np.maximum(image, 0.0))


def _volume_mip(volume: np.ndarray, view: str) -> np.ndarray:
    if view == "xy":
        return volume.max(axis=2).T
    if view == "xz":
        return volume.max(axis=1).T
    if view == "yz":
        return volume.max(axis=0).T
    raise ValueError(view)


def _plot_3d_support(ax: plt.Axes, volume: np.ndarray, title: str, threshold: float, vmax: float) -> None:
    coords = np.argwhere(volume >= threshold)
    if coords.shape[0] > 900:
        values = volume[tuple(coords.T)]
        keep = np.argsort(values)[-900:]
        coords = coords[keep]
    if coords.size:
        values = volume[tuple(coords.T)]
        ax.scatter(
            coords[:, 0],
            coords[:, 1],
            coords[:, 2],
            c=values,
            cmap="viridis",
            vmin=0.0,
            vmax=vmax,
            s=18,
            alpha=0.84,
            depthshade=False,
        )
    ax.view_init(elev=24, azim=-54)
    ax.set_xlim(0, TARGET_SHAPE[0] - 1)
    ax.set_ylim(0, TARGET_SHAPE[1] - 1)
    ax.set_zlim(0, TARGET_SHAPE[2] - 1)
    ax.set_box_aspect((1.0, 1.0, 1.0))
    ax.set_title(title, fontsize=11, pad=0)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_zticks([])
    ax.set_xlabel("x", labelpad=-8)
    ax.set_ylabel("y", labelpad=-8)
    ax.set_zlabel("z", labelpad=-8)


def _plot_mip(ax: plt.Axes, volume: np.ndarray, view: str, vmax: float, title: str | None = None) -> None:
    image = _volume_mip(volume, view)
    ax.imshow(_log_image(image), origin="lower", cmap="viridis", vmin=0.0, vmax=max(np.log10(1.0 + vmax), 1.0e-6))
    if title is not None:
        ax.set_title(title, fontsize=11)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlabel(view[0])
    ax.set_ylabel(view[1])


def render_main_composite(volumes: dict[str, np.ndarray], output_path: Path) -> None:
    vmax = max(float(np.percentile(volumes[label], 99.7)) for label in LABELS)
    vmax = max(vmax, 1.0e-6)
    fig = plt.figure(figsize=(15.2, 8.6))
    for col, label in enumerate(LABELS):
        ax3d = fig.add_subplot(3, len(LABELS), col + 1, projection="3d")
        _plot_3d_support(ax3d, volumes[label], label, threshold=SUPPORT_THRESHOLD, vmax=vmax)

        ax_xy = fig.add_subplot(3, len(LABELS), len(LABELS) + col + 1)
        _plot_mip(ax_xy, volumes[label], "xy", vmax, "top-like MIP" if col == 0 else None)

        ax_xz = fig.add_subplot(3, len(LABELS), 2 * len(LABELS) + col + 1)
        _plot_mip(ax_xz, volumes[label], "xz", vmax, "side-like MIP" if col == 0 else None)

    fig.suptitle("Manisali-inspired compact volumetric Y: GT, ref3, ref9, BP, and ordinary U-Net", fontsize=14)
    fig.tight_layout(rect=[0, 0, 1, 0.955])
    fig.savefig(output_path, dpi=240)
    plt.close(fig)


def render_individual_outputs(volumes: dict[str, np.ndarray], output_dir: Path) -> None:
    single_3d = ensure_dir(output_dir / "single_3d")
    single_mip = ensure_dir(output_dir / "single_mip")
    vmax = max(float(np.percentile(volumes[label], 99.7)) for label in LABELS)
    vmax = max(vmax, 1.0e-6)
    for label in LABELS:
        slug = "gt" if label == "GT" else METHOD_SLUG[label]
        fig = plt.figure(figsize=(4.2, 4.0))
        ax = fig.add_subplot(1, 1, 1, projection="3d")
        _plot_3d_support(ax, volumes[label], label, threshold=SUPPORT_THRESHOLD, vmax=vmax)
        fig.tight_layout()
        fig.savefig(single_3d / f"{slug}_3d.png", dpi=240)
        plt.close(fig)

        fig2, axes = plt.subplots(1, 3, figsize=(8.8, 3.0), squeeze=False)
        for ax2, view in zip(axes[0], ["xy", "xz", "yz"]):
            _plot_mip(ax2, volumes[label], view, vmax, view.upper())
        fig2.suptitle(label, fontsize=12)
        fig2.tight_layout(rect=[0, 0, 1, 0.90])
        fig2.savefig(single_mip / f"{slug}_mips.png", dpi=240)
        plt.close(fig2)


def reconstruct_target(output_root: Path) -> dict[str, Any]:
    dataset_dir = ensure_dir(output_root / "dataset")
    scene_dir = ensure_dir(dataset_dir / "scenes")
    echo_dir = ensure_dir(dataset_dir / "echoes")
    gt_dir = ensure_dir(dataset_dir / "gt_volumes")
    recon_dir = ensure_dir(output_root / "recon_cache")

    scene = build_manisali_inspired_y_scene()
    scene_path = scene_dir / f"{scene['sample_id']}.json"
    write_json(scene_path, scene)
    gt_payload = build_ground_truth(scene)
    gt_path = gt_dir / f"{scene['sample_id']}_gt.npz"
    np.savez_compressed(gt_path, **gt_payload)
    simulate_meta = simulate_sample(scene, echo_dir)
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
            recon_dir / f"manisali_y_{METHOD_SLUG[method]}.npz",
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
    display_volumes = {"GT": gt_fit.astype(np.float32) / gt_peak}
    display_volumes.update({method: fitted[method].astype(np.float32) / gt_peak for method in METHODS})

    write_json(
        dataset_dir / "index.json",
        [
            {
                "target_key": "manisali_y",
                "sample_id": scene["sample_id"],
                "scene_path": str(scene_path.relative_to(output_root)),
                "gt_path": str(gt_path.relative_to(output_root)),
                "echo_path": str(echo_path.relative_to(output_root)),
                "point_count": len(scene["points"]),
            }
        ],
    )
    for method in METHODS:
        slug = METHOD_SLUG[method]
        np.savez_compressed(recon_dir / f"manisali_y_{slug}_display.npz", volume=display_volumes[method].astype(np.float32))

    return {
        "scene": scene,
        "volumes": display_volumes,
        "target_stats": _target_stats(scene, gt_payload["volume"], gt_fit),
        "runtime_rows": runtime_rows,
    }


def write_metrics(output_root: Path, payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    gt = payload["volumes"]["GT"]
    for method in METHODS:
        pred = payload["volumes"][method]
        rows.append(
            {
                "target": "manisali_y",
                "method": method,
                "nmse": nmse(pred, gt),
                "psnr": psnr(pred, gt),
                "ssim": ssim_global(pred, gt),
                "peak_value": float(pred.max()),
                "support_voxels_at_threshold": int(np.count_nonzero(pred >= SUPPORT_THRESHOLD)),
            }
        )
    write_json(output_root / "metrics_draw004.json", rows)
    return rows


def write_report(output_root: Path, payload: dict[str, Any], metrics: list[dict[str, Any]]) -> None:
    stats = payload["target_stats"]
    lines = [
        "# task_real_draw004 report",
        "",
        "## Task objective",
        "",
        "Generate an overall 3D qualitative imaging figure for a Manisali-inspired volumetric Y target, using GT, ref3, ref9, BP, and the ordinary residual U-Net baseline.",
        "",
        "## Context files used",
        "",
        "- `CONTEXT/manisali_inspired_target_protocol.md`",
        "- `CONTEXT/remic_net_effect_figure_design_recommendations.md`",
        "- `CONTEXT/visualization_protocol.md`",
        "",
        "## Target design",
        "",
        "- Target family: compact finite-thickness structured Y, inspired by the Manisali-style overall 3D imaging protocol rather than reproducing an external object.",
        f"- Point count after grid deduplication: `{stats['point_count']}`.",
        f"- rho range: `{stats['rho_min_m']:.4f}` to `{stats['rho_max_m']:.4f}` m.",
        f"- z range: `{stats['z_min_m']:.4f}` to `{stats['z_max_m']:.4f}` m.",
        f"- theta span: `{stats['theta_span_deg']:.2f}` deg.",
        f"- Mean / max distance to nearest ref3 radius: `{stats['nearest_ref3_distance_mean_m']:.4f}` / `{stats['nearest_ref3_distance_max_m']:.4f}` m.",
        "- Scatter model: mild magnitude variation M1, phase P0.",
        "",
        "## Draw003 issue avoided",
        "",
        f"- Raw GT patch shape: `{stats['raw_gt_shape']}`.",
        f"- U-Net/display target shape: `{stats['target_shape_for_unet']}`.",
        f"- Raw GT nonzero voxels: `{stats['raw_gt_nonzero_voxels']}`.",
        f"- Fitted GT nonzero voxels: `{stats['fit_gt_nonzero_voxels']}`.",
        f"- Support lost during 24^3 fitting: `{stats['fit_support_lost_voxels']}`.",
        f"- Fits 24^3 without crop: `{stats['fits_24_cube_without_crop']}`.",
        "",
        "## Outputs",
        "",
        f"- Main 3x5 composite: `{output_root / 'viz/paper_candidates/qualitative/manisali_y_3x5.png'}`",
        f"- Individual 3D renders: `{output_root / 'viz/paper_candidates/qualitative/single_3d'}`",
        f"- Individual MIP panels: `{output_root / 'viz/paper_candidates/qualitative/single_mip'}`",
        f"- Progress copy: `{output_root / 'viz/progress/manisali_y_3x5.png'}`",
        "",
        "## Visualization policy",
        "",
        f"- All methods use the same 24^3 display grid, the same GT-peak normalization, the same log10(1 + A) MIP display, and the same 3D support threshold `{SUPPORT_THRESHOLD}`.",
        "- The ordinary U-Net panel is the final compensated reconstruction from the task_real_008 residual U-Net baseline, not ReMiC-Net / RSB-FiLM.",
        "",
        "## Metrics side check",
        "",
        "| Target | Method | NMSE | PSNR | SSIM | peak | support voxels |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in metrics:
        lines.append(
            f"| {row['target']} | {row['method']} | {row['nmse']:.4f} | {row['psnr']:.4f} | "
            f"{row['ssim']:.4f} | {row['peak_value']:.4f} | {row['support_voxels_at_threshold']} |"
        )
    lines += [
        "",
        "## Interpretation",
        "",
        "This figure is intended as an overall 3D qualitative visualization rather than a radial-mismatch diagnostic. The compact target keeps the bifurcation and both branches visible while staying within the 24^3 display volume without support loss, so the comparison is more suitable than draw003 for reader-facing overall imaging.",
    ]
    write_text(output_root / "task_real_draw004_report.md", "\n".join(lines) + "\n")


def run(output_root: Path) -> dict[str, Any]:
    qualitative_dir = ensure_dir(output_root / "viz" / "paper_candidates" / "qualitative")
    progress_dir = ensure_dir(output_root / "viz" / "progress")
    manifest_dir = ensure_dir(output_root / "viz" / "manifest")

    payload = reconstruct_target(output_root)
    main_path = qualitative_dir / "manisali_y_3x5.png"
    render_main_composite(payload["volumes"], main_path)
    render_individual_outputs(payload["volumes"], qualitative_dir)
    render_main_composite(payload["volumes"], progress_dir / "manisali_y_3x5.png")
    metrics = write_metrics(output_root, payload)

    manifest = {
        "task": TASK_NAME,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "prompt": "PROMPTS/task_real_draw004.md",
        "context": [
            "CONTEXT/manisali_inspired_target_protocol.md",
            "CONTEXT/remic_net_effect_figure_design_recommendations.md",
            "CONTEXT/visualization_protocol.md",
        ],
        "methods": METHODS,
        "unet_definition": "ordinary residual 3D U-Net baseline checkpoint from task_real_008; not RSB-FiLM/ReMiC-Net",
        "unet_checkpoint": str(BASELINE_CKPT),
        "target_stats": payload["target_stats"],
        "runtime_rows": payload["runtime_rows"],
        "main_composite": str(main_path.relative_to(output_root)),
        "individual_3d_dir": str((qualitative_dir / "single_3d").relative_to(output_root)),
        "individual_mip_dir": str((qualitative_dir / "single_mip").relative_to(output_root)),
        "metrics": metrics,
    }
    write_json(output_root / "draw004_manifest.json", manifest)
    write_json(manifest_dir / "draw004_viz_manifest.json", manifest)
    write_report(output_root, payload, metrics)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate task_real_draw004 Manisali-inspired 3D qualitative figures.")
    parser.add_argument("--output-root", default=None)
    args = parser.parse_args()
    if args.output_root is None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_root = PROJECT_ROOT / "exp" / "task_real_draw004_qualitative" / stamp
    else:
        output_root = Path(args.output_root)
    ensure_dir(output_root)
    manifest = run(output_root)
    print(f"Wrote draw004 qualitative figure outputs to {output_root}")
    print(f"Main composite: {output_root / manifest['main_composite']}")


if __name__ == "__main__":
    main()
