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
from workspace.train.physics_consistency import (
    EchoSubsetConfig,
    GeometryAwareConfig,
    echo_geo_nmse_loss,
    extract_center_patch,
    load_sparse_echo_subset,
    summarize_config,
    summarize_geometry_config,
)
from workspace.train.train_two_stage_et import TARGET_SHAPE, _fit_to_shape, _normalize_pair


class PCDataset(Dataset):
    def __init__(self, samples: list[dict[str, Any]], source_root: Path) -> None:
        self.rows = samples
        self.source_root = source_root

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int) -> dict[str, Any]:
        row = self.rows[index]
        coarse_npz = np.load(self.source_root / row["ref3_path"])
        gt_npz = np.load(self.source_root / row["gt_path"])
        coarse_raw = coarse_npz["volume"].astype(np.float32)
        gt_raw = gt_npz["volume"].astype(np.float32)
        scale = max(float(np.max(gt_raw)), float(np.max(coarse_raw)), 1.0e-6)
        coarse, gt = _normalize_pair(_fit_to_shape(coarse_raw, TARGET_SHAPE), _fit_to_shape(gt_raw, TARGET_SHAPE))
        return {
            "input": torch.from_numpy(coarse[None, ...]),
            "target": torch.from_numpy(gt[None, ...]),
            "sample_id": row["sample_id"],
            "family": row["family"],
            "raw_shape": tuple(int(v) for v in coarse_raw.shape),
            "x_values": gt_npz["x_values"],
            "y_values": gt_npz["y_values"],
            "z_values": gt_npz["z_values"],
            "echo_path": str(self.source_root / row["echo_path"]),
            "scale": scale,
        }


def _collate(batch: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "input": torch.stack([item["input"] for item in batch], dim=0),
        "target": torch.stack([item["target"] for item in batch], dim=0),
        "sample_id": [item["sample_id"] for item in batch],
        "family": [item["family"] for item in batch],
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
    geo_cfg: GeometryAwareConfig,
    lambda_pc: float,
) -> dict[str, float]:
    model.train(optimizer is not None)
    total_vals = []
    image_vals = []
    geo_vals = []
    weight_vals = []
    support_vals = []
    boundary_vals = []
    for batch in loader:
        inputs = batch["input"].to(device)
        targets = batch["target"].to(device)
        preds = model(inputs)
        image_loss = _image_loss(preds, targets)
        geo_losses = []
        summaries = []
        for idx, sample_id in enumerate(batch["sample_id"]):
            subset = load_sparse_echo_subset(Path(batch["echo_path"][idx]), sample_id, subset_cfg)
            pred_raw = extract_center_patch(preds[idx, 0], batch["raw_shape"][idx])
            geo_loss, summary = echo_geo_nmse_loss(
                pred_volume=pred_raw,
                x_values=batch["x_values"][idx],
                y_values=batch["y_values"][idx],
                z_values=batch["z_values"][idx],
                subset=subset,
                scale=batch["scale"][idx],
                device=device,
                geo_config=geo_cfg,
            )
            geo_losses.append(geo_loss)
            summaries.append(summary)
        geo_loss = torch.stack(geo_losses).mean()
        total_loss = image_loss + float(lambda_pc) * geo_loss
        if optimizer is not None:
            optimizer.zero_grad()
            total_loss.backward()
            optimizer.step()
        total_vals.append(float(total_loss.item()))
        image_vals.append(float(image_loss.item()))
        geo_vals.append(float(geo_loss.item()))
        weight_vals.extend(summary["measurement_weight_mean"] for summary in summaries)
        support_vals.extend(summary["support_fraction"] for summary in summaries)
        boundary_vals.extend(summary["boundary_fraction"] for summary in summaries)
    return {
        "total_loss": float(np.mean(total_vals)) if total_vals else 0.0,
        "image_loss": float(np.mean(image_vals)) if image_vals else 0.0,
        "geo_loss": float(np.mean(geo_vals)) if geo_vals else 0.0,
        "measurement_weight_mean": float(np.mean(weight_vals)) if weight_vals else 1.0,
        "support_fraction_mean": float(np.mean(support_vals)) if support_vals else 0.0,
        "boundary_fraction_mean": float(np.mean(boundary_vals)) if boundary_vals else 0.0,
    }


def _evaluate(
    model: nn.Module,
    rows: list[dict[str, Any]],
    source_root: Path,
    output_root: Path,
    device: torch.device,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, int], dict[str, Any]]:
    model.eval()
    pred_root = ensure_dir(output_root / "predictions" / "pc_p2a")
    sample_rows = []
    family_group: dict[str, list[dict[str, Any]]] = {}
    failure_counts = {"baseline": {}, "p2a": {}}
    total_time = 0.0
    with torch.no_grad():
        for row in rows:
            coarse_npz = np.load(source_root / row["ref3_path"])
            gt_npz = np.load(source_root / row["gt_path"])
            coarse, gt = _normalize_pair(_fit_to_shape(coarse_npz["volume"], TARGET_SHAPE), _fit_to_shape(gt_npz["volume"], TARGET_SHAPE))
            inp = torch.from_numpy(coarse[None, None, ...]).to(device)
            t0 = time.perf_counter()
            pred = model(inp).cpu().numpy()[0, 0]
            total_time += time.perf_counter() - t0
            np.savez_compressed(pred_root / f"{row['sample_id']}_pc_pred.npz", pred=pred.astype(np.float32), coarse=coarse.astype(np.float32), gt=gt.astype(np.float32))
            base_fail = _failure_tags(coarse, gt, row["family"], nmse(coarse, gt))
            p2_fail = _failure_tags(pred, gt, row["family"], nmse(pred, gt))
            for label in base_fail["tags"]:
                failure_counts["baseline"][label] = failure_counts["baseline"].get(label, 0) + 1
            for label in p2_fail["tags"]:
                failure_counts["p2a"][label] = failure_counts["p2a"].get(label, 0) + 1
            payload = {
                "sample_id": row["sample_id"],
                "family": row["family"],
                "ref3_nmse": nmse(coarse, gt),
                "p2a_nmse": nmse(pred, gt),
                "ref3_psnr": psnr(coarse, gt),
                "p2a_psnr": psnr(pred, gt),
                "ref3_ssim": ssim_global(coarse, gt),
                "p2a_ssim": ssim_global(pred, gt),
            }
            sample_rows.append(payload)
            family_group.setdefault(row["family"], []).append(payload)
    overall = {
        "num_test_samples": len(rows),
        "ref3_nmse_mean": float(np.mean([row["ref3_nmse"] for row in sample_rows])),
        "p2a_nmse_mean": float(np.mean([row["p2a_nmse"] for row in sample_rows])),
        "nmse_gain_vs_ref3": float(np.mean([row["ref3_nmse"] - row["p2a_nmse"] for row in sample_rows])),
        "avg_inference_time_sec": float(total_time / max(len(rows), 1)),
    }
    family_metrics = {}
    for family, values in family_group.items():
        family_metrics[family] = {
            "count": len(values),
            "baseline_nmse_mean": float(np.mean([row["ref3_nmse"] for row in values])),
            "p2a_nmse_mean": float(np.mean([row["p2a_nmse"] for row in values])),
            "nmse_gain": float(np.mean([row["ref3_nmse"] - row["p2a_nmse"] for row in values])),
        }
    return overall, sample_rows, failure_counts, family_metrics


def train_pc_p2a(
    output_root: Path,
    source_root: Path,
    p1_root: Path,
    epochs: int,
    batch_size: int,
    lr: float,
    lambda_pc: float,
    subset_cfg: EchoSubsetConfig,
    geo_cfg: GeometryAwareConfig,
) -> dict[str, Any]:
    source_manifest = read_json(source_root / "learning_handoff_manifest_main_800_100_100.json")
    shutil.copyfile(source_root / "learning_handoff_manifest_main_800_100_100.json", output_root / "learning_handoff_manifest_main_800_100_100.json")
    shutil.copyfile(source_root / "learning_handoff_manifest_main_800_100_100.json", output_root / "learning_handoff_manifest_full.json")
    shutil.copyfile(source_root / "dataset_protocol_snapshot.md", output_root / "dataset_protocol_snapshot.md")
    shutil.copyfile(source_root / "data_origin_statement.md", output_root / "data_origin_statement.md")

    train_rows = [row for row in source_manifest["samples"] if row["split"] == "train"]
    val_rows = [row for row in source_manifest["samples"] if row["split"] == "val"]
    test_rows = [row for row in source_manifest["samples"] if row["split"] == "test"]
    train_loader = DataLoader(PCDataset(train_rows, source_root), batch_size=batch_size, shuffle=True, collate_fn=_collate)
    val_loader = DataLoader(PCDataset(val_rows, source_root), batch_size=batch_size, shuffle=False, collate_fn=_collate)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = UNet3DSmall(base_channels=8).to(device)
    p1_ckpt = torch.load(p1_root / "checkpoints" / "pc_p1" / "best.pt", map_location=device)
    model.load_state_dict(p1_ckpt["model_state"])
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    ckpt_dir = ensure_dir(output_root / "checkpoints" / "pc_p2a")
    best_path = ckpt_dir / "best.pt"

    history = {
        "train_total": [],
        "train_image": [],
        "train_geo": [],
        "train_weight": [],
        "val_total": [],
        "val_image": [],
        "val_geo": [],
        "val_weight": [],
    }
    best_val = float("inf")
    for _epoch in range(epochs):
        train_stats = _run_epoch(model, train_loader, device, optimizer, subset_cfg, geo_cfg, lambda_pc)
        val_stats = _run_epoch(model, val_loader, device, None, subset_cfg, geo_cfg, lambda_pc)
        history["train_total"].append(train_stats["total_loss"])
        history["train_image"].append(train_stats["image_loss"])
        history["train_geo"].append(train_stats["geo_loss"])
        history["train_weight"].append(train_stats["measurement_weight_mean"])
        history["val_total"].append(val_stats["total_loss"])
        history["val_image"].append(val_stats["image_loss"])
        history["val_geo"].append(val_stats["geo_loss"])
        history["val_weight"].append(val_stats["measurement_weight_mean"])
        if val_stats["total_loss"] < best_val:
            best_val = val_stats["total_loss"]
            torch.save({"model_state": model.state_dict()}, best_path)

    model.load_state_dict(torch.load(best_path, map_location=device)["model_state"])
    overall, sample_rows, failure_counts, family_metrics = _evaluate(model, test_rows, source_root, output_root, device)
    payload = {
        "training_config": {
            "epochs": epochs,
            "batch_size": batch_size,
            "lr": lr,
            "lambda_pc": lambda_pc,
            "device": str(device),
            "source_checkpoint_p1": str(p1_root / "checkpoints" / "pc_p1" / "best.pt"),
            "subset_config": summarize_config(subset_cfg, lambda_pc),
            "geometry_config": summarize_geometry_config(geo_cfg),
        },
        "history": history,
        "overall": overall,
        "family_metrics": family_metrics,
        "failure_counts": failure_counts,
        "best_checkpoint": str(best_path.relative_to(output_root)),
    }
    write_json(output_root / "metrics_pc_p2a.json", payload)
    write_json(output_root / "predictions" / "pc_p2a_sample_metrics.json", sample_rows)
    config_lines = [
        "mode: Ours-PC-P2A",
        f"epochs: {epochs}",
        f"batch_size: {batch_size}",
        f"lr: {lr}",
        f"lambda_pc: {lambda_pc}",
        f"active_cells_per_sample: {subset_cfg.active_cells_per_sample}",
        f"frequencies_per_cell: {subset_cfg.frequencies_per_cell}",
        f"fixed_subset: {subset_cfg.fixed_subset}",
        f"subset_seed: {subset_cfg.subset_seed}",
        f"support_threshold_ratio: {geo_cfg.support_threshold_ratio}",
        f"dilation_radius: {geo_cfg.dilation_radius}",
        f"support_weight: {geo_cfg.support_weight}",
        f"boundary_weight: {geo_cfg.boundary_weight}",
        f"use_boundary: {str(geo_cfg.use_boundary).lower()}",
        "mask_mode: dynamic_prediction_support",
    ]
    write_text(output_root / "consistency_config_P2A.yaml", "\n".join(config_lines) + "\n")
    fig, ax = plt.subplots(figsize=(8.4, 4.6))
    ax.plot(history["train_total"], label="train_total")
    ax.plot(history["val_total"], label="val_total")
    ax.plot(history["train_geo"], label="train_geo")
    ax.plot(history["val_geo"], label="val_geo")
    ax.plot(history["val_weight"], label="val_weight")
    ax.set_title("PC-P2A training curves")
    ax.legend()
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(ensure_dir(output_root / "viz" / "progress" / "curves") / "pc_p2a_training_curves.png", dpi=170)
    plt.close(fig)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Train geometry-aware physics-consistency P2A model.")
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--p1-root", required=True)
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--lambda-pc", type=float, default=0.06)
    parser.add_argument("--active-cells", type=int, default=12)
    parser.add_argument("--freq-count", type=int, default=24)
    parser.add_argument("--support-threshold-ratio", type=float, default=0.18)
    parser.add_argument("--dilation-radius", type=int, default=1)
    parser.add_argument("--support-weight", type=float, default=2.0)
    parser.add_argument("--boundary-weight", type=float, default=1.35)
    args = parser.parse_args()
    payload = train_pc_p2a(
        output_root=Path(args.output_root),
        source_root=Path(args.source_root),
        p1_root=Path(args.p1_root),
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        lambda_pc=args.lambda_pc,
        subset_cfg=EchoSubsetConfig(active_cells_per_sample=args.active_cells, frequencies_per_cell=args.freq_count),
        geo_cfg=GeometryAwareConfig(
            support_threshold_ratio=args.support_threshold_ratio,
            support_weight=args.support_weight,
            boundary_weight=args.boundary_weight,
            dilation_radius=args.dilation_radius,
            use_boundary=False,
        ),
    )
    print(
        f"Finished pc_p2a learned_nmse={payload['overall']['p2a_nmse_mean']:.6f} "
        f"gain={payload['overall']['nmse_gain_vs_ref3']:.6f}"
    )


if __name__ == "__main__":
    main()
