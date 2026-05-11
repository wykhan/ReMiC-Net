from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

from workspace.common.io_utils import ensure_dir, write_json, write_text
from workspace.eval.metrics_3d import nmse, psnr, ssim_global
from workspace.eval.task_real_draw001_qualitative import PROJECT_ROOT, _fit_volume
from workspace.eval.task_real_draw005_dense_volume import _plot_mip, _plot_volume


TASK_NAME = "task_real_draw005b"
SOURCE_ROOT = PROJECT_ROOT / "exp" / "task_real_draw005_dense_volume" / "20260511_000001"
GRID_SHAPE = (24, 24, 24)
SUPPORT_ABS_THRESHOLD = 0.10

METHOD_SPECS_3X6 = [
    ("GT", "GT", "gt"),
    ("ref3", "ref3", "ref3"),
    ("ref9", "ref9", "ref9"),
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


def _load_volume(path: Path) -> np.ndarray:
    return np.load(path)["volume"].astype(np.float32)


def load_draw005_volumes(source_root: Path) -> dict[str, np.ndarray]:
    gt_raw = _load_volume(source_root / "dataset" / "gt_volumes" / "draw005_dense_manisali_y_gt_from_dense_voxels.npz")
    gt_fit = _fit_volume(gt_raw)
    gt_peak = max(float(gt_fit.max()), 1.0e-6)
    ref3 = _load_volume(source_root / "recon_cache" / "dense_y_ref3_display.npz")
    ref9 = _load_volume(source_root / "recon_cache" / "dense_y_ref9_display.npz")
    bp = _load_volume(source_root / "recon_cache" / "dense_y_bp_display.npz")
    unet_residual = _load_volume(source_root / "recon_cache" / "dense_y_unet_display.npz")
    ref3_plus_unet = np.maximum(ref3 + unet_residual, 0.0).astype(np.float32)
    return {
        "GT": (gt_fit.astype(np.float32) / gt_peak),
        "ref3": ref3,
        "ref9": ref9,
        "BP": bp,
        "U-Net residual": unet_residual,
        "ref3+U-Net": ref3_plus_unet,
    }


def compute_metrics(volumes: dict[str, np.ndarray]) -> list[dict[str, Any]]:
    gt = volumes["GT"]
    rows = []
    for label in ["ref3", "ref9", "BP", "U-Net residual", "ref3+U-Net"]:
        pred = volumes[label]
        local_peak = max(float(pred.max()), 1.0e-6)
        rows.append(
            {
                "target": "dense_manisali_y",
                "method": label,
                "role": "residual_only_not_final_reconstruction" if label == "U-Net residual" else "displayed_reconstruction",
                "nmse": nmse(pred, gt),
                "psnr": psnr(pred, gt),
                "ssim": ssim_global(pred, gt),
                "peak_value": float(pred.max()),
                "support_voxels_ge_0p10": int(np.count_nonzero(pred >= SUPPORT_ABS_THRESHOLD)),
                "support_voxels_ge_0p22_local_peak": int(np.count_nonzero(pred >= 0.22 * local_peak)),
            }
        )
    return rows


def render_composite(
    volumes: dict[str, np.ndarray],
    metrics: list[dict[str, Any]],
    specs: list[tuple[str, str, str]],
    output_path: Path,
    title: str,
) -> None:
    lookup = {row["method"]: row for row in metrics}
    fig = plt.figure(figsize=(18.0 if len(specs) == 6 else 15.0, 8.9))
    gs = fig.add_gridspec(3, len(specs), height_ratios=[1.08, 1.0, 1.0], hspace=0.42, wspace=0.33)
    vmax = max(float(np.max(volumes[label])) for label, _, _ in specs)
    for col, (label, panel_title, _) in enumerate(specs):
        ax3d = fig.add_subplot(gs[0, col], projection="3d")
        _plot_volume(ax3d, volumes[label], panel_title, vmax)

        ax_xy = fig.add_subplot(gs[1, col])
        if label == "GT":
            metric_title = ""
        else:
            row = lookup[label]
            metric_title = f"PSNR {row['psnr']:.2f} dB - SSIM {row['ssim']:.2f}"
        _plot_mip(ax_xy, volumes[label], "xy", metric_title, colorbar=True)

        ax_yz = fig.add_subplot(gs[2, col])
        _plot_mip(ax_yz, volumes[label], "yz", None, colorbar=False)

    fig.suptitle(title, fontsize=13)
    fig.subplots_adjust(left=0.045, right=0.988, top=0.90, bottom=0.065)
    fig.savefig(output_path, dpi=240)
    fig.savefig(output_path.with_suffix(".pdf"))
    plt.close(fig)


def render_ref3_plus_unet_individual(volumes: dict[str, np.ndarray], output_dir: Path) -> None:
    single_3d = ensure_dir(output_dir / "single_3d")
    single_mip = ensure_dir(output_dir / "single_mip")
    vmax = max(float(np.max(volumes[label])) for label in ["GT", "ref3", "ref9", "BP", "U-Net residual", "ref3+U-Net"])

    fig = plt.figure(figsize=(4.6, 4.6))
    ax = fig.add_subplot(1, 1, 1, projection="3d")
    _plot_volume(ax, volumes["ref3+U-Net"], "ref3+U-Net", vmax)
    fig.tight_layout()
    fig.savefig(single_3d / "ref3_plus_unet_volume.png", dpi=240)
    plt.close(fig)

    fig2, axes = plt.subplots(1, 2, figsize=(6.6, 3.2), squeeze=False)
    _plot_mip(axes[0, 0], volumes["ref3+U-Net"], "xy", "front x-y", colorbar=True)
    _plot_mip(axes[0, 1], volumes["ref3+U-Net"], "yz", "side y-z", colorbar=True)
    fig2.suptitle("ref3+U-Net", fontsize=12)
    fig2.tight_layout(rect=[0, 0, 1, 0.92])
    fig2.savefig(single_mip / "ref3_plus_unet_mips_db.png", dpi=240)
    plt.close(fig2)


def write_report(output_root: Path, source_root: Path, metrics: list[dict[str, Any]]) -> None:
    lookup = {row["method"]: row for row in metrics}
    ref3 = lookup["ref3"]
    corrected = lookup["ref3+U-Net"]
    lines = [
        "# task_real_draw005b report",
        "",
        "## Objective",
        "",
        "draw005b adds the final corrected reconstruction `ref3 + U-Net residual` to the draw005 Manisali-style dense-volume figure.",
        "",
        "## Relation to draw005",
        "",
        "draw005 produced a visually successful Manisali-style dense-volume figure, but the last learning column was residual-only for this task's interpretation. draw005b keeps that residual column and adds a new final `ref3+U-Net` column.",
        "",
        "## Corrected reconstruction definition",
        "",
        "The corrected display volume is computed on the same fitted 24^3 display grid as draw005:",
        "",
        "```python",
        "ref3_plus_unet = ref3 + u_net_residual",
        "ref3_plus_unet = np.maximum(ref3_plus_unet, 0.0)",
        "```",
        "",
        "All displayed volumes are reused from draw005 display caches and remain normalized by the draw005 GT peak.",
        "",
        "## Visualization design",
        "",
        "- Preserves the draw005 Manisali-style translucent voxel-volume 3D rendering.",
        "- Preserves front/side dB MIP projections with `20*log10(abs(x))` and `[-40, 0]` dB display.",
        "- Uses the same viewpoint, same cube, same spatial bounds, and the same non-scatter rendering style.",
        "- The residual-only panel is explicitly labeled `U-Net residual`; the final corrected panel is labeled `ref3+U-Net`.",
        "",
        "## Output inventory",
        "",
        f"- Source draw005 experiment: `{source_root}`",
        f"- Required 3x6 figure: `{output_root / 'viz/paper_candidates/manisali_style/dense_y_manisali_3x6_with_ref3_plus_unet.png'}`",
        f"- Required 3x6 PDF: `{output_root / 'viz/paper_candidates/manisali_style/dense_y_manisali_3x6_with_ref3_plus_unet.pdf'}`",
        f"- Clean 3x5 figure: `{output_root / 'viz/paper_candidates/manisali_style/dense_y_manisali_3x5_clean_ref3_plus_unet.png'}`",
        f"- Clean 3x5 PDF: `{output_root / 'viz/paper_candidates/manisali_style/dense_y_manisali_3x5_clean_ref3_plus_unet.pdf'}`",
        f"- Corrected display cache: `{output_root / 'recon_cache/dense_y_ref3_plus_unet_display.npz'}`",
        f"- Individual 3D panel: `{output_root / 'viz/paper_candidates/manisali_style/single_3d/ref3_plus_unet_volume.png'}`",
        f"- Individual MIP panel: `{output_root / 'viz/paper_candidates/manisali_style/single_mip/ref3_plus_unet_mips_db.png'}`",
        "",
        "## Metrics",
        "",
        "| Target | Method | Role | NMSE | PSNR | SSIM | peak | support >=0.10 | support >=0.22 local peak |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in metrics:
        lines.append(
            f"| {row['target']} | {row['method']} | {row['role']} | {row['nmse']:.4f} | "
            f"{row['psnr']:.4f} | {row['ssim']:.4f} | {row['peak_value']:.4f} | "
            f"{row['support_voxels_ge_0p10']} | {row['support_voxels_ge_0p22_local_peak']} |"
        )
    lines += [
        "",
        "## Qualitative observations",
        "",
        "- `ref3+U-Net` is much more interpretable than the residual-only panel because it is a full reconstruction volume rather than a weak correction field.",
        "- Compared with `ref3`, the corrected result visually remains close to the ref3 reconstruction because the cached residual amplitude is small.",
        "- Compared with `ref9` and `BP`, the corrected result does not recover the same degree of localization in this ordinary U-Net baseline.",
        f"- Metric side check: ref3 PSNR/SSIM is `{ref3['psnr']:.4f}` / `{ref3['ssim']:.4f}`, while ref3+U-Net is `{corrected['psnr']:.4f}` / `{corrected['ssim']:.4f}`. This indicates that the current ordinary residual baseline should not be over-claimed as a quantitative improvement in this draw005b run.",
        "",
        "## Recommendation",
        "",
        "Use the 3x6 figure for internal explanation because it shows both the residual-only field and the corrected reconstruction. For a manuscript figure, prefer the clean 3x5 version with `GT | ref3 | ref9 | BP | ref3+U-Net`, while the caption should state that this is the ordinary U-Net residual baseline rather than the final ReMiC-Net / RSB-FiLM model.",
    ]
    write_text(output_root / "task_real_draw005b_report.md", "\n".join(lines) + "\n")


def run(output_root: Path, source_root: Path) -> dict[str, Any]:
    style_dir = ensure_dir(output_root / "viz" / "paper_candidates" / "manisali_style")
    progress_dir = ensure_dir(output_root / "viz" / "progress")
    manifest_dir = ensure_dir(output_root / "viz" / "manifest")
    recon_dir = ensure_dir(output_root / "recon_cache")

    volumes = load_draw005_volumes(source_root)
    np.savez_compressed(recon_dir / "dense_y_ref3_plus_unet_display.npz", volume=volumes["ref3+U-Net"].astype(np.float32))
    metrics = compute_metrics(volumes)
    write_json(output_root / "metrics_draw005b.json", metrics)

    main_path = style_dir / "dense_y_manisali_3x6_with_ref3_plus_unet.png"
    clean_path = style_dir / "dense_y_manisali_3x5_clean_ref3_plus_unet.png"
    render_composite(
        volumes,
        metrics,
        METHOD_SPECS_3X6,
        main_path,
        "Dense-volume Y target: residual and final ref3+U-Net correction",
    )
    render_composite(
        volumes,
        metrics,
        METHOD_SPECS_CLEAN,
        clean_path,
        "Dense-volume Y target: clean final-reconstruction comparison",
    )
    render_composite(
        volumes,
        metrics,
        METHOD_SPECS_3X6,
        progress_dir / "dense_y_manisali_3x6_with_ref3_plus_unet.png",
        "Dense-volume Y target: residual and final ref3+U-Net correction",
    )
    render_ref3_plus_unet_individual(volumes, style_dir)

    manifest = {
        "task": TASK_NAME,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "prompt": "PROMPTS/task_real_draw005b.md",
        "source_draw005": str(source_root),
        "definition": {
            "u_net_residual_source": str(source_root / "recon_cache" / "dense_y_unet_display.npz"),
            "ref3_source": str(source_root / "recon_cache" / "dense_y_ref3_display.npz"),
            "formula": "ref3_plus_unet = np.maximum(ref3 + u_net_residual, 0.0)",
            "normalization": "draw005 display volumes normalized by the draw005 GT peak",
        },
        "columns_3x6": [label for label, _, _ in METHOD_SPECS_3X6],
        "columns_clean_3x5": [label for label, _, _ in METHOD_SPECS_CLEAN],
        "main_composite": str(main_path.relative_to(output_root)),
        "main_composite_pdf": str(main_path.with_suffix(".pdf").relative_to(output_root)),
        "clean_composite": str(clean_path.relative_to(output_root)),
        "clean_composite_pdf": str(clean_path.with_suffix(".pdf").relative_to(output_root)),
        "corrected_cache": "recon_cache/dense_y_ref3_plus_unet_display.npz",
        "metrics": metrics,
    }
    write_json(output_root / "draw005b_manifest.json", manifest)
    write_json(manifest_dir / "draw005b_viz_manifest.json", manifest)
    write_report(output_root, source_root, metrics)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate draw005b ref3+U-Net corrected dense-volume figure.")
    parser.add_argument("--source-root", default=str(SOURCE_ROOT))
    parser.add_argument("--output-root", default=None)
    args = parser.parse_args()
    source_root = Path(args.source_root)
    if args.output_root is None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_root = PROJECT_ROOT / "exp" / "task_real_draw005b_ref3_plus_unet" / stamp
    else:
        output_root = Path(args.output_root)
    ensure_dir(output_root)
    manifest = run(output_root, source_root)
    print(f"Wrote draw005b outputs to {output_root}")
    print(f"Main composite: {output_root / manifest['main_composite']}")


if __name__ == "__main__":
    main()
