from __future__ import annotations

import argparse
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import torch

from workspace.common.io_utils import ensure_dir, write_json, write_text
from workspace.eval.metrics_3d import nmse, psnr, ssim_global
from workspace.eval.task_real_draw001_qualitative import (
    BASELINE_CKPT,
    METHODS,
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
    build_scenes,
)
from workspace.recon.cyl_fast_reference_engine import build_ground_truth, reconstruct_cylindrical_reference
from workspace.sim.forward_cylindrical_point import simulate_sample


TASK_NAME = "task_real_draw002"
PRIMARY_TARGETS = [("y", "Y-shaped target"), ("random_ext", "Random connected extended target")]
ALL_COLUMNS = ["GT", "ref3", "ref9", "BP", "U-Net"]
FORK_ROI = {"rho_min": 0.195, "rho_max": 0.255, "z_min": -0.030, "z_max": 0.095}
RANDOM_ROI = {"rho_min": 0.185, "rho_max": 0.265, "z_min": -0.155, "z_max": 0.155}


def _log_image(image: np.ndarray) -> np.ndarray:
    return np.log10(1.0 + np.maximum(image, 0.0))


def _roi_to_indices(rho_axis: np.ndarray, z_axis: np.ndarray, roi: dict[str, float]) -> tuple[slice, slice]:
    rmask = np.where((rho_axis >= roi["rho_min"]) & (rho_axis <= roi["rho_max"]))[0]
    zmask = np.where((z_axis >= roi["z_min"]) & (z_axis <= roi["z_max"]))[0]
    if len(rmask) == 0 or len(zmask) == 0:
        return slice(0, len(rho_axis)), slice(0, len(z_axis))
    return slice(int(rmask[0]), int(rmask[-1]) + 1), slice(int(zmask[0]), int(zmask[-1]) + 1)


def _render_mip_panel(ax: plt.Axes, volume: np.ndarray, view: str, vmax: float, title: str | None = None) -> None:
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
        raise ValueError(f"Unsupported view: {view}")
    ax.imshow(_log_image(image), origin="lower", cmap="viridis", vmin=0.0, vmax=max(np.log10(1.0 + vmax), 1.0e-6))
    if title:
        ax.set_title(title, fontsize=11)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_xticks([])
    ax.set_yticks([])


def _render_family_a(target_key: str, row_label: str, volumes: dict[str, np.ndarray], output_path: Path) -> None:
    vmax = max(float(np.percentile(volumes[col], 99.5)) for col in ALL_COLUMNS)
    fig, axes = plt.subplots(3, len(ALL_COLUMNS), figsize=(14.5, 8.0), squeeze=False)
    for col_idx, method in enumerate(ALL_COLUMNS):
        for row_idx, view in enumerate(["xy", "xz", "yz"]):
            title = method if row_idx == 0 else None
            _render_mip_panel(axes[row_idx, col_idx], volumes[method], view, vmax, title)
            if col_idx == 0:
                axes[row_idx, col_idx].set_ylabel(f"{view.upper()} MIP")
    fig.suptitle(row_label, fontsize=14)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(output_path, dpi=220)
    plt.close(fig)


def _render_family_a_combined(target_payloads: dict[str, dict[str, Any]], output_path: Path) -> None:
    fig, axes = plt.subplots(len(PRIMARY_TARGETS) * 3, len(ALL_COLUMNS), figsize=(14.5, 14.5), squeeze=False)
    for target_idx, (target_key, row_label) in enumerate(PRIMARY_TARGETS):
        payload = target_payloads[target_key]
        volumes = payload["volumes"]
        vmax = max(float(np.percentile(volumes[col], 99.5)) for col in ALL_COLUMNS)
        for view_idx, view in enumerate(["xy", "xz", "yz"]):
            row = target_idx * 3 + view_idx
            for col_idx, method in enumerate(ALL_COLUMNS):
                _render_mip_panel(axes[row, col_idx], volumes[method], view, vmax, method if row == 0 else None)
                if col_idx == 0:
                    axes[row, col_idx].set_ylabel(f"{row_label}\n{view.upper()} MIP")
    fig.tight_layout()
    fig.savefig(output_path, dpi=220)
    plt.close(fig)


def _render_rhoz_panel(
    ax: plt.Axes,
    image: np.ndarray,
    gt_contour: np.ndarray,
    rho_axis: np.ndarray,
    z_axis: np.ndarray,
    vmax: float,
    title: str,
    roi: dict[str, float] | None = None,
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
    contour_level = max(float(np.percentile(gt_contour[gt_contour > 0], 60)) if np.any(gt_contour > 0) else 1.0e-6, 1.0e-6)
    ax.contour(rho_axis, z_axis, gt_contour.T, levels=[contour_level], colors="white", linewidths=1.0)
    for radius in REF3_RADII:
        ax.axvline(radius, color="white", linestyle="--", linewidth=0.8, alpha=0.75)
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


def _render_family_b(target_key: str, row_label: str, payload: dict[str, Any], output_path: Path, roi: dict[str, float]) -> None:
    projections = payload["projections"]
    rho_axis = payload["rho_axis"]
    z_axis = payload["z_axis"]
    vmax = max(float(np.percentile(projections[col], 99.5)) for col in ALL_COLUMNS)
    fig, axes = plt.subplots(1, len(ALL_COLUMNS), figsize=(16.0, 3.6), squeeze=False)
    for col_idx, method in enumerate(ALL_COLUMNS):
        _render_rhoz_panel(axes[0, col_idx], projections[method], projections["GT"], rho_axis, z_axis, vmax, method, roi)
        if col_idx > 0:
            axes[0, col_idx].set_ylabel("")
            axes[0, col_idx].set_yticklabels([])
    fig.suptitle(f"{row_label}: rho-z mechanism view with GT contour and ref3 reference surfaces", fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.92])
    fig.savefig(output_path, dpi=220)
    plt.close(fig)


def _render_family_b_combined(target_payloads: dict[str, dict[str, Any]], output_path: Path) -> None:
    fig, axes = plt.subplots(len(PRIMARY_TARGETS), len(ALL_COLUMNS), figsize=(16.0, 6.8), squeeze=False)
    for row_idx, (target_key, row_label) in enumerate(PRIMARY_TARGETS):
        payload = target_payloads[target_key]
        roi = FORK_ROI if target_key == "y" else RANDOM_ROI
        projections = payload["projections"]
        rho_axis = payload["rho_axis"]
        z_axis = payload["z_axis"]
        vmax = max(float(np.percentile(projections[col], 99.5)) for col in ALL_COLUMNS)
        for col_idx, method in enumerate(ALL_COLUMNS):
            _render_rhoz_panel(axes[row_idx, col_idx], projections[method], projections["GT"], rho_axis, z_axis, vmax, method if row_idx == 0 else "", roi)
            if col_idx == 0:
                axes[row_idx, col_idx].set_ylabel(f"{row_label}\nz (m)")
            else:
                axes[row_idx, col_idx].set_ylabel("")
                axes[row_idx, col_idx].set_yticklabels([])
    fig.tight_layout()
    fig.savefig(output_path, dpi=220)
    plt.close(fig)


def _render_family_c(target_key: str, row_label: str, payload: dict[str, Any], output_path: Path, roi: dict[str, float]) -> None:
    projections = payload["projections"]
    rho_axis = payload["rho_axis"]
    z_axis = payload["z_axis"]
    rs, zs = _roi_to_indices(rho_axis, z_axis, roi)
    cropped_rho = rho_axis[rs]
    cropped_z = z_axis[zs]
    cols = ALL_COLUMNS
    recon_vmax = max(float(np.percentile(projections[col][rs, zs], 99.5)) for col in cols)
    err_maps = {method: np.abs(projections[method] - projections["GT"]) for method in METHODS}
    err_vmax = max(float(np.percentile(err_maps[method][rs, zs], 99.0)) for method in METHODS)
    corr_maps = {method: np.abs(projections[method] - projections["ref3"]) for method in ["ref9", "BP", "U-Net"]}
    corr_vmax = max(float(np.percentile(corr_maps[method][rs, zs], 99.0)) for method in corr_maps)

    fig, axes = plt.subplots(3, len(cols), figsize=(15.8, 8.4), squeeze=False)
    for col_idx, method in enumerate(cols):
        ax = axes[0, col_idx]
        roi_img = projections[method][rs, zs]
        ax.imshow(
            _log_image(roi_img).T,
            origin="lower",
            aspect="auto",
            cmap="viridis",
            vmin=0.0,
            vmax=max(np.log10(1.0 + recon_vmax), 1.0e-6),
            extent=[float(cropped_rho.min()), float(cropped_rho.max()), float(cropped_z.min()), float(cropped_z.max())],
        )
        gt_roi = projections["GT"][rs, zs]
        if np.any(gt_roi > 0):
            ax.contour(cropped_rho, cropped_z, gt_roi.T, levels=[float(np.percentile(gt_roi[gt_roi > 0], 60))], colors="white", linewidths=1.0)
        ax.set_title(method, fontsize=11)
        ax.set_xlabel("rho (m)")
        if col_idx == 0:
            ax.set_ylabel("ROI recon\nz (m)")
        else:
            ax.set_yticklabels([])

        ax = axes[1, col_idx]
        if method == "GT":
            ax.axis("off")
            ax.text(0.5, 0.5, "GT reference", ha="center", va="center", transform=ax.transAxes)
        else:
            ax.imshow(
                err_maps[method][rs, zs].T,
                origin="lower",
                aspect="auto",
                cmap="inferno",
                vmin=0.0,
                vmax=max(err_vmax, 1.0e-6),
                extent=[float(cropped_rho.min()), float(cropped_rho.max()), float(cropped_z.min()), float(cropped_z.max())],
            )
            ax.set_xlabel("rho (m)")
            if col_idx == 0:
                ax.set_ylabel("|method-GT|\nz (m)")
            else:
                ax.set_yticklabels([])

        ax = axes[2, col_idx]
        if method in ["GT", "ref3"]:
            ax.axis("off")
            label = "GT" if method == "GT" else "ref3 baseline"
            ax.text(0.5, 0.5, label, ha="center", va="center", transform=ax.transAxes)
        else:
            ax.imshow(
                corr_maps[method][rs, zs].T,
                origin="lower",
                aspect="auto",
                cmap="magma",
                vmin=0.0,
                vmax=max(corr_vmax, 1.0e-6),
                extent=[float(cropped_rho.min()), float(cropped_rho.max()), float(cropped_z.min()), float(cropped_z.max())],
            )
            ax.set_xlabel("rho (m)")
            if col_idx == 0:
                ax.set_ylabel("|method-ref3|\nz (m)")
            else:
                ax.set_yticklabels([])
    fig.suptitle(f"{row_label}: deliberate ROI zoom around fork / connected structure", fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(output_path, dpi=220)
    plt.close(fig)


def _reconstruct_targets(output_root: Path) -> dict[str, dict[str, Any]]:
    scenes = build_scenes()
    dataset_dir = ensure_dir(output_root / "dataset")
    scene_dir = ensure_dir(dataset_dir / "scenes")
    echo_dir = ensure_dir(dataset_dir / "echoes")
    gt_dir = ensure_dir(dataset_dir / "gt_volumes")
    recon_dir = ensure_dir(output_root / "recon_cache")
    unet = _load_unet()
    payloads: dict[str, dict[str, Any]] = {}
    index_rows = []

    for target_key, row_label in PRIMARY_TARGETS:
        scene = scenes[target_key]
        sample_id = scene["sample_id"].replace("draw001", "draw002")
        scene = {**scene, "sample_id": sample_id, "shape_params": {**scene.get("shape_params", {}), "draw002_reuse": "reused draw001 target geometry for continuity"}}
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
            np.savez_compressed(
                recon_dir / f"{target_key}_{METHOD_SLUG[method]}_display.npz",
                volume=volumes[method].astype(np.float32),
                rho_z_projection=projections[method].astype(np.float32),
                rho_axis=rho_axis,
                z_axis=z_proj_axis,
            )
        payloads[target_key] = {
            "row_label": row_label,
            "sample_id": sample_id,
            "volumes": volumes,
            "projections": projections,
            "rho_axis": rho_axis,
            "z_axis": z_proj_axis,
        }

    write_json(dataset_dir / "index.json", index_rows)
    return payloads


def _write_metrics(output_root: Path, target_payloads: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    records = []
    for target_key, payload in target_payloads.items():
        gt = payload["volumes"]["GT"]
        for method in METHODS:
            pred = payload["volumes"][method]
            records.append(
                {
                    "target": target_key,
                    "method": method,
                    "nmse": nmse(pred, gt),
                    "psnr": psnr(pred, gt),
                    "ssim": ssim_global(pred, gt),
                }
            )
    write_json(output_root / "metrics_draw002.json", records)
    return records


def _write_report(output_root: Path, metrics: list[dict[str, Any]]) -> None:
    lines = [
        "# task_real_draw002 report",
        "",
        "## 1. Task objective",
        "",
        "Draw002 is a second-round redesign focused on reader-readable qualitative figures. It keeps the draw001 scientific target but separates shape-readable views from mechanism-diagnostic views.",
        "",
        "## 2. Summary of draw001 limitation",
        "",
        "Draw001 relied on rho-z max-over-theta projections. That preserved radial mismatch information, but readers could not immediately recognize the Y-shaped or random extended targets, and the compensation region was not sufficiently explicit.",
        "",
        "## 3. Figure families implemented",
        "",
        f"- Figure Family A: `{output_root / 'viz/paper_candidates/familyA'}`",
        f"- Figure Family B: `{output_root / 'viz/paper_candidates/familyB'}`",
        f"- Figure Family C: `{output_root / 'viz/paper_candidates/familyC'}`",
        "- No point-target primary qualitative panel was produced.",
        "",
        "## 4. Target definitions",
        "",
        "- Y-shaped target: reused from draw001 for continuity; it contains a thin trunk and two branches at inter-reference radii.",
        "- Random connected extended target: reused from draw001 for continuity; it contains irregular connected/semi-connected clusters and sparse bridges.",
        "- No geometry change was made relative to draw001; the redesign is in rendering and annotation.",
        "",
        "## 5. Visualization choices",
        "",
        "- Family A uses three orthogonal MIP views (xy, xz, yz) for each target and method so the target shape is recognizable.",
        "- Family B uses rho-z max-over-theta projections with GT contour overlays, ref3 reference-surface markers, and cyan ROI boxes.",
        "- Family C zooms into a deliberate ROI around the Y bifurcation/fork region, then shows reconstruction, absolute error to GT, and correction magnitude relative to ref3.",
        "- Shape and mechanism panels use shared per-target normalization and log10(1 + A) rendering for dynamic-range control.",
        "- Error maps use absolute amplitude error with one shared color scale within the figure.",
        "",
        "## 6. Reader-interpretability assessment",
        "",
        "- Family A is the most reader-readable: the Y structure and irregular connected target can be recognized before studying method differences.",
        "- Family B is the best mechanism bridge: it preserves rho while adding GT context and ref3 reference surfaces.",
        "- Family C is the strongest reviewer-facing compensation figure for the Y target because the ROI is tied to the bifurcation and branch-continuity failure mode.",
        "",
        "## 7. Scientific interpretation",
        "",
        "The ref3 panels show broader radial spread and weaker structural localization than ref9/BP in the diagnostic views. Ref9 generally moves closer to BP by reducing the reference-surface approximation gap. The ordinary U-Net baseline changes the ref3 output but does not consistently recover the BP-like structure in these reader-facing panels; this is important because draw002 intentionally keeps U-Net distinct from ReMiC-Net/RSB-FiLM.",
        "",
        "## 8. Recommendation for manuscript use",
        "",
        "Use Family A as the primary qualitative reconstruction figure, and use Family B or C as a mechanism-oriented companion figure. A draw003 follow-up should focus on a true ReMiC-Net/RSB-FiLM compensation figure or a shell-wise error/improvement figure if the manuscript needs a stronger compensation claim than the ordinary U-Net baseline can support.",
        "",
        "## Metrics side check",
        "",
        "| Target | Method | NMSE | PSNR | SSIM |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for row in metrics:
        lines.append(f"| {row['target']} | {row['method']} | {row['nmse']:.4f} | {row['psnr']:.4f} | {row['ssim']:.4f} |")
    write_text(output_root / "task_real_draw002_report.md", "\n".join(lines) + "\n")


def run(output_root: Path) -> dict[str, Any]:
    family_a_dir = ensure_dir(output_root / "viz" / "paper_candidates" / "familyA")
    family_b_dir = ensure_dir(output_root / "viz" / "paper_candidates" / "familyB")
    family_c_dir = ensure_dir(output_root / "viz" / "paper_candidates" / "familyC")
    progress_dir = ensure_dir(output_root / "viz" / "progress")
    manifest_dir = ensure_dir(output_root / "viz" / "manifest")

    target_payloads = _reconstruct_targets(output_root)
    _render_family_a("y", "Y-shaped target", target_payloads["y"]["volumes"], family_a_dir / "familyA_shape_readable_y.png")
    _render_family_a(
        "random_ext",
        "Random connected extended target",
        target_payloads["random_ext"]["volumes"],
        family_a_dir / "familyA_shape_readable_random_ext.png",
    )
    _render_family_a_combined(target_payloads, family_a_dir / "familyA_shape_readable_combined.png")

    _render_family_b("y", "Y-shaped target", target_payloads["y"], family_b_dir / "familyB_mechanism_y_rhoz.png", FORK_ROI)
    _render_family_b(
        "random_ext",
        "Random connected extended target",
        target_payloads["random_ext"],
        family_b_dir / "familyB_mechanism_random_ext_rhoz.png",
        RANDOM_ROI,
    )
    _render_family_b_combined(target_payloads, family_b_dir / "familyB_mechanism_combined.png")

    _render_family_c("y", "Y-shaped target", target_payloads["y"], family_c_dir / "familyC_zoom_error_y.png", FORK_ROI)
    _render_family_c(
        "random_ext",
        "Random connected extended target",
        target_payloads["random_ext"],
        family_c_dir / "familyC_zoom_error_random_ext.png",
        RANDOM_ROI,
    )
    _render_family_a_combined(target_payloads, progress_dir / "draw002_familyA_shape_readable_combined.png")

    metrics = _write_metrics(output_root, target_payloads)
    manifest = {
        "task": TASK_NAME,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "prompt": "PROMPTS/task_real_draw002.md",
        "source_draw001": "exp/task_real_draw001_qualitative/20260511_000001",
        "methods": METHODS,
        "unet_definition": "ordinary residual 3D U-Net baseline checkpoint from task_real_008; not RSB-FiLM/ReMiC-Net",
        "unet_checkpoint": str(BASELINE_CKPT),
        "primary_targets": [key for key, _ in PRIMARY_TARGETS],
        "familyA": str((family_a_dir).relative_to(output_root)),
        "familyB": str((family_b_dir).relative_to(output_root)),
        "familyC": str((family_c_dir).relative_to(output_root)),
        "roi_y": FORK_ROI,
        "roi_random_ext": RANDOM_ROI,
    }
    write_json(output_root / "draw002_manifest.json", manifest)
    write_json(manifest_dir / "draw002_viz_manifest.json", manifest)
    _write_report(output_root, metrics)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate task_real_draw002 reader-readable qualitative figures.")
    parser.add_argument("--output-root", default=None)
    args = parser.parse_args()
    if args.output_root is None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_root = PROJECT_ROOT / "exp" / "task_real_draw002_qualitative" / stamp
    else:
        output_root = Path(args.output_root)
    ensure_dir(output_root)
    manifest = run(output_root)
    print(f"Wrote draw002 qualitative figure outputs to {output_root}")
    print(f"Family A dir: {output_root / manifest['familyA']}")


if __name__ == "__main__":
    main()
