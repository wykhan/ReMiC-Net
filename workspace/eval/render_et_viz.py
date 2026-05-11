from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

from workspace.common.io_utils import ensure_dir, read_json


METHOD_ORDER = ["ref3", "ref5", "ref7", "ref9", "BP"]


def _load_recon(cache_dir: Path, sample_id: str, method: str) -> tuple[np.ndarray, np.ndarray]:
    payload = np.load(cache_dir / f"{sample_id}_{method}_et.npz")
    return payload["volume"], payload["gt_volume"]


def _render_scene_points(scene: dict[str, Any], output_path: Path) -> None:
    xyz = np.array([[p["x_m"], p["y_m"], p["z_m"]] for p in scene["points"]], dtype=np.float64)
    amps = np.array([p["amplitude"] for p in scene["points"]], dtype=np.float64)
    fig = plt.figure(figsize=(6.2, 5.2))
    ax = fig.add_subplot(111, projection="3d")
    ax.scatter(xyz[:, 0], xyz[:, 1], xyz[:, 2], c=amps, cmap="viridis", s=55)
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_zlabel("z (m)")
    fig.tight_layout()
    fig.savefig(output_path, dpi=170)
    plt.close(fig)


def _render_three_views(scene: dict[str, Any], output_path: Path) -> None:
    xyz = np.array([[p["x_m"], p["y_m"], p["z_m"]] for p in scene["points"]], dtype=np.float64)
    amps = np.array([p["amplitude"] for p in scene["points"]], dtype=np.float64)
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.4))
    axes[0].scatter(xyz[:, 0], xyz[:, 1], c=amps, cmap="viridis", s=32)
    axes[0].set_title("Top")
    axes[1].scatter(xyz[:, 0], xyz[:, 2], c=amps, cmap="viridis", s=32)
    axes[1].set_title("Front")
    axes[2].scatter(xyz[:, 1], xyz[:, 2], c=amps, cmap="viridis", s=32)
    axes[2].set_title("Side")
    for ax in axes:
        ax.set_aspect("auto")
    fig.tight_layout()
    fig.savefig(output_path, dpi=170)
    plt.close(fig)


def _render_gt_slice_montage(gt: np.ndarray, output_path: Path) -> None:
    z_idx = np.linspace(0, gt.shape[2] - 1, 6, dtype=int)
    fig, axes = plt.subplots(2, 3, figsize=(10, 6))
    for ax, idx in zip(axes.ravel(), z_idx):
        ax.imshow(gt[:, :, idx], cmap="viridis")
        ax.set_title(f"z={idx}")
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(output_path, dpi=170)
    plt.close(fig)


def _render_compare(sample_id: str, cache_dir: Path, output_path: Path) -> None:
    fig, axes = plt.subplots(2, 3, figsize=(12, 7))
    bp_volume, gt = _load_recon(cache_dir, sample_id, "BP")
    del bp_volume
    items = [("GT", gt)] + [(method, _load_recon(cache_dir, sample_id, method)[0]) for method in METHOD_ORDER]
    for ax, (label, volume) in zip(axes.ravel(), items):
        ax.imshow(volume.max(axis=2), cmap="viridis")
        ax.set_title(label)
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(output_path, dpi=170)
    plt.close(fig)


def _render_slices(sample_id: str, method: str, cache_dir: Path, output_path: Path) -> None:
    volume, gt = _load_recon(cache_dir, sample_id, method)
    x_idx = volume.shape[0] // 2
    y_idx = volume.shape[1] // 2
    z_idx = volume.shape[2] // 2
    fig, axes = plt.subplots(3, 3, figsize=(10, 10))
    slice_specs = [
        ("xy", gt[:, :, z_idx], volume[:, :, z_idx]),
        ("xz", gt[:, y_idx, :], volume[:, y_idx, :]),
        ("yz", gt[x_idx, :, :], volume[x_idx, :, :]),
    ]
    for row_idx, (name, gt_slice, pred_slice) in enumerate(slice_specs):
        axes[row_idx, 0].imshow(gt_slice, cmap="viridis")
        axes[row_idx, 0].set_title(f"GT {name}")
        axes[row_idx, 1].imshow(pred_slice, cmap="viridis")
        axes[row_idx, 1].set_title(f"{method} {name}")
        axes[row_idx, 2].imshow(np.abs(pred_slice - gt_slice), cmap="magma")
        axes[row_idx, 2].set_title(f"abs err {name}")
        for col_idx in range(3):
            axes[row_idx, col_idx].axis("off")
    fig.tight_layout()
    fig.savefig(output_path, dpi=170)
    plt.close(fig)


def _choose_representatives(metrics: dict[str, Any]) -> list[dict[str, str]]:
    ref3_rows = [row for row in metrics["per_sample"] if row["method"] == "ref3"]
    easiest = min(ref3_rows, key=lambda row: row["nmse"])
    hardest = max(ref3_rows, key=lambda row: row["nmse"])
    edge_hard = max(
        [row for row in ref3_rows if row["family"] in {"line", "double-line", "small_rect_edge", "L-shape"}],
        key=lambda row: row["nmse"],
    )
    chosen = []
    used_ids = set()
    for label, row in [
        ("easy_for_ref3", easiest),
        ("hard_for_ref3", hardest),
        ("edge_thin_difficult", edge_hard),
    ]:
        if row["sample_id"] in used_ids:
            continue
        used_ids.add(row["sample_id"])
        chosen.append({"label": label, "sample_id": row["sample_id"], "family": row["family"]})
    return chosen


def _plot_curves(output_root: Path, metrics: dict[str, Any], failures: list[dict[str, Any]]) -> None:
    curves_dir = ensure_dir(output_root / "viz" / "curves")
    aggregate = metrics["aggregate"]
    methods = METHOD_ORDER
    runtimes = [aggregate[method]["wall_time_mean_sec"] for method in methods]
    speedups = [aggregate[method]["speedup_vs_bp"] for method in methods]
    nmse = [aggregate[method]["nmse_mean"] for method in methods]
    psnr = [aggregate[method]["psnr_mean"] for method in methods]
    ssim = [aggregate[method]["ssim_mean"] for method in methods]

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(methods, runtimes, color="#5b7c99")
    ax.set_ylabel("seconds")
    ax.set_title("Runtime vs method")
    fig.tight_layout()
    fig.savefig(curves_dir / "runtime_vs_method_et.png", dpi=170)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(methods, speedups, color="#c77d3f")
    ax.set_ylabel("speedup vs BP")
    ax.set_title("Speedup vs BP")
    fig.tight_layout()
    fig.savefig(curves_dir / "speedup_vs_bp_et.png", dpi=170)
    plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8))
    axes[0].plot(methods, nmse, marker="o")
    axes[0].set_title("NMSE")
    axes[1].plot(methods, psnr, marker="o")
    axes[1].set_title("PSNR")
    axes[2].plot(methods, ssim, marker="o")
    axes[2].set_title("SSIM")
    for ax in axes:
        ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(curves_dir / "quality_vs_method_et.png", dpi=170)
    plt.close(fig)

    families = list(metrics["by_family"].keys())
    x = np.arange(len(families))
    width = 0.14
    fig, ax = plt.subplots(figsize=(12, 4.8))
    for idx, method in enumerate(methods):
        values = [metrics["by_family"][family][method]["nmse_mean"] for family in families]
        ax.bar(x + (idx - 2) * width, values, width=width, label=method)
    ax.set_xticks(x)
    ax.set_xticklabels(families, rotation=20)
    ax.set_ylabel("NMSE mean")
    ax.set_title("Metrics by family")
    ax.legend(ncol=3, fontsize=8)
    fig.tight_layout()
    fig.savefig(curves_dir / "metrics_by_family.png", dpi=170)
    plt.close(fig)

    labels = metrics["failure_summary"]["labels"]
    counts_by_method = metrics["failure_summary"]["counts_by_method"]
    fig, ax = plt.subplots(figsize=(10, 4.5))
    bottom = np.zeros(len(methods), dtype=np.float64)
    for label in labels:
        vals = np.array([counts_by_method[method][label] for method in methods], dtype=np.float64)
        ax.bar(methods, vals, bottom=bottom, label=label)
        bottom += vals
    ax.set_ylabel("count")
    ax.set_title("Failure mode count by method")
    ax.legend(ncol=3, fontsize=8)
    fig.tight_layout()
    fig.savefig(curves_dir / "failure_mode_count_by_method.png", dpi=170)
    plt.close(fig)

    for metric_name, values in [("nmse", nmse), ("psnr", psnr), ("ssim", ssim)]:
        fig, ax = plt.subplots(figsize=(12, 4.8))
        for method in methods:
            ax.plot(families, [metrics["by_family"][family][method][f"{metric_name}_mean"] for family in families], marker="o", label=method)
        ax.set_title(f"{metric_name.upper()} by family")
        ax.grid(alpha=0.25)
        ax.legend(ncol=3, fontsize=8)
        fig.tight_layout()
        fig.savefig(curves_dir / f"{metric_name}_by_family.png", dpi=170)
        plt.close(fig)


def render(output_root: Path) -> None:
    metrics = read_json(output_root / "baseline_metrics_et.json")
    index = read_json(output_root / "dataset" / "index.json")
    failure_cases = read_json(output_root / "failure_case_index.json")
    cache_dir = output_root / "et_recon_cache"
    scene_dir = ensure_dir(output_root / "viz" / "scene_3d")
    compare_dir = ensure_dir(output_root / "viz" / "recon_compare")
    slice_dir = ensure_dir(output_root / "viz" / "slices")

    representatives = _choose_representatives(metrics)
    read_json_path = {row["sample_id"]: row for row in index}
    for rep in representatives:
        sample_id = rep["sample_id"]
        scene = read_json(output_root / read_json_path[sample_id]["scene_path"])
        _, gt = _load_recon(cache_dir, sample_id, "BP")
        prefix = f"{rep['label']}_{sample_id}"
        _render_scene_points(scene, scene_dir / f"{prefix}_gt_3d.png")
        _render_three_views(scene, scene_dir / f"{prefix}_gt_views.png")
        _render_gt_slice_montage(gt, scene_dir / f"{prefix}_gt_slice_montage.png")
        _render_compare(sample_id, cache_dir, compare_dir / f"{prefix}_compare.png")
        for method in METHOD_ORDER:
            _render_slices(sample_id, method, cache_dir, slice_dir / f"{prefix}_{method}_slices.png")

    _plot_curves(output_root, metrics, failure_cases)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render ET dataset and reconstruction visualizations.")
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()
    render(Path(args.output_root))
    print("Rendered ET visualizations")


if __name__ == "__main__":
    main()
