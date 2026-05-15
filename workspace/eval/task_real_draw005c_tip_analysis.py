from __future__ import annotations

import argparse
import csv
import math
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

from workspace.common.io_utils import ensure_dir, write_json, write_text
from workspace.common.protocol import PROTOCOL_V1, wrap_angle
from workspace.eval.metrics_3d import nmse, psnr, ssim_global
from workspace.eval.task_real_draw001_qualitative import PROJECT_ROOT
from workspace.eval.task_real_draw005_dense_volume import (
    GRID_SHAPE,
    TARGET_CENTER_M,
    _db_image,
    _fit_volume,
    _plot_volume,
    _rotation_matrix,
)
from workspace.eval.task_real_draw005b_ref3_plus_unet import METHOD_SPECS_3X6, METHOD_SPECS_CLEAN, SOURCE_ROOT


TASK_NAME = "task_real_draw005c"
SOURCE_DRAW005B_ROOT = PROJECT_ROOT / "exp" / "task_real_draw005b_ref3_plus_unet" / "20260511_175843"
SUPPORT_ABS_THRESHOLD = 0.10
DB_FLOOR = -40.0
TIP_NEIGHBORHOOD_RADIUS = 2


TIP_LOCAL_COORDS = {
    "left upper tip": np.array([-0.028, 0.000, 0.033], dtype=np.float64),
    "right upper tip": np.array([0.028, 0.000, 0.033], dtype=np.float64),
    "lower tip": np.array([0.000, 0.000, -0.030], dtype=np.float64),
}


def _load_volume(path: Path) -> np.ndarray:
    return np.load(path)["volume"].astype(np.float32)


def _load_draw005c_volumes(source_root: Path, draw005b_root: Path) -> tuple[dict[str, np.ndarray], float]:
    ref3_payload = np.load(source_root / "recon_cache" / "dense_y_ref3.npz")
    gt_fit = _fit_volume(ref3_payload["gt_volume"].astype(np.float32))
    raw = {
        "GT": gt_fit,
        "ref3": _fit_volume(ref3_payload["volume"].astype(np.float32)),
        "ref9": _fit_volume(_load_volume(source_root / "recon_cache" / "dense_y_ref9.npz")),
        "BP": _fit_volume(_load_volume(source_root / "recon_cache" / "dense_y_bp.npz")),
    }
    scale = max(float(np.max(raw["ref3"])), float(np.max(raw["GT"])), 1.0e-6)
    volumes = {label: volume.astype(np.float32) / scale for label, volume in raw.items()}
    volumes["U-Net residual"] = _load_volume(draw005b_root / "recon_cache" / "dense_y_unet_residual_positive_display.npz")
    volumes["ref3+U-Net"] = _load_volume(draw005b_root / "recon_cache" / "dense_y_ref3_plus_unet_display.npz")
    return volumes, scale


def _evaluate_volume(label: str, volume: np.ndarray, gt: np.ndarray, role: str) -> dict[str, Any]:
    local_peak = max(float(volume.max()), 1.0e-6)
    return {
        "target": "dense_manisali_y",
        "method": label,
        "role": role,
        "nmse": nmse(volume, gt),
        "psnr": psnr(volume, gt),
        "ssim": ssim_global(volume, gt),
        "peak_value": float(volume.max()),
        "support_voxels_ge_0p10": int(np.count_nonzero(volume >= SUPPORT_ABS_THRESHOLD)),
        "support_voxels_ge_0p22_local_peak": int(np.count_nonzero(volume >= 0.22 * local_peak)),
    }


def compute_metrics(volumes: dict[str, np.ndarray]) -> list[dict[str, Any]]:
    gt = volumes["GT"]
    rows = []
    for label in ["ref3", "ref9", "BP", "U-Net residual", "ref3+U-Net"]:
        role = "positive_part_of_calibrated_residual_delta" if label == "U-Net residual" else "displayed_reconstruction"
        rows.append(_evaluate_volume(label, volumes[label], gt, role))
    return rows


def _mip(volume: np.ndarray, view: str) -> np.ndarray:
    if view == "xy":
        return volume.max(axis=2)
    if view == "yz":
        return volume.max(axis=0).T
    if view == "xz":
        return volume.max(axis=1).T
    raise ValueError(view)


def _plot_mip(ax: plt.Axes, volume: np.ndarray, view: str, title: str | None, colorbar: bool = False) -> None:
    image_db = _db_image(_mip(volume, view))
    origin = "upper" if view == "xy" else "lower"
    im = ax.imshow(image_db, cmap="jet", origin=origin, vmin=DB_FLOOR, vmax=0.0, aspect="equal")
    if title:
        ax.text(0.5, 1.24 if colorbar else 1.04, title, transform=ax.transAxes, ha="center", va="bottom", fontsize=8.5)
    if view == "xy":
        ax.set_xlabel("y (m)", fontsize=8)
        ax.set_ylabel("x (m)", fontsize=8)
    elif view == "yz":
        ax.set_xlabel("y (m)", fontsize=8)
        ax.set_ylabel("z (m)", fontsize=8)
    else:
        ax.set_xlabel("x (m)", fontsize=8)
        ax.set_ylabel("z (m)", fontsize=8)
    ax.set_xticks([0, 12, 23])
    ax.set_yticks([0, 12, 23])
    ax.set_xticklabels(["-0.06", "0", "0.06"], fontsize=7)
    ax.set_yticklabels(["-0.06", "0", "0.06"], fontsize=7)
    if colorbar:
        cb = plt.colorbar(im, ax=ax, fraction=0.045, pad=0.035, orientation="horizontal", location="top")
        cb.set_ticks([-40, -30, -20, -10, 0])
        cb.ax.tick_params(labelsize=6, pad=1)


def render_composite(
    volumes: dict[str, np.ndarray],
    metrics: list[dict[str, Any]],
    specs: list[tuple[str, str, str]],
    output_path: Path,
    title: str,
) -> None:
    lookup = {row["method"]: row for row in metrics}
    fig = plt.figure(figsize=(18.0 if len(specs) == 6 else 15.0, 11.4))
    gs = fig.add_gridspec(4, len(specs), height_ratios=[1.08, 1.0, 1.0, 1.0], hspace=0.42, wspace=0.33)
    vmax = max(float(np.max(volumes[label])) for label, _, _ in specs)
    for col, (label, panel_title, _) in enumerate(specs):
        ax3d = fig.add_subplot(gs[0, col], projection="3d")
        _plot_volume(ax3d, volumes[label], panel_title, vmax)

        ax_xy = fig.add_subplot(gs[1, col])
        metric_title = ""
        if label != "GT":
            row = lookup[label]
            metric_title = f"PSNR {row['psnr']:.2f} dB - SSIM {row['ssim']:.2f}"
        _plot_mip(ax_xy, volumes[label], "xy", metric_title, colorbar=True)

        ax_yz = fig.add_subplot(gs[2, col])
        _plot_mip(ax_yz, volumes[label], "yz", None, colorbar=False)

        ax_xz = fig.add_subplot(gs[3, col])
        _plot_mip(ax_xz, volumes[label], "xz", None, colorbar=False)

    fig.suptitle(title, fontsize=13)
    fig.subplots_adjust(left=0.045, right=0.988, top=0.925, bottom=0.055)
    fig.savefig(output_path, dpi=240)
    fig.savefig(output_path.with_suffix(".pdf"))
    plt.close(fig)


def render_single_xz_mips(volumes: dict[str, np.ndarray], output_dir: Path) -> None:
    for label, _, slug in METHOD_SPECS_3X6:
        fig, ax = plt.subplots(1, 1, figsize=(3.4, 3.2))
        _plot_mip(ax, volumes[label], "xz", f"{label} x-z", colorbar=True)
        fig.tight_layout()
        fig.savefig(output_dir / f"{slug}_xz_mip.png", dpi=240)
        plt.close(fig)


def _voxel_grid_values() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    protocol = PROTOCOL_V1
    x_values = TARGET_CENTER_M[0] + (np.arange(GRID_SHAPE[0], dtype=np.float64) - (GRID_SHAPE[0] - 1) / 2.0) * protocol.xy_spacing
    y_values = TARGET_CENTER_M[1] + (np.arange(GRID_SHAPE[1], dtype=np.float64) - (GRID_SHAPE[1] - 1) / 2.0) * protocol.xy_spacing
    z_values = TARGET_CENTER_M[2] + (np.arange(GRID_SHAPE[2], dtype=np.float64) - (GRID_SHAPE[2] - 1) / 2.0) * protocol.height_spacing
    return x_values, y_values, z_values


def _nearest_index(values: np.ndarray, value: float) -> int:
    return int(np.argmin(np.abs(values - value)))


def _nearest_reference(rho: float, method: str) -> tuple[int, float, float]:
    refs = PROTOCOL_V1.reference_sets[method]
    idx = int(np.argmin(np.abs(refs - rho)))
    radius = float(refs[idx])
    return idx, radius, float(abs(rho - radius))


def _local_peak_stats(volume: np.ndarray, index_xyz: tuple[int, int, int]) -> dict[str, Any]:
    x, y, z = index_xyz
    r = TIP_NEIGHBORHOOD_RADIUS
    local = volume[
        max(0, x - r) : min(volume.shape[0], x + r + 1),
        max(0, y - r) : min(volume.shape[1], y + r + 1),
        max(0, z - r) : min(volume.shape[2], z + r + 1),
    ]
    peak = float(np.max(local)) if local.size else 0.0
    return {
        "local_peak_r2": peak,
        "support_ge_0p10_r2": int(np.count_nonzero(local >= SUPPORT_ABS_THRESHOLD)),
        "retained_ge_0p22_local_peak": bool(peak >= 0.22 * max(float(volume.max()), 1.0e-6)),
    }


def analyze_tips(volumes: dict[str, np.ndarray]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    x_values, y_values, z_values = _voxel_grid_values()
    rows: list[dict[str, Any]] = []
    local_rows: list[dict[str, Any]] = []
    rotation = _rotation_matrix()
    for name, local_coord in TIP_LOCAL_COORDS.items():
        world = local_coord @ rotation.T + TARGET_CENTER_M
        x, y, z = [float(v) for v in world]
        rho = float(np.hypot(x, y))
        theta = float(wrap_angle(np.arctan2(y, x)))
        ref3_idx, ref3_radius, ref3_dist = _nearest_reference(rho, "ref3")
        ref9_idx, ref9_radius, ref9_dist = _nearest_reference(rho, "ref9")
        nearest_xyz = (_nearest_index(x_values, x), _nearest_index(y_values, y), _nearest_index(z_values, z))
        row = {
            "tip": name,
            "x_m": x,
            "y_m": y,
            "z_m": z,
            "rho_m": rho,
            "theta_rad": theta,
            "theta_deg": math.degrees(theta),
            "nearest_voxel_x": int(nearest_xyz[0]),
            "nearest_voxel_y": int(nearest_xyz[1]),
            "nearest_voxel_z": int(nearest_xyz[2]),
            "nearest_ref3_index": ref3_idx,
            "nearest_ref3_radius_m": ref3_radius,
            "dist_to_ref3_m": ref3_dist,
            "nearest_ref9_index": ref9_idx,
            "nearest_ref9_radius_m": ref9_radius,
            "dist_to_ref9_m": ref9_dist,
        }
        rows.append(row)
        for method in ["GT", "ref3", "ref9", "BP", "U-Net residual", "ref3+U-Net"]:
            stats = _local_peak_stats(volumes[method], nearest_xyz)
            local_rows.append({"tip": name, "method": method, **stats})
    return rows, local_rows


def write_tip_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "tip",
        "x_m",
        "y_m",
        "z_m",
        "rho_m",
        "theta_rad",
        "theta_deg",
        "nearest_voxel_x",
        "nearest_voxel_y",
        "nearest_voxel_z",
        "nearest_ref3_index",
        "nearest_ref3_radius_m",
        "dist_to_ref3_m",
        "nearest_ref9_index",
        "nearest_ref9_radius_m",
        "dist_to_ref9_m",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_local_diag_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = ["tip", "method", "local_peak_r2", "support_ge_0p10_r2", "retained_ge_0p22_local_peak"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def render_local_tip_zoomins(volumes: dict[str, np.ndarray], tip_rows: list[dict[str, Any]], output_dir: Path) -> None:
    methods = ["GT", "ref3", "ref9", "BP", "ref3+U-Net"]
    for tip in tip_rows:
        xi, yi, zi = int(tip["nearest_voxel_x"]), int(tip["nearest_voxel_y"]), int(tip["nearest_voxel_z"])
        r = 4
        fig, axes = plt.subplots(3, len(methods), figsize=(3.0 * len(methods), 8.0), squeeze=False)
        for col, method in enumerate(methods):
            vol = volumes[method]
            xy = _db_image(vol[max(0, xi - r) : min(vol.shape[0], xi + r + 1), max(0, yi - r) : min(vol.shape[1], yi + r + 1), :].max(axis=2))
            yz = _db_image(vol[:, max(0, yi - r) : min(vol.shape[1], yi + r + 1), max(0, zi - r) : min(vol.shape[2], zi + r + 1)].max(axis=0).T)
            xz = _db_image(vol[max(0, xi - r) : min(vol.shape[0], xi + r + 1), :, max(0, zi - r) : min(vol.shape[2], zi + r + 1)].max(axis=1).T)
            for row, image in enumerate([xy, yz, xz]):
                axes[row, col].imshow(image, cmap="jet", origin="lower", vmin=DB_FLOOR, vmax=0.0, aspect="equal")
                axes[row, col].set_xticks([])
                axes[row, col].set_yticks([])
            axes[0, col].set_title(method, fontsize=10, fontweight="bold")
        axes[0, 0].set_ylabel("local x-y", fontsize=9)
        axes[1, 0].set_ylabel("local z-y", fontsize=9)
        axes[2, 0].set_ylabel("local x-z", fontsize=9)
        fig.suptitle(tip["tip"], fontsize=12)
        fig.tight_layout(rect=[0, 0, 1, 0.95])
        slug = tip["tip"].replace(" ", "_")
        fig.savefig(output_dir / f"{slug}_local_zoomins.png", dpi=220)
        plt.close(fig)


def _tip_table_markdown(rows: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| Tip | x | y | z | rho | theta | nearest ref3 radius | dist to ref3 | nearest ref9 radius | dist to ref9 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row['tip']} | {row['x_m']:.4f} | {row['y_m']:.4f} | {row['z_m']:.4f} | "
            f"{row['rho_m']:.4f} | {row['theta_deg']:.2f} deg | "
            f"{row['nearest_ref3_radius_m']:.2f} | {row['dist_to_ref3_m']:.4f} | "
            f"{row['nearest_ref9_radius_m']:.2f} | {row['dist_to_ref9_m']:.4f} |"
        )
    return lines


def _local_diag_markdown(local_rows: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| Tip | Method | local peak r=2 | support >=0.10 | retained >=22% method peak |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for row in local_rows:
        lines.append(
            f"| {row['tip']} | {row['method']} | {row['local_peak_r2']:.4f} | "
            f"{row['support_ge_0p10_r2']} | {row['retained_ge_0p22_local_peak']} |"
        )
    return lines


def _metrics_markdown(metrics: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| Method | Role | NMSE | PSNR | SSIM | peak | support >=0.10 | support >=0.22 local peak |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in metrics:
        lines.append(
            f"| {row['method']} | {row['role']} | {row['nmse']:.4f} | {row['psnr']:.4f} | "
            f"{row['ssim']:.4f} | {row['peak_value']:.4f} | {row['support_voxels_ge_0p10']} | "
            f"{row['support_voxels_ge_0p22_local_peak']} |"
        )
    return lines


def _distance_summary(rows: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    return {row["tip"]: row for row in rows}


def write_interpretation(output_root: Path, tip_rows: list[dict[str, Any]], local_rows: list[dict[str, Any]]) -> None:
    tips = _distance_summary(tip_rows)
    left = tips["left upper tip"]
    right = tips["right upper tip"]
    lower = tips["lower tip"]
    lines = [
        "# Trans-level figure interpretation",
        "",
        "## Figure caption candidate",
        "",
        "Dense-volume Y-shaped target reconstructed with reduced-reference cylindrical operators and residual learning. Columns show the ground truth, ref3, ref9, BP, the positive residual predicted by the calibrated U-Net, and the final ref3+U-Net reconstruction. Rows show a Manisali-style translucent 3D volume rendering followed by dB maximum-intensity projections in the x-y, z-y, and x-z planes. The added x-z view exposes the axial separation of the forked tips and reveals structured losses that can be hidden when only x-y and z-y projections are inspected.",
        "",
        "## Main-text interpretation",
        "",
        "The four-row layout is designed to separate volumetric continuity from projection-dependent visibility. The 3D row verifies whether each method preserves a connected Y-shaped support, while the x-y, z-y, and x-z dB projections test the same object under complementary collapses of depth. The x-z projection is especially useful for this target because the two upper branches and the lower stem differ in both lateral position and height; a missing terminal response can therefore be distinguished from a mere overlap artifact in the x-y or z-y views.",
        "",
        f"The reduced-reference results exhibit a structured mismatch rather than random blur. In ref3, the left upper tip lies {left['dist_to_ref3_m']:.4f} m from its nearest reference radius, whereas the right upper and lower tips lie {right['dist_to_ref3_m']:.4f} m and {lower['dist_to_ref3_m']:.4f} m away, respectively. This radial placement helps explain why one upper terminal remains more visible while the other upper terminal and the lower terminal are suppressed or spread below the display threshold. Ref9 reduces the radial mismatch for the left and right upper tips to {left['dist_to_ref9_m']:.4f} m and {right['dist_to_ref9_m']:.4f} m, which is consistent with the recovery of both upper tips. The lower tip remains less clearly expressed even under ref9 because the denser reference set does not eliminate residual model mismatch, and the local response is more susceptible to projection and threshold suppression along the stem direction.",
        "",
        "The ref3+U-Net column is more interpretable than a residual-only display because it shows the final physical reconstruction after compensation, while the residual panel isolates where the learned correction adds support to the reduced-reference output. This pairing makes the figure useful for explaining both the failure mode of coarse reference operators and the mechanism by which a learned residual can repair connected volumetric structure.",
        "",
        "## Brief discussion note for the manuscript",
        "",
        "The figure should be used as a main qualitative example with a short supporting note on tip-to-reference-surface distances. It demonstrates that the error pattern is geometry dependent: increasing the number of reference radii improves the forked upper branches, but does not fully remove the lower-stem failure. This is a stronger claim than a generic improvement statement because it links visual recovery to the target's radial placement with respect to the operator design.",
        "",
        "## Optional Chinese explanation note for internal use",
        "",
        "这张图建议作为正文主图或正文主图加补充说明使用。x-z 视图补上后，Y 形结构三个端点在高度和横向上的关系更清楚；ref3/ref9 的差异也能用端点到参考半径面的距离来解释，而不是只做主观视觉判断。ref3+U-Net 应作为最终重建结果展示，残差列只用于解释学习补偿的位置。",
        "",
        "## Local diagnostic note",
        "",
        "The local peak/support table below is a diagnostic aid rather than a standalone metric.",
        "",
        *_local_diag_markdown(local_rows),
    ]
    write_text(output_root / "trans_level_figure_interpretation.md", "\n".join(lines) + "\n")


def write_report(
    output_root: Path,
    source_root: Path,
    draw005b_root: Path,
    metrics: list[dict[str, Any]],
    tip_rows: list[dict[str, Any]],
    local_rows: list[dict[str, Any]],
    scale: float,
) -> None:
    tips = _distance_summary(tip_rows)
    left = tips["left upper tip"]
    right = tips["right upper tip"]
    lower = tips["lower tip"]
    lines = [
        "# task_real_draw005c report",
        "",
        "## Objective",
        "",
        "draw005c extends draw005b by adding the missing x-z projection, analyzing the three Y tips relative to ref3/ref9 reference surfaces, and producing a manuscript-oriented interpretation of the dense-volume Manisali-style figure.",
        "",
        "## Relation to draw005b",
        "",
        f"The figure reuses draw005b as the direct source baseline: `{draw005b_root}`. The method columns, dense Y target, normalization convention, translucent 3D rendering, and dB MIP style are retained. The analytical extension is the fourth orthogonal row and the explicit tip-to-reference-surface analysis.",
        "",
        "## Added x-z view",
        "",
        "draw005b included the 3D, x-y, and z-y views. The missing x-z row is now added as the fourth row, computed as a maximum-intensity projection along y and displayed with the same `20*log10(abs(x))` convention and `[-40, 0]` dB range. This view is useful because it shows lateral x displacement and vertical z separation together, making the lower stem and the two upper terminals easier to distinguish from projection overlap.",
        "",
        "## Tip definition",
        "",
        "The three tips are derived from the same local control points used by the draw005 dense Y generator, then transformed back into world coordinates using the draw005 rotation and target center. Each ideal tip is also mapped to its nearest 24^3 display-grid voxel for local amplitude diagnostics.",
        "",
        "## Tip-to-reference-surface distances",
        "",
        *_tip_table_markdown(tip_rows),
        "",
        "Distances are radial distances to the nearest cylindrical reference surface, computed separately for the ref3 and ref9 reference-radius sets. Smaller values indicate a more favorable radial placement for the corresponding reduced-reference operator, but visibility also depends on branch orientation, local support spread, and dB display thresholding.",
        "",
        "## Local tip diagnostics",
        "",
        *_local_diag_markdown(local_rows),
        "",
        "## Visual interpretation of ref3",
        "",
        f"The ref3 operator uses only radii 0.00, 0.15, and 0.30 m. The left upper tip is closest to a favorable ref3 radius with distance {left['dist_to_ref3_m']:.4f} m, while the right upper and lower tips are farther away at {right['dist_to_ref3_m']:.4f} m and {lower['dist_to_ref3_m']:.4f} m. This supports the observed pattern: one upper terminal can remain visible, whereas the other upper terminal and the lower terminal are more affected by structured radial mismatch. The x-y, z-y, and x-z rows are all needed here because a weak terminal can disappear either through true local suppression or by being spread along a projection direction until it falls below the dB display threshold.",
        "",
        "The lower tip is also geometrically disadvantaged because it lies along the stem direction and is less reinforced by the forked high-response region. Under coarse ref3 sampling, its local energy can be redistributed into a broader artifact rather than a compact terminal peak, so it is not clearly retained in the Manisali-style rendering.",
        "",
        "## Visual interpretation of ref9",
        "",
        f"Ref9 substantially densifies the reference radii. The two upper tips have smaller ref9 distances, {left['dist_to_ref9_m']:.4f} m and {right['dist_to_ref9_m']:.4f} m, which is consistent with both upper branches becoming visible. The lower tip remains weak because ref9 reduces but does not remove structured mismatch; the local response near the lower stem is still vulnerable to axial spreading and display-threshold suppression. Thus, ref9 improves the upper fork but does not fully recover every terminal structure.",
        "",
        "## Figure-level scientific interpretation",
        "",
        "The updated 4x6 figure should be interpreted as a geometry-dependent failure and repair example. BP provides the high-reference comparison, ref3 and ref9 expose how reduced-reference operators lose different parts of the same continuous target, the U-Net residual column localizes the learned compensation field, and ref3+U-Net shows the final reconstructed volume. Showing the final ref3+U-Net result is more interpretable than showing only the residual because the reader can judge whether the compensation restores a coherent physical object.",
        "",
        "## Metrics",
        "",
        *_metrics_markdown(metrics),
        "",
        "## Output inventory",
        "",
        f"- Main 4x6 PNG: `{output_root / 'viz/paper_candidates/manisali_style/dense_y_manisali_4x6_with_xz_and_ref3_plus_unet.png'}`",
        f"- Main 4x6 PDF: `{output_root / 'viz/paper_candidates/manisali_style/dense_y_manisali_4x6_with_xz_and_ref3_plus_unet.pdf'}`",
        f"- Clean 4x5 PNG: `{output_root / 'viz/paper_candidates/manisali_style/dense_y_manisali_4x5_clean_with_xz_and_ref3_plus_unet.png'}`",
        f"- Tip CSV: `{output_root / 'tip_reference_surface_analysis.csv'}`",
        f"- Tip JSON: `{output_root / 'tip_reference_surface_analysis.json'}`",
        f"- Trans-level interpretation: `{output_root / 'trans_level_figure_interpretation.md'}`",
        f"- Shared display scale inherited from draw005/draw005b source volumes: `{scale:.8f}`",
        "",
        "## Recommendation",
        "",
        "Use the 4x6 figure as the main internal paper candidate because it contains the residual column needed to explain the repair mechanism. For a space-limited manuscript, use the clean 4x5 version as the main figure and keep the residual column plus tip diagnostics as supplementary material. The figure is suitable for main-text use if described as a controlled dense-Y visualization and not as an unseen-target generalization claim.",
    ]
    write_text(output_root / "task_real_draw005c_report.md", "\n".join(lines) + "\n")


def run(output_root: Path, source_root: Path, draw005b_root: Path) -> dict[str, Any]:
    style_dir = ensure_dir(output_root / "viz" / "paper_candidates" / "manisali_style")
    single_mip_dir = ensure_dir(style_dir / "single_mip")
    local_zoom_dir = ensure_dir(style_dir / "local_tip_zoomins")
    manifest_dir = ensure_dir(output_root / "viz" / "manifest")

    volumes, scale = _load_draw005c_volumes(source_root, draw005b_root)
    metrics = compute_metrics(volumes)
    tip_rows, local_rows = analyze_tips(volumes)

    write_json(output_root / "metrics_draw005c.json", metrics)
    write_json(output_root / "tip_reference_surface_analysis.json", tip_rows)
    write_json(output_root / "local_tip_diagnostics.json", local_rows)
    write_tip_csv(output_root / "tip_reference_surface_analysis.csv", tip_rows)
    write_local_diag_csv(output_root / "local_tip_diagnostics.csv", local_rows)

    main_path = style_dir / "dense_y_manisali_4x6_with_xz_and_ref3_plus_unet.png"
    clean_path = style_dir / "dense_y_manisali_4x5_clean_with_xz_and_ref3_plus_unet.png"
    render_composite(
        volumes,
        metrics,
        METHOD_SPECS_3X6,
        main_path,
        "Dense-volume Y target: orthogonal-view analysis of ref3/ref9 mismatch and ref3+U-Net correction",
    )
    render_composite(
        volumes,
        metrics,
        METHOD_SPECS_CLEAN,
        clean_path,
        "Dense-volume Y target: clean orthogonal-view reconstruction comparison",
    )
    render_single_xz_mips(volumes, single_mip_dir)
    render_local_tip_zoomins(volumes, tip_rows, local_zoom_dir)
    write_interpretation(output_root, tip_rows, local_rows)
    write_report(output_root, source_root, draw005b_root, metrics, tip_rows, local_rows, scale)

    manifest = {
        "task": TASK_NAME,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "prompt": "PROMPTS/task_real_draw005c.md",
        "source_draw005": str(source_root),
        "source_draw005b": str(draw005b_root),
        "columns_4x6": [label for label, _, _ in METHOD_SPECS_3X6],
        "columns_clean_4x5": [label for label, _, _ in METHOD_SPECS_CLEAN],
        "view_rows": ["3D volumetric rendering", "x-y projection", "z-y projection", "x-z projection"],
        "main_composite": str(main_path.relative_to(output_root)),
        "main_composite_pdf": str(main_path.with_suffix(".pdf").relative_to(output_root)),
        "clean_composite": str(clean_path.relative_to(output_root)),
        "clean_composite_pdf": str(clean_path.with_suffix(".pdf").relative_to(output_root)),
        "tip_reference_surface_analysis_csv": "tip_reference_surface_analysis.csv",
        "tip_reference_surface_analysis_json": "tip_reference_surface_analysis.json",
        "local_tip_diagnostics_csv": "local_tip_diagnostics.csv",
        "trans_level_interpretation": "trans_level_figure_interpretation.md",
        "metrics": metrics,
        "tip_rows": tip_rows,
        "local_tip_diagnostics": local_rows,
    }
    write_json(output_root / "draw005c_manifest.json", manifest)
    write_json(manifest_dir / "draw005c_viz_manifest.json", manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate task_real_draw005c dense-Y x-z view and tip-reference analysis.")
    parser.add_argument("--source-root", default=str(SOURCE_ROOT))
    parser.add_argument("--draw005b-root", default=str(SOURCE_DRAW005B_ROOT))
    parser.add_argument("--output-root", default=None)
    args = parser.parse_args()
    source_root = Path(args.source_root)
    draw005b_root = Path(args.draw005b_root)
    if args.output_root is None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_root = PROJECT_ROOT / "exp" / "task_real_draw005c_tip_analysis" / stamp
    else:
        output_root = Path(args.output_root)
    ensure_dir(output_root)
    manifest = run(output_root, source_root, draw005b_root)
    print(f"Wrote draw005c outputs to {output_root}")
    print(f"Main composite: {output_root / manifest['main_composite']}")


if __name__ == "__main__":
    main()
