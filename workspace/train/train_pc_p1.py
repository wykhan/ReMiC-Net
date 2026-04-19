from __future__ import annotations

import argparse
import json
import shutil
import time
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

from workspace.common.io_utils import ensure_dir, read_json, write_json, write_text
from workspace.eval.eval_et_baselines_variantB import _failure_tags
from workspace.eval.metrics_3d import nmse, psnr, ssim_global
from workspace.models.unet3d_small import UNet3DSmall
from workspace.train.physics_consistency import EchoSubsetConfig, echo_nmse_loss, extract_center_patch, load_sparse_echo_subset, summarize_config
from workspace.train.train_two_stage_et import TARGET_SHAPE, _fit_to_shape, _normalize_pair


class PCDataset(Dataset):
    def __init__(self, samples: list[dict[str, Any]], output_root: Path) -> None:
        self.rows = samples
        self.output_root = output_root

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int) -> dict[str, Any]:
        row = self.rows[index]
        coarse_npz = np.load(self.output_root / row["ref3_path"])
        gt_npz = np.load(self.output_root / row["gt_path"])
        coarse_raw = coarse_npz["volume"].astype(np.float32)
        gt_raw = gt_npz["volume"].astype(np.float32)
        scale = max(float(np.max(gt_raw)), float(np.max(coarse_raw)), 1.0e-6)
        coarse, gt = _normalize_pair(_fit_to_shape(coarse_raw, TARGET_SHAPE), _fit_to_shape(gt_raw, TARGET_SHAPE))
        return {
            "input": torch.from_numpy(coarse[None, ...]),
            "target": torch.from_numpy(gt[None, ...]),
            "sample_id": row["sample_id"],
            "family": row["family"],
            "dataset_source": row["dataset_source"],
            "raw_shape": tuple(int(v) for v in coarse_raw.shape),
            "x_values": gt_npz["x_values"],
            "y_values": gt_npz["y_values"],
            "z_values": gt_npz["z_values"],
            "echo_path": str(self.output_root / row["echo_path"]),
            "scale": scale,
        }


def _collate(batch: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "input": torch.stack([item["input"] for item in batch], dim=0),
        "target": torch.stack([item["target"] for item in batch], dim=0),
        "sample_id": [item["sample_id"] for item in batch],
        "family": [item["family"] for item in batch],
        "dataset_source": [item["dataset_source"] for item in batch],
        "raw_shape": [item["raw_shape"] for item in batch],
        "x_values": [item["x_values"] for item in batch],
        "y_values": [item["y_values"] for item in batch],
        "z_values": [item["z_values"] for item in batch],
        "echo_path": [item["echo_path"] for item in batch],
        "scale": [item["scale"] for item in batch],
    }


def _image_loss(pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    base = nn.functional.smooth_l1_loss(pred, target)
    nmse_term = torch.sum((pred - target) ** 2) / (torch.sum(target**2) + 1.0e-8)
    return base + 0.1 * nmse_term


def _run_epoch(
    model: nn.Module,
    loader: DataLoader,
    device: torch.device,
    optimizer: torch.optim.Optimizer | None,
    subset_cfg: EchoSubsetConfig,
    lambda_pc: float,
) -> dict[str, float]:
    model.train(optimizer is not None)
    loss_values = []
    image_values = []
    echo_values = []
    for batch in loader:
        inputs = batch["input"].to(device)
        targets = batch["target"].to(device)
        preds = model(inputs)
        image_loss = _image_loss(preds, targets)
        echo_losses = []
        for idx, sample_id in enumerate(batch["sample_id"]):
            subset = load_sparse_echo_subset(Path(batch["echo_path"][idx]), sample_id, subset_cfg)
            pred_raw = extract_center_patch(preds[idx, 0], batch["raw_shape"][idx])
            echo_losses.append(
                echo_nmse_loss(
                    pred_volume=pred_raw,
                    x_values=batch["x_values"][idx],
                    y_values=batch["y_values"][idx],
                    z_values=batch["z_values"][idx],
                    subset=subset,
                    scale=batch["scale"][idx],
                    device=device,
                )
            )
        echo_loss = torch.stack(echo_losses).mean()
        total_loss = image_loss + float(lambda_pc) * echo_loss
        if optimizer is not None:
            optimizer.zero_grad()
            total_loss.backward()
            optimizer.step()
        loss_values.append(float(total_loss.item()))
        image_values.append(float(image_loss.item()))
        echo_values.append(float(echo_loss.item()))
    return {
        "total_loss": float(np.mean(loss_values)) if loss_values else 0.0,
        "image_loss": float(np.mean(image_values)) if image_values else 0.0,
        "echo_loss": float(np.mean(echo_values)) if echo_values else 0.0,
    }


def _evaluate(
    model: nn.Module,
    rows: list[dict[str, Any]],
    output_root: Path,
    device: torch.device,
    pred_dir_name: str,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, int], dict[str, Any]]:
    model.eval()
    pred_root = ensure_dir(output_root / "predictions" / pred_dir_name)
    sample_rows = []
    family_group: dict[str, list[dict[str, Any]]] = {}
    failure_counts = {"baseline": {}, "pc": {}}
    total_time = 0.0
    with torch.no_grad():
        for row in rows:
            coarse_npz = np.load(output_root / row["ref3_path"])
            gt_npz = np.load(output_root / row["gt_path"])
            coarse, gt = _normalize_pair(_fit_to_shape(coarse_npz["volume"], TARGET_SHAPE), _fit_to_shape(gt_npz["volume"], TARGET_SHAPE))
            inp = torch.from_numpy(coarse[None, None, ...]).to(device)
            t0 = time.perf_counter()
            pred = model(inp).cpu().numpy()[0, 0]
            total_time += time.perf_counter() - t0
            np.savez_compressed(pred_root / f"{row['sample_id']}_pc_pred.npz", pred=pred.astype(np.float32), coarse=coarse.astype(np.float32), gt=gt.astype(np.float32))
            base_fail = _failure_tags(coarse, gt, row["family"], nmse(coarse, gt))
            pc_fail = _failure_tags(pred, gt, row["family"], nmse(pred, gt))
            for label in base_fail["tags"]:
                failure_counts["baseline"][label] = failure_counts["baseline"].get(label, 0) + 1
            for label in pc_fail["tags"]:
                failure_counts["pc"][label] = failure_counts["pc"].get(label, 0) + 1
            payload = {
                "sample_id": row["sample_id"],
                "family": row["family"],
                "ref3_nmse": nmse(coarse, gt),
                "ref3_psnr": psnr(coarse, gt),
                "ref3_ssim": ssim_global(coarse, gt),
                "pc_nmse": nmse(pred, gt),
                "pc_psnr": psnr(pred, gt),
                "pc_ssim": ssim_global(pred, gt),
            }
            sample_rows.append(payload)
            family_group.setdefault(row["family"], []).append(payload)
    overall = {
        "num_test_samples": len(rows),
        "ref3_nmse_mean": float(np.mean([row["ref3_nmse"] for row in sample_rows])),
        "ref3_psnr_mean": float(np.mean([row["ref3_psnr"] for row in sample_rows])),
        "ref3_ssim_mean": float(np.mean([row["ref3_ssim"] for row in sample_rows])),
        "pc_nmse_mean": float(np.mean([row["pc_nmse"] for row in sample_rows])),
        "pc_psnr_mean": float(np.mean([row["pc_psnr"] for row in sample_rows])),
        "pc_ssim_mean": float(np.mean([row["pc_ssim"] for row in sample_rows])),
        "nmse_gain_vs_ref3": float(np.mean([row["ref3_nmse"] - row["pc_nmse"] for row in sample_rows])),
        "psnr_gain_vs_ref3": float(np.mean([row["pc_psnr"] - row["ref3_psnr"] for row in sample_rows])),
        "ssim_gain_vs_ref3": float(np.mean([row["pc_ssim"] - row["ref3_ssim"] for row in sample_rows])),
        "avg_inference_time_sec": float(total_time / max(len(rows), 1)),
    }
    family_metrics = {}
    for family, values in family_group.items():
        family_metrics[family] = {
            "count": len(values),
            "baseline_nmse_mean": float(np.mean([row["ref3_nmse"] for row in values])),
            "pc_nmse_mean": float(np.mean([row["pc_nmse"] for row in values])),
            "baseline_psnr_mean": float(np.mean([row["ref3_psnr"] for row in values])),
            "pc_psnr_mean": float(np.mean([row["pc_psnr"] for row in values])),
            "baseline_ssim_mean": float(np.mean([row["ref3_ssim"] for row in values])),
            "pc_ssim_mean": float(np.mean([row["pc_ssim"] for row in values])),
            "nmse_gain": float(np.mean([row["ref3_nmse"] - row["pc_nmse"] for row in values])),
        }
    return overall, sample_rows, failure_counts, family_metrics


def train_pc_p1(
    output_root: Path,
    source_root: Path,
    epochs: int,
    batch_size: int,
    lr: float,
    lambda_pc: float,
    subset_cfg: EchoSubsetConfig,
) -> dict[str, Any]:
    source_manifest = read_json(source_root / "learning_handoff_manifest_main_800_100_100.json")
    shutil.copyfile(source_root / "learning_handoff_manifest_main_800_100_100.json", output_root / "learning_handoff_manifest_main_800_100_100.json")
    shutil.copyfile(source_root / "learning_handoff_manifest_main_800_100_100.json", output_root / "learning_handoff_manifest_full.json")
    shutil.copyfile(source_root / "dataset_protocol_snapshot.md", output_root / "dataset_protocol_snapshot.md")
    shutil.copyfile(source_root / "data_origin_statement.md", output_root / "data_origin_statement.md")
    if (output_root / "checkpoints").exists():
        pass
    train_rows = [row for row in source_manifest["samples"] if row["split"] == "train"]
    val_rows = [row for row in source_manifest["samples"] if row["split"] == "val"]
    test_rows = [row for row in source_manifest["samples"] if row["split"] == "test"]
    train_loader = DataLoader(PCDataset(train_rows, source_root), batch_size=batch_size, shuffle=True, collate_fn=_collate)
    val_loader = DataLoader(PCDataset(val_rows, source_root), batch_size=batch_size, shuffle=False, collate_fn=_collate)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = UNet3DSmall(base_channels=8).to(device)
    baseline_ckpt = torch.load(source_root / "checkpoints" / "frozen_mainline" / "best.pt", map_location=device)
    model.load_state_dict(baseline_ckpt["model_state"])
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    ckpt_dir = ensure_dir(output_root / "checkpoints" / "pc_p1")
    best_path = ckpt_dir / "best.pt"

    history = {"train_total": [], "train_image": [], "train_echo": [], "val_total": [], "val_image": [], "val_echo": []}
    best_val = float("inf")
    for _epoch in range(epochs):
        train_stats = _run_epoch(model, train_loader, device, optimizer, subset_cfg, lambda_pc)
        val_stats = _run_epoch(model, val_loader, device, None, subset_cfg, lambda_pc)
        history["train_total"].append(train_stats["total_loss"])
        history["train_image"].append(train_stats["image_loss"])
        history["train_echo"].append(train_stats["echo_loss"])
        history["val_total"].append(val_stats["total_loss"])
        history["val_image"].append(val_stats["image_loss"])
        history["val_echo"].append(val_stats["echo_loss"])
        if val_stats["total_loss"] < best_val:
            best_val = val_stats["total_loss"]
            torch.save({"model_state": model.state_dict()}, best_path)

    model.load_state_dict(torch.load(best_path, map_location=device)["model_state"])
    overall, sample_rows, failure_counts, family_metrics = _evaluate(model, test_rows, source_root, device, "pc_p1")
    payload = {
        "training_config": {
            "epochs": epochs,
            "batch_size": batch_size,
            "lr": lr,
            "lambda_pc": lambda_pc,
            "device": str(device),
            "baseline_checkpoint": str(source_root / "checkpoints" / "frozen_mainline" / "best.pt"),
            "consistency": summarize_config(subset_cfg, lambda_pc),
        },
        "history": history,
        "overall": overall,
        "family_metrics": family_metrics,
        "failure_counts": failure_counts,
        "best_checkpoint": str(best_path.relative_to(output_root)),
    }
    write_json(output_root / "metrics_pc_p1.json", payload)
    write_json(output_root / "predictions" / "pc_p1_sample_metrics.json", sample_rows)
    config_lines = [
        "mode: Ours-PC-P1",
        f"epochs: {epochs}",
        f"batch_size: {batch_size}",
        f"lr: {lr}",
        f"lambda_pc: {lambda_pc}",
        f"active_cells_per_sample: {subset_cfg.active_cells_per_sample}",
        f"frequencies_per_cell: {subset_cfg.frequencies_per_cell}",
        f"fixed_subset: {subset_cfg.fixed_subset}",
        f"subset_seed: {subset_cfg.subset_seed}",
    ]
    write_text(output_root / "consistency_config_P1.yaml", "\n".join(config_lines) + "\n")
    fig, ax = plt.subplots(figsize=(8, 4.4))
    ax.plot(history["train_total"], label="train_total")
    ax.plot(history["val_total"], label="val_total")
    ax.plot(history["train_echo"], label="train_echo")
    ax.plot(history["val_echo"], label="val_echo")
    ax.set_title("PC-P1 training curves")
    ax.legend()
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(ensure_dir(output_root / "viz" / "progress" / "curves") / "pc_p1_training_curves.png", dpi=170)
    plt.close(fig)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Train physics-consistency P1 model.")
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--lr", type=float, default=5e-4)
    parser.add_argument("--lambda-pc", type=float, default=0.05)
    parser.add_argument("--active-cells", type=int, default=12)
    parser.add_argument("--freq-count", type=int, default=24)
    args = parser.parse_args()
    payload = train_pc_p1(
        output_root=Path(args.output_root),
        source_root=Path(args.source_root),
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        lambda_pc=args.lambda_pc,
        subset_cfg=EchoSubsetConfig(active_cells_per_sample=args.active_cells, frequencies_per_cell=args.freq_count),
    )
    print(
        f"Finished pc_p1 learned_nmse={payload['overall']['pc_nmse_mean']:.6f} "
        f"gain={payload['overall']['nmse_gain_vs_ref3']:.6f}"
    )


if __name__ == "__main__":
    main()
