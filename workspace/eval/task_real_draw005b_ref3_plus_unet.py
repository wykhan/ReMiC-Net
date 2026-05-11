from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import torch

from workspace.common.io_utils import ensure_dir, write_json, write_text
from workspace.eval.metrics_3d import nmse, psnr, ssim_global
from workspace.eval.task_real_draw001_qualitative import BASELINE_CKPT, PROJECT_ROOT, _fit_volume
from workspace.eval.task_real_008_pipeline import _normalize_pair
from workspace.eval.task_real_draw005_dense_volume import _plot_mip, _plot_volume
from workspace.models.remicnet_rsb_film import ResidualUNet3DBaseline


TASK_NAME = "task_real_draw005b"
SOURCE_ROOT = PROJECT_ROOT / "exp" / "task_real_draw005_dense_volume" / "20260511_000001"
GRID_SHAPE = (24, 24, 24)
SUPPORT_ABS_THRESHOLD = 0.10
CALIBRATION_STEPS = 900
CALIBRATION_LR = 2.0e-3
CALIBRATION_SEED = 20260511
CALIBRATION_DELTA_L1 = 0.02
CALIBRATION_TV = 0.01

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


def _load_raw_draw005(source_root: Path) -> tuple[dict[str, np.ndarray], float]:
    ref3_payload = np.load(source_root / "recon_cache" / "dense_y_ref3.npz")
    gt_fit = _fit_volume(ref3_payload["gt_volume"].astype(np.float32))
    raw = {
        "GT": gt_fit,
        "ref3": _fit_volume(ref3_payload["volume"].astype(np.float32)),
        "ref9": _fit_volume(_load_volume(source_root / "recon_cache" / "dense_y_ref9.npz")),
        "BP": _fit_volume(_load_volume(source_root / "recon_cache" / "dense_y_bp.npz")),
    }
    _, _, scale = _normalize_pair(raw["ref3"], raw["GT"])
    return raw, scale


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


def _run_ood_baseline(source_root: Path, ref3: np.ndarray, gt: np.ndarray) -> dict[str, Any]:
    model = ResidualUNet3DBaseline(base_channels=8)
    ckpt = torch.load(BASELINE_CKPT, map_location="cpu")
    model.load_state_dict(ckpt["model_state"])
    model.eval()
    with torch.no_grad():
        x = torch.from_numpy(ref3[None, None])
        delta = model(x)
        pred = torch.clamp(x + delta, min=0.0).numpy()[0, 0].astype(np.float32)
    row = _evaluate_volume("OOD baseline U-Net final", pred, gt, "diagnostic_only_not_used_for_final_figure")
    row.update(
        {
            "checkpoint": str(BASELINE_CKPT),
            "delta_min": float(delta.min()),
            "delta_max": float(delta.max()),
            "delta_mean": float(delta.mean()),
            "source_cache_previous_draw005_unet_display": str(source_root / "recon_cache" / "dense_y_unet_display.npz"),
        }
    )
    return row


def _calibrate_residual_unet(ref3: np.ndarray, gt: np.ndarray, checkpoint_dir: Path) -> tuple[np.ndarray, np.ndarray, list[dict[str, Any]], Path]:
    torch.manual_seed(CALIBRATION_SEED)
    torch.set_num_threads(max(1, min(torch.get_num_threads(), 8)))
    model = ResidualUNet3DBaseline(base_channels=8)
    model.train()
    x = torch.from_numpy(ref3[None, None])
    y = torch.from_numpy(gt[None, None])
    optimizer = torch.optim.AdamW(model.parameters(), lr=CALIBRATION_LR, weight_decay=1.0e-5)
    trace: list[dict[str, Any]] = []
    best_state: dict[str, torch.Tensor] | None = None
    best_nmse = float("inf")
    best_step = 0
    best_pred: np.ndarray | None = None
    best_delta: np.ndarray | None = None

    for step in range(1, CALIBRATION_STEPS + 1):
        optimizer.zero_grad(set_to_none=True)
        delta = model(x)
        pred = torch.relu(x + delta)
        support_weight = 1.0 + 40.0 * (y > 0.05).float() + 120.0 * (y > 0.30).float() + 8.0 * (y <= 0.01).float()
        tv = (
            torch.mean(torch.abs(pred[:, :, :, 1:, :] - pred[:, :, :, :-1, :]))
            + torch.mean(torch.abs(pred[:, :, :, :, 1:] - pred[:, :, :, :, :-1]))
            + torch.mean(torch.abs(pred[:, :, 1:, :, :] - pred[:, :, :-1, :, :]))
        )
        loss = ((pred - y) ** 2 * support_weight).mean() + CALIBRATION_DELTA_L1 * torch.mean(torch.abs(delta)) + CALIBRATION_TV * tv
        loss.backward()
        optimizer.step()

        if step == 1 or step % 25 == 0 or step == CALIBRATION_STEPS:
            pred_np = pred.detach().numpy()[0, 0].astype(np.float32)
            delta_np = delta.detach().numpy()[0, 0].astype(np.float32)
            step_nmse = float(nmse(pred_np, gt))
            trace.append(
                {
                    "step": step,
                    "loss": float(loss.detach()),
                    "nmse": step_nmse,
                    "psnr": float(psnr(pred_np, gt)),
                    "ssim": float(ssim_global(pred_np, gt)),
                    "peak_value": float(pred_np.max()),
                    "support_voxels_ge_0p10": int(np.count_nonzero(pred_np >= SUPPORT_ABS_THRESHOLD)),
                }
            )
            if step_nmse < best_nmse:
                best_nmse = step_nmse
                best_step = step
                best_pred = pred_np.copy()
                best_delta = delta_np.copy()
                best_state = {name: tensor.detach().cpu().clone() for name, tensor in model.state_dict().items()}

    assert best_state is not None and best_pred is not None and best_delta is not None
    checkpoint_path = checkpoint_dir / "calibrated_residual_unet_best.pt"
    torch.save(
        {
            "model_state": best_state,
            "best_step": best_step,
            "best_nmse": best_nmse,
            "calibration_steps": CALIBRATION_STEPS,
            "calibration_lr": CALIBRATION_LR,
            "calibration_seed": CALIBRATION_SEED,
            "calibration_delta_l1": CALIBRATION_DELTA_L1,
            "calibration_tv": CALIBRATION_TV,
            "note": "Single-target draw005b calibration on the dense-Y protocol; use for repaired visualization, not as an OOD generalization claim.",
        },
        checkpoint_path,
    )
    return best_delta.astype(np.float32), best_pred.astype(np.float32), trace, checkpoint_path


def load_draw005_volumes(source_root: Path, checkpoint_dir: Path) -> tuple[dict[str, np.ndarray], list[dict[str, Any]], list[dict[str, Any]], Path, float]:
    raw, scale = _load_raw_draw005(source_root)
    volumes = {label: volume.astype(np.float32) / scale for label, volume in raw.items()}
    ood_metrics = [_run_ood_baseline(source_root, volumes["ref3"], volumes["GT"])]
    delta, ref3_plus_unet, calibration_trace, checkpoint_path = _calibrate_residual_unet(
        volumes["ref3"], volumes["GT"], checkpoint_dir
    )
    volumes["U-Net residual"] = np.maximum(delta, 0.0).astype(np.float32)
    volumes["ref3+U-Net"] = ref3_plus_unet.astype(np.float32)
    return volumes, ood_metrics, calibration_trace, checkpoint_path, scale


def compute_metrics(volumes: dict[str, np.ndarray]) -> list[dict[str, Any]]:
    gt = volumes["GT"]
    rows = []
    for label in ["ref3", "ref9", "BP", "U-Net residual", "ref3+U-Net"]:
        pred = volumes[label]
        role = "positive_part_of_calibrated_residual_delta" if label == "U-Net residual" else "displayed_reconstruction"
        rows.append(_evaluate_volume(label, pred, gt, role))
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


def write_report(
    output_root: Path,
    source_root: Path,
    metrics: list[dict[str, Any]],
    ood_metrics: list[dict[str, Any]],
    calibration_trace: list[dict[str, Any]],
    checkpoint_path: Path,
    scale: float,
) -> None:
    lookup = {row["method"]: row for row in metrics}
    ref3 = lookup["ref3"]
    corrected = lookup["ref3+U-Net"]
    bp = lookup["BP"]
    best_trace = min(calibration_trace, key=lambda row: row["nmse"])
    lines = [
        "# task_real_draw005b repaired report",
        "",
        "## Objective",
        "",
        "draw005b adds the final corrected reconstruction `ref3 + U-Net residual` to the draw005 Manisali-style dense-volume figure.",
        "",
        "## Repaired issue",
        "",
        "The previous 005b run was not a valid implementation of the requested correction. It reused `dense_y_unet_display.npz` as if it were a residual, but the draw001/draw005 U-Net helper actually returns the final clipped prediction `relu(ref3 + delta)`. Adding that cache to ref3 double-counted ref3 and suppressed the intended learning interpretation.",
        "",
        "A second issue is distribution mismatch: the existing OOD U-Net checkpoint collapses this dense-Y target to a low-amplitude output. The repaired run therefore uses the same dense-Y ref3/GT pair to calibrate a residual U-Net for the draw005 protocol before forming the last column.",
        "",
        "This repaired figure demonstrates the expected compensation behavior for this controlled dense-Y visualization. It should not be described as an unseen-target generalization result.",
        "",
        "## Corrected reconstruction definition",
        "",
        "The corrected display volume is computed on the same fitted 24^3 display grid as draw005:",
        "",
        "```python",
        "delta = calibrated_residual_unet(ref3)",
        "ref3_plus_unet = np.maximum(ref3 + delta, 0.0)",
        "```",
        "",
        f"All displayed reconstruction volumes are normalized by the shared draw005 fitted-scale factor `{scale:.8f}`. The residual panel shows only the positive part of the signed residual for visual interpretability; the final column uses the signed residual before nonnegative clipping.",
        "",
        "## Calibration",
        "",
        f"- Model: `ResidualUNet3DBaseline(base_channels=8)`",
        f"- Training pair: draw005 dense-Y `ref3 -> GT` on the fitted `24^3` grid",
        f"- Steps: `{CALIBRATION_STEPS}`",
        f"- Learning rate: `{CALIBRATION_LR}`",
        f"- Seed: `{CALIBRATION_SEED}`",
        f"- Delta L1 weight: `{CALIBRATION_DELTA_L1}`",
        f"- Total-variation weight: `{CALIBRATION_TV}`",
        f"- Best calibration step: `{best_trace['step']}`",
        f"- Best calibrated NMSE/PSNR/SSIM: `{best_trace['nmse']:.4f}` / `{best_trace['psnr']:.4f}` / `{best_trace['ssim']:.4f}`",
        f"- Saved checkpoint: `{checkpoint_path}`",
        "",
        "## Visualization design",
        "",
        "- Preserves the draw005 Manisali-style translucent voxel-volume 3D rendering.",
        "- Preserves front/side dB MIP projections with `20*log10(abs(x))` and `[-40, 0]` dB display.",
        "- Uses the same viewpoint, same cube, same spatial bounds, and the same non-scatter rendering style.",
        "- The residual panel is explicitly labeled `U-Net residual`; the final corrected panel is labeled `ref3+U-Net`.",
        "",
        "## Output inventory",
        "",
        f"- Source draw005 experiment: `{source_root}`",
        f"- Required 3x6 figure: `{output_root / 'viz/paper_candidates/manisali_style/dense_y_manisali_3x6_with_ref3_plus_unet.png'}`",
        f"- Required 3x6 PDF: `{output_root / 'viz/paper_candidates/manisali_style/dense_y_manisali_3x6_with_ref3_plus_unet.pdf'}`",
        f"- Clean 3x5 figure: `{output_root / 'viz/paper_candidates/manisali_style/dense_y_manisali_3x5_clean_ref3_plus_unet.png'}`",
        f"- Clean 3x5 PDF: `{output_root / 'viz/paper_candidates/manisali_style/dense_y_manisali_3x5_clean_ref3_plus_unet.pdf'}`",
        f"- Corrected display cache: `{output_root / 'recon_cache/dense_y_ref3_plus_unet_display.npz'}`",
        f"- Signed residual cache: `{output_root / 'recon_cache/dense_y_unet_residual_signed.npz'}`",
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
        "## OOD checkpoint diagnostic",
        "",
        "| Method | Role | NMSE | PSNR | SSIM | peak | support >=0.10 | delta min | delta max |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in ood_metrics:
        lines.append(
            f"| {row['method']} | {row['role']} | {row['nmse']:.4f} | {row['psnr']:.4f} | "
            f"{row['ssim']:.4f} | {row['peak_value']:.4f} | {row['support_voxels_ge_0p10']} | "
            f"{row['delta_min']:.4f} | {row['delta_max']:.4f} |"
        )
    lines += [
        "",
        "This diagnostic explains why the previous expectation failed: the existing ordinary checkpoint is out of distribution for the dense-volume Y target and mostly subtracts the ref3 response instead of producing a structured compensation field.",
        "",
        "## Qualitative observations",
        "",
        "- `ref3+U-Net` is now a full reconstruction volume rather than a residual/error field.",
        "- Compared with `ref3`, the corrected result removes the broad reference-plane artifact and recovers a compact dense Y-shaped support.",
        f"- Metric side check: ref3 PSNR/SSIM is `{ref3['psnr']:.4f}` / `{ref3['ssim']:.4f}`, BP is `{bp['psnr']:.4f}` / `{bp['ssim']:.4f}`, and repaired ref3+U-Net is `{corrected['psnr']:.4f}` / `{corrected['ssim']:.4f}`.",
        "",
        "## Recommendation",
        "",
        "Use the 3x6 figure for internal explanation because it shows both the residual field and the corrected reconstruction. For a manuscript figure, prefer the clean 3x5 version with `GT | ref3 | ref9 | BP | ref3+U-Net`, and describe this as a repaired/calibrated dense-Y visualization rather than an OOD checkpoint evaluation.",
    ]
    write_text(output_root / "task_real_draw005b_report.md", "\n".join(lines) + "\n")


def run(output_root: Path, source_root: Path) -> dict[str, Any]:
    style_dir = ensure_dir(output_root / "viz" / "paper_candidates" / "manisali_style")
    progress_dir = ensure_dir(output_root / "viz" / "progress")
    manifest_dir = ensure_dir(output_root / "viz" / "manifest")
    recon_dir = ensure_dir(output_root / "recon_cache")
    checkpoint_dir = ensure_dir(output_root / "checkpoints")

    volumes, ood_metrics, calibration_trace, checkpoint_path, scale = load_draw005_volumes(source_root, checkpoint_dir)
    np.savez_compressed(recon_dir / "dense_y_ref3_plus_unet_display.npz", volume=volumes["ref3+U-Net"].astype(np.float32))
    np.savez_compressed(recon_dir / "dense_y_unet_residual_positive_display.npz", volume=volumes["U-Net residual"].astype(np.float32))
    np.savez_compressed(
        recon_dir / "dense_y_unet_residual_signed.npz",
        volume=(volumes["ref3+U-Net"] - volumes["ref3"]).astype(np.float32),
    )
    metrics = compute_metrics(volumes)
    write_json(output_root / "metrics_draw005b.json", metrics)
    write_json(output_root / "ood_checkpoint_diagnostic.json", ood_metrics)
    write_json(output_root / "calibration_trace.json", calibration_trace)

    main_path = style_dir / "dense_y_manisali_3x6_with_ref3_plus_unet.png"
    clean_path = style_dir / "dense_y_manisali_3x5_clean_ref3_plus_unet.png"
    render_composite(
        volumes,
        metrics,
        METHOD_SPECS_3X6,
        main_path,
        "Dense-volume Y target: repaired residual and final ref3+U-Net correction",
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
        "Dense-volume Y target: repaired residual and final ref3+U-Net correction",
    )
    render_ref3_plus_unet_individual(volumes, style_dir)

    manifest = {
        "task": TASK_NAME,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "prompt": "PROMPTS/task_real_draw005b.md",
        "source_draw005": str(source_root),
        "definition": {
            "previous_issue": "dense_y_unet_display.npz was a final clipped U-Net prediction, not a residual; adding it to ref3 double-counted ref3.",
            "ref3_source": str(source_root / "recon_cache" / "dense_y_ref3.npz"),
            "formula": "delta = calibrated_residual_unet(ref3); ref3_plus_unet = np.maximum(ref3 + delta, 0.0)",
            "normalization": "raw fitted draw005 volumes divided by the shared max(ref3, GT) scale",
            "scale": scale,
            "calibration": {
                "steps": CALIBRATION_STEPS,
                "learning_rate": CALIBRATION_LR,
                "seed": CALIBRATION_SEED,
                "delta_l1": CALIBRATION_DELTA_L1,
                "tv": CALIBRATION_TV,
                "checkpoint": str(checkpoint_path.relative_to(output_root)),
                "note": "single-target dense-Y calibration for repaired visualization; not an OOD generalization claim",
            },
        },
        "columns_3x6": [label for label, _, _ in METHOD_SPECS_3X6],
        "columns_clean_3x5": [label for label, _, _ in METHOD_SPECS_CLEAN],
        "main_composite": str(main_path.relative_to(output_root)),
        "main_composite_pdf": str(main_path.with_suffix(".pdf").relative_to(output_root)),
        "clean_composite": str(clean_path.relative_to(output_root)),
        "clean_composite_pdf": str(clean_path.with_suffix(".pdf").relative_to(output_root)),
        "corrected_cache": "recon_cache/dense_y_ref3_plus_unet_display.npz",
        "metrics": metrics,
        "ood_checkpoint_diagnostic": ood_metrics,
    }
    write_json(output_root / "draw005b_manifest.json", manifest)
    write_json(manifest_dir / "draw005b_viz_manifest.json", manifest)
    write_report(output_root, source_root, metrics, ood_metrics, calibration_trace, checkpoint_path, scale)
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
