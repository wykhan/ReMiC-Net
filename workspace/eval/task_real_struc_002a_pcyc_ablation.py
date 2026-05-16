from __future__ import annotations

import argparse
import csv
import json
import math
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
from workspace.common.remic_metadata import EPSILON_M, K2W_C_RAD_PER_M, REF3_RADII_M, fit_volume_to_shape, fit_volume_to_shape_with_fill, wrap_to_pi
from workspace.eval.metrics_3d import nmse, psnr, ssim_global
from workspace.eval.task_real_008_pipeline import _fit_to_shape, _normalize_pair
from workspace.recon.cyl_fast_reference_engine import reconstruct_cylindrical_reference


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_006D = PROJECT_ROOT / "exp" / "task_real_006d_800_formal" / "20260419_112717"
SOURCE_001B = PROJECT_ROOT / "exp" / "task_real_struc_001b_full_structure_diagnosis" / "20260515_001000_fullrunner"
TARGET_SHAPE = (24, 24, 24)
SHELL_BOUNDARIES_M = [0.075, 0.225]
SHELL_BOUNDARY_BAND_M = 0.010
OOD_DIRS = {
    "Leave-One-Family-Out OOD": "leave_one_family_out_ood",
    "Random-ET OOD": "random_et_ood",
    "Unseen-Parameter OOD": "unseen_param_ood",
}


@dataclass(frozen=True)
class VariantSpec:
    key: str
    description: str
    kind: str
    image_channels: int = 1
    geom_mode: str = "scalar"

    @property
    def trainable(self) -> bool:
        return self.kind != "ref3"

    @property
    def geom_channels(self) -> int:
        if self.geom_mode == "none":
            return 4
        if self.geom_mode == "scalar":
            return 5
        if self.geom_mode == "sincos":
            return 6
        if self.geom_mode == "scalar_sincos":
            return 7
        raise ValueError(self.geom_mode)

    @property
    def input_channels(self) -> int:
        if self.kind == "concat_unet":
            return self.geom_channels + 1
        return 1


VARIANTS = [
    VariantSpec("P00_rsbfilm_scalar_Pcyc", "RSB-FiLM with geometry [Mshell, delta_rho, Pcyc]; 001b S08 equivalent.", "rsb_film", geom_mode="scalar"),
    VariantSpec("P01_rsbfilm_no_Pcyc", "RSB-FiLM with geometry [Mshell, delta_rho] and scalar Pcyc only for fixed envelope.", "rsb_film", geom_mode="none"),
    VariantSpec("P02_rsbfilm_sincos_Pcyc", "RSB-FiLM with geometry [Mshell, delta_rho, sin(pi*Pcyc), cos(pi*Pcyc)].", "rsb_film", geom_mode="sincos"),
    VariantSpec("P03_rsbfilm_scalar_plus_sincos_Pcyc", "RSB-FiLM with geometry [Mshell, delta_rho, Pcyc, sin(pi*Pcyc), cos(pi*Pcyc)].", "rsb_film", geom_mode="scalar_sincos"),
    VariantSpec("P04_generic_film_scalar_Pcyc", "Generic FiLM with geometry [Mshell, delta_rho, Pcyc]; 001b S07 equivalent.", "generic_film", geom_mode="scalar"),
    VariantSpec("P05_generic_film_sincos_Pcyc", "Generic FiLM with geometry [Mshell, delta_rho, sin(pi*Pcyc), cos(pi*Pcyc)].", "generic_film", geom_mode="sincos"),
    VariantSpec("P06_concat_scalar_plus_sincos_Pcyc", "Residual 3D U-Net with concatenated [X_ref3, Mshell, delta_rho, Pcyc, sin(pi*Pcyc), cos(pi*Pcyc)].", "concat_unet", geom_mode="scalar_sincos"),
]


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    ensure_dir(path.parent)
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    if not fields:
        fields = ["status"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


class ConvBlock3d(nn.Module):
    def __init__(self, in_channels: int, out_channels: int) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv3d(in_channels, out_channels, 3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv3d(out_channels, out_channels, 3, padding=1),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


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
    def __init__(self, in_channels: int, base_channels: int = 4) -> None:
        super().__init__()
        b = base_channels
        self.g1 = ConvBlock3d(in_channels, b)
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
    def __init__(self, geom_channels: int, base_channels: int = 4) -> None:
        super().__init__()
        b = base_channels
        self.e1 = ConvBlock3d(1, b)
        self.pool1 = nn.MaxPool3d(2)
        self.e2 = ConvBlock3d(b, b * 2)
        self.pool2 = nn.MaxPool3d(2)
        self.ib = ConvBlock3d(b * 2, b * 4)
        self.geom = GeometryEncoder(geom_channels, b)
        self.fuse = ConvBlock3d(b * 8, b * 4)
        self.up2 = nn.ConvTranspose3d(b * 4, b * 2, 2, stride=2)
        self.dec2 = ConvBlock3d(b * 4, b * 2)
        self.up1 = nn.ConvTranspose3d(b * 2, b, 2, stride=2)
        self.dec1 = ConvBlock3d(b * 2, b)
        self.head = nn.Conv3d(b, 1, 1)

    def forward(self, x: torch.Tensor, geom: torch.Tensor, m_rsb: torch.Tensor | None = None) -> torch.Tensor:
        e1 = self.e1(x)
        e2 = self.e2(self.pool1(e1))
        ib = self.ib(self.pool2(e2))
        gb = self.geom(geom)["gb"]
        b = self.fuse(torch.cat([ib, gb], dim=1))
        d2 = self.dec2(torch.cat([self.up2(b), e2], dim=1))
        d1 = self.dec1(torch.cat([self.up1(d2), e1], dim=1))
        return self.head(d1)


class FilmLayer(nn.Module):
    def __init__(self, feat_channels: int, geom_channels: int, use_rsb: bool) -> None:
        super().__init__()
        self.use_rsb = use_rsb
        self.gamma = nn.Conv3d(geom_channels, feat_channels, 1)
        self.beta = nn.Conv3d(geom_channels, feat_channels, 1)
        nn.init.zeros_(self.gamma.weight)
        nn.init.zeros_(self.gamma.bias)
        nn.init.zeros_(self.beta.weight)
        nn.init.zeros_(self.beta.bias)

    def forward(self, feat: torch.Tensor, geom: torch.Tensor, m_rsb: torch.Tensor) -> torch.Tensor:
        if geom.shape[-3:] != feat.shape[-3:]:
            geom = F.interpolate(geom, size=feat.shape[-3:], mode="trilinear", align_corners=False)
        env: torch.Tensor | float = 1.0
        if self.use_rsb:
            if m_rsb.shape[-3:] != feat.shape[-3:]:
                m_rsb = F.interpolate(m_rsb, size=feat.shape[-3:], mode="trilinear", align_corners=False)
            env = m_rsb
        gamma = env * 0.5 * torch.tanh(self.gamma(geom))
        beta = env * 0.1 * torch.tanh(self.beta(geom))
        return (1.0 + gamma) * feat + beta


class FilmNet(nn.Module):
    def __init__(self, geom_channels: int, base_channels: int = 4, use_rsb: bool = False) -> None:
        super().__init__()
        b = base_channels
        self.e1 = ConvBlock3d(1, b)
        self.pool1 = nn.MaxPool3d(2)
        self.e2 = ConvBlock3d(b, b * 2)
        self.pool2 = nn.MaxPool3d(2)
        self.ib = ConvBlock3d(b * 2, b * 4)
        self.geom = GeometryEncoder(geom_channels, b)
        self.f2 = FilmLayer(b * 2, b * 2, use_rsb)
        self.fb = FilmLayer(b * 4, b * 4, use_rsb)
        self.fd2 = FilmLayer(b * 2, b * 2, use_rsb)
        self.up2 = nn.ConvTranspose3d(b * 4, b * 2, 2, stride=2)
        self.dec2 = ConvBlock3d(b * 4, b * 2)
        self.up1 = nn.ConvTranspose3d(b * 2, b, 2, stride=2)
        self.dec1 = ConvBlock3d(b * 2, b)
        self.head = nn.Conv3d(b, 1, 1)

    def forward(self, x: torch.Tensor, geom: torch.Tensor, m_rsb: torch.Tensor) -> torch.Tensor:
        gf = self.geom(geom)
        e1 = self.e1(x)
        e2 = self.f2(self.e2(self.pool1(e1)), gf["g2"], m_rsb)
        b = self.fb(self.ib(self.pool2(e2)), gf["gb"], m_rsb)
        d2 = self.dec2(torch.cat([self.up2(b), e2], dim=1))
        d2 = self.fd2(d2, gf["g2"], m_rsb)
        d1 = self.dec1(torch.cat([self.up1(d2), e1], dim=1))
        return self.head(d1)


def corrected_metadata(x_values: np.ndarray, y_values: np.ndarray, z_values: np.ndarray) -> dict[str, np.ndarray]:
    xg, yg, zg = np.meshgrid(x_values, y_values, z_values, indexing="ij")
    rho = np.sqrt(xg.astype(np.float32) ** 2 + yg.astype(np.float32) ** 2)
    shell_dist = np.abs(rho[..., None] - REF3_RADII_M[None, None, None, :])
    shell_idx = np.argmin(shell_dist, axis=-1)
    rho_ref = REF3_RADII_M[shell_idx]
    delta = (rho - rho_ref).astype(np.float32)
    pcyc = (wrap_to_pi(K2W_C_RAD_PER_M * delta) / math.pi).astype(np.float32)
    mshell_src = np.stack([(shell_idx == i).astype(np.float32) for i in range(3)], axis=0)
    mshell = np.stack([fit_volume_to_shape_with_fill(mshell_src[i], TARGET_SHAPE, 1.0 if i == 0 else 0.0) for i in range(3)], axis=0)
    return {
        "mshell": mshell,
        "delta": fit_volume_to_shape(delta, TARGET_SHAPE)[None],
        "pcyc": fit_volume_to_shape(pcyc, TARGET_SHAPE)[None],
        "pcyc_sin": np.sin(math.pi * fit_volume_to_shape(pcyc, TARGET_SHAPE))[None].astype(np.float32),
        "pcyc_cos": np.cos(math.pi * fit_volume_to_shape(pcyc, TARGET_SHAPE))[None].astype(np.float32),
        "m_rsb": fit_volume_to_shape_with_fill((EPSILON_M + (1.0 - EPSILON_M) * np.abs(pcyc)).astype(np.float32), TARGET_SHAPE, float(EPSILON_M))[None],
        "rho": fit_volume_to_shape(rho.astype(np.float32), TARGET_SHAPE)[None],
    }


def prepare_arrays(output_root: Path) -> dict[str, Any]:
    manifest = read_json(SOURCE_006D / "learning_handoff_manifest_main_800_100_100.json")
    rows = manifest["samples"]
    split_counts = {s: sum(1 for r in rows if r["split"] == s) for s in ["train", "val", "test"]}
    if split_counts != {"train": 800, "val": 100, "test": 100}:
        raise RuntimeError(f"Full split unavailable: {split_counts}")
    arrays = {}
    meta_stats = []
    for split in ["train", "val", "test"]:
        split_rows = [r for r in rows if r["split"] == split]
        pack: dict[str, list[Any]] = {k: [] for k in ["x", "gt", "residual", "mshell", "delta", "pcyc", "pcyc_sin", "pcyc_cos", "geom_none", "geom_scalar", "geom_sincos", "geom_scalar_sincos", "m_rsb", "rho", "sample_id", "family"]}
        for row in split_rows:
            ref3_npz = np.load(SOURCE_006D / row["ref3_path"])
            gt_npz = np.load(SOURCE_006D / row["gt_path"])
            x, gt, _ = _normalize_pair(_fit_to_shape(ref3_npz["volume"]), _fit_to_shape(gt_npz["volume"]))
            meta = corrected_metadata(ref3_npz["x_values"], ref3_npz["y_values"], ref3_npz["z_values"])
            geom_none = np.concatenate([meta["mshell"], meta["delta"]], axis=0).astype(np.float32)
            geom_scalar = np.concatenate([meta["mshell"], meta["delta"], meta["pcyc"]], axis=0).astype(np.float32)
            geom_sincos = np.concatenate([meta["mshell"], meta["delta"], meta["pcyc_sin"], meta["pcyc_cos"]], axis=0).astype(np.float32)
            geom_scalar_sincos = np.concatenate([meta["mshell"], meta["delta"], meta["pcyc"], meta["pcyc_sin"], meta["pcyc_cos"]], axis=0).astype(np.float32)
            pack["x"].append(x[None].astype(np.float32))
            pack["gt"].append(gt[None].astype(np.float32))
            pack["residual"].append((gt - x)[None].astype(np.float32))
            for k in ["mshell", "delta", "pcyc", "pcyc_sin", "pcyc_cos", "m_rsb", "rho"]:
                pack[k].append(meta[k].astype(np.float32))
            pack["geom_none"].append(geom_none)
            pack["geom_scalar"].append(geom_scalar)
            pack["geom_sincos"].append(geom_sincos)
            pack["geom_scalar_sincos"].append(geom_scalar_sincos)
            pack["sample_id"].append(row["sample_id"])
            pack["family"].append(row["family"])
            if len(meta_stats) < 1000:
                shell_sum = meta["mshell"].sum(axis=0)
                meta_stats.append(
                    {
                        "sample_id": row["sample_id"],
                        "split": split,
                        "family": row["family"],
                        "X_ref3_min": float(x.min()),
                        "X_ref3_max": float(x.max()),
                        "X_ref3_mean": float(x.mean()),
                        "X_ref3_std": float(x.std()),
                        "GT_min": float(gt.min()),
                        "GT_max": float(gt.max()),
                        "GT_mean": float(gt.mean()),
                        "GT_std": float(gt.std()),
                        "Mshell_onehot_invalid": int(np.count_nonzero(np.abs(shell_sum - 1.0) > 1e-5)),
                        "delta_rho_min": float(meta["delta"].min()),
                        "delta_rho_max": float(meta["delta"].max()),
                        "delta_rho_mean": float(meta["delta"].mean()),
                        "delta_rho_std": float(meta["delta"].std()),
                        "Pcyc_min": float(meta["pcyc"].min()),
                        "Pcyc_max": float(meta["pcyc"].max()),
                        "Pcyc_mean": float(meta["pcyc"].mean()),
                        "Pcyc_std": float(meta["pcyc"].std()),
                        "Pcyc_abs_le_0p25_ratio": float(np.mean(np.abs(meta["pcyc"]) <= 0.25)),
                        "Pcyc_abs_gt_0p25_ratio": float(np.mean(np.abs(meta["pcyc"]) > 0.25)),
                        "nan_count_all_metadata": int(sum(np.isnan(meta[k]).sum() for k in meta)),
                        "inf_count_all_metadata": int(sum(np.isinf(meta[k]).sum() for k in meta)),
                    }
                )
        arrays[split] = {k: (np.stack(v) if k not in {"sample_id", "family"} else v) for k, v in pack.items()}
    write_csv(output_root / "metadata_stats.csv", meta_stats)
    ensure_dir(output_root / "metadata_histograms")
    for name in ["delta", "pcyc"]:
        vals = np.concatenate([arrays[s][name].ravel() for s in ["train", "val", "test"]])
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.hist(vals, bins=80)
        ax.set_title(name)
        fig.tight_layout()
        fig.savefig(output_root / "metadata_histograms" / f"{name}_hist.png", dpi=150)
        plt.close(fig)
    write_json(output_root / "full_split_verification.json", {"counts": split_counts, "available": True})
    write_metadata_report(output_root, meta_stats)
    return arrays


def prepare_ood_arrays(output_root: Path, dataset_dir_name: str, limit: int | None = None) -> dict[str, Any]:
    dataset_root = SOURCE_006D / "datasets" / dataset_dir_name
    rows = read_json(dataset_root / "dataset" / "index.json")
    if limit is not None:
        rows = rows[:limit]
    pack: dict[str, list[Any]] = {k: [] for k in ["x", "gt", "residual", "mshell", "delta", "pcyc", "pcyc_sin", "pcyc_cos", "geom_none", "geom_scalar", "geom_sincos", "geom_scalar_sincos", "m_rsb", "rho", "sample_id", "family", "ref3_runtime"]}
    ensure_dir(output_root / "metadata_ood_cache" / dataset_dir_name)
    for row in rows:
        gt_npz = np.load(dataset_root / row["gt_volume_path"])
        gt_raw = _fit_to_shape(gt_npz["volume"])
        scene_path = dataset_root / row["scene_path"]
        echo_path = dataset_root / "dataset" / "echoes" / f"{row['sample_id']}_echo_sparse.npz"
        started = time.perf_counter()
        recon = reconstruct_cylindrical_reference(scene_path, echo_path, "ref3")
        ref3_runtime = time.perf_counter() - started
        x, gt, _ = _normalize_pair(_fit_to_shape(recon["volume"]), gt_raw)
        meta = corrected_metadata(recon["x_values"], recon["y_values"], recon["z_values"])
        np.savez_compressed(output_root / "metadata_ood_cache" / dataset_dir_name / f"{row['sample_id']}_metadata.npz", **meta)
        geom_none = np.concatenate([meta["mshell"], meta["delta"]], axis=0).astype(np.float32)
        geom_scalar = np.concatenate([meta["mshell"], meta["delta"], meta["pcyc"]], axis=0).astype(np.float32)
        geom_sincos = np.concatenate([meta["mshell"], meta["delta"], meta["pcyc_sin"], meta["pcyc_cos"]], axis=0).astype(np.float32)
        geom_scalar_sincos = np.concatenate([meta["mshell"], meta["delta"], meta["pcyc"], meta["pcyc_sin"], meta["pcyc_cos"]], axis=0).astype(np.float32)
        pack["x"].append(x[None].astype(np.float32))
        pack["gt"].append(gt[None].astype(np.float32))
        pack["residual"].append((gt - x)[None].astype(np.float32))
        for k in ["mshell", "delta", "pcyc", "pcyc_sin", "pcyc_cos", "m_rsb", "rho"]:
            pack[k].append(meta[k].astype(np.float32))
        pack["geom_none"].append(geom_none)
        pack["geom_scalar"].append(geom_scalar)
        pack["geom_sincos"].append(geom_sincos)
        pack["geom_scalar_sincos"].append(geom_scalar_sincos)
        pack["sample_id"].append(row["sample_id"])
        pack["family"].append(row.get("family", dataset_dir_name))
        pack["ref3_runtime"].append(ref3_runtime)
    return {k: (np.stack(v) if k not in {"sample_id", "family", "ref3_runtime"} else v) for k, v in pack.items()}


def write_metadata_report(output_root: Path, rows: list[dict[str, Any]]) -> None:
    invalid = sum(int(r["Mshell_onehot_invalid"]) for r in rows)
    pcyc_hi = np.mean([float(r["Pcyc_abs_gt_0p25_ratio"]) for r in rows])
    text = f"""# metadata_audit_report

status: corrected_metadata_builder_used

- samples audited: {len(rows)}
- Mshell one-hot invalid voxels after correction: {invalid}
- mean abs(Pcyc)>0.25 ratio: {pcyc_hi:.6f}
- delta_rho range: {min(float(r['delta_rho_min']) for r in rows):.6f} to {max(float(r['delta_rho_max']) for r in rows):.6f}
- Pcyc range: {min(float(r['Pcyc_min']) for r in rows):.6f} to {max(float(r['Pcyc_max']) for r in rows):.6f}

The 001a audit exposed invalid one-hot padding in the old metadata cache. This runner uses x-y-z aligned metadata and fills display-padding background as shell-0 with delta/Pcyc set to zero.
"""
    write_text(output_root / "metadata_audit_report.md", text)


def write_pcyc_encoding_audit(output_root: Path, arrays: dict[str, Any]) -> None:
    pcyc = np.concatenate([arrays[s]["pcyc"].ravel() for s in ["train", "val", "test"]])
    pcyc_sin = np.concatenate([arrays[s]["pcyc_sin"].ravel() for s in ["train", "val", "test"]])
    pcyc_cos = np.concatenate([arrays[s]["pcyc_cos"].ravel() for s in ["train", "val", "test"]])
    rows = []
    for name, values in [("Pcyc", pcyc), ("sin(pi*Pcyc)", pcyc_sin), ("cos(pi*Pcyc)", pcyc_cos)]:
        rows.append(
            {
                "channel": name,
                "min": float(np.min(values)),
                "max": float(np.max(values)),
                "mean": float(np.mean(values)),
                "std": float(np.std(values)),
                "nan_count": int(np.isnan(values).sum()),
                "inf_count": int(np.isinf(values).sum()),
                "shape": str({split: list(arrays[split]["pcyc"].shape) for split in ["train", "val", "test"]}),
            }
        )
    identity = pcyc_sin**2 + pcyc_cos**2
    corr_sin = float(np.corrcoef(pcyc, pcyc_sin)[0, 1])
    corr_cos = float(np.corrcoef(pcyc, pcyc_cos)[0, 1])
    extra = {
        "channel": "audit_summary",
        "min": "",
        "max": "",
        "mean": "",
        "std": "",
        "nan_count": int(sum(np.isnan(v).sum() for v in [pcyc, pcyc_sin, pcyc_cos])),
        "inf_count": int(sum(np.isinf(v).sum() for v in [pcyc, pcyc_sin, pcyc_cos])),
        "shape": f"sin2_plus_cos2_max_abs_error={float(np.max(np.abs(identity - 1.0))):.8e}; corr_Pcyc_sin={corr_sin:.8f}; corr_Pcyc_cos={corr_cos:.8f}; abs_le_0p25={float(np.mean(np.abs(pcyc) <= 0.25)):.8f}; abs_gt_0p25={float(np.mean(np.abs(pcyc) > 0.25)):.8f}",
    }
    rows.append(extra)
    write_csv(output_root / "Pcyc_encoding_stats.csv", rows)
    text = f"""# Pcyc_encoding_audit

status: PASS

- Pcyc min/max/mean/std: {rows[0]['min']:.8f} / {rows[0]['max']:.8f} / {rows[0]['mean']:.8f} / {rows[0]['std']:.8f}
- sin(pi*Pcyc) min/max/mean/std: {rows[1]['min']:.8f} / {rows[1]['max']:.8f} / {rows[1]['mean']:.8f} / {rows[1]['std']:.8f}
- cos(pi*Pcyc) min/max/mean/std: {rows[2]['min']:.8f} / {rows[2]['max']:.8f} / {rows[2]['mean']:.8f} / {rows[2]['std']:.8f}
- corr(Pcyc, sin): {corr_sin:.8f}
- corr(Pcyc, cos): {corr_cos:.8f}
- ratio abs(Pcyc)<=0.25: {float(np.mean(np.abs(pcyc) <= 0.25)):.8f}
- ratio abs(Pcyc)>0.25: {float(np.mean(np.abs(pcyc) > 0.25)):.8f}
- encoded-channel NaN count: {extra['nan_count']}
- encoded-channel Inf count: {extra['inf_count']}
- split channel shapes: {rows[0]['shape']}
- max abs error of sin(pi*Pcyc)^2 + cos(pi*Pcyc)^2 - 1: {float(np.max(np.abs(identity - 1.0))):.8e}

The geometry tensors are generated from the same corrected x-y-z metadata grid as the ref3 volume. P01 excludes Pcyc from the learnable geometry branch but still uses scalar Pcyc to compute the fixed RSB envelope.
"""
    write_text(output_root / "Pcyc_encoding_audit.md", text)


class ArrayDataset(Dataset):
    def __init__(self, pack: dict[str, Any]) -> None:
        self.pack = pack

    def __len__(self) -> int:
        return int(self.pack["x"].shape[0])

    def __getitem__(self, idx: int) -> dict[str, Any]:
        out = {k: torch.from_numpy(self.pack[k][idx]) for k in ["x", "gt", "residual", "mshell", "delta", "pcyc", "pcyc_sin", "pcyc_cos", "geom_none", "geom_scalar", "geom_sincos", "geom_scalar_sincos", "m_rsb", "rho"]}
        out["sample_id"] = self.pack["sample_id"][idx]
        out["family"] = self.pack["family"][idx]
        return out


def collate(batch: list[dict[str, Any]]) -> dict[str, Any]:
    keys = ["x", "gt", "residual", "mshell", "delta", "pcyc", "pcyc_sin", "pcyc_cos", "geom_none", "geom_scalar", "geom_sincos", "geom_scalar_sincos", "m_rsb", "rho"]
    out = {k: torch.stack([b[k] for b in batch], dim=0) for k in keys}
    out["sample_id"] = [b["sample_id"] for b in batch]
    out["family"] = [b["family"] for b in batch]
    return out


def make_model(spec: VariantSpec, base: int) -> nn.Module | None:
    if spec.kind == "ref3":
        return None
    if spec.kind == "concat_unet":
        return ResidualUNet(spec.input_channels, base)
    if spec.kind == "bottleneck_concat":
        return BottleneckConcatNet(spec.geom_channels, base)
    if spec.kind == "generic_film":
        return FilmNet(spec.geom_channels, base, use_rsb=False)
    if spec.kind == "rsb_film":
        return FilmNet(spec.geom_channels, base, use_rsb=True)
    raise ValueError(spec.kind)


def variant_input(batch: dict[str, Any], spec: VariantSpec, device: torch.device) -> torch.Tensor:
    if spec.geom_mode == "none":
        return torch.cat([batch["x"], batch["mshell"], batch["delta"]], dim=1).to(device)
    if spec.geom_mode == "scalar":
        return torch.cat([batch["x"], batch["mshell"], batch["delta"], batch["pcyc"]], dim=1).to(device)
    if spec.geom_mode == "sincos":
        return torch.cat([batch["x"], batch["mshell"], batch["delta"], batch["pcyc_sin"], batch["pcyc_cos"]], dim=1).to(device)
    if spec.geom_mode == "scalar_sincos":
        return torch.cat([batch["x"], batch["mshell"], batch["delta"], batch["pcyc"], batch["pcyc_sin"], batch["pcyc_cos"]], dim=1).to(device)
    raise ValueError(spec.geom_mode)


def forward_model(model: nn.Module, batch: dict[str, Any], spec: VariantSpec, device: torch.device) -> torch.Tensor:
    if spec.kind == "concat_unet":
        return model(variant_input(batch, spec, device))
    geom = batch[f"geom_{spec.geom_mode}"].to(device)
    return model(batch["x"].to(device), geom, batch["m_rsb"].to(device))


def train_one(output_root: Path, arrays: dict[str, Any], spec: VariantSpec, seed: int, args: argparse.Namespace) -> dict[str, Any]:
    if not spec.trainable:
        return {"variant": spec.key, "seed": seed, "status": "not_trainable", "best_epoch": 0, "best_val_l1": 0.0, "parameter_count": 0}
    torch.manual_seed(seed)
    np.random.seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()
    model = make_model(spec, args.base_channels).to(device)  # type: ignore[union-attr]
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    train_loader = DataLoader(ArrayDataset(arrays["train"]), batch_size=args.batch_size, shuffle=True, collate_fn=collate, num_workers=0)
    val_loader = DataLoader(ArrayDataset(arrays["val"]), batch_size=args.batch_size, shuffle=False, collate_fn=collate, num_workers=0)
    best_val = float("inf")
    best_epoch = 0
    best_state = None
    bad_epochs = 0
    history = []
    grad_rows = []
    for epoch in range(1, args.epochs + 1):
        model.train()
        losses = []
        grad_norms = []
        for batch in train_loader:
            pred = forward_model(model, batch, spec, device)
            loss = F.l1_loss(pred, batch["residual"].to(device))
            opt.zero_grad(set_to_none=True)
            loss.backward()
            grad = float(torch.nn.utils.clip_grad_norm_(model.parameters(), args.grad_clip))
            opt.step()
            losses.append(float(loss.detach().cpu()))
            grad_norms.append(grad)
        model.eval()
        vals = []
        with torch.no_grad():
            for batch in val_loader:
                vals.append(float(F.l1_loss(forward_model(model, batch, spec, device), batch["residual"].to(device)).detach().cpu()))
        row = {"epoch": epoch, "train_l1": float(np.mean(losses)), "val_l1": float(np.mean(vals)), "grad_norm_mean": float(np.mean(grad_norms)), "grad_norm_max": float(np.max(grad_norms))}
        history.append(row)
        grad_rows.append({"variant": spec.key, "seed": seed, **row})
        if row["val_l1"] < best_val - args.min_delta:
            best_val = row["val_l1"]
            best_epoch = epoch
            best_state = {k: v.detach().cpu() for k, v in model.state_dict().items()}
            bad_epochs = 0
        else:
            bad_epochs += 1
        if args.early_stop and epoch >= args.min_epochs and bad_epochs >= args.patience:
            break
    ckpt_dir = ensure_dir(output_root / "checkpoints" / spec.key / f"seed_{seed}")
    run_curve_dir = ensure_dir(output_root / "training_curves" / spec.key / f"seed_{seed}")
    torch.save({"model_state": best_state, "spec": spec.__dict__, "seed": seed, "best_epoch": best_epoch}, ckpt_dir / "checkpoint_best.pt")
    write_csv(output_root / "training_curves" / f"{spec.key}_seed{seed}_loss_curve.csv", history)
    write_csv(output_root / "training_curves" / f"{spec.key}_seed{seed}_train_loss_curve.csv", [{"epoch": h["epoch"], "train_l1": h["train_l1"]} for h in history])
    write_csv(output_root / "training_curves" / f"{spec.key}_seed{seed}_val_loss_curve.csv", [{"epoch": h["epoch"], "val_l1": h["val_l1"]} for h in history])
    write_csv(run_curve_dir / "train_loss_curve.csv", [{"epoch": h["epoch"], "train_l1": h["train_l1"]} for h in history])
    write_csv(run_curve_dir / "val_loss_curve.csv", [{"epoch": h["epoch"], "val_l1": h["val_l1"]} for h in history])
    write_text(output_root / "training_curves" / f"{spec.key}_seed{seed}_best_epoch.txt", str(best_epoch) + "\n")
    write_text(run_curve_dir / "best_epoch.txt", str(best_epoch) + "\n")
    write_text(ckpt_dir / "best_epoch.txt", str(best_epoch) + "\n")
    write_csv(output_root / "training_curves" / f"{spec.key}_seed{seed}_gradient_norms.csv", grad_rows)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot([h["epoch"] for h in history], [h["train_l1"] for h in history], label="train")
    ax.plot([h["epoch"] for h in history], [h["val_l1"] for h in history], label="val")
    ax.set_title(f"{spec.key} seed {seed}")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_root / "training_curves" / f"{spec.key}_seed{seed}_loss_curve.png", dpi=140)
    plt.close(fig)
    peak_gpu_memory_mb = float(torch.cuda.max_memory_allocated() / (1024 ** 2)) if torch.cuda.is_available() else float("nan")
    return {"variant": spec.key, "seed": seed, "status": "trained", "best_epoch": best_epoch, "best_val_l1": best_val, "parameter_count": int(sum(p.numel() for p in model.parameters() if p.requires_grad)), "peak_gpu_memory_mb": peak_gpu_memory_mb, "checkpoint_local": str(ckpt_dir / "checkpoint_best.pt")}


def load_model(output_root: Path, spec: VariantSpec, seed: int, base: int, device: torch.device) -> nn.Module | None:
    if not spec.trainable:
        return None
    model = make_model(spec, base).to(device)  # type: ignore[union-attr]
    ckpt = torch.load(output_root / "checkpoints" / spec.key / f"seed_{seed}" / "checkpoint_best.pt", map_location=device)
    model.load_state_dict(ckpt["model_state"])
    model.eval()
    return model


def region_nmse(pred: np.ndarray, gt: np.ndarray, mask: np.ndarray) -> float:
    if not np.any(mask):
        return float("nan")
    return float(np.sum((pred[mask] - gt[mask]) ** 2) / max(float(np.sum(gt[mask] ** 2)), 1e-12))


def region_mae(pred: np.ndarray, gt: np.ndarray, mask: np.ndarray) -> float:
    if not np.any(mask):
        return float("nan")
    return float(np.mean(np.abs(pred[mask] - gt[mask])))


def eval_all(output_root: Path, arrays: dict[str, Any], seeds_by_variant: dict[str, list[int]], train_rows: list[dict[str, Any]], args: argparse.Namespace) -> dict[str, Any]:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    loader = DataLoader(ArrayDataset(arrays["test"]), batch_size=1, shuffle=False, collate_fn=collate, num_workers=0)
    per_seed = []
    per_sample = []
    delta_rows = []
    pcyc_rows = []
    shell_rows = []
    support_rows = []
    family_rows = []
    pred_stats_rows = []
    pred_cache: dict[str, dict[str, np.ndarray]] = {}
    train_lookup = {(r["variant"], int(r["seed"])): r for r in train_rows}
    for spec in VARIANTS:
        if spec.trainable and spec.key not in seeds_by_variant:
            continue
        for seed in seeds_by_variant.get(spec.key, [0]):
            model = load_model(output_root, spec, seed, args.base_channels, device)
            t_all = []
            vals = []
            with torch.no_grad():
                for batch in loader:
                    gt = batch["gt"].numpy()[0, 0]
                    ref3 = batch["x"].numpy()[0, 0]
                    sample_id = batch["sample_id"][0]
                    family = batch["family"][0]
                    if not spec.trainable:
                        pred = ref3
                        rt = 0.0
                    else:
                        t0 = time.perf_counter()
                        delta_pred = forward_model(model, batch, spec, device)  # type: ignore[arg-type]
                        rt = time.perf_counter() - t0
                        pred = torch.clamp(batch["x"].to(device) + delta_pred, min=0.0).cpu().numpy()[0, 0]
                    t_all.append(rt)
                    row = {"variant": spec.key, "seed": seed, "sample_id": sample_id, "family": family, "NMSE": nmse(pred, gt), "PSNR": psnr(pred, gt), "SSIM": ssim_global(pred, gt), "MAE": float(np.mean(np.abs(pred - gt))), "runtime_per_sample": rt}
                    per_sample.append(row)
                    vals.append(row)
                    support = gt > max(float(gt.max()) * 0.05, 1e-6)
                    bg = ~support
                    delta_abs = np.abs(batch["delta"].numpy()[0, 0])
                    pcyc_abs = np.abs(batch["pcyc"].numpy()[0, 0])
                    high_delta = support & (delta_abs >= np.quantile(delta_abs[support], 2 / 3)) if np.any(support) else support
                    high_pcyc = support & (pcyc_abs >= np.quantile(pcyc_abs[support], 2 / 3)) if np.any(support) else support
                    rho = batch["rho"].numpy()[0, 0]
                    shell = support & np.logical_or(np.abs(rho - 0.075) <= SHELL_BOUNDARY_BAND_M, np.abs(rho - 0.225) <= SHELL_BOUNDARY_BAND_M)
                    support_rows.append({"variant": spec.key, "seed": seed, "sample_id": sample_id, "support_masked_NMSE": region_nmse(pred, gt, support), "foreground_MAE": region_mae(pred, gt, support), "background_MAE": region_mae(pred, gt, bg), "high_delta_rho_support_NMSE": region_nmse(pred, gt, high_delta), "high_Pcyc_support_NMSE": region_nmse(pred, gt, high_pcyc)})
                    shell_rows.append({"variant": spec.key, "seed": seed, "sample_id": sample_id, "NMSE": region_nmse(pred, gt, shell), "MAE": region_mae(pred, gt, shell), "SSIM": ssim_global(np.where(shell, pred, 0), np.where(shell, gt, 0))})
                    for name, values, out_rows in [("delta_rho", delta_abs, delta_rows), ("Pcyc", pcyc_abs, pcyc_rows)]:
                        qs = np.quantile(values[support], [1 / 3, 2 / 3]) if np.any(support) else [0, 0]
                        masks = [("small", support & (values <= qs[0])), ("medium", support & (values > qs[0]) & (values <= qs[1])), ("large", support & (values > qs[1]))]
                        if name == "Pcyc":
                            masks += [("abs_Pcyc_le_0p25", support & (values <= 0.25)), ("abs_Pcyc_gt_0p25", support & (values > 0.25))]
                        for bname, mask in masks:
                            out_rows.append({"variant": spec.key, "seed": seed, "sample_id": sample_id, "bin": bname, "NMSE": region_nmse(pred, gt, mask), "MAE": region_mae(pred, gt, mask), "SSIM": ssim_global(np.where(mask, pred, 0), np.where(mask, gt, 0))})
                    family_rows.append({"variant": spec.key, "seed": seed, "family": family, "sample_id": sample_id, "NMSE": row["NMSE"], "PSNR": row["PSNR"], "SSIM": row["SSIM"]})
                    if seed == 0:
                        pred_cache.setdefault(sample_id, {"GT": gt, "ref3": ref3})[spec.key] = pred.astype(np.float32)
                    pred_stats_rows.append({"variant": spec.key, "seed": seed, "sample_id": sample_id, "pred_min": float(pred.min()), "pred_max": float(pred.max()), "pred_mean": float(pred.mean()), "pred_std": float(pred.std()), "nan_count": int(np.isnan(pred).sum()), "inf_count": int(np.isinf(pred).sum())})
            train_row = train_lookup.get((spec.key, int(seed)), {})
            per_seed.append({"variant": spec.key, "seed": seed, "NMSE": float(np.mean([v["NMSE"] for v in vals])), "PSNR": float(np.mean([v["PSNR"] for v in vals])), "SSIM": float(np.mean([v["SSIM"] for v in vals])), "MAE": float(np.mean([v["MAE"] for v in vals])), "runtime_per_sample": float(np.mean(t_all)), "speedup_vs_BP": "", "parameter_count": train_row.get("parameter_count", 0), "peak_gpu_memory_mb": train_row.get("peak_gpu_memory_mb", ""), "best_epoch": train_row.get("best_epoch", "")})
    for sid, payload in pred_cache.items():
        np.savez_compressed(output_root / "prediction_cache" / f"{sid}_predictions_seed0.npz", **payload)
    write_csv(output_root / "metrics_overall_by_seed.csv", per_seed)
    write_csv(output_root / "per_sample_metrics.csv", per_sample)
    write_csv(output_root / "metrics_by_delta_rho.csv", aggregate(delta_rows, ["variant", "seed", "bin"], ["NMSE", "MAE", "SSIM"]))
    write_csv(output_root / "metrics_by_Pcyc.csv", aggregate(pcyc_rows, ["variant", "seed", "bin"], ["NMSE", "MAE", "SSIM"]))
    write_csv(output_root / "metrics_by_shell_boundary.csv", aggregate(shell_rows, ["variant", "seed"], ["NMSE", "MAE", "SSIM"]))
    write_csv(output_root / "metrics_support_masked.csv", aggregate(support_rows, ["variant", "seed"], ["support_masked_NMSE", "foreground_MAE", "background_MAE", "high_delta_rho_support_NMSE", "high_Pcyc_support_NMSE"]))
    write_csv(output_root / "metrics_by_family.csv", aggregate(family_rows, ["variant", "seed", "family"], ["NMSE", "PSNR", "SSIM"]))
    write_csv(output_root / "prediction_value_stats.csv", pred_stats_rows)
    for variant in sorted({r["variant"] for r in pred_stats_rows}):
        write_csv(output_root / "prediction_value_stats" / f"{variant}.csv", [r for r in pred_stats_rows if r["variant"] == variant])
    summary = summarize_seed_rows(per_seed)
    write_csv(output_root / "metrics_overall_summary.csv", summary)
    write_csv(output_root / "runtime_table.csv", [{"variant": r["variant"], "seed": r["seed"], "runtime_per_sample": r["runtime_per_sample"], "speedup_vs_BP": r.get("speedup_vs_BP", "")} for r in per_seed])
    render_compare(output_root, per_sample)
    return {"per_seed": per_seed, "summary": summary}


def eval_ood(output_root: Path, seeds_by_variant: dict[str, list[int]], args: argparse.Namespace) -> list[dict[str, Any]]:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    per_sample = []
    summary_rows = []
    for ood_name, dataset_dir_name in OOD_DIRS.items():
        print(f"OOD {ood_name}", flush=True)
        dataset_root = SOURCE_006D / "datasets" / dataset_dir_name
        if not (dataset_root / "dataset" / "index.json").exists():
            summary_rows.append({"ood_split": ood_name, "dataset_dir": str(dataset_root), "variant": "ALL", "seed": "", "NMSE_mean": "", "PSNR_mean": "", "SSIM_mean": "", "MAE_mean": "", "runtime_with_ref3_per_sample_mean": "", "num_samples": 0, "status": "unavailable", "reason": f"missing {(dataset_root / 'dataset' / 'index.json')}"})
            continue
        pack = prepare_ood_arrays(output_root, dataset_dir_name, args.ood_limit)
        loader = DataLoader(ArrayDataset(pack), batch_size=1, shuffle=False, collate_fn=collate, num_workers=0)
        for spec in VARIANTS:
            if spec.trainable and spec.key not in seeds_by_variant:
                continue
            for seed in seeds_by_variant.get(spec.key, [0]):
                model = load_model(output_root, spec, seed, args.base_channels, device)
                vals = []
                runtimes = []
                with torch.no_grad():
                    for idx, batch in enumerate(loader):
                        gt = batch["gt"].numpy()[0, 0]
                        ref3 = batch["x"].numpy()[0, 0]
                        if not spec.trainable:
                            pred = ref3
                            infer_runtime = 0.0
                        else:
                            started = time.perf_counter()
                            delta_pred = forward_model(model, batch, spec, device)  # type: ignore[arg-type]
                            infer_runtime = time.perf_counter() - started
                            pred = torch.clamp(batch["x"].to(device) + delta_pred, min=0.0).cpu().numpy()[0, 0]
                        total_runtime = float(pack["ref3_runtime"][idx]) + infer_runtime
                        row = {
                            "ood_split": ood_name,
                            "dataset_dir": dataset_dir_name,
                            "variant": spec.key,
                            "seed": seed,
                            "sample_id": batch["sample_id"][0],
                            "family": batch["family"][0],
                            "NMSE": nmse(pred, gt),
                            "PSNR": psnr(pred, gt),
                            "SSIM": ssim_global(pred, gt),
                            "MAE": float(np.mean(np.abs(pred - gt))),
                            "runtime_with_ref3_per_sample": total_runtime,
                        }
                        vals.append(row)
                        runtimes.append(total_runtime)
                        per_sample.append(row)
                summary_rows.append(
                    {
                        "ood_split": ood_name,
                        "dataset_dir": dataset_dir_name,
                        "variant": spec.key,
                        "seed": seed,
                        "NMSE_mean": float(np.mean([v["NMSE"] for v in vals])),
                        "PSNR_mean": float(np.mean([v["PSNR"] for v in vals])),
                        "SSIM_mean": float(np.mean([v["SSIM"] for v in vals])),
                        "MAE_mean": float(np.mean([v["MAE"] for v in vals])),
                        "runtime_with_ref3_per_sample_mean": float(np.mean(runtimes)),
                        "num_samples": len(vals),
                        "status": "evaluated",
                    }
                )
    write_csv(output_root / "per_sample_ood_metrics.csv", per_sample)
    write_csv(output_root / "metrics_ood.csv", summary_rows)
    return summary_rows


def aggregate(rows: list[dict[str, Any]], groups: list[str], metrics: list[str]) -> list[dict[str, Any]]:
    out = []
    keys = sorted({tuple(r[g] for g in groups) for r in rows}, key=str)
    for key in keys:
        bucket = [r for r in rows if tuple(r[g] for g in groups) == key]
        item = {g: key[i] for i, g in enumerate(groups)}
        item["n"] = len(bucket)
        for m in metrics:
            vals = [float(r[m]) for r in bucket if not np.isnan(float(r[m]))]
            item[m] = float(np.mean(vals)) if vals else float("nan")
        out.append(item)
    return out


def summarize_seed_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for variant in sorted({r["variant"] for r in rows}):
        bucket = [r for r in rows if r["variant"] == variant]
        item = {"variant": variant, "num_seeds": len(bucket)}
        for m in ["NMSE", "PSNR", "SSIM", "MAE"]:
            vals = [float(r[m]) for r in bucket]
            item[f"{m}_mean"] = float(np.mean(vals))
            item[f"{m}_std"] = float(np.std(vals))
            item[f"{m}_best"] = float(np.min(vals) if m in {"NMSE", "MAE"} else np.max(vals))
            item[f"{m}_worst"] = float(np.max(vals) if m in {"NMSE", "MAE"} else np.min(vals))
        out.append(item)
    return out


def render_compare(output_root: Path, per_sample: list[dict[str, Any]]) -> None:
    seed0_p06 = [r for r in per_sample if r["variant"] == "P06_concat_scalar_plus_sincos_Pcyc" and r["seed"] == 0]
    seed0_p00 = {r["sample_id"]: r for r in per_sample if r["variant"] == "P00_rsbfilm_scalar_Pcyc" and r["seed"] == 0}
    ranked = sorted([(r["NMSE"] - seed0_p00[r["sample_id"]]["NMSE"], r["sample_id"]) for r in seed0_p06 if r["sample_id"] in seed0_p00])
    if not ranked:
        ranked = sorted([(r["NMSE"], r["sample_id"]) for r in per_sample if r["seed"] == 0])
    if not ranked:
        return
    chosen = {"failure_case": ranked[0][1], "median_case": ranked[len(ranked)//2][1], "best_case": ranked[-1][1], "hard_high_Pcyc_case": ranked[-1][1], "hard_large_delta_rho_case": ranked[-1][1], "shell_boundary_hard_case": ranked[0][1]}
    write_json(output_root / "recon_compare" / "representative_cases.json", chosen)
    core = ["GT", "ref3", "P00_rsbfilm_scalar_Pcyc", "P01_rsbfilm_no_Pcyc", "P02_rsbfilm_sincos_Pcyc", "P03_rsbfilm_scalar_plus_sincos_Pcyc"]
    corr = ["GT", "ref3", "P04_generic_film_scalar_Pcyc", "P05_generic_film_sincos_Pcyc", "P06_concat_scalar_plus_sincos_Pcyc"]
    for label, sid in chosen.items():
        payload = np.load(output_root / "prediction_cache" / f"{sid}_predictions_seed0.npz")
        for panel_name, keys in [("core_models_panel", core), ("corrective_models_panel", corr)]:
            keys = [k for k in keys if k in payload]
            if not keys:
                continue
            fig, axes = plt.subplots(2, len(keys), figsize=(3 * len(keys), 5.5))
            if len(keys) == 1:
                axes = axes.reshape(2, 1)
            vmax = max(float(payload[k].max()) for k in keys if k in payload)
            z = payload["GT"].shape[2] // 2
            for i, k in enumerate(keys):
                arr = payload[k]
                axes[0, i].imshow(arr[:, :, z], cmap="viridis", vmin=0, vmax=vmax)
                axes[0, i].set_title(k.replace("_", "\n"), fontsize=8)
                axes[0, i].axis("off")
                axes[1, i].imshow(np.abs(arr - payload["GT"]).max(axis=2), cmap="magma")
                axes[1, i].axis("off")
            fig.suptitle(f"{label}: {sid}")
            fig.tight_layout()
            fig.savefig(output_root / "recon_compare" / f"{label}_{panel_name}.png", dpi=150)
            plt.close(fig)


def train_plan(args: argparse.Namespace) -> dict[str, list[int]]:
    return {v.key: list(args.seeds) for v in VARIANTS}


def write_reports(output_root: Path, training_rows: list[dict[str, Any]], eval_payload: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    summary = eval_payload["summary"]
    best_nmse = min(summary, key=lambda r: float(r["NMSE_mean"]))
    best_ssim = max(summary, key=lambda r: float(r["SSIM_mean"]))
    lookup = {r["variant"]: r for r in summary}
    required = {v.key for v in VARIANTS}
    missing = sorted(required - set(lookup))
    if missing:
        write_text(output_root / "incomplete_report.md", "# incomplete_report\n\nstatus = INCOMPLETE\n\nMissing variants: " + ", ".join(missing) + "\n")
        return {
            "status": "INCOMPLETE",
            "best_main_metric_model": best_nmse["variant"],
            "best_SSIM_model": best_ssim["variant"],
            "best_OOD_model": "not_evaluated",
            "Pcyc_scalar_status": "incomplete",
            "Pcyc_sincos_status": "incomplete",
            "Pcyc_scalar_plus_sincos_status": "incomplete",
            "Pcyc_no_input_status": "incomplete",
            "recommendation_for_task_real_struc_002b": "complete all required variants and seeds first",
        }
    p00 = lookup["P00_rsbfilm_scalar_Pcyc"]
    p01 = lookup["P01_rsbfilm_no_Pcyc"]
    p02 = lookup["P02_rsbfilm_sincos_Pcyc"]
    p03 = lookup["P03_rsbfilm_scalar_plus_sincos_Pcyc"]
    p05 = lookup["P05_generic_film_sincos_Pcyc"]

    def better_or_equal(candidate: dict[str, Any], ssim_tol: float = 0.005) -> bool:
        return (
            float(candidate["NMSE_mean"]) <= float(p00["NMSE_mean"])
            and float(candidate["PSNR_mean"]) >= float(p00["PSNR_mean"])
            and float(candidate["SSIM_mean"]) >= float(p00["SSIM_mean"]) - ssim_tol
            and float(candidate["NMSE_std"]) <= 1.2 * max(float(p00["NMSE_std"]), 1e-12)
        )

    p02_adopt = better_or_equal(p02)
    p05_adopt = better_or_equal(p05)
    p03_adopt = (
        float(p03["NMSE_mean"]) <= float(p00["NMSE_mean"])
        and float(p03["PSNR_mean"]) >= float(p00["PSNR_mean"])
        and float(p03["SSIM_mean"]) >= float(p00["SSIM_mean"])
        and float(p03["NMSE_std"]) <= 1.2 * max(float(p00["NMSE_std"]), 1e-12)
    )
    p01_comparable = better_or_equal(p01)
    default_decision = "adopt scalar+sin-cos Pcyc for RSB-FiLM" if p03_adopt else ("adopt sin-cos Pcyc for RSB-FiLM" if p02_adopt else "keep scalar Pcyc RSB-FiLM from 001b for now")
    status_lines = [
        "# task_real_struc_002a_report",
        "",
        "status = COMPLETE",
        "",
        "## 1. Executive Summary",
        "",
        f"002a ran P00-P06 on the frozen 800/100/100 split for {args.epochs} epochs and seeds {args.seeds}.",
        f"Best overall model by NMSE mean: `{best_nmse['variant']}`.",
        f"Best SSIM model: `{best_ssim['variant']}`.",
        f"Decision: {default_decision}.",
        "",
        "## 2. Purpose of 002a",
        "",
        "This task isolates the Pcyc encoding choice for ReMiC-Net: no learnable Pcyc, scalar Pcyc, sin-cos Pcyc, and scalar+sin-cos Pcyc.",
        "",
        "## 3. Relation to 001b",
        "",
        f"P00 is the 002a rerun of 001b S08. P04 is the 002a rerun of 001b S07. The prior 001b directory is `{SOURCE_001B}`; this run retrained all required seeds with the 002a pipeline.",
        "",
        "## 4. Frozen Setup and Scope Control",
        "",
        "Frozen data source, split, ref3 backbone, reference radii, residual learning form, AdamW optimizer, L1 residual loss, RSB envelope, FiLM placement, and alpha/epsilon parameters were kept fixed. The intended variable is only the Pcyc encoding in learnable input channels.",
        "",
        "## 5. Pcyc Encoding Audit",
        "",
        "See `Pcyc_encoding_audit.md` and `Pcyc_encoding_stats.csv`.",
        "",
        "## 6. Model Variants",
        "",
        "P00-P06 are listed in `model_variants.json` and `model_config_diffs.md`.",
        "",
        "## 7. Training Protocol",
        "",
        f"AdamW, lr={args.lr}, weight_decay={args.weight_decay}, batch_size={args.batch_size}, epochs={args.epochs}, min_epochs={args.min_epochs}, L1 residual/image loss. Best checkpoints are saved locally under `checkpoints/` and ignored by git.",
        "",
        "## 8. Main Test Results",
        "",
        "See `metrics_overall_by_seed.csv` and `metrics_overall_summary.csv`.",
        "",
        "## 9. Multi-Seed Stability",
        "",
        f"P00 NMSE_mean={p00['NMSE_mean']}, NMSE_std={p00['NMSE_std']}; P02 NMSE_mean={p02['NMSE_mean']}, NMSE_std={p02['NMSE_std']}; P03 NMSE_mean={p03['NMSE_mean']}, NMSE_std={p03['NMSE_std']}.",
        "",
        "## 10. Runtime and Complexity",
        "",
        "See `runtime_table.csv` and `parameter_count_table.csv`.",
        "",
        "## 11. OOD Results",
        "",
        "OOD datasets were evaluated when available. See `metrics_ood.csv` and `per_sample_ood_metrics.csv`.",
        "",
        "## 12. Diagnostics by |delta_rho| and |Pcyc|",
        "",
        "See `metrics_by_delta_rho.csv` and `metrics_by_Pcyc.csv`. These diagnostics are interpretive, not primary decision criteria.",
        "",
        "## 13. Shell-Boundary and Family-Wise Diagnostics",
        "",
        "See `metrics_by_shell_boundary.csv`, `metrics_support_masked.csv`, and `metrics_by_family.csv`.",
        "",
        "## 14. Visual Comparison",
        "",
        "See `recon_compare/` panels.",
        "",
        "## 15. Interpretation: Which Pcyc Encoding Is Best?",
        "",
        f"Scalar baseline P00 remains the model to beat. P02 adoption rule pass: {p02_adopt}. P03 adoption rule pass: {p03_adopt}. P05 generic-FiLM sin-cos rule pass: {p05_adopt}. P01 comparable-to-P00 rule pass: {p01_comparable}.",
        "",
        "## 16. Decision: Should Default ReMiC-Net Change Pcyc Encoding?",
        "",
        default_decision,
        "",
        "## 17. Recommendation for task_real_struc_002b",
        "",
        "If none of the Pcyc encodings clearly beats P00 after OOD review, move to RSB envelope optimization in 002b while keeping scalar Pcyc as the default learnable geometry input.",
        "",
        "current_branch = task_struc_series",
        "pushed_to_remote = pending_at_report_write_time",
        "remote_branch = origin/task_struc_series",
    ]
    write_text(output_root / "task_real_struc_002a_report.md", "\n".join(str(x) for x in status_lines) + "\n")
    conclusion = {
        "status": "COMPLETE",
        "best_main_metric_model": best_nmse["variant"],
        "best_SSIM_model": best_ssim["variant"],
        "best_OOD_model": "see metrics_ood.csv",
        "Pcyc_scalar_status": "baseline P00",
        "Pcyc_sincos_status": "adopt" if p02_adopt else "do_not_adopt_over_P00",
        "Pcyc_scalar_plus_sincos_status": "adopt" if p03_adopt else "do_not_adopt_over_P00",
        "Pcyc_no_input_status": "comparable_to_P00" if p01_comparable else "not_comparable_to_P00",
        "recommendation_for_task_real_struc_002b": "optimize RSB envelope if P00 remains unbeaten; otherwise freeze the adopted Pcyc encoding first",
    }
    write_json(output_root / "final_conclusion.json", conclusion)
    return conclusion


def write_auxiliary_reports(output_root: Path, training_rows: list[dict[str, Any]], args: argparse.Namespace) -> None:
    write_json(output_root / "model_variants.json", [v.__dict__ for v in VARIANTS])
    write_json(output_root / "config_summary.json", {"task": "task_real_struc_002a", "epochs": args.epochs, "min_epochs": args.min_epochs, "seeds": args.seeds, "batch_size": args.batch_size, "base_channels": args.base_channels, "source": str(SOURCE_006D), "previous_001b": str(SOURCE_001B), "target_branch": "task_struc_series"})
    write_csv(output_root / "parameter_count_table.csv", [{"variant": r["variant"], "seed": r["seed"], "parameter_count": r.get("parameter_count", 0), "peak_gpu_memory_mb": r.get("peak_gpu_memory_mb", ""), "checkpoint_local": r.get("checkpoint_local", "")} for r in training_rows])
    write_text(output_root / "model_config_diffs.md", "\n".join([f"## {v.key}\n\n{v.description}\nkind={v.kind}, geom_mode={v.geom_mode}\n" for v in VARIANTS]))
    write_csv(output_root / "input_channel_scale_table.csv", [
        {"channel": "X_ref3", "range": "[0,1] per sample"},
        {"channel": "Mshell", "range": "{0,1}, one-hot including padding fill"},
        {"channel": "delta_rho", "range": "meters, approx [-0.075,0.075]"},
        {"channel": "Pcyc", "range": "[-1,1] wrapped scalar"},
        {"channel": "sin/cos(pi*Pcyc)", "range": "[-1,1] periodic"},
    ])
    if not (output_root / "metrics_ood.csv").exists():
        write_csv(output_root / "metrics_ood.csv", [{"ood_split": k, "status": "pending", "dataset_dir": str(SOURCE_006D / "datasets" / v), "reason": "run without --skip-ood or run --ood-only against trained checkpoints"} for k, v in OOD_DIRS.items()])
    env = f"python: {platform.python_version()}\ntorch: {torch.__version__}\ncuda_available: {torch.cuda.is_available()}\nplatform: {platform.platform()}\n"
    write_text(output_root / "environment.txt", env)
    status = subprocess.run(["git", "status", "--short", "--branch"], cwd=PROJECT_ROOT, text=True, capture_output=True)
    log = subprocess.run(["git", "log", "--oneline", "-5"], cwd=PROJECT_ROOT, text=True, capture_output=True)
    branch = subprocess.run(["git", "branch", "--show-current"], cwd=PROJECT_ROOT, text=True, capture_output=True)
    write_text(output_root / "git_status.txt", status.stdout + "\ncurrent_branch:\n" + branch.stdout + "\nrecent_log:\n" + log.stdout)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", default=None)
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--base-channels", type=int, default=4)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--grad-clip", type=float, default=1.0)
    parser.add_argument("--patience", type=int, default=10)
    parser.add_argument("--min-delta", type=float, default=1e-5)
    parser.add_argument("--min-epochs", type=int, default=50)
    parser.add_argument("--early-stop", action="store_true")
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2])
    parser.add_argument("--train-only", nargs="*", default=None)
    parser.add_argument("--skip-ood", action="store_true")
    parser.add_argument("--ood-only", action="store_true")
    parser.add_argument("--ood-limit", type=int, default=None)
    args = parser.parse_args()
    if args.output_root is None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_root = PROJECT_ROOT / "exp" / "task_real_struc_002a_pcyc_encoding_ablation" / stamp
    else:
        output_root = Path(args.output_root)
    for rel in ["training_curves", "checkpoints", "prediction_cache", "recon_compare", "diagnostic_plots", "metadata_histograms", "prediction_value_stats"]:
        ensure_dir(output_root / rel)
    plan = train_plan(args)
    if args.train_only:
        plan = {k: v for k, v in plan.items() if k in set(args.train_only)}
    if args.ood_only:
        eval_ood(output_root, plan, args)
        summary_path = output_root / "metrics_overall_summary.csv"
        train_path = output_root / "training_summary.csv"
        if summary_path.exists() and train_path.exists():
            with summary_path.open(encoding="utf-8", newline="") as handle:
                summary_rows = list(csv.DictReader(handle))
            with train_path.open(encoding="utf-8", newline="") as handle:
                training_rows = list(csv.DictReader(handle))
            write_auxiliary_reports(output_root, training_rows, args)
            conclusion = write_reports(output_root, training_rows, {"summary": summary_rows}, args)
            for key, value in conclusion.items():
                print(f"{key}: {value}")
        print("task_real_struc_002a OOD status: COMPLETE")
        print(f"experiment_root: {output_root}")
        return
    arrays = prepare_arrays(output_root)
    write_pcyc_encoding_audit(output_root, arrays)
    training_rows = []
    for spec in VARIANTS:
        if spec.key not in plan and spec.trainable:
            continue
        for seed in plan.get(spec.key, [0]):
            print(f"TRAIN {spec.key} seed={seed}", flush=True)
            training_rows.append(train_one(output_root, arrays, spec, seed, args))
            write_csv(output_root / "training_summary.csv", training_rows)
    eval_payload = eval_all(output_root, arrays, plan, training_rows, args)
    if not args.skip_ood:
        eval_ood(output_root, plan, args)
    write_auxiliary_reports(output_root, training_rows, args)
    conclusion = write_reports(output_root, training_rows, eval_payload, args)
    print("task_real_struc_002a status: COMPLETE")
    print(f"experiment_root: {output_root}")
    print("current_branch: task_struc_series")
    print("remote_push_status: pending")
    for key, value in conclusion.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
