from __future__ import annotations

import argparse
import math
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import torch

from workspace.common.io_utils import ensure_dir, write_json, write_text
from workspace.common.protocol import PROTOCOL_V1, wrap_angle
from workspace.eval.metrics_3d import nmse, psnr, ssim_global
from workspace.models.remicnet_rsb_film import ResidualUNet3DBaseline
from workspace.recon.cyl_fast_reference_engine import build_ground_truth, reconstruct_cylindrical_reference
from workspace.sim.forward_cylindrical_point import simulate_sample


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TASK_NAME = "task_real_draw001"
TARGET_SHAPE = (24, 24, 24)
METHODS = ["ref3", "ref9", "BP", "U-Net"]
METHOD_SLUG = {"ref3": "ref3", "ref9": "ref9", "BP": "bp", "U-Net": "unet"}
TARGET_ROWS = [
    ("point", "Two isolated points"),
    ("y", "Y-shaped target"),
    ("random_ext", "Random extended target"),
]
REF3_RADII = [0.0, 0.15, 0.30]
BASELINE_CKPT = PROJECT_ROOT / "exp" / "task_real_008_remicnet_eval" / "20260511_082329" / "checkpoints" / "baseline" / "best.pt"


def _make_point(rho_m: float, theta_rad: float, z_m: float, amplitude: float = 1.0) -> dict[str, Any]:
    protocol = PROTOCOL_V1
    theta_rad = float(wrap_angle(theta_rad))
    x_m = float(rho_m * math.cos(theta_rad))
    y_m = float(rho_m * math.sin(theta_rad))
    return {
        "x_m": round(x_m, 6),
        "y_m": round(y_m, 6),
        "z_m": round(float(z_m), 6),
        "rho_m": round(float(rho_m), 6),
        "theta_rad": round(theta_rad, 6),
        "amplitude": round(float(amplitude), 6),
        "phase_rad": 0.0,
        "grid_x": protocol.world_to_grid_xy(x_m),
        "grid_y": protocol.world_to_grid_xy(y_m),
        "grid_z": protocol.world_to_grid_z(float(z_m)),
    }


def _snap_xy(value: float) -> float:
    protocol = PROTOCOL_V1
    return float(protocol.grid_to_world_xy(protocol.clip_xy_index(protocol.world_to_grid_xy(value))))


def _snap_z(value: float) -> float:
    protocol = PROTOCOL_V1
    return float(protocol.grid_to_world_z(protocol.clip_z_index(protocol.world_to_grid_z(value))))


def _dedupe(points: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[tuple[float, float, float], dict[str, Any]] = {}
    for point in points:
        key = (point["x_m"], point["y_m"], point["z_m"])
        if key not in merged or point["amplitude"] > merged[key]["amplitude"]:
            merged[key] = point
    return list(merged.values())


def _line_points(
    start: tuple[float, float, float],
    stop: tuple[float, float, float],
    count: int,
    amplitude: float,
) -> list[dict[str, Any]]:
    points = []
    for alpha in np.linspace(0.0, 1.0, count):
        rho = (1.0 - alpha) * start[0] + alpha * stop[0]
        theta = (1.0 - alpha) * start[1] + alpha * stop[1]
        z_m = (1.0 - alpha) * start[2] + alpha * stop[2]
        points.append(_make_point(float(rho), float(theta), _snap_z(float(z_m)), amplitude))
    return points


def _scene(sample_id: str, scene_type: str, points: list[dict[str, Any]], notes: dict[str, Any]) -> dict[str, Any]:
    return {
        "sample_id": sample_id,
        "split": "draw",
        "seed": 20260511,
        "scene_type": scene_type,
        "family": scene_type,
        "shape_params": notes,
        "point_count": len(points),
        "scatter_rule": {"phase_randomized": False},
        "points": _dedupe(points),
    }


def build_scenes() -> dict[str, dict[str, Any]]:
    rng = np.random.default_rng(20260511)

    point_scene = _scene(
        "draw001_two_points",
        "two_isolated_points",
        [
            _make_point(0.150, -0.18, -0.120, 1.0),
            _make_point(0.225, 0.24, 0.180, 0.95),
        ],
        {
            "purpose": "one point lies on ref3 rho=0.15 m, the other lies midway between ref3 rho=0.15 and 0.30 m",
            "nearest_ref_distance_m": [0.0, 0.075],
        },
    )

    y_points: list[dict[str, Any]] = []
    fork = (0.225, 0.02, 0.010)
    y_points += _line_points((0.225, 0.02, -0.145), fork, 12, 1.0)
    y_points += _line_points(fork, (0.205, -0.115, 0.175), 12, 0.92)
    y_points += _line_points(fork, (0.248, 0.150, 0.170), 12, 0.88)
    y_scene = _scene(
        "draw001_y_target",
        "y_shaped_target",
        y_points,
        {
            "purpose": "thin Y-shaped extended target at inter-reference radii to expose branch continuity and fork preservation",
            "branch_count": 3,
        },
    )

    random_points: list[dict[str, Any]] = []
    anchors = [
        (0.205, -0.150, -0.110),
        (0.245, -0.060, -0.030),
        (0.215, 0.055, 0.055),
        (0.255, 0.145, 0.140),
    ]
    for start, stop in zip(anchors[:-1], anchors[1:]):
        random_points += _line_points(start, stop, 9, 0.72)
    for rho, theta, z_m in anchors:
        for _ in range(5):
            random_points.append(
                _make_point(
                    float(np.clip(rho + rng.normal(0.0, 0.012), 0.05, 0.29)),
                    float(theta + rng.normal(0.0, 0.025)),
                    _snap_z(float(z_m + rng.normal(0.0, 0.022))),
                    float(rng.uniform(0.62, 1.12)),
                )
            )
    random_scene = _scene(
        "draw001_random_extended",
        "random_extended_target",
        random_points,
        {
            "purpose": "new synthetic irregular connected/semi-connected extended target inspired only by generic Manisali-style ET demonstrations",
            "anchor_count": len(anchors),
        },
    )

    return {"point": point_scene, "y": y_scene, "random_ext": random_scene}


def _fit_volume(volume: np.ndarray, target_shape: tuple[int, int, int] = TARGET_SHAPE) -> np.ndarray:
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


def _resample_axis(values: np.ndarray, length: int) -> np.ndarray:
    if len(values) == length:
        return values.astype(np.float32)
    return np.linspace(float(values.min()), float(values.max()), length, dtype=np.float32)


def _normalize_pair(coarse: np.ndarray, gt: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    scale = max(float(np.max(np.abs(coarse))), float(np.max(np.abs(gt))), 1.0e-6)
    return coarse.astype(np.float32) / scale, gt.astype(np.float32) / scale, scale


def _load_unet() -> ResidualUNet3DBaseline:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = ResidualUNet3DBaseline(base_channels=8).to(device)
    ckpt = torch.load(BASELINE_CKPT, map_location=device)
    model.load_state_dict(ckpt["model_state"])
    model.eval()
    return model


def _run_unet(model: ResidualUNet3DBaseline, ref3: np.ndarray, gt: np.ndarray) -> np.ndarray:
    device = next(model.parameters()).device
    coarse, _, _ = _normalize_pair(ref3, gt)
    with torch.no_grad():
        input_tensor = torch.from_numpy(coarse[None, None, ...]).to(device)
        delta = model(input_tensor)
        pred = torch.clamp(input_tensor + delta, min=0.0).cpu().numpy()[0, 0]
    return pred.astype(np.float32)


def _rho_z_projection(volume: np.ndarray, x_values: np.ndarray, y_values: np.ndarray, z_values: np.ndarray, rho_bins: int = 96) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    xg, yg = np.meshgrid(x_values, y_values, indexing="ij")
    rho = np.sqrt(xg**2 + yg**2)
    edges = np.linspace(0.0, PROTOCOL_V1.scene_radius, rho_bins + 1, dtype=np.float32)
    proj = np.zeros((rho_bins, len(z_values)), dtype=np.float32)
    for ridx in range(rho_bins):
        mask = (rho >= edges[ridx]) & (rho < edges[ridx + 1])
        if np.any(mask):
            proj[ridx, :] = volume[mask, :].max(axis=0)
    centers = 0.5 * (edges[:-1] + edges[1:])
    return proj, centers, z_values.astype(np.float32)


def _plot_panel(
    image: np.ndarray,
    rho_axis: np.ndarray,
    z_axis: np.ndarray,
    output_path: Path,
    title: str,
    vmax: float,
    show_colorbar: bool = True,
) -> None:
    fig, ax = plt.subplots(figsize=(4.0, 3.2))
    image_show = np.log10(1.0 + np.maximum(image, 0.0))
    vmax_show = float(np.log10(1.0 + max(vmax, 1.0e-6)))
    im = ax.imshow(
        image_show.T,
        origin="lower",
        aspect="auto",
        cmap="viridis",
        vmin=0.0,
        vmax=max(vmax_show, 1.0e-6),
        extent=[float(rho_axis.min()), float(rho_axis.max()), float(z_axis.min()), float(z_axis.max())],
    )
    for radius in REF3_RADII:
        ax.axvline(radius, color="white", linestyle="--", linewidth=0.7, alpha=0.75)
    ax.set_title(title, fontsize=10)
    ax.set_xlabel("rho (m)")
    ax.set_ylabel("z (m)")
    if show_colorbar:
        cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label("log10(1 + A)", fontsize=8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=220)
    plt.close(fig)


def _plot_composite(rows: list[dict[str, Any]], output_path: Path, include_gt: bool = False) -> None:
    col_labels = (["GT"] if include_gt else []) + METHODS
    fig, axes = plt.subplots(len(rows), len(col_labels), figsize=(3.2 * len(col_labels), 8.6), squeeze=False)
    for row_idx, row in enumerate(rows):
        row_vmax = row["display_vmax"]
        for col_idx, label in enumerate(col_labels):
            method_key = "GT" if label == "GT" else label
            proj = row["projections"][method_key]
            proj_show = np.log10(1.0 + np.maximum(proj, 0.0))
            vmax_show = float(np.log10(1.0 + max(row_vmax, 1.0e-6)))
            ax = axes[row_idx, col_idx]
            im = ax.imshow(
                proj_show.T,
                origin="lower",
                aspect="auto",
                cmap="viridis",
                vmin=0.0,
                vmax=max(vmax_show, 1.0e-6),
                extent=[
                    float(row["rho_axis"].min()),
                    float(row["rho_axis"].max()),
                    float(row["z_axis"].min()),
                    float(row["z_axis"].max()),
                ],
            )
            for radius in REF3_RADII:
                ax.axvline(radius, color="white", linestyle="--", linewidth=0.65, alpha=0.72)
            if row_idx == 0:
                ax.set_title(label, fontsize=12)
            if col_idx == 0:
                ax.set_ylabel(f"{row['row_label']}\nz (m)", fontsize=10)
            else:
                ax.set_yticks([])
            ax.set_xlabel("rho (m)")
            if col_idx == len(col_labels) - 1:
                cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
                cbar.set_label("log10(1 + A)", fontsize=8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=220)
    plt.close(fig)


def run(output_root: Path) -> dict[str, Any]:
    scenes = build_scenes()
    dataset_dir = ensure_dir(output_root / "dataset")
    scene_dir = ensure_dir(dataset_dir / "scenes")
    echo_dir = ensure_dir(dataset_dir / "echoes")
    gt_dir = ensure_dir(dataset_dir / "gt_volumes")
    recon_dir = ensure_dir(output_root / "recon_cache")
    single_dir = ensure_dir(output_root / "viz" / "paper_candidates" / "qualitative" / "single_images")
    progress_dir = ensure_dir(output_root / "viz" / "progress" / "recon_compare")
    manifest_dir = ensure_dir(output_root / "viz" / "manifest")

    unet = _load_unet()
    rows_for_plot: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    index_rows: list[dict[str, Any]] = []

    for target_key, row_label in TARGET_ROWS:
        scene = scenes[target_key]
        sample_id = scene["sample_id"]
        scene_path = scene_dir / f"{sample_id}.json"
        write_json(scene_path, scene)
        gt_payload = build_ground_truth(scene)
        gt_path = gt_dir / f"{sample_id}_gt.npz"
        np.savez_compressed(gt_path, **gt_payload)
        simulate_meta = simulate_sample(scene, echo_dir)
        echo_path = Path(simulate_meta["echo_path"])
        index_rows.append(
            {
                "target_key": target_key,
                "sample_id": sample_id,
                "scene_path": str(scene_path.relative_to(output_root)),
                "gt_path": str(gt_path.relative_to(output_root)),
                "echo_path": str(echo_path.relative_to(output_root)),
                "point_count": len(scene["points"]),
            }
        )

        raw_recons: dict[str, np.ndarray] = {}
        raw_axes: dict[str, np.ndarray] = {}
        for method in ["ref3", "ref9", "BP"]:
            started = time.perf_counter()
            recon = reconstruct_cylindrical_reference(scene_path, echo_path, method)
            runtime = time.perf_counter() - started
            raw_recons[method] = recon["volume"].astype(np.float32)
            raw_axes = {"x": recon["x_values"], "y": recon["y_values"], "z": recon["z_values"]}
            np.savez_compressed(
                recon_dir / f"{target_key}_{METHOD_SLUG[method]}.npz",
                volume=recon["volume"].astype(np.float32),
                gt_volume=recon["gt_volume"].astype(np.float32),
                x_values=recon["x_values"],
                y_values=recon["y_values"],
                z_values=recon["z_values"],
                runtime_sec=np.array(runtime, dtype=np.float32),
            )

        gt_fit = _fit_volume(gt_payload["volume"])
        fitted = {method: _fit_volume(raw_recons[method]) for method in ["ref3", "ref9", "BP"]}
        fitted["U-Net"] = _run_unet(unet, fitted["ref3"], gt_fit)
        gt_norm_reference = max(float(np.max(gt_fit)), 1.0e-6)
        display_volumes = {"GT": gt_fit / gt_norm_reference}
        display_volumes.update({method: fitted[method] / gt_norm_reference for method in METHODS})

        x_axis = _resample_axis(raw_axes["x"], TARGET_SHAPE[0])
        y_axis = _resample_axis(raw_axes["y"], TARGET_SHAPE[1])
        z_axis = _resample_axis(raw_axes["z"], TARGET_SHAPE[2])
        projections: dict[str, np.ndarray] = {}
        rho_axis = None
        z_proj_axis = None
        for label, volume in display_volumes.items():
            proj, rho_axis, z_proj_axis = _rho_z_projection(volume, x_axis, y_axis, z_axis)
            projections[label] = proj
        assert rho_axis is not None and z_proj_axis is not None
        display_vmax = max(float(np.percentile(projections[method], 99.5)) for method in METHODS + ["GT"])
        display_vmax = max(display_vmax, 1.0e-6)

        for method in METHODS:
            output_path = single_dir / f"{target_key}_{METHOD_SLUG[method]}.png"
            _plot_panel(projections[method], rho_axis, z_proj_axis, output_path, f"{row_label} | {method}", display_vmax)
            np.savez_compressed(
                recon_dir / f"{target_key}_{METHOD_SLUG[method]}_display.npz",
                volume=display_volumes[method].astype(np.float32),
                rho_z_projection=projections[method].astype(np.float32),
                rho_axis=rho_axis,
                z_axis=z_proj_axis,
            )
            metric_pred = display_volumes[method]
            peak_idx = np.unravel_index(int(np.argmax(projections[method])), projections[method].shape)
            records.append(
                {
                    "target": target_key,
                    "sample_id": sample_id,
                    "method": method,
                    "nmse": nmse(metric_pred, display_volumes["GT"]),
                    "psnr": psnr(metric_pred, display_volumes["GT"]),
                    "ssim": ssim_global(metric_pred, display_volumes["GT"]),
                    "projection_peak_rho_m": float(rho_axis[peak_idx[0]]),
                    "projection_peak_z_m": float(z_proj_axis[peak_idx[1]]),
                    "projection_peak_value": float(projections[method][peak_idx]),
                    "display_vmax_linear_before_log": float(display_vmax),
                }
            )
        _plot_panel(projections["GT"], rho_axis, z_proj_axis, single_dir / f"{target_key}_gt.png", f"{row_label} | GT", display_vmax)

        rows_for_plot.append(
            {
                "target_key": target_key,
                "row_label": row_label,
                "projections": projections,
                "rho_axis": rho_axis,
                "z_axis": z_proj_axis,
                "display_vmax": display_vmax,
            }
        )

    composite_path = output_root / "viz" / "paper_candidates" / "qualitative" / "qualitative_comparison_3x4.png"
    composite_gt_path = output_root / "viz" / "paper_candidates" / "qualitative" / "qualitative_comparison_3x5_with_gt.png"
    _plot_composite(rows_for_plot, composite_path, include_gt=False)
    _plot_composite(rows_for_plot, composite_gt_path, include_gt=True)
    _plot_composite(rows_for_plot, progress_dir / "draw001_qualitative_comparison_3x4.png", include_gt=False)

    write_json(dataset_dir / "index.json", index_rows)
    write_json(output_root / "metrics_draw001.json", records)
    manifest = {
        "task": TASK_NAME,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "blueprint": "CONTEXT/remic_net_effect_figure_design_recommendations.md",
        "prompt": "PROMPTS/task_real_draw001.md",
        "methods": METHODS,
        "unet_definition": "ordinary residual 3D U-Net baseline checkpoint from task_real_008, not RSB-FiLM/ReMiC-Net",
        "unet_checkpoint": str(BASELINE_CKPT),
        "display": {
            "panel_type": "rho-z max-over-theta projection",
            "normalization": "per-target GT peak normalization, shared across the four method columns",
            "render_transform": "log10(1 + A), with one shared color scale per target row",
            "ref3_reference_radii_m": REF3_RADII,
        },
        "primary_composite": str(composite_path.relative_to(output_root)),
        "auxiliary_gt_composite": str(composite_gt_path.relative_to(output_root)),
        "single_image_dir": str(single_dir.relative_to(output_root)),
        "records": records,
    }
    write_json(output_root / "draw001_manifest.json", manifest)
    write_json(manifest_dir / "draw001_viz_manifest.json", manifest)

    interpretation = _build_interpretation(output_root, records)
    write_text(output_root / "task_real_draw001_report.md", interpretation)
    return manifest


def _build_interpretation(output_root: Path, records: list[dict[str, Any]]) -> str:
    by_target = {key: [row for row in records if row["target"] == key] for key, _ in TARGET_ROWS}
    lines = [
        "# task_real_draw001 report",
        "",
        "## Outputs",
        "",
        f"- Primary 3x4 composite: `{output_root / 'viz/paper_candidates/qualitative/qualitative_comparison_3x4.png'}`",
        f"- GT auxiliary composite: `{output_root / 'viz/paper_candidates/qualitative/qualitative_comparison_3x5_with_gt.png'}`",
        f"- Single panels: `{output_root / 'viz/paper_candidates/qualitative/single_images'}`",
        f"- Manifest: `{output_root / 'draw001_manifest.json'}`",
        "",
        "## Method scope",
        "",
        "- `U-Net` is the ordinary residual 3D U-Net baseline from task_real_008.",
        "- It is not the RSB-FiLM/ReMiC-Net branch.",
        "- Panels use rho-z max-over-theta projections to retain the radial reference-surface dimension.",
        "- Each target row uses one shared GT-peak color scale across ref3/ref9/BP/U-Net.",
        "- Rendering uses `log10(1 + A)` after shared per-row normalization to keep the point-target dynamic range inspectable.",
        "",
        "## Projection side check",
        "",
        "| Target | Method | peak rho (m) | peak z (m) | peak value |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for target_key, _ in TARGET_ROWS:
        lookup = {row["method"]: row for row in by_target[target_key]}
        for method in METHODS:
            lines.append(
                f"| {target_key} | {method} | "
                f"{lookup[method]['projection_peak_rho_m']:.4f} | "
                f"{lookup[method]['projection_peak_z_m']:.4f} | "
                f"{lookup[method]['projection_peak_value']:.4g} |"
            )
    lines += [
        "",
        "## Scientific interpretation",
        "",
        "This first-round figure family is useful as a qualitative screening tool because the rho-z display keeps the radial mismatch axis visible while still fitting the requested 3x4 multi-method layout.",
        "",
        "The two-point row is the most direct diagnostic for reference-surface mismatch: one scatterer is on the rho=0.15 m ref3 surface and the other is between rho=0.15 m and rho=0.30 m. It should be used to judge localization sharpness and inter-reference defocus.",
        "",
        "The Y-shaped target is the most useful structure-preservation case. The fork and branch tips make it easier to see whether a method preserves continuity or smears thin geometry along rho.",
        "",
        "The random extended target provides a broader clutter/artifact check, but it is less mechanism-specific than the first two rows. It is better suited as a supplementary qualitative row unless its artifacts are visibly distinctive in follow-up rounds.",
        "",
        "For the next round, a shell-wise figure or local zoom around the two-point inter-reference scatterer and the Y bifurcation would be a stronger paper candidate than adding more random targets.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate task_real_draw001 qualitative comparison figures.")
    parser.add_argument("--output-root", default=None)
    args = parser.parse_args()
    if args.output_root is None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_root = PROJECT_ROOT / "exp" / "task_real_draw001_qualitative" / stamp
    else:
        output_root = Path(args.output_root)
    ensure_dir(output_root)
    manifest = run(output_root)
    print(f"Wrote draw001 qualitative figure outputs to {output_root}")
    print(f"Primary composite: {output_root / manifest['primary_composite']}")


if __name__ == "__main__":
    main()
