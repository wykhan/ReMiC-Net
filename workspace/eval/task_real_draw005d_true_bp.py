from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

from workspace.common.io_utils import ensure_dir, write_json, write_text
from workspace.eval.metrics_3d import nmse, psnr, ssim_global
from workspace.eval.task_real_draw001_qualitative import _fit_volume
from workspace.eval.task_real_draw005c_tip_analysis import (
    SOURCE_DRAW005B_ROOT,
    _db_image,
    _load_draw005c_volumes,
    _local_peak_stats,
    _local_diag_markdown,
    _metrics_markdown,
    _mip,
    _plot_mip,
    _tip_table_markdown,
    _voxel_grid_values,
    analyze_tips,
)
from workspace.eval.task_real_draw005b_ref3_plus_unet import SOURCE_ROOT
from workspace.recon.cyl_true_bp_engine import (
    simulate_single_voxel_echo,
    true_backproject_sparse_echo,
    write_sparse_echo_npz,
)


TASK_NAME = "task_real_draw005d"
SOURCE_DRAW005C_ROOT = Path(__file__).resolve().parents[2] / "exp" / "task_real_draw005c_tip_analysis" / "20260515_000001"
ECHO_PATH = SOURCE_ROOT / "dataset" / "echoes" / "draw005_dense_manisali_y_echo_sparse.npz"
SUPPORT_ABS_THRESHOLD = 0.10
XZ_DB_THRESHOLD = -20.0


METHOD_SPECS_4X7 = [
    ("GT", "GT", "gt"),
    ("ref3", "ref3", "ref3"),
    ("ref9", "ref9", "ref9"),
    ("ref31", "ref31", "ref31"),
    ("BP", "BP", "bp"),
    ("U-Net residual", "U-Net residual", "unet_residual"),
    ("ref3+U-Net", "ref3+U-Net", "ref3_plus_unet"),
]
METHOD_SPECS_CLEAN = [
    ("GT", "GT", "gt"),
    ("ref3", "ref3", "ref3"),
    ("ref9", "ref9", "ref9"),
    ("BP", "BP", "bp"),
    ("ref3+U-Net", "ref3+U-Net", "ref3_plus_unet"),
]


def render_draw005d_composite(
    volumes: dict[str, np.ndarray],
    metrics: list[dict[str, Any]],
    specs: list[tuple[str, str, str]],
    output_path: Path,
    title: str,
) -> None:
    from workspace.eval.task_real_draw005_dense_volume import _plot_volume

    lookup = {row["method"]: row for row in metrics}
    fig = plt.figure(figsize=(3.0 * len(specs), 11.4))
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
    fig.subplots_adjust(left=0.04, right=0.99, top=0.925, bottom=0.055)
    fig.savefig(output_path, dpi=240)
    fig.savefig(output_path.with_suffix(".pdf"))
    plt.close(fig)


def _align_to_gt(volume: np.ndarray, gt: np.ndarray) -> tuple[np.ndarray, float]:
    denom = max(float(np.sum(volume * volume)), 1.0e-12)
    scale = float(np.sum(volume * gt) / denom)
    return np.maximum(volume * scale, 0.0).astype(np.float32), scale


def _evaluate_volume(label: str, volume: np.ndarray, gt: np.ndarray, role: str) -> dict[str, Any]:
    local_peak = max(float(volume.max()), 1.0e-6)
    xz = _xz_support_stats(volume)
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
        **xz,
    }


def _xz_support_stats(volume: np.ndarray, threshold_db: float = XZ_DB_THRESHOLD) -> dict[str, Any]:
    image_db = _db_image(_mip(volume, "xz"))
    mask = image_db >= threshold_db
    coords = np.argwhere(mask)
    if coords.size == 0:
        return {
            "xz_threshold_db": threshold_db,
            "xz_support_area": 0,
            "xz_bbox_width_px": 0,
            "xz_bbox_height_px": 0,
            "xz_bbox_area_px": 0,
            "xz_fill_ratio": 0.0,
        }
    z_min, x_min = coords.min(axis=0)
    z_max, x_max = coords.max(axis=0)
    width = int(x_max - x_min + 1)
    height = int(z_max - z_min + 1)
    area = int(mask.sum())
    return {
        "xz_threshold_db": threshold_db,
        "xz_support_area": area,
        "xz_bbox_width_px": width,
        "xz_bbox_height_px": height,
        "xz_bbox_area_px": int(width * height),
        "xz_fill_ratio": float(area / max(width * height, 1)),
    }


def compute_metrics(volumes: dict[str, np.ndarray]) -> list[dict[str, Any]]:
    gt = volumes["GT"]
    rows = []
    for label in ["ref3", "ref9", "ref31", "BP", "U-Net residual", "ref3+U-Net"]:
        role = "positive_part_of_calibrated_residual_delta" if label == "U-Net residual" else "displayed_reconstruction"
        if label == "ref31":
            role = "dense_reference_ref31"
        if label == "BP":
            role = "voxelwise_phase_compensated_backprojection"
        rows.append(_evaluate_volume(label, volumes[label], gt, role))
    return rows


def validate_one_voxel(output_root: Path) -> dict[str, Any]:
    x_values, y_values, z_values = _voxel_grid_values()
    true_idx = (12, 12, 12)
    true_coord = (float(x_values[true_idx[0]]), float(y_values[true_idx[1]]), float(z_values[true_idx[2]]))
    sparse = simulate_single_voxel_echo(*true_coord, amplitude=1.0)
    echo_path = output_root / "validation" / "single_voxel_echo_sparse.npz"
    write_sparse_echo_npz(echo_path, sparse)
    xs = x_values[8:17]
    ys = y_values[8:17]
    zs = z_values[8:17]
    recon = true_backproject_sparse_echo(echo_path, xs, ys, zs, voxel_chunk=128, measurement_chunk=512, n_fft=4096)
    vol = recon["volume"]
    peak_idx_local = tuple(int(v) for v in np.unravel_index(int(np.argmax(vol)), vol.shape))
    peak_coord = (float(xs[peak_idx_local[0]]), float(ys[peak_idx_local[1]]), float(zs[peak_idx_local[2]]))
    error = float(np.linalg.norm(np.array(peak_coord) - np.array(true_coord)))
    flat = np.sort(vol.ravel())
    peak_to_second = float(flat[-1] / max(flat[-2], 1.0e-12)) if flat.size > 1 else float("inf")
    return {
        "true_voxel_index_full_grid": true_idx,
        "true_coordinate_m": true_coord,
        "peak_index_local_grid": peak_idx_local,
        "peak_coordinate_m": peak_coord,
        "localization_error_m": error,
        "peak_to_second_largest_ratio": peak_to_second,
        "runtime_sec": recon["runtime_sec"],
        "active_measurement_count": recon["active_measurement_count"],
        "num_freq": recon["num_freq"],
        "reconstructed_voxels": recon["reconstructed_voxels"],
    }


def run_bp(output_root: Path, gt: np.ndarray) -> tuple[np.ndarray, dict[str, Any]]:
    source_axes = np.load(SOURCE_ROOT / "recon_cache" / "dense_y_ref3.npz")
    x_values = source_axes["x_values"].astype(np.float64)
    y_values = source_axes["y_values"].astype(np.float64)
    z_values = source_axes["z_values"].astype(np.float64)
    recon = true_backproject_sparse_echo(ECHO_PATH, x_values, y_values, z_values, voxel_chunk=384, measurement_chunk=512, n_fft=4096)
    fitted = _fit_volume(recon["volume"].astype(np.float32))
    aligned, scale = _align_to_gt(fitted, gt)
    np.savez_compressed(
        output_root / "recon_cache" / "dense_y_bp_display.npz",
        volume=aligned.astype(np.float32),
        raw_volume=recon["volume"].astype(np.float32),
        fitted_volume=fitted.astype(np.float32),
        amplitude_alignment_scale=np.array(scale, dtype=np.float32),
        x_values=x_values,
        y_values=y_values,
        z_values=z_values,
    )
    meta = {k: v for k, v in recon.items() if k not in {"volume", "x_values", "y_values", "z_values"}}
    meta["amplitude_alignment"] = "least_squares_to_GT_for_display_and_metrics"
    meta["amplitude_alignment_scale"] = scale
    meta["display_grid_alignment"] = "BP reconstructed on the same source patch axes as ref3/ref9/ref31, then centered with _fit_volume to the shared 24^3 display grid"
    meta["source_patch_shape"] = [int(len(x_values)), int(len(y_values)), int(len(z_values))]
    return aligned, meta


def render_individual_bp(volumes: dict[str, np.ndarray], output_dir: Path) -> None:
    single_3d = ensure_dir(output_dir / "single_3d")
    single_mip = ensure_dir(output_dir / "single_mip")
    from workspace.eval.task_real_draw005_dense_volume import _plot_volume

    vmax = max(float(np.max(volumes[label])) for label, _, _ in METHOD_SPECS_4X7)
    fig = plt.figure(figsize=(4.6, 4.6))
    ax = fig.add_subplot(1, 1, 1, projection="3d")
    _plot_volume(ax, volumes["BP"], "BP", vmax)
    fig.tight_layout()
    fig.savefig(single_3d / "bp_volume.png", dpi=240)
    plt.close(fig)

    fig2, axes = plt.subplots(1, 3, figsize=(9.8, 3.2), squeeze=False)
    _plot_mip(axes[0, 0], volumes["BP"], "xy", "x-y", colorbar=True)
    _plot_mip(axes[0, 1], volumes["BP"], "yz", "z-y", colorbar=True)
    _plot_mip(axes[0, 2], volumes["BP"], "xz", "x-z", colorbar=True)
    fig2.suptitle("BP", fontsize=12)
    fig2.tight_layout(rect=[0, 0, 1, 0.92])
    fig2.savefig(single_mip / "bp_mips_db.png", dpi=240)
    plt.close(fig2)


def render_xz_diagnostic(volumes: dict[str, np.ndarray], rows: list[dict[str, Any]], output_path: Path) -> None:
    methods = ["ref31", "BP", "ref3", "ref9", "ref3+U-Net"]
    fig, axes = plt.subplots(1, len(methods), figsize=(3.1 * len(methods), 3.3), squeeze=False)
    lookup = {row["method"]: row for row in rows}
    for col, method in enumerate(methods):
        ax = axes[0, col]
        _plot_mip(ax, volumes[method], "xz", None, colorbar=(col == 0))
        row = lookup[method]
        ax.set_title(f"{method}\narea {row['xz_support_area']}, box {row['xz_bbox_width_px']}x{row['xz_bbox_height_px']}", fontsize=9)
    fig.tight_layout()
    fig.savefig(output_path, dpi=240)
    plt.close(fig)


def render_tip_comparison(volumes: dict[str, np.ndarray], tip_rows: list[dict[str, Any]], output_path: Path) -> None:
    methods = ["ref3", "ref9", "ref31", "BP", "ref3+U-Net"]
    fig, axes = plt.subplots(len(tip_rows), len(methods), figsize=(3.0 * len(methods), 2.8 * len(tip_rows)), squeeze=False)
    for row_idx, tip in enumerate(tip_rows):
        xi, yi, zi = int(tip["nearest_voxel_x"]), int(tip["nearest_voxel_y"]), int(tip["nearest_voxel_z"])
        r = 4
        for col, method in enumerate(methods):
            vol = volumes[method]
            local = vol[max(0, xi - r) : min(vol.shape[0], xi + r + 1), :, max(0, zi - r) : min(vol.shape[2], zi + r + 1)]
            image = _db_image(local.max(axis=1).T)
            axes[row_idx, col].imshow(image, cmap="jet", origin="lower", vmin=-40, vmax=0, aspect="equal")
            axes[row_idx, col].set_xticks([])
            axes[row_idx, col].set_yticks([])
            if row_idx == 0:
                axes[row_idx, col].set_title(method, fontsize=10, fontweight="bold")
        axes[row_idx, 0].set_ylabel(tip["tip"], fontsize=9)
    fig.tight_layout()
    fig.savefig(output_path, dpi=240)
    plt.close(fig)


def write_report(
    output_root: Path,
    metrics: list[dict[str, Any]],
    validation: dict[str, Any],
    bp_meta: dict[str, Any],
    tip_rows: list[dict[str, Any]],
    local_rows: list[dict[str, Any]],
    xz_rows: list[dict[str, Any]],
) -> None:
    lookup = {row["method"]: row for row in metrics}
    pseudo = lookup["ref31"]
    true = lookup["BP"]
    lines = [
        "# task_real_draw005d report",
        "",
        "## Objective",
        "",
        "draw005d implements a direct cylindrical-aperture BP baseline and redraws the dense-Y Manisali-style figure with both the previous ref31 column and the new BP column.",
        "",
        "## Why draw005d is needed",
        "",
        "The draw005c x-z projection showed a visibly thick BP result. Because the existing code path labels `method='BP'` but reconstructs through the reference-surface engine, a direct voxel-wise BP baseline is needed before using this column as a high-quality manuscript reference.",
        "",
        "## Code inspection result",
        "",
        "`workspace/recon/cyl_fast_reference_engine.py::reconstruct_cylindrical_reference` obtains `refs = PROTOCOL_V1.reference_sets[method]`. For `method='BP'`, `ProtocolV1.reference_sets` maps BP to `rho_ref_full`, then `_reference_surface_stack(...)` and `sinc_geometry_correction(...)` produce the Cartesian volume. Therefore the old BP column is a dense-reference ref31 baseline, not true voxel-wise BP.",
        "",
        "## BP implementation",
        "",
        "`workspace/recon/cyl_true_bp_engine.py::true_backproject_sparse_echo` directly evaluates the project-consistent phase-compensated sum `sum y(a,h,k) exp(+j k R(a,h,p))` for each Cartesian voxel. It uses the sparse active echo cells written by the dense-volume forward simulator, the protocol-v1 azimuth/height/frequency samples, and the same `measurement_range` helper. A zero-padded inverse FFT over frequency is used only to interpolate the same k-domain summation as a range profile; no reference surfaces or geometry-correction stack are used.",
        "",
        "For visual alignment, BP is reconstructed on the same source patch axes stored with the draw005 ref3 result and then centered with `_fit_volume` onto the shared 24^3 display grid. This matches the display convention already used by ref3, ref9, ref31, GT, and ref3+U-Net.",
        "",
        f"- Dense-Y runtime: `{bp_meta['runtime_sec']:.2f}` sec",
        f"- Active measurement cells: `{bp_meta['active_measurement_count']}`",
        f"- Frequencies: `{bp_meta['num_freq']}`",
        f"- Reconstructed voxels: `{bp_meta['reconstructed_voxels']}`",
        f"- Voxel chunk / measurement chunk: `{bp_meta['voxel_chunk']}` / `{bp_meta['measurement_chunk']}`",
        f"- FFT range bins: `{bp_meta['n_fft']}`",
        f"- Estimated peak memory: `{bp_meta['estimated_peak_memory_mb']:.2f}` MB",
        "",
        "## Validation",
        "",
        f"The one-voxel sanity check used target coordinate `{validation['true_coordinate_m']}` m. The reconstructed peak was at `{validation['peak_coordinate_m']}` m, giving localization error `{validation['localization_error_m']:.6f}` m. The peak-to-second-largest ratio was `{validation['peak_to_second_largest_ratio']:.4f}`.",
        "",
        "## Main figure outputs",
        "",
        f"- 4x7 main figure: `{output_root / 'viz/paper_candidates/manisali_style/dense_y_manisali_4x7_with_bp.png'}`",
        f"- 4x7 main PDF: `{output_root / 'viz/paper_candidates/manisali_style/dense_y_manisali_4x7_with_bp.pdf'}`",
        f"- 4x5 clean figure: `{output_root / 'viz/paper_candidates/manisali_style/dense_y_manisali_4x5_clean_bp.png'}`",
        f"- x-z diagnostic: `{output_root / 'viz/diagnostics/xz_ref31_vs_bp.png'}`",
        "",
        "## x-z bloating analysis",
        "",
        f"At the fixed {XZ_DB_THRESHOLD:.0f} dB x-z projection threshold, ref31 has support area `{pseudo['xz_support_area']}` pixels and bounding box `{pseudo['xz_bbox_width_px']}x{pseudo['xz_bbox_height_px']}`. BP has support area `{true['xz_support_area']}` pixels and bounding box `{true['xz_bbox_width_px']}x{true['xz_bbox_height_px']}`. In the 3D volume, BP uses fewer voxels above 0.10 (`{true['support_voxels_ge_0p10']}`) than ref31 (`{pseudo['support_voxels_ge_0p10']}`), but the x-z projection support at this dB threshold is not smaller.",
        "",
        "Therefore, the previous x-z bloating should not be attributed solely to the dense-reference ref31 approximation. BP improves the physics baseline and reduces volumetric support, but the x-z projection still broadens under the finite aperture, finite tube radius, projection collapse, and the chosen dB threshold. The dense-reference ref31 label remains necessary for correctness, but the x-z thickness is a mixed effect rather than a pure ref31 artifact.",
        "",
        "| Method | x-z support area | bbox width | bbox height | bbox area | fill ratio |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in xz_rows:
        lines.append(
            f"| {row['method']} | {row['xz_support_area']} | {row['xz_bbox_width_px']} | {row['xz_bbox_height_px']} | "
            f"{row['xz_bbox_area_px']} | {row['xz_fill_ratio']:.4f} |"
        )
    lines += [
        "",
        "## Tip-level analysis",
        "",
        *_tip_table_markdown(tip_rows),
        "",
        *_local_diag_markdown(local_rows),
        "",
        "BP is added to the same local-tip diagnostic used in draw005c. The result should be interpreted together with the x-z diagnostic: BP provides a direct physical baseline for whether each Y terminal is locally focused, while ref3/ref9 expose reference-radius mismatch and ref3+U-Net shows learned compensation.",
        "",
        "## Metrics",
        "",
        *_metrics_markdown(metrics),
        "",
        "## Manuscript recommendation",
        "",
        "Future paper figures should use BP when the column is meant to represent a high-quality physics baseline. The old BP column should be renamed ref31 or dense-reference BP. For the main paper, keep BP and ref3+U-Net in the clean comparison; retain ref31 in supplementary analysis when discussing why the previous x-z panel appeared bloated.",
    ]
    write_text(output_root / "task_real_draw005d_report.md", "\n".join(lines) + "\n")


def run(output_root: Path) -> dict[str, Any]:
    style_dir = ensure_dir(output_root / "viz" / "paper_candidates" / "manisali_style")
    diag_dir = ensure_dir(output_root / "viz" / "diagnostics")
    ensure_dir(output_root / "recon_cache")
    ensure_dir(output_root / "viz" / "manifest")

    base_volumes, _ = _load_draw005c_volumes(SOURCE_ROOT, SOURCE_DRAW005B_ROOT)
    volumes = {**base_volumes}
    volumes["ref31"] = volumes.pop("BP")

    validation = validate_one_voxel(output_root)
    bp, bp_meta = run_bp(output_root, volumes["GT"])
    volumes["BP"] = bp

    metrics = compute_metrics(volumes)
    tip_input = {**volumes, "BP": volumes["ref31"]}
    tip_rows, local_rows = analyze_tips(tip_input)
    for row in local_rows:
        if row["method"] == "BP":
            row["method"] = "ref31"
    for tip in tip_rows:
        nearest_xyz = (int(tip["nearest_voxel_x"]), int(tip["nearest_voxel_y"]), int(tip["nearest_voxel_z"]))
        local_rows.append({"tip": tip["tip"], "method": "BP", **_local_peak_stats(volumes["BP"], nearest_xyz)})
    xz_rows = [row for row in metrics if row["method"] in {"ref3", "ref9", "ref31", "BP", "ref3+U-Net"}]

    main_path = style_dir / "dense_y_manisali_4x7_with_bp.png"
    clean_path = style_dir / "dense_y_manisali_4x5_clean_bp.png"
    render_draw005d_composite(volumes, metrics, METHOD_SPECS_4X7, main_path, "Dense-volume Y target: ref31 versus BP")
    render_draw005d_composite(volumes, metrics, METHOD_SPECS_CLEAN, clean_path, "Dense-volume Y target: clean BP comparison")
    render_individual_bp(volumes, style_dir)
    render_xz_diagnostic(volumes, metrics, diag_dir / "xz_ref31_vs_bp.png")
    render_tip_comparison(volumes, tip_rows, diag_dir / "tip_local_comparison_bp.png")

    write_json(output_root / "metrics_draw005d.json", metrics)
    write_json(output_root / "bp_validation.json", validation)
    write_json(output_root / "bp_runtime_meta.json", bp_meta)
    write_json(output_root / "xz_bloating_analysis.json", xz_rows)
    write_json(output_root / "tip_analysis_with_bp.json", {"tip_rows": tip_rows, "local_rows": local_rows})
    write_report(output_root, metrics, validation, bp_meta, tip_rows, local_rows, xz_rows)

    manifest = {
        "task": TASK_NAME,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "prompt": "PROMPTS/task_real_draw005d.md",
        "source_draw005c": str(SOURCE_DRAW005C_ROOT),
        "source_echo": str(ECHO_PATH),
        "main_composite": str(main_path.relative_to(output_root)),
        "main_composite_pdf": str(main_path.with_suffix(".pdf").relative_to(output_root)),
        "clean_composite": str(clean_path.relative_to(output_root)),
        "clean_composite_pdf": str(clean_path.with_suffix(".pdf").relative_to(output_root)),
        "bp_cache": "recon_cache/dense_y_bp_display.npz",
        "columns_4x7": [label for label, _, _ in METHOD_SPECS_4X7],
        "view_rows": ["3D volumetric rendering", "x-y projection", "z-y projection", "x-z projection"],
        "validation": validation,
        "bp_meta": bp_meta,
        "metrics": metrics,
    }
    write_json(output_root / "draw005d_manifest.json", manifest)
    write_json(output_root / "viz" / "manifest" / "draw005d_viz_manifest.json", manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate draw005d BP dense-Y comparison.")
    parser.add_argument("--output-root", default=None)
    args = parser.parse_args()
    if args.output_root is None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_root = Path(__file__).resolve().parents[2] / "exp" / "task_real_draw005d_bp" / stamp
    else:
        output_root = Path(args.output_root)
    ensure_dir(output_root)
    manifest = run(output_root)
    print(f"Wrote draw005d outputs to {output_root}")
    print(f"Main composite: {output_root / manifest['main_composite']}")


if __name__ == "__main__":
    main()
