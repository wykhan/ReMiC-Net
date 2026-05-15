from __future__ import annotations

import argparse
import csv
import json
import platform
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn.functional as F
from torch import nn
from torch.utils.data import DataLoader, Dataset

from workspace.common.io_utils import ensure_dir, read_json, write_json, write_text
from workspace.common.remic_metadata import (
    EPSILON_M,
    FC_HZ,
    K2W_C_RAD_PER_M,
    LAMBDA_C_M,
    REF3_RADII_M,
    build_remic_metadata,
    write_metadata_npz,
)
from workspace.eval.metrics_3d import nmse, psnr, ssim_global
from workspace.eval.task_real_008_pipeline import _fit_to_shape, _normalize_pair


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_006D = PROJECT_ROOT / "exp" / "task_real_006d_800_formal" / "20260419_112717"
TARGET_SHAPE = (24, 24, 24)
SEED = 0
SHELL_BOUNDARIES_M = [0.075, 0.225]
SHELL_BOUNDARY_BAND_M = 0.010


@dataclass(frozen=True)
class VariantSpec:
    key: str
    description: str
    kind: str
    input_channels: int
    geom_channels: int = 5


VARIANTS = [
    VariantSpec("S01_ref3", "No learning: ref3 physical reconstruction directly.", "ref3", 1),
    VariantSpec("S02_plain_residual_unet", "Residual 3D U-Net with X_ref3 only.", "concat_unet", 1),
    VariantSpec("S03_concat_Mshell", "Residual 3D U-Net with [X_ref3, Mshell].", "concat_unet", 4),
    VariantSpec("S04_concat_Mshell_delta", "Residual 3D U-Net with [X_ref3, Mshell, delta_rho].", "concat_unet", 5),
    VariantSpec("S05_concat_Mshell_delta_Pcyc", "Residual 3D U-Net with [X_ref3, Mshell, delta_rho, Pcyc].", "concat_unet", 6),
    VariantSpec("S06_geometry_branch_bottleneck_concat", "Image branch plus geometry branch with bottleneck concat.", "bottleneck_concat", 1),
    VariantSpec("S07_generic_film_middeep", "Geometry branch plus generic FiLM at available mid/deep stages.", "generic_film", 1),
    VariantSpec("S08_rsbfilm_middeep_default", "Geometry branch plus RSB-FiLM envelope and bounded gamma/beta.", "rsb_film", 1),
]


class ConvBlock3d(nn.Module):
    def __init__(self, in_channels: int, out_channels: int) -> None:
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv3d(in_channels, out_channels, 3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv3d(out_channels, out_channels, 3, padding=1),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.block(x)


class ResidualUNet(nn.Module):
    def __init__(self, in_channels: int, base_channels: int = 4) -> None:
        super().__init__()
        b = base_channels
        self.enc1 = ConvBlock3d(in_channels, b)
        self.pool1 = nn.MaxPool3d(2)
        self.enc2 = ConvBlock3d(b, b * 2)
        self.pool2 = nn.MaxPool3d(2)
        self.bottleneck = ConvBlock3d(b * 2, b * 4)
        self.up2 = nn.ConvTranspose3d(b * 4, b * 2, 2, stride=2)
        self.dec2 = ConvBlock3d(b * 4, b * 2)
        self.up1 = nn.ConvTranspose3d(b * 2, b, 2, stride=2)
        self.dec1 = ConvBlock3d(b * 2, b)
        self.head = nn.Conv3d(b, 1, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        e1 = self.enc1(x)
        e2 = self.enc2(self.pool1(e1))
        b = self.bottleneck(self.pool2(e2))
        d2 = self.dec2(torch.cat([self.up2(b), e2], dim=1))
        d1 = self.dec1(torch.cat([self.up1(d2), e1], dim=1))
        return self.head(d1)


class GeometryEncoder(nn.Module):
    def __init__(self, geom_channels: int = 5, base_channels: int = 4) -> None:
        super().__init__()
        b = base_channels
        self.g1 = ConvBlock3d(geom_channels, b)
        self.pool1 = nn.AvgPool3d(2)
        self.g2 = ConvBlock3d(b, b * 2)
        self.pool2 = nn.AvgPool3d(2)
        self.gb = ConvBlock3d(b * 2, b * 4)

    def forward(self, g: torch.Tensor) -> dict[str, torch.Tensor]:
        g1 = self.g1(g)
        g2 = self.g2(self.pool1(g1))
        gb = self.gb(self.pool2(g2))
        return {"g1": g1, "g2": g2, "gb": gb}


class BottleneckConcatNet(nn.Module):
    def __init__(self, geom_channels: int = 5, base_channels: int = 4) -> None:
        super().__init__()
        b = base_channels
        self.img_e1 = ConvBlock3d(1, b)
        self.pool1 = nn.MaxPool3d(2)
        self.img_e2 = ConvBlock3d(b, b * 2)
        self.pool2 = nn.MaxPool3d(2)
        self.img_b = ConvBlock3d(b * 2, b * 4)
        self.geom = GeometryEncoder(geom_channels, b)
        self.fuse = ConvBlock3d(b * 8, b * 4)
        self.up2 = nn.ConvTranspose3d(b * 4, b * 2, 2, stride=2)
        self.dec2 = ConvBlock3d(b * 4, b * 2)
        self.up1 = nn.ConvTranspose3d(b * 2, b, 2, stride=2)
        self.dec1 = ConvBlock3d(b * 2, b)
        self.head = nn.Conv3d(b, 1, 1)

    def forward(self, x: torch.Tensor, geom: torch.Tensor, m_rsb: torch.Tensor | None = None) -> torch.Tensor:
        e1 = self.img_e1(x)
        e2 = self.img_e2(self.pool1(e1))
        ib = self.img_b(self.pool2(e2))
        gb = self.geom(geom)["gb"]
        b = self.fuse(torch.cat([ib, gb], dim=1))
        d2 = self.dec2(torch.cat([self.up2(b), e2], dim=1))
        d1 = self.dec1(torch.cat([self.up1(d2), e1], dim=1))
        return self.head(d1)


class FilmLayer(nn.Module):
    def __init__(self, feat_channels: int, geom_channels: int, alpha_gamma: float = 0.5, alpha_beta: float = 0.1, use_rsb: bool = False) -> None:
        super().__init__()
        self.alpha_gamma = alpha_gamma
        self.alpha_beta = alpha_beta
        self.use_rsb = use_rsb
        self.gamma = nn.Conv3d(geom_channels, feat_channels, 1)
        self.beta = nn.Conv3d(geom_channels, feat_channels, 1)
        nn.init.zeros_(self.gamma.weight)
        nn.init.zeros_(self.gamma.bias)
        nn.init.zeros_(self.beta.weight)
        nn.init.zeros_(self.beta.bias)

    def forward(self, feat: torch.Tensor, geom_feat: torch.Tensor, m_rsb: torch.Tensor) -> torch.Tensor:
        if geom_feat.shape[-3:] != feat.shape[-3:]:
            geom_feat = F.interpolate(geom_feat, size=feat.shape[-3:], mode="trilinear", align_corners=False)
        env = 1.0
        if self.use_rsb:
            if m_rsb.shape[-3:] != feat.shape[-3:]:
                m_rsb = F.interpolate(m_rsb, size=feat.shape[-3:], mode="trilinear", align_corners=False)
            env = m_rsb
        gamma = env * self.alpha_gamma * torch.tanh(self.gamma(geom_feat))
        beta = env * self.alpha_beta * torch.tanh(self.beta(geom_feat))
        return (1.0 + gamma) * feat + beta


class FilmUNet(nn.Module):
    def __init__(self, geom_channels: int = 5, base_channels: int = 4, use_rsb: bool = False) -> None:
        super().__init__()
        b = base_channels
        self.img_e1 = ConvBlock3d(1, b)
        self.pool1 = nn.MaxPool3d(2)
        self.img_e2 = ConvBlock3d(b, b * 2)
        self.pool2 = nn.MaxPool3d(2)
        self.img_b = ConvBlock3d(b * 2, b * 4)
        self.geom = GeometryEncoder(geom_channels, b)
        self.film_e2 = FilmLayer(b * 2, b * 2, use_rsb=use_rsb)
        self.film_b = FilmLayer(b * 4, b * 4, use_rsb=use_rsb)
        self.film_d2 = FilmLayer(b * 2, b * 2, use_rsb=use_rsb)
        self.up2 = nn.ConvTranspose3d(b * 4, b * 2, 2, stride=2)
        self.dec2 = ConvBlock3d(b * 4, b * 2)
        self.up1 = nn.ConvTranspose3d(b * 2, b, 2, stride=2)
        self.dec1 = ConvBlock3d(b * 2, b)
        self.head = nn.Conv3d(b, 1, 1)

    def forward(self, x: torch.Tensor, geom: torch.Tensor, m_rsb: torch.Tensor) -> torch.Tensor:
        gf = self.geom(geom)
        e1 = self.img_e1(x)
        e2 = self.img_e2(self.pool1(e1))
        e2 = self.film_e2(e2, gf["g2"], m_rsb)
        b = self.img_b(self.pool2(e2))
        b = self.film_b(b, gf["gb"], m_rsb)
        d2 = self.dec2(torch.cat([self.up2(b), e2], dim=1))
        d2 = self.film_d2(d2, gf["g2"], m_rsb)
        d1 = self.dec1(torch.cat([self.up1(d2), e1], dim=1))
        return self.head(d1)


class StrucDataset(Dataset):
    def __init__(self, rows: list[dict[str, Any]], source_root: Path, output_root: Path) -> None:
        self.rows = rows
        self.source_root = source_root
        self.output_root = output_root

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, idx: int) -> dict[str, Any]:
        row = self.rows[idx]
        ref3_npz = np.load(self.source_root / row["ref3_path"])
        gt_npz = np.load(self.source_root / row["gt_path"])
        ref3, gt, _ = _normalize_pair(_fit_to_shape(ref3_npz["volume"]), _fit_to_shape(gt_npz["volume"]))
        meta = np.load(self.output_root / row["metadata_rel_path"])
        geom = np.concatenate([meta["mshell"], meta["delta_rho_raw"], meta["pcyc"]], axis=0).astype(np.float32)
        return {
            "x": torch.from_numpy(ref3[None].astype(np.float32)),
            "gt": torch.from_numpy(gt[None].astype(np.float32)),
            "residual": torch.from_numpy((gt - ref3)[None].astype(np.float32)),
            "mshell": torch.from_numpy(meta["mshell"].astype(np.float32)),
            "delta": torch.from_numpy(meta["delta_rho_raw"].astype(np.float32)),
            "pcyc": torch.from_numpy(meta["pcyc"].astype(np.float32)),
            "geom": torch.from_numpy(geom),
            "m_rsb": torch.from_numpy(meta["m_rsb"].astype(np.float32)),
            "rho": torch.from_numpy(meta["rho"].astype(np.float32)),
            "sample_id": row["sample_id"],
            "family": row["family"],
        }


def collate(batch: list[dict[str, Any]]) -> dict[str, Any]:
    keys = ["x", "gt", "residual", "mshell", "delta", "pcyc", "geom", "m_rsb", "rho"]
    out = {key: torch.stack([item[key] for item in batch], dim=0) for key in keys}
    out["sample_id"] = [item["sample_id"] for item in batch]
    out["family"] = [item["family"] for item in batch]
    return out


def stable_subset(rows: list[dict[str, Any]], split: str, limit: int) -> list[dict[str, Any]]:
    bucket = [row for row in rows if row["split"] == split]
    by_family: dict[str, list[dict[str, Any]]] = {}
    for row in bucket:
        by_family.setdefault(row["family"], []).append(row)
    selected = []
    families = sorted(by_family)
    while len(selected) < min(limit, len(bucket)):
        progressed = False
        for family in families:
            idx = sum(1 for row in selected if row["family"] == family)
            if idx < len(by_family[family]):
                selected.append(by_family[family][idx])
                progressed = True
                if len(selected) >= limit:
                    break
        if not progressed:
            break
    return selected


def prepare_rows(output_root: Path, train_limit: int, val_limit: int, test_limit: int) -> list[dict[str, Any]]:
    manifest = read_json(SOURCE_006D / "learning_handoff_manifest_main_800_100_100.json")
    chosen = (
        stable_subset(manifest["samples"], "train", train_limit)
        + stable_subset(manifest["samples"], "val", val_limit)
        + stable_subset(manifest["samples"], "test", test_limit)
    )
    rows = []
    for row in chosen:
        ref3_npz = np.load(SOURCE_006D / row["ref3_path"])
        meta = build_remic_metadata(ref3_npz["x_values"], ref3_npz["y_values"], ref3_npz["z_values"], TARGET_SHAPE)
        rel = Path("metadata_cache") / f"{row['sample_id']}_remic_meta.npz"
        write_metadata_npz(output_root / rel, meta)
        rows.append({**row, "metadata_rel_path": str(rel)})
    write_json(
        output_root / "dataset_subset_manifest.json",
        {
            "source_manifest": str(SOURCE_006D / "learning_handoff_manifest_main_800_100_100.json"),
            "selection": {"train_limit": train_limit, "val_limit": val_limit, "test_limit": test_limit, "seed": SEED},
            "rows": rows,
            "full_split_counts": {split: sum(1 for row in manifest["samples"] if row["split"] == split) for split in ["train", "val", "test"]},
            "first_pass_diagnostic": True,
        },
    )
    return rows


def model_for(spec: VariantSpec, base_channels: int) -> nn.Module | None:
    if spec.kind == "ref3":
        return None
    if spec.kind == "concat_unet":
        return ResidualUNet(spec.input_channels, base_channels)
    if spec.kind == "bottleneck_concat":
        return BottleneckConcatNet(spec.geom_channels, base_channels)
    if spec.kind == "generic_film":
        return FilmUNet(spec.geom_channels, base_channels, use_rsb=False)
    if spec.kind == "rsb_film":
        return FilmUNet(spec.geom_channels, base_channels, use_rsb=True)
    raise ValueError(spec.kind)


def input_for_variant(batch: dict[str, Any], spec: VariantSpec, device: torch.device) -> torch.Tensor:
    if spec.key == "S02_plain_residual_unet":
        return batch["x"].to(device)
    if spec.key == "S03_concat_Mshell":
        return torch.cat([batch["x"], batch["mshell"]], dim=1).to(device)
    if spec.key == "S04_concat_Mshell_delta":
        return torch.cat([batch["x"], batch["mshell"], batch["delta"]], dim=1).to(device)
    if spec.key == "S05_concat_Mshell_delta_Pcyc":
        return torch.cat([batch["x"], batch["mshell"], batch["delta"], batch["pcyc"]], dim=1).to(device)
    return batch["x"].to(device)


def forward_variant(model: nn.Module, batch: dict[str, Any], spec: VariantSpec, device: torch.device) -> torch.Tensor:
    if spec.kind == "concat_unet":
        return model(input_for_variant(batch, spec, device))
    return model(batch["x"].to(device), batch["geom"].to(device), batch["m_rsb"].to(device))


def count_parameters(model: nn.Module | None) -> int:
    if model is None:
        return 0
    return int(sum(p.numel() for p in model.parameters() if p.requires_grad))


def train_variant(
    output_root: Path,
    spec: VariantSpec,
    rows: list[dict[str, Any]],
    epochs: int,
    batch_size: int,
    lr: float,
    weight_decay: float,
    base_channels: int,
) -> dict[str, Any]:
    if spec.kind == "ref3":
        return {"variant": spec.key, "executed": True, "training": "not_applicable"}
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model_for(spec, base_channels).to(device)  # type: ignore[union-attr]
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    train_loader = DataLoader(StrucDataset([r for r in rows if r["split"] == "train"], SOURCE_006D, output_root), batch_size=batch_size, shuffle=True, collate_fn=collate)
    val_loader = DataLoader(StrucDataset([r for r in rows if r["split"] == "val"], SOURCE_006D, output_root), batch_size=batch_size, shuffle=False, collate_fn=collate)
    history = []
    best_val = float("inf")
    best_state = None
    for epoch in range(1, epochs + 1):
        model.train()
        train_losses = []
        for batch in train_loader:
            pred = forward_variant(model, batch, spec, device)
            loss = F.l1_loss(pred, batch["residual"].to(device))
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            train_losses.append(float(loss.detach().cpu()))
        model.eval()
        val_losses = []
        with torch.no_grad():
            for batch in val_loader:
                pred = forward_variant(model, batch, spec, device)
                val_losses.append(float(F.l1_loss(pred, batch["residual"].to(device)).detach().cpu()))
        row = {"epoch": epoch, "train_l1": float(np.mean(train_losses)), "val_l1": float(np.mean(val_losses))}
        history.append(row)
        if row["val_l1"] < best_val:
            best_val = row["val_l1"]
            best_state = {k: v.detach().cpu() for k, v in model.state_dict().items()}
    ckpt_dir = ensure_dir(output_root / "checkpoints")
    torch.save({"model_state": best_state, "spec": spec.__dict__, "history": history}, ckpt_dir / f"{spec.key}.pt")
    write_csv(output_root / "training_curves" / f"{spec.key}.csv", history)
    plot_curve(output_root / "training_curves" / f"{spec.key}.png", history, spec.key)
    return {"variant": spec.key, "executed": True, "best_val_l1": best_val, "history": history, "parameter_count": count_parameters(model)}


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    ensure_dir(path.parent)
    if fieldnames is None:
        if rows:
            seen: list[str] = []
            for row in rows:
                for key in row.keys():
                    if key not in seen:
                        seen.append(key)
            fieldnames = seen
        else:
            fieldnames = ["status"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        if rows:
            writer.writerows(rows)


def plot_curve(path: Path, history: list[dict[str, Any]], title: str) -> None:
    fig, ax = plt.subplots(figsize=(5.5, 3.6))
    ax.plot([r["epoch"] for r in history], [r["train_l1"] for r in history], label="train")
    ax.plot([r["epoch"] for r in history], [r["val_l1"] for r in history], label="val")
    ax.set_xlabel("epoch")
    ax.set_ylabel("residual L1")
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def load_trained(output_root: Path, spec: VariantSpec, base_channels: int, device: torch.device) -> nn.Module | None:
    model = model_for(spec, base_channels)
    if model is None:
        return None
    ckpt = torch.load(output_root / "checkpoints" / f"{spec.key}.pt", map_location=device)
    model.load_state_dict(ckpt["model_state"])
    model.to(device)
    model.eval()
    return model


def masked_nmse(pred: np.ndarray, gt: np.ndarray, mask: np.ndarray) -> float:
    if not np.any(mask):
        return float("nan")
    num = float(np.sum((pred[mask] - gt[mask]) ** 2))
    den = max(float(np.sum(gt[mask] ** 2)), 1.0e-12)
    return num / den


def masked_mae(pred: np.ndarray, gt: np.ndarray, mask: np.ndarray) -> float:
    if not np.any(mask):
        return float("nan")
    return float(np.mean(np.abs(pred[mask] - gt[mask])))


def masked_ssim(pred: np.ndarray, gt: np.ndarray, mask: np.ndarray) -> float:
    if not np.any(mask):
        return float("nan")
    return ssim_global(np.where(mask, pred, 0.0), np.where(mask, gt, 0.0))


def region_metric(pred: np.ndarray, gt: np.ndarray, mask: np.ndarray) -> dict[str, float]:
    return {"nmse": masked_nmse(pred, gt, mask), "ssim": masked_ssim(pred, gt, mask), "mae": masked_mae(pred, gt, mask)}


def bin_masks(values: np.ndarray, support: np.ndarray) -> list[tuple[str, np.ndarray]]:
    vals = np.abs(values[support])
    if vals.size == 0:
        return []
    q1, q2 = np.quantile(vals, [1 / 3, 2 / 3])
    return [
        ("small", support & (np.abs(values) <= q1)),
        ("medium", support & (np.abs(values) > q1) & (np.abs(values) <= q2)),
        ("large", support & (np.abs(values) > q2)),
    ]


def load_bp_runtime_mean() -> float | None:
    path = SOURCE_006D / "mainline_vs_baselines_metrics.json"
    if not path.exists():
        return None
    rows = read_json(path).get("per_sample", [])
    vals = [float(row["wall_time_sec"]) for row in rows if row.get("method") == "BP"]
    return float(np.mean(vals)) if vals else None


def evaluate(output_root: Path, rows: list[dict[str, Any]], base_channels: int) -> dict[str, Any]:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    test_rows = [r for r in rows if r["split"] == "test"]
    loader = DataLoader(StrucDataset(test_rows, SOURCE_006D, output_root), batch_size=1, shuffle=False, collate_fn=collate)
    models = {spec.key: load_trained(output_root, spec, base_channels, device) for spec in VARIANTS}
    bp_runtime = load_bp_runtime_mean()
    per_sample = []
    predictions: dict[str, dict[str, np.ndarray]] = {}
    runtime_rows = []
    with torch.no_grad():
        for batch in loader:
            sample_id = batch["sample_id"][0]
            family = batch["family"][0]
            gt = batch["gt"].numpy()[0, 0]
            ref3 = batch["x"].numpy()[0, 0]
            meta = {
                "delta": batch["delta"].numpy()[0, 0],
                "pcyc": batch["pcyc"].numpy()[0, 0],
                "rho": batch["rho"].numpy()[0, 0],
            }
            predictions[sample_id] = {"GT": gt, "ref3": ref3}
            for spec in VARIANTS:
                if spec.kind == "ref3":
                    pred = ref3
                    rt = 0.0
                else:
                    model = models[spec.key]
                    t0 = time.perf_counter()
                    delta = forward_variant(model, batch, spec, device)  # type: ignore[arg-type]
                    rt = time.perf_counter() - t0
                    pred = torch.clamp(batch["x"].to(device) + delta, min=0.0).cpu().numpy()[0, 0]
                per_sample.append(
                    {
                        "variant": spec.key,
                        "sample_id": sample_id,
                        "family": family,
                        "nmse": nmse(pred, gt),
                        "psnr": psnr(pred, gt),
                        "ssim": ssim_global(pred, gt),
                        "runtime_per_sample": rt,
                    }
                )
                if spec.kind != "ref3":
                    predictions[sample_id][spec.key] = pred.astype(np.float32)
            np.savez_compressed(output_root / "prediction_cache" / f"{sample_id}_predictions.npz", **predictions[sample_id], delta=meta["delta"], pcyc=meta["pcyc"], rho=meta["rho"])
    overall = summarize_overall(per_sample, bp_runtime)
    write_csv(output_root / "metrics_overall.csv", overall)
    write_csv(output_root / "per_sample_metrics.csv", per_sample)
    runtime_rows = [
        {
            "variant": row["variant"],
            "runtime_per_sample_mean": row["runtime_per_sample"],
            "speedup_vs_BP": row.get("speedup_vs_BP", ""),
            "peak_GPU_memory": row.get("peak_GPU_memory", ""),
        }
        for row in overall
    ]
    write_csv(output_root / "runtime_table.csv", runtime_rows)
    diagnostic_tables(output_root, rows, per_sample, test_rows)
    render_representatives(output_root, per_sample)
    render_diagnostic_plots(output_root, overall)
    return {"overall": overall, "per_sample": per_sample}


def summarize_overall(per_sample: list[dict[str, Any]], bp_runtime: float | None) -> list[dict[str, Any]]:
    rows = []
    peak_memory = f"{torch.cuda.max_memory_allocated() / (1024.0 * 1024.0):.2f} MB" if torch.cuda.is_available() else "not_available_cpu"
    for spec in VARIANTS:
        bucket = [r for r in per_sample if r["variant"] == spec.key]
        rt = float(np.mean([r["runtime_per_sample"] for r in bucket])) if bucket else 0.0
        rows.append(
            {
                "variant": spec.key,
                "description": spec.description,
                "NMSE": float(np.mean([r["nmse"] for r in bucket])) if bucket else float("nan"),
                "PSNR": float(np.mean([r["psnr"] for r in bucket])) if bucket else float("nan"),
                "SSIM": float(np.mean([r["ssim"] for r in bucket])) if bucket else float("nan"),
                "runtime_per_sample": rt,
                "speedup_vs_BP": float(bp_runtime / rt) if bp_runtime and rt > 0 else ("not_applicable" if spec.kind == "ref3" else "BP_runtime_unavailable"),
                "peak_GPU_memory": peak_memory,
                "num_test_samples": len(bucket),
            }
        )
    return rows


def diagnostic_tables(output_root: Path, rows: list[dict[str, Any]], per_sample: list[dict[str, Any]], test_rows: list[dict[str, Any]]) -> None:
    delta_rows = []
    pcyc_rows = []
    shell_rows = []
    family_rows = []
    detailed = {r["sample_id"]: r for r in test_rows}
    for row in test_rows:
        pred_npz = np.load(output_root / "prediction_cache" / f"{row['sample_id']}_predictions.npz")
        gt = pred_npz["GT"]
        support = gt > max(float(gt.max()) * 0.05, 1.0e-6)
        delta = pred_npz["delta"]
        pcyc = pred_npz["pcyc"]
        rho = pred_npz["rho"]
        delta_masks = bin_masks(delta, support)
        pcyc_masks = bin_masks(pcyc, support)
        pcyc_quarter_masks = [("abs_pcyc_le_0p25", support & (np.abs(pcyc) <= 0.25)), ("abs_pcyc_gt_0p25", support & (np.abs(pcyc) > 0.25))]
        shell_mask = support & np.logical_or.reduce([np.abs(rho - b) <= SHELL_BOUNDARY_BAND_M for b in SHELL_BOUNDARIES_M])
        for spec in VARIANTS:
            pred_name = "ref3" if spec.kind == "ref3" else spec.key
            pred = pred_npz[pred_name]
            for label, mask in delta_masks:
                m = region_metric(pred, gt, mask)
                delta_rows.append({"variant": spec.key, "sample_id": row["sample_id"], "bin": label, **m})
            for label, mask in pcyc_masks + pcyc_quarter_masks:
                m = region_metric(pred, gt, mask)
                pcyc_rows.append({"variant": spec.key, "sample_id": row["sample_id"], "bin": label, **m})
            m = region_metric(pred, gt, shell_mask)
            shell_rows.append({"variant": spec.key, "sample_id": row["sample_id"], "boundary_band_m": SHELL_BOUNDARY_BAND_M, **m})
            family_rows.append({"variant": spec.key, "sample_id": row["sample_id"], "family": row["family"], "nmse": nmse(pred, gt), "psnr": psnr(pred, gt), "ssim": ssim_global(pred, gt)})
    write_csv(output_root / "metrics_by_delta_rho.csv", aggregate_region_rows(delta_rows, "bin"))
    write_csv(output_root / "metrics_by_Pcyc.csv", aggregate_region_rows(pcyc_rows, "bin"))
    write_csv(output_root / "metrics_by_shell_boundary.csv", aggregate_region_rows(shell_rows, "boundary_band_m"))
    write_csv(output_root / "metrics_by_family.csv", aggregate_region_rows(family_rows, "family", metric_keys=("nmse", "psnr", "ssim")))
    write_csv(output_root / "region_metrics_raw.csv", delta_rows + pcyc_rows + shell_rows)


def aggregate_region_rows(rows: list[dict[str, Any]], group_key: str, metric_keys: tuple[str, ...] = ("nmse", "ssim", "mae")) -> list[dict[str, Any]]:
    out = []
    for variant in [v.key for v in VARIANTS]:
        for group in sorted({r[group_key] for r in rows if r["variant"] == variant}, key=str):
            bucket = [r for r in rows if r["variant"] == variant and r[group_key] == group]
            item = {"variant": variant, group_key: group, "num_regions": len(bucket)}
            for key in metric_keys:
                vals = [float(r[key]) for r in bucket if not np.isnan(float(r[key]))]
                item[key.upper() if key != "mae" else "MAE"] = float(np.mean(vals)) if vals else float("nan")
            out.append(item)
    return out


def render_representatives(output_root: Path, per_sample: list[dict[str, Any]]) -> None:
    by_s02 = [r for r in per_sample if r["variant"] == "S02_plain_residual_unet"]
    by_s08 = {r["sample_id"]: r for r in per_sample if r["variant"] == "S08_rsbfilm_middeep_default"}
    ranked = []
    for r in by_s02:
        s08 = by_s08[r["sample_id"]]
        ranked.append((r["nmse"] - s08["nmse"], r["sample_id"]))
    ranked.sort()
    chosen = {
        "failure_case": ranked[0][1],
        "median_case": ranked[len(ranked) // 2][1],
        "best_case": ranked[-1][1],
    }
    # hard cases by metadata on saved predictions
    hard_delta = max(chosen.values(), key=lambda sid: float(np.mean(np.abs(np.load(output_root / "prediction_cache" / f"{sid}_predictions.npz")["delta"]))))
    hard_pcyc = max(chosen.values(), key=lambda sid: float(np.mean(np.abs(np.load(output_root / "prediction_cache" / f"{sid}_predictions.npz")["pcyc"]))))
    chosen["hard_large_delta_rho_case"] = hard_delta
    chosen["hard_high_Pcyc_case"] = hard_pcyc
    write_json(output_root / "recon_compare" / "representative_cases.json", chosen)
    for label, sid in chosen.items():
        arr = np.load(output_root / "prediction_cache" / f"{sid}_predictions.npz")
        panels = [
            ("GT", arr["GT"]),
            ("ref3", arr["ref3"]),
            ("S02", arr["S02_plain_residual_unet"]),
            ("S05", arr["S05_concat_Mshell_delta_Pcyc"]),
            ("S07", arr["S07_generic_film_middeep"]),
            ("S08", arr["S08_rsbfilm_middeep_default"]),
        ]
        vmax = max(float(np.max(a)) for _, a in panels)
        z = panels[0][1].shape[2] // 2
        fig, axes = plt.subplots(2, len(panels), figsize=(3.0 * len(panels), 5.5))
        for col, (name, vol) in enumerate(panels):
            axes[0, col].imshow(vol[:, :, z], cmap="viridis", vmin=0.0, vmax=vmax)
            axes[0, col].set_title(name)
            axes[0, col].axis("off")
            err = np.abs(vol - arr["GT"])
            axes[1, col].imshow(err.max(axis=2), cmap="magma")
            axes[1, col].axis("off")
        axes[0, 0].set_ylabel("central z")
        axes[1, 0].set_ylabel("error MIP")
        fig.suptitle(f"{label}: {sid}")
        fig.tight_layout()
        fig.savefig(output_root / "recon_compare" / f"{label}_{sid}.png", dpi=170)
        plt.close(fig)


def render_diagnostic_plots(output_root: Path, overall: list[dict[str, Any]]) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2))
    labels = [row["variant"].replace("_", "\n", 1) for row in overall]
    x = np.arange(len(overall))
    axes[0].bar(x, [float(row["NMSE"]) for row in overall])
    axes[0].set_xticks(x, labels, rotation=40, ha="right", fontsize=7)
    axes[0].set_ylabel("NMSE")
    axes[0].set_title("Overall NMSE")
    axes[1].bar(x, [float(row["SSIM"]) for row in overall])
    axes[1].set_xticks(x, labels, rotation=40, ha="right", fontsize=7)
    axes[1].set_ylabel("SSIM")
    axes[1].set_title("Overall SSIM")
    fig.tight_layout()
    fig.savefig(output_root / "diagnostic_plots" / "overall_structure_diagnosis.png", dpi=170)
    plt.close(fig)


def unavailable_ood(output_root: Path) -> None:
    rows = [
        {"ood_split": "Leave-One-Family-Out OOD", "status": "not_evaluated_in_struc_001_first_pass", "reason": "interface exists in prior task_real_008; S01-S08 OOD evaluation not run in this bounded first-pass diagnosis"},
        {"ood_split": "Random-ET OOD", "status": "not_evaluated_in_struc_001_first_pass", "reason": "interface exists in prior task_real_008; S01-S08 OOD evaluation not run in this bounded first-pass diagnosis"},
        {"ood_split": "Unseen-Parameter OOD", "status": "not_evaluated_in_struc_001_first_pass", "reason": "interface exists in prior task_real_008; S01-S08 OOD evaluation not run in this bounded first-pass diagnosis"},
    ]
    write_csv(output_root / "metrics_ood.csv", rows)


def write_environment(output_root: Path) -> None:
    lines = [
        f"python: {platform.python_version()}",
        f"platform: {platform.platform()}",
        f"torch: {torch.__version__}",
        f"cuda_available: {torch.cuda.is_available()}",
        f"numpy: {np.__version__}",
    ]
    write_text(output_root / "environment.txt", "\n".join(lines) + "\n")
    status = subprocess.run(["git", "status", "--short", "--branch"], cwd=PROJECT_ROOT, text=True, capture_output=True, check=False)
    log = subprocess.run(["git", "log", "--oneline", "-5"], cwd=PROJECT_ROOT, text=True, capture_output=True, check=False)
    write_text(output_root / "git_status.txt", status.stdout + "\n" + log.stdout)


def write_config_files(output_root: Path, args: argparse.Namespace, training: list[dict[str, Any]], param_rows: list[dict[str, Any]]) -> None:
    write_json(
        output_root / "config_summary.json",
        {
            "task": "task_real_struc_001",
            "seed": SEED,
            "source_dataset": str(SOURCE_006D),
            "target_shape": TARGET_SHAPE,
            "ref3_radii_m": [float(x) for x in REF3_RADII_M],
            "metadata": {"Mshell": "3-channel ref3 nearest-surface allocation", "delta_rho": "signed rho-rho_ref_star in meters", "Pcyc": "wrapped 2-way phase mismatch divided by pi"},
            "training": vars(args),
            "first_pass_diagnostic": True,
        },
    )
    write_json(output_root / "model_variants.json", [v.__dict__ for v in VARIANTS])
    write_csv(output_root / "parameter_count_table.csv", param_rows)
    lines = ["# model_config_diffs", ""]
    for v in VARIANTS:
        lines += [f"## {v.key}", "", v.description, ""]
    write_text(output_root / "model_config_diffs.md", "\n".join(lines))
    write_json(output_root / "training_summary.json", training)


def write_debug(output_root: Path) -> None:
    write_text(
        output_root / "debug.md",
        "# debug\n\n- First-pass diagnostic intentionally uses a deterministic subset and one seed to keep S01-S08 comparable and tractable in this run.\n- OOD S01-S08 evaluation was not run; `metrics_ood.csv` records this limitation.\n- Generic FiLM uses bounded tanh gamma/beta without RSB envelope; RSB-FiLM uses the frozen envelope only for feature modulation strength.\n",
    )


def table_md(rows: list[dict[str, Any]], cols: list[str]) -> str:
    out = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for row in rows:
        vals = []
        for c in cols:
            val = row.get(c, "")
            if isinstance(val, float):
                vals.append(f"{val:.5f}")
            else:
                vals.append(str(val))
        out.append("| " + " | ".join(vals) + " |")
    return "\n".join(out)


def write_report(output_root: Path, eval_payload: dict[str, Any], args: argparse.Namespace) -> dict[str, str]:
    overall = eval_payload["overall"]
    lookup = {r["variant"]: r for r in overall}
    def better(a: str, b: str) -> bool:
        return float(lookup[a]["NMSE"]) < float(lookup[b]["NMSE"]) or float(lookup[a]["SSIM"]) > float(lookup[b]["SSIM"])

    s02_s05 = "S05 improves over S02" if better("S05_concat_Mshell_delta_Pcyc", "S02_plain_residual_unet") else "S05 does not improve over S02"
    s05_s07 = "S07 improves over S05" if better("S07_generic_film_middeep", "S05_concat_Mshell_delta_Pcyc") else "S07 does not improve over S05"
    s07_s08 = "S08 improves over S07" if better("S08_rsbfilm_middeep_default", "S07_generic_film_middeep") else "S08 does not improve over S07"
    best = min(overall[1:], key=lambda r: float(r["NMSE"]))
    recommendation = "Audit metadata and run longer/full-split training before tuning RSB-FiLM." if best["variant"] == "S02_plain_residual_unet" else "Continue with the best structured variant and validate on OOD in task_real_struc_002."
    report = f"""# task_real_struc_001_report

## 1. Executive Summary

This is a first-pass, one-seed structure diagnosis on a deterministic subset of the frozen 800/100/100 dataset. All S01-S08 variants were executed under the same residual-learning protocol. The run is diagnostic, not final model tuning.

- S02 vs S05: {s02_s05}
- S05 vs S07: {s05_s07}
- S07 vs S08: {s07_s08}
- Best current candidate by NMSE: `{best['variant']}`

## 2. Repository and Code Inspection

Inspected `CONTEXT/`, `PROMPTS/`, `scripts/`, `exp/`, `doc/`, and `workspace/`. Reused the frozen `ref3` protocol, `workspace/common/remic_metadata.py`, existing 3D residual U-Net patterns, existing ReMiC-Net/RSB-FiLM concepts, and frozen 006d learning handoff data. The previous task_real_008 implementation compared only baseline U-Net and one ReMiC-Net; this task adds S01-S08 structural ablations.

## 3. Dataset and Split Description

Source manifest: `{SOURCE_006D / 'learning_handoff_manifest_main_800_100_100.json'}`. Full split is 800 train / 100 val / 100 test; this run used `{args.train_limit}` train, `{args.val_limit}` val, `{args.test_limit}` test samples selected deterministically and stratified by family. OOD interfaces exist in prior scripts, but S01-S08 OOD evaluation was not run in this bounded first-pass diagnosis.

## 4. Model Variants

{table_md([v.__dict__ for v in VARIANTS], ['key', 'kind', 'description'])}

## 5. Training Protocol

Seed `{SEED}`, AdamW, learning rate `{args.lr}`, weight decay `{args.weight_decay}`, batch size `{args.batch_size}`, epochs `{args.epochs}`, residual L1 loss. The supervised label is GT reflectivity magnitude; BP is not used as label. No support head, BCE/Dice, support prior, FOV mask, or complex echo loss was added.

## 6. Overall Results

{table_md(overall, ['variant', 'NMSE', 'PSNR', 'SSIM', 'runtime_per_sample', 'speedup_vs_BP', 'peak_GPU_memory', 'num_test_samples'])}

## 7. Diagnostics by |delta_rho|

See `metrics_by_delta_rho.csv`. Bins are per-sample support quantiles: small, medium, large.

## 8. Diagnostics by |Pcyc|

See `metrics_by_Pcyc.csv`. Includes quantile bins and the physical split `abs(Pcyc)<=0.25` versus `abs(Pcyc)>0.25`.

## 9. Shell-Boundary Diagnostics

See `metrics_by_shell_boundary.csv`. Shell-boundary band is +/- `{SHELL_BOUNDARY_BAND_M}` m around rho=0.075 m and rho=0.225 m.

## 10. Family-Wise Results

See `metrics_by_family.csv`. Family labels are inherited from the frozen handoff manifest.

## 11. OOD Results

See `metrics_ood.csv`. OOD S01-S08 execution is recorded as not evaluated in this first-pass run; no OOD conclusions are claimed.

## 12. Runtime and Complexity

See `runtime_table.csv` and `parameter_count_table.csv`.

## 13. Visual Comparison

Representative panels are saved under `recon_compare/` for best, median, failure, hard high-|Pcyc|, and hard large-|delta_rho| cases. Panels include GT, ref3, S02, S05, S07, S08, plus error MIPs.

## 14. Key Findings

{s02_s05}. {s05_s07}. {s07_s08}. The first-pass result should be interpreted as a structure signal under limited compute rather than a final ranking.

## 15. Failure Analysis

If structured variants underperform S02, likely bottlenecks are metadata scaling/encoding, FiLM placement in the shallow two-downsample trunk, and training dominated by easy regions. The run does not prove ReMiC-Net ineffective.

## 16. Decision: Is ReMiC-Net structurally justified?

Current decision: `{'yes, provisionally' if best['variant'] != 'S02_plain_residual_unet' else 'not yet proven'}`. Metadata/FiLM justification requires longer/full-split confirmation and OOD hard-region evaluation.

## 17. Recommendation for task_real_struc_002

{recommendation}
"""
    write_text(output_root / "task_real_struc_001_report.md", report)
    return {
        "S02 vs S05": s02_s05,
        "S05 vs S07": s05_s07,
        "S07 vs S08": s07_s08,
        "Best current candidate": str(best["variant"]),
        "Main bottleneck": "first-pass limited training; likely metadata scaling/FiLM placement if structured variants do not beat S02",
        "Recommendation for task_real_struc_002": recommendation,
    }


def run(output_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    for rel in ["training_curves", "recon_compare", "diagnostic_plots", "prediction_cache", "metadata_cache", "checkpoints"]:
        ensure_dir(output_root / rel)
    write_environment(output_root)
    rows = prepare_rows(output_root, args.train_limit, args.val_limit, args.test_limit)
    training = []
    param_rows = [{"variant": "S01_ref3", "number_of_parameters": 0}]
    for spec in VARIANTS:
        result = train_variant(output_root, spec, rows, args.epochs, args.batch_size, args.lr, args.weight_decay, args.base_channels)
        training.append(result)
        if spec.kind != "ref3":
            param_rows.append({"variant": spec.key, "number_of_parameters": result["parameter_count"]})
    eval_payload = evaluate(output_root, rows, args.base_channels)
    unavailable_ood(output_root)
    write_config_files(output_root, args, training, param_rows)
    write_debug(output_root)
    conclusion = write_report(output_root, eval_payload, args)
    write_json(output_root / "final_conclusion.json", conclusion)
    return {"experiment_root": str(output_root), "conclusion": conclusion}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run task_real_struc_001 ReMiC-Net core structure diagnosis.")
    parser.add_argument("--output-root", default=None)
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--lr", type=float, default=1.0e-3)
    parser.add_argument("--weight-decay", type=float, default=1.0e-4)
    parser.add_argument("--base-channels", type=int, default=4)
    parser.add_argument("--train-limit", type=int, default=48)
    parser.add_argument("--val-limit", type=int, default=12)
    parser.add_argument("--test-limit", type=int, default=24)
    args = parser.parse_args()
    if args.output_root is None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_root = PROJECT_ROOT / "exp" / "task_real_struc_001_remicnet_core_structure_diagnosis" / stamp
    else:
        output_root = Path(args.output_root)
    ensure_dir(output_root)
    payload = run(output_root, args)
    print(payload["experiment_root"])
    for key, value in payload["conclusion"].items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
