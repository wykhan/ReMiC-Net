from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

from workspace.common.io_utils import ensure_dir, read_json, write_json
from workspace.models.unet3d_small import UNet3DSmall
from workspace.recon.reference_recon import reconstruct_from_scene_path


class PointReconDataset(Dataset):
    def __init__(self, output_root: Path, split: str, limit: int) -> None:
        index = read_json(output_root / "dataset" / "index.json")
        selected = [item for item in index if item["split"] == split][:limit]
        self.samples = []
        cache_dir = ensure_dir(output_root / "learning_cache")
        for item in selected:
            result = reconstruct_from_scene_path(output_root / item["scene_path"], method="ref3", output_dir=cache_dir)
            volume = _fit_to_shape(result["volume"], target_shape=(24, 24, 24))
            gt_volume = _fit_to_shape(result["gt_volume"], target_shape=(24, 24, 24))
            self.samples.append(
                (
                    volume[None, ...].astype(np.float32),
                    gt_volume[None, ...].astype(np.float32),
                    item["sample_id"],
                )
            )

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor, str]:
        x, y, sample_id = self.samples[index]
        return torch.from_numpy(x), torch.from_numpy(y), sample_id


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


def _save_training_visual(output_dir: Path, sample_id: str, pred: np.ndarray, target: np.ndarray, baseline: np.ndarray) -> None:
    pred_mip = pred.max(axis=2)
    target_mip = target.max(axis=2)
    baseline_mip = baseline.max(axis=2)
    fig, axes = plt.subplots(1, 3, figsize=(10, 3.5))
    axes[0].imshow(baseline_mip, cmap="viridis")
    axes[0].set_title("ref3")
    axes[1].imshow(pred_mip, cmap="viridis")
    axes[1].set_title("UNet pred")
    axes[2].imshow(target_mip, cmap="viridis")
    axes[2].set_title("GT")
    for ax in axes:
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(output_dir / f"{sample_id}_learning_smoke.png", dpi=160)
    plt.close(fig)


def train_smoke(output_root: Path, train_limit: int, val_limit: int, epochs: int) -> dict:
    train_ds = PointReconDataset(output_root, split="train", limit=train_limit)
    val_ds = PointReconDataset(output_root, split="val", limit=val_limit)
    train_loader = DataLoader(train_ds, batch_size=2, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=2, shuffle=False)

    model = UNet3DSmall()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    criterion = nn.MSELoss()

    train_losses: list[float] = []
    val_losses: list[float] = []

    for _epoch in range(epochs):
        model.train()
        epoch_train: list[float] = []
        for inputs, targets, _sample_ids in train_loader:
            optimizer.zero_grad()
            preds = model(inputs)
            loss = criterion(preds, targets)
            loss.backward()
            optimizer.step()
            epoch_train.append(float(loss.item()))
        train_losses.append(float(np.mean(epoch_train)))

        model.eval()
        epoch_val: list[float] = []
        with torch.no_grad():
            for inputs, targets, _sample_ids in val_loader:
                preds = model(inputs)
                epoch_val.append(float(criterion(preds, targets).item()))
        val_losses.append(float(np.mean(epoch_val)))

    model.eval()
    visual_dir = ensure_dir(output_root / "sample_visuals")
    with torch.no_grad():
        baseline, target, sample_id = val_ds[0]
        pred = model(baseline.unsqueeze(0)).squeeze(0).numpy()[0]
        baseline_np = baseline.numpy()[0]
        target_np = target.numpy()[0]
        _save_training_visual(visual_dir, sample_id, pred, target_np, baseline_np)

    metrics = {
        "train_losses": train_losses,
        "val_losses": val_losses,
        "final_train_loss": train_losses[-1],
        "final_val_loss": val_losses[-1],
        "val_sample_id": sample_id,
    }
    write_json(output_root / "point_learning_smoke_metrics.json", metrics)
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the minimal ref3 -> 3D U-Net smoke model.")
    parser.add_argument("--output-root", required=True, help="Task artifact root.")
    parser.add_argument("--train-limit", type=int, default=8)
    parser.add_argument("--val-limit", type=int, default=4)
    parser.add_argument("--epochs", type=int, default=3)
    args = parser.parse_args()
    metrics = train_smoke(Path(args.output_root), args.train_limit, args.val_limit, args.epochs)
    print(f"Smoke training done final_val_loss={metrics['final_val_loss']:.6f}")


if __name__ == "__main__":
    main()
