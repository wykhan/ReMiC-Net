from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from workspace.common.io_utils import ensure_dir, read_json


VARIANT_ORDER = ["A", "B", "C", "D"]
METHOD_ORDER = ["ref7", "ref9", "BP"]


def _render_scene(scene: dict, output_path: Path) -> None:
    pts = scene["points"]
    xyz = np.array([[p["x_m"], p["y_m"], p["z_m"]] for p in pts], dtype=np.float64)
    amps = [p["amplitude"] for p in pts]
    fig = plt.figure(figsize=(6, 5))
    ax = fig.add_subplot(111, projection="3d")
    ax.scatter(xyz[:, 0], xyz[:, 1], xyz[:, 2], c=amps, cmap="viridis", s=80)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_zlabel("z")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def _show_three_views(scene: dict, output_path: Path) -> None:
    xyz = np.array([[p["x_m"], p["y_m"], p["z_m"]] for p in scene["points"]], dtype=np.float64)
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


def _load_variant(cache_dir: Path, sample_id: str, method: str, variant: str) -> tuple[np.ndarray, np.ndarray]:
    data = np.load(cache_dir / f"{sample_id}_{method}_{variant}.npz")
    return data["volume"], data["gt_volume"]


def render(output_root: Path) -> None:
    scene_dir = ensure_dir(output_root / "viz" / "scene_3d")
    compare_dir = ensure_dir(output_root / "viz" / "recon_compare")
    slice_dir = ensure_dir(output_root / "viz" / "slices")
    index = read_json(output_root / "dataset" / "index.json")
    cache_dir = output_root / "wrap_variant_cache"
    representative_ids = [
        "inner_mid_negpi_exact",
        "inner_mid_pi_exact",
        "mid_high_negpi_p1",
        "outer_low_pi_m2",
    ]

    for sample_id in representative_ids:
        item = next(row for row in index if row["sample_id"] == sample_id)
        scene = read_json(output_root / item["scene_path"])
        _render_scene(scene, scene_dir / f"{sample_id}_gt_3d.png")
        _show_three_views(scene, scene_dir / f"{sample_id}_gt_views.png")

        fig, axes = plt.subplots(1, 4, figsize=(12, 3))
        volume, gt = _load_variant(cache_dir, sample_id, "BP", "A")
        axes[0].imshow(gt.max(axis=2), cmap="viridis")
        axes[0].set_title("GT")
        for ax, method in zip(axes[1:], METHOD_ORDER):
            volume, _ = _load_variant(cache_dir, sample_id, method, "A")
            ax.imshow(volume.max(axis=2), cmap="viridis")
            ax.set_title(f"{method}-A")
        for ax in axes:
            ax.axis("off")
        fig.tight_layout()
        fig.savefig(compare_dir / f"{sample_id}_method_compare.png", dpi=160)
        plt.close(fig)

        for method in ["ref7", "ref9", "BP"]:
            fig, axes = plt.subplots(1, 5, figsize=(15, 3))
            volume, gt = _load_variant(cache_dir, sample_id, method, "A")
            axes[0].imshow(gt.max(axis=2), cmap="viridis")
            axes[0].set_title("GT")
            for ax, variant in zip(axes[1:], VARIANT_ORDER):
                volume, gt = _load_variant(cache_dir, sample_id, method, variant)
                ax.imshow(volume.max(axis=2), cmap="viridis")
                ax.set_title(f"{method}-{variant}")
            for ax in axes:
                ax.axis("off")
            fig.tight_layout()
            fig.savefig(compare_dir / f"{sample_id}_{method}_variant_compare.png", dpi=160)
            plt.close(fig)

            fig, axes = plt.subplots(4, 3, figsize=(9, 10))
            for row_idx, variant in enumerate(VARIANT_ORDER):
                volume, gt = _load_variant(cache_dir, sample_id, method, variant)
                z_idx = volume.shape[2] // 2
                axes[row_idx, 0].imshow(gt[:, :, z_idx], cmap="viridis")
                axes[row_idx, 0].set_title(f"GT-{variant}")
                axes[row_idx, 1].imshow(volume[:, :, z_idx], cmap="viridis")
                axes[row_idx, 1].set_title(f"{method}-{variant}")
                axes[row_idx, 2].imshow(np.abs(volume[:, :, z_idx] - gt[:, :, z_idx]), cmap="magma")
                axes[row_idx, 2].set_title("abs error")
                for col_idx in range(3):
                    axes[row_idx, col_idx].axis("off")
            fig.tight_layout()
            fig.savefig(slice_dir / f"{sample_id}_{method}_variant_slices.png", dpi=160)
            plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render wrap-hardening visualizations.")
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()
    render(Path(args.output_root))
    print("Rendered wrap visualization outputs")


if __name__ == "__main__":
    main()
