from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from workspace.common.io_utils import ensure_dir, read_json


METHOD_ORDER = ["ref3", "ref5", "ref7", "ref9", "BP"]


def _render_scene(scene: dict, output_path: Path) -> None:
    pts = scene["points"]
    xs = [p["x_m"] for p in pts]
    ys = [p["y_m"] for p in pts]
    zs = [p["z_m"] for p in pts]
    amps = [p["amplitude"] for p in pts]
    fig = plt.figure(figsize=(6, 5))
    ax = fig.add_subplot(111, projection="3d")
    ax.scatter(xs, ys, zs, c=amps, cmap="viridis", s=80)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_zlabel("z")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def _show_three_views(scene: dict, output_path: Path) -> None:
    pts = scene["points"]
    xyz = np.array([[p["x_m"], p["y_m"], p["z_m"]] for p in pts], dtype=np.float64)
    fig, axes = plt.subplots(1, 3, figsize=(10, 3))
    axes[0].scatter(xyz[:, 0], xyz[:, 1], c="tab:blue")
    axes[0].set_title("top")
    axes[1].scatter(xyz[:, 0], xyz[:, 2], c="tab:orange")
    axes[1].set_title("front")
    axes[2].scatter(xyz[:, 1], xyz[:, 2], c="tab:green")
    axes[2].set_title("side")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def _load_recon(cache_dir: Path, sample_id: str, method: str) -> tuple[np.ndarray, np.ndarray]:
    data = np.load(cache_dir / f"{sample_id}_{method}_faithful.npz")
    return data["volume"], data["gt_volume"]


def render(output_root: Path) -> None:
    scene_dir = ensure_dir(output_root / "viz" / "scene_3d")
    compare_dir = ensure_dir(output_root / "viz" / "recon_compare")
    slice_dir = ensure_dir(output_root / "viz" / "slices")
    index = read_json(output_root / "dataset" / "index.json")
    cache_dir = output_root / "faithful_recon_cache"

    representative_ids = ["rho_000", "rho_015", "rho_030", "az_outer_negpi", "z_outer_high"]

    for sample_id in representative_ids:
        item = next(row for row in index if row["sample_id"] == sample_id)
        scene = read_json(output_root / item["scene_path"])
        _render_scene(scene, scene_dir / f"{sample_id}_gt_3d.png")
        _show_three_views(scene, scene_dir / f"{sample_id}_gt_views.png")

        fig, axes = plt.subplots(2, 3, figsize=(10, 6))
        for ax, method in zip(axes.ravel(), ["GT"] + METHOD_ORDER):
            if method == "GT":
                volume, gt = _load_recon(cache_dir, sample_id, "BP")
                mip = gt.max(axis=2)
                ax.imshow(mip, cmap="viridis")
                ax.set_title("GT")
            else:
                volume, gt = _load_recon(cache_dir, sample_id, method)
                mip = volume.max(axis=2)
                ax.imshow(mip, cmap="viridis")
                ax.set_title(method)
            ax.axis("off")
        fig.tight_layout()
        fig.savefig(compare_dir / f"{sample_id}_compare.png", dpi=160)
        plt.close(fig)

        volume, gt = _load_recon(cache_dir, sample_id, "ref3")
        z_idx = volume.shape[2] // 2
        fig, axes = plt.subplots(1, 3, figsize=(9, 3))
        axes[0].imshow(gt[:, :, z_idx], cmap="viridis")
        axes[0].set_title("GT slice")
        axes[1].imshow(volume[:, :, z_idx], cmap="viridis")
        axes[1].set_title("ref3 slice")
        axes[2].imshow(np.abs(volume[:, :, z_idx] - gt[:, :, z_idx]), cmap="magma")
        axes[2].set_title("abs error")
        for ax in axes:
            ax.axis("off")
        fig.tight_layout()
        fig.savefig(slice_dir / f"{sample_id}_ref3_slices.png", dpi=160)
        plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render task_real_003 point visualization outputs.")
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()
    render(Path(args.output_root))
    print("Rendered point visualization outputs")


if __name__ == "__main__":
    main()
