from __future__ import annotations

import argparse
import csv
import json
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler

from workspace.common.io_utils import ensure_dir, read_json, write_json, write_text
from workspace.eval.eval_et_baselines_variantB import _failure_tags
from workspace.eval.metrics_3d import nmse, psnr, ssim_global
from workspace.models.unet3d_small import UNet3DSmall
from workspace.recon.cyl_fast_reference_engine import reconstruct_cylindrical_reference


TARGET_SHAPE = (24, 24, 24)
HARD_FAMILIES = {"point_cluster", "line", "L-shape"}


def _fit_to_shape(volume: np.ndarray, target_shape: tuple[int, int, int]) -> np.ndarray:
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


def _normalize_pair(coarse: np.ndarray, gt: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    coarse = coarse.astype(np.float32)
    gt = gt.astype(np.float32)
    scale = max(float(np.max(gt)), float(np.max(coarse)), 1.0e-6)
    return coarse / scale, gt / scale


class ETFullDataset(Dataset):
    def __init__(self, samples: list[dict[str, Any]], output_root: Path) -> None:
        self.rows = samples
        self.output_root = output_root

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int) -> dict[str, Any]:
        row = self.rows[index]
        coarse_npz = np.load(self.output_root / row["ref3_path"])
        gt_npz = np.load(self.output_root / row["gt_path"])
        coarse, gt = _normalize_pair(
            _fit_to_shape(coarse_npz["volume"], TARGET_SHAPE),
            _fit_to_shape(gt_npz["volume"], TARGET_SHAPE),
        )
        return {
            "input": torch.from_numpy(coarse[None, ...]),
            "target": torch.from_numpy(gt[None, ...]),
            "sample_id": row["sample_id"],
            "family": row["family"],
            "dataset_source": row["dataset_source"],
        }


def _collate(batch: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "input": torch.stack([item["input"] for item in batch], dim=0),
        "target": torch.stack([item["target"] for item in batch], dim=0),
        "sample_id": [item["sample_id"] for item in batch],
        "family": [item["family"] for item in batch],
        "dataset_source": [item["dataset_source"] for item in batch],
    }


def _select_rows(manifest: dict[str, Any], split: str, mode: str) -> list[dict[str, Any]]:
    rows = [row for row in manifest["samples"] if row["split"] == split]
    if mode == "M2":
        rows = [row for row in rows if not row["is_random_et"]]
    return rows


def _make_loader(dataset: ETFullDataset, mode: str, batch_size: int, shuffle: bool) -> DataLoader:
    if mode != "M3" or not shuffle:
        return DataLoader(dataset, batch_size=batch_size, shuffle=shuffle, collate_fn=_collate)
    weights = []
    for row in dataset.rows:
        weight = 1.0
        if row["family"] in HARD_FAMILIES:
            weight *= 2.5
        if row["dataset_source"] == "random_et":
            weight *= 0.9
        weights.append(weight)
    sampler = WeightedRandomSampler(weights=weights, num_samples=len(weights), replacement=True)
    return DataLoader(dataset, batch_size=batch_size, sampler=sampler, collate_fn=_collate)


def _loss_fn(pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    base = nn.functional.smooth_l1_loss(pred, target)
    nmse_term = torch.sum((pred - target) ** 2) / (torch.sum(target**2) + 1.0e-8)
    return base + 0.1 * nmse_term


def _run_epoch(model: nn.Module, loader: DataLoader, device: torch.device, optimizer: torch.optim.Optimizer | None, mode: str) -> float:
    train_mode = optimizer is not None
    model.train(train_mode)
    losses: list[float] = []
    for batch in loader:
        inputs = batch["input"].to(device)
        targets = batch["target"].to(device)
        preds = model(inputs)
        loss = _loss_fn(preds, targets)
        if train_mode:
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        losses.append(float(loss.item()))
    return float(np.mean(losses)) if losses else 0.0


def _write_training_config(output_root: Path, mode: str, config: dict[str, Any]) -> None:
    lines = []
    for key, value in config.items():
        lines.append(f"{key}: {json.dumps(value) if isinstance(value, (dict, list)) else value}")
    write_text(output_root / f"training_config_{mode}.yaml", "\n".join(lines) + "\n")


def _evaluate_rows(
    model: nn.Module,
    rows: list[dict[str, Any]],
    output_root: Path,
    device: torch.device,
    mode: str,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    model.eval()
    sample_rows: list[dict[str, Any]] = []
    family_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    failure_counts = {"ref3": defaultdict(int), mode: defaultdict(int)}
    total_infer_time = 0.0
    pred_cache = ensure_dir(output_root / "predictions" / mode)
    with torch.no_grad():
        for row in rows:
            coarse_npz = np.load(output_root / row["ref3_path"])
            gt_npz = np.load(output_root / row["gt_path"])
            coarse, gt = _normalize_pair(
                _fit_to_shape(coarse_npz["volume"], TARGET_SHAPE),
                _fit_to_shape(gt_npz["volume"], TARGET_SHAPE),
            )
            input_tensor = torch.from_numpy(coarse[None, None, ...]).to(device)
            started = time.perf_counter()
            pred = model(input_tensor).cpu().numpy()[0, 0]
            total_infer_time += time.perf_counter() - started
            np.savez_compressed(
                pred_cache / f"{row['sample_id']}_{mode}_pred.npz",
                pred=pred.astype(np.float32),
                coarse=coarse.astype(np.float32),
                gt=gt.astype(np.float32),
            )
            ref3_fail = _failure_tags(coarse, gt, row["family"], nmse(coarse, gt))
            pred_fail = _failure_tags(pred, gt, row["family"], nmse(pred, gt))
            for label in ref3_fail["tags"]:
                failure_counts["ref3"][label] += 1
            for label in pred_fail["tags"]:
                failure_counts[mode][label] += 1
            item = {
                "sample_id": row["sample_id"],
                "family": row["family"],
                "dataset_source": row["dataset_source"],
                "ref3_nmse": nmse(coarse, gt),
                "ref3_psnr": psnr(coarse, gt),
                "ref3_ssim": ssim_global(coarse, gt),
                "learned_nmse": nmse(pred, gt),
                "learned_psnr": psnr(pred, gt),
                "learned_ssim": ssim_global(pred, gt),
                "ref3_failure_tags": ref3_fail["tags"],
                "learned_failure_tags": pred_fail["tags"],
            }
            sample_rows.append(item)
            family_group[row["family"]].append(item)
    overall = {
        "mode": mode,
        "num_test_samples": len(rows),
        "ref3_nmse_mean": float(np.mean([row["ref3_nmse"] for row in sample_rows])),
        "ref3_psnr_mean": float(np.mean([row["ref3_psnr"] for row in sample_rows])),
        "ref3_ssim_mean": float(np.mean([row["ref3_ssim"] for row in sample_rows])),
        "learned_nmse_mean": float(np.mean([row["learned_nmse"] for row in sample_rows])),
        "learned_psnr_mean": float(np.mean([row["learned_psnr"] for row in sample_rows])),
        "learned_ssim_mean": float(np.mean([row["learned_ssim"] for row in sample_rows])),
        "nmse_gain_vs_ref3": float(np.mean([row["ref3_nmse"] - row["learned_nmse"] for row in sample_rows])),
        "psnr_gain_vs_ref3": float(np.mean([row["learned_psnr"] - row["ref3_psnr"] for row in sample_rows])),
        "ssim_gain_vs_ref3": float(np.mean([row["learned_ssim"] - row["ref3_ssim"] for row in sample_rows])),
        "avg_inference_time_sec": float(total_infer_time / max(len(rows), 1)),
    }
    family_metrics = {}
    for family, family_rows in family_group.items():
        family_metrics[family] = {
            "count": len(family_rows),
            "ref3_nmse_mean": float(np.mean([row["ref3_nmse"] for row in family_rows])),
            "learned_nmse_mean": float(np.mean([row["learned_nmse"] for row in family_rows])),
            "ref3_psnr_mean": float(np.mean([row["ref3_psnr"] for row in family_rows])),
            "learned_psnr_mean": float(np.mean([row["learned_psnr"] for row in family_rows])),
            "ref3_ssim_mean": float(np.mean([row["ref3_ssim"] for row in family_rows])),
            "learned_ssim_mean": float(np.mean([row["learned_ssim"] for row in family_rows])),
            "nmse_gain_vs_ref3": float(np.mean([row["ref3_nmse"] - row["learned_nmse"] for row in family_rows])),
        }
    return overall, sample_rows, family_metrics, {k: dict(v) for k, v in failure_counts.items()}


def train_mode(output_root: Path, mode: str, epochs: int, batch_size: int, lr: float, smoke_limit: int) -> dict[str, Any]:
    manifest = read_json(output_root / "learning_handoff_manifest_full.json")
    train_rows = _select_rows(manifest, "train", mode)
    val_rows = _select_rows(manifest, "val", mode)
    test_rows = _select_rows(manifest, "test", mode)
    train_ds = ETFullDataset(train_rows, output_root)
    val_ds = ETFullDataset(val_rows, output_root)
    train_loader = _make_loader(train_ds, mode=mode, batch_size=batch_size, shuffle=True)
    val_loader = _make_loader(val_ds, mode=mode, batch_size=batch_size, shuffle=False)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = UNet3DSmall(base_channels=8).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    checkpoint_dir = ensure_dir(output_root / "checkpoints" / mode)

    smoke_train_rows = train_rows[: min(smoke_limit, len(train_rows))]
    smoke_val_rows = val_rows[: min(max(smoke_limit // 2, 1), len(val_rows))]
    smoke_train_loss = 0.0
    smoke_val_loss = 0.0
    if smoke_train_rows and smoke_val_rows:
        smoke_train_loader = _make_loader(ETFullDataset(smoke_train_rows, output_root), mode=mode, batch_size=min(batch_size, 4), shuffle=True)
        smoke_val_loader = _make_loader(ETFullDataset(smoke_val_rows, output_root), mode=mode, batch_size=min(batch_size, 4), shuffle=False)
        smoke_train_loss = _run_epoch(model, smoke_train_loader, device, optimizer, mode)
        smoke_val_loss = _run_epoch(model, smoke_val_loader, device, None, mode)

    history = {"train_losses": [], "val_losses": [], "smoke_train_loss": smoke_train_loss, "smoke_val_loss": smoke_val_loss}
    best_val = float("inf")
    best_ckpt = checkpoint_dir / "best.pt"
    for _epoch in range(epochs):
        train_loss = _run_epoch(model, train_loader, device, optimizer, mode)
        val_loss = _run_epoch(model, val_loader, device, None, mode)
        history["train_losses"].append(train_loss)
        history["val_losses"].append(val_loss)
        if val_loss < best_val:
            best_val = val_loss
            torch.save({"model_state": model.state_dict(), "mode": mode, "target_shape": TARGET_SHAPE}, best_ckpt)

    ckpt = torch.load(best_ckpt, map_location=device)
    model.load_state_dict(ckpt["model_state"])
    overall, sample_rows, family_metrics, failure_counts = _evaluate_rows(model, test_rows, output_root, device, mode)
    history["best_val_loss"] = best_val
    history["epochs"] = epochs

    metrics_payload = {
        "mode": mode,
        "config": {
            "epochs": epochs,
            "batch_size": batch_size,
            "lr": lr,
            "train_count": len(train_rows),
            "val_count": len(val_rows),
            "test_count": len(test_rows),
            "device": str(device),
        },
        "history": history,
        "overall": overall,
        "family_metrics": family_metrics,
        "failure_counts": failure_counts,
        "best_checkpoint": str(best_ckpt.relative_to(output_root)),
    }
    write_json(output_root / f"metrics_{mode}.json", metrics_payload)
    write_json(output_root / "predictions" / f"{mode}_sample_metrics.json", sample_rows)
    _write_training_config(output_root, mode, metrics_payload["config"])
    return metrics_payload


def render_loss_curve(output_root: Path, mode: str, metrics: dict[str, Any]) -> None:
    curves_dir = ensure_dir(output_root / "viz" / "curves")
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(metrics["history"]["train_losses"], label="train")
    ax.plot(metrics["history"]["val_losses"], label="val")
    ax.set_title(f"Train / val loss {mode}")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(curves_dir / f"train_val_loss_{mode}.png", dpi=170)
    plt.close(fig)


def _render_scene_points(scene: dict[str, Any], output_path: Path) -> None:
    scene_dir = ensure_dir(output_path.parent)
    del scene_dir
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


def _representative_compare(
    output_root: Path,
    mode: str,
    sample_id: str,
    scene_rel: str,
    echo_rel: str,
    learned_pred_path: Path,
) -> None:
    compare_dir = ensure_dir(output_root / "viz" / "recon_compare")
    slice_dir = ensure_dir(output_root / "viz" / "slices")
    pred_npz = np.load(learned_pred_path)
    pred = pred_npz["pred"]
    coarse = pred_npz["coarse"]
    gt = pred_npz["gt"]
    scene = read_json(output_root / scene_rel)
    scene_dir = ensure_dir(output_root / "viz" / "scene_3d")
    recon_cache = ensure_dir(output_root / "viz" / "representative_cache")
    _render_scene_points(scene, scene_dir / f"{sample_id}_gt_3d.png")
    _render_three_views(scene, scene_dir / f"{sample_id}_gt_views.png")
    _render_gt_slice_montage(gt, scene_dir / f"{sample_id}_gt_slice_montage.png")
    refs = {
        "ref5": reconstruct_cylindrical_reference(output_root / scene_rel, output_root / echo_rel, "ref5")["volume"],
        "ref7": reconstruct_cylindrical_reference(output_root / scene_rel, output_root / echo_rel, "ref7")["volume"],
        "BP": reconstruct_cylindrical_reference(output_root / scene_rel, output_root / echo_rel, "BP")["volume"],
    }
    refs = {key: _fit_to_shape(value, TARGET_SHAPE) for key, value in refs.items()}
    np.savez_compressed(recon_cache / f"{sample_id}_{mode}_compare_refs.npz", **refs)
    fig, axes = plt.subplots(2, 3, figsize=(12, 7))
    items = [("GT", gt), ("ref3", coarse), (mode, pred), ("ref5", refs["ref5"]), ("ref7", refs["ref7"]), ("BP", refs["BP"])]
    for ax, (label, volume) in zip(axes.ravel(), items):
        ax.imshow(volume.max(axis=2), cmap="viridis")
        ax.set_title(label)
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(compare_dir / f"{mode}_{sample_id}_compare.png", dpi=170)
    plt.close(fig)

    z_idx = gt.shape[2] // 2
    fig, axes = plt.subplots(2, 3, figsize=(11, 7))
    slices = [
        ("GT", gt[:, :, z_idx]),
        ("ref3", coarse[:, :, z_idx]),
        (mode, pred[:, :, z_idx]),
        ("abs err learned", np.abs(pred[:, :, z_idx] - gt[:, :, z_idx])),
        ("abs err ref3", np.abs(coarse[:, :, z_idx] - gt[:, :, z_idx])),
        ("BP", refs["BP"][:, :, z_idx]),
    ]
    for ax, (label, image) in zip(axes.ravel(), slices):
        ax.imshow(image, cmap="viridis" if "err" not in label else "magma")
        ax.set_title(label)
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(slice_dir / f"{mode}_{sample_id}_slices.png", dpi=170)
    plt.close(fig)


def _append_family_metrics_csv(output_root: Path, mode: str, metrics: dict[str, Any]) -> None:
    path = output_root / "family_metrics.csv"
    write_header = not path.exists()
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["mode", "family", "count", "ref3_nmse_mean", "learned_nmse_mean", "ref3_psnr_mean", "learned_psnr_mean", "ref3_ssim_mean", "learned_ssim_mean", "nmse_gain_vs_ref3"],
        )
        if write_header:
            writer.writeheader()
        for family, row in metrics["family_metrics"].items():
            payload = {"mode": mode, "family": family}
            payload.update(row)
            writer.writerow(payload)


def _append_failure_csv(output_root: Path, mode: str, metrics: dict[str, Any]) -> None:
    path = output_root / "failure_mode_improvement.csv"
    write_header = not path.exists()
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["mode", "failure_label", "ref3_count", "learned_count", "improvement_count"])
        if write_header:
            writer.writeheader()
        for label in ["F2", "F3", "F4"]:
            ref3_count = metrics["failure_counts"]["ref3"].get(label, 0)
            learned_count = metrics["failure_counts"][mode].get(label, 0)
            writer.writerow(
                {
                    "mode": mode,
                    "failure_label": label,
                    "ref3_count": ref3_count,
                    "learned_count": learned_count,
                    "improvement_count": ref3_count - learned_count,
                }
            )


def _write_representative_manifest(output_root: Path, mode: str) -> None:
    manifest = read_json(output_root / "learning_handoff_manifest_full.json")
    sample_rows = read_json(output_root / "predictions" / f"{mode}_sample_metrics.json")
    row_by_id = {row["sample_id"]: row for row in manifest["samples"]}
    hard_rows = [row for row in sample_rows if row["family"] in HARD_FAMILIES]
    improved = max(hard_rows, key=lambda row: row["ref3_nmse"] - row["learned_nmse"])
    stubborn = max(hard_rows, key=lambda row: row["learned_nmse"])
    ordinary_pool = [row for row in sample_rows if row["family"] not in HARD_FAMILIES and not row["dataset_source"].startswith("random_et")]
    if not ordinary_pool:
        ordinary_pool = [row for row in sample_rows if row["family"] not in HARD_FAMILIES]
    if not ordinary_pool:
        ordinary_pool = sample_rows[:]
    ordinary_success = max(ordinary_pool, key=lambda row: row["ref3_nmse"] - row["learned_nmse"])
    representatives = {
        "hard_improved": improved["sample_id"],
        "hard_still_failing": stubborn["sample_id"],
        "ordinary_success": ordinary_success["sample_id"],
    }
    for label, sample_id in representatives.items():
        meta = row_by_id[sample_id]
        _representative_compare(
            output_root=output_root,
            mode=mode,
            sample_id=f"{label}_{sample_id}",
            scene_rel=meta["scene_path"],
            echo_rel=meta["echo_path"],
            learned_pred_path=output_root / "predictions" / mode / f"{sample_id}_{mode}_pred.npz",
        )
    write_json(output_root / "predictions" / f"{mode}_representatives.json", representatives)


def main() -> None:
    parser = argparse.ArgumentParser(description="Train and evaluate the task_real_006 two-stage ET model.")
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--mode", required=True, choices=["M1", "M2", "M3"])
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--smoke-limit", type=int, default=16)
    args = parser.parse_args()
    metrics = train_mode(Path(args.output_root), args.mode, args.epochs, args.batch_size, args.lr, args.smoke_limit)
    render_loss_curve(Path(args.output_root), args.mode, metrics)
    _append_family_metrics_csv(Path(args.output_root), args.mode, metrics)
    _append_failure_csv(Path(args.output_root), args.mode, metrics)
    _write_representative_manifest(Path(args.output_root), args.mode)
    print(
        f"Finished {args.mode} learned_nmse={metrics['overall']['learned_nmse_mean']:.6f} "
        f"gain={metrics['overall']['nmse_gain_vs_ref3']:.6f}"
    )


if __name__ == "__main__":
    main()
