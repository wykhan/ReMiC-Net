from __future__ import annotations

import argparse
import csv
import json
import math
import shutil
import subprocess
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn.functional as F
from torch import nn
from torch.utils.data import DataLoader, Dataset

from workspace.common.io_utils import ensure_dir, read_json, write_json, write_text
from workspace.common.remic_metadata import EPSILON_M, FC_HZ, K2W_C_RAD_PER_M, LAMBDA_C_M, REF3_RADII_M, build_remic_metadata, write_metadata_npz
from workspace.eval.metrics_3d import nmse, psnr, ssim_global
from workspace.models.remicnet_rsb_film import ReMiCNetRSBFiLM, ResidualUNet3DBaseline
from workspace.recon.cyl_fast_reference_engine import reconstruct_cylindrical_reference


PROJECT_ROOT = Path("/home/superws/2026_Projects/Codex_reference_plane_real")
SOURCE_006D = PROJECT_ROOT / "exp" / "task_real_006d_800_formal" / "20260419_112717"
SOURCE_006E = PROJECT_ROOT / "exp" / "task_real_006e_comprehensive_eval" / "20260419_190046"
SOURCE_007 = PROJECT_ROOT / "exp" / "task_real_007_physics_consistency" / "20260419_201254"
SOURCE_007B = PROJECT_ROOT / "exp" / "task_real_007b_geometry_aware_consistency" / "20260419_204405"
TARGET_SHAPE = (24, 24, 24)
HARD_FAMILIES = ["point_cluster", "line", "L-shape"]
PCT_BINS = [0.0, 0.1, 0.25, 0.5, 0.75, 1.01]
DELTA_BINS = [0.0, 0.01, 0.025, 0.04, 0.055, 0.076]
OOD_DATASET_DIRS = {
    "Unseen-Parameter OOD": "unseen_param_ood",
    "Leave-One-Family-Out Focused OOD": "leave_one_family_out_ood",
    "Random-ET OOD": "random_et_ood",
}
OOD_OUTPUT_FILES = {
    "Unseen-Parameter OOD": "metrics_baseline_vs_remicnet_unseen_param_ood.csv",
    "Leave-One-Family-Out Focused OOD": "metrics_baseline_vs_remicnet_leave_one_family_out_ood.csv",
    "Random-ET OOD": "metrics_baseline_vs_remicnet_random_et_ood.csv",
}
OOD_SUMMARY_FILES_006E = {
    "Unseen-Parameter OOD": SOURCE_006E / "ood_unseen_param_metrics_all_methods.csv",
    "Leave-One-Family-Out Focused OOD": SOURCE_006E / "ood_leave_one_family_out_metrics_all_methods.csv",
    "Random-ET OOD": SOURCE_006E / "ood_random_et_metrics_all_methods.csv",
}


def _stage_log(output_root: Path, stage: str, text: str) -> None:
    ensure_dir(output_root / "logs")
    with (output_root / "logs" / f"{stage}.log").open("a", encoding="utf-8") as handle:
        handle.write(text.rstrip() + "\n")


def _ensure_dirs(output_root: Path) -> None:
    for rel in [
        "logs",
        "checkpoints/baseline",
        "checkpoints/remicnet",
        "viz/progress/curves",
        "viz/progress/recon_compare",
        "viz/progress/slices",
        "viz/progress/scene_3d",
        "viz/paper_candidates/curves",
        "viz/paper_candidates/qualitative",
        "viz/paper_candidates/tables_as_figs",
        "viz/paper_candidates/supplementary",
        "viz/manifest",
        "metadata_cache/main_800_100_100",
        "metadata_cache/unseen_param_ood",
        "metadata_cache/leave_one_family_out_ood",
        "metadata_cache/random_et_ood",
        "prediction_cache/main",
        "prediction_cache/ood",
    ]:
        ensure_dir(output_root / rel)


def _normalize_pair(coarse: np.ndarray, gt: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    coarse = coarse.astype(np.float32)
    gt = gt.astype(np.float32)
    scale = max(float(np.max(gt)), float(np.max(coarse)), 1.0e-6)
    return coarse / scale, gt / scale, scale


def _fit_to_shape(volume: np.ndarray) -> np.ndarray:
    output = np.zeros(TARGET_SHAPE, dtype=np.float32)
    src_shape = volume.shape
    copy_shape = tuple(min(src_shape[i], TARGET_SHAPE[i]) for i in range(3))
    src_start = tuple(max((src_shape[i] - copy_shape[i]) // 2, 0) for i in range(3))
    dst_start = tuple(max((TARGET_SHAPE[i] - copy_shape[i]) // 2, 0) for i in range(3))
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


def _load_npz_volume(path: Path) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    payload = np.load(path)
    arrays = {name: payload[name] for name in payload.files}
    return arrays["volume"], arrays


def _bool_support_mask(gt: np.ndarray) -> np.ndarray:
    return gt > (0.05 * max(float(np.max(gt)), 1.0e-6))


def _summarize_geometry(metadata: dict[str, np.ndarray], gt_norm: np.ndarray) -> dict[str, float]:
    support = _bool_support_mask(gt_norm)
    delta = np.abs(metadata["delta_rho_raw"][0])
    pcyc = np.abs(metadata["pcyc"][0])
    if not np.any(support):
        support = gt_norm > 0
    if not np.any(support):
        support = np.ones_like(gt_norm, dtype=bool)
    return {
        "support_mean_abs_delta_rho": float(np.mean(delta[support])),
        "support_mean_abs_pcyc": float(np.mean(pcyc[support])),
        "support_fraction_pcyc_gt_quarter": float(np.mean((pcyc[support] > 0.25).astype(np.float32))),
        "support_max_abs_pcyc": float(np.max(pcyc[support])),
        "support_max_abs_delta_rho": float(np.max(delta[support])),
    }


class ReMiCDataset(Dataset):
    def __init__(self, rows: list[dict[str, Any]], source_root: Path, output_root: Path) -> None:
        self.rows = rows
        self.source_root = source_root
        self.output_root = output_root

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int) -> dict[str, Any]:
        row = self.rows[index]
        coarse_npz = np.load(self.source_root / row["ref3_path"])
        gt_npz = np.load(self.source_root / row["gt_path"])
        coarse, gt, _ = _normalize_pair(_fit_to_shape(coarse_npz["volume"]), _fit_to_shape(gt_npz["volume"]))
        metadata_npz = np.load(self.output_root / row["metadata_rel_path"])
        residual = gt - coarse
        return {
            "input": torch.from_numpy(coarse[None, ...]),
            "target": torch.from_numpy(residual[None, ...]),
            "coarse": torch.from_numpy(coarse[None, ...]),
            "gt": torch.from_numpy(gt[None, ...]),
            "geometry": torch.from_numpy(np.concatenate([metadata_npz["mshell"], metadata_npz["delta_rho_raw"], metadata_npz["pcyc"]], axis=0)),
            "m_rsb": torch.from_numpy(metadata_npz["m_rsb"]),
            "sample_id": row["sample_id"],
            "family": row["family"],
        }


def _collate(batch: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "input": torch.stack([item["input"] for item in batch], dim=0),
        "target": torch.stack([item["target"] for item in batch], dim=0),
        "coarse": torch.stack([item["coarse"] for item in batch], dim=0),
        "gt": torch.stack([item["gt"] for item in batch], dim=0),
        "geometry": torch.stack([item["geometry"] for item in batch], dim=0),
        "m_rsb": torch.stack([item["m_rsb"] for item in batch], dim=0),
        "sample_id": [item["sample_id"] for item in batch],
        "family": [item["family"] for item in batch],
    }


def _select_rows(rows: list[dict[str, Any]], split: str) -> list[dict[str, Any]]:
    return [row for row in rows if row["split"] == split]


def _loss_fn(delta_pred: torch.Tensor, delta_target: torch.Tensor) -> torch.Tensor:
    return F.l1_loss(delta_pred, delta_target)


def _run_epoch(
    model: nn.Module,
    loader: DataLoader,
    device: torch.device,
    optimizer: torch.optim.Optimizer | None,
    model_kind: str,
) -> float:
    train_mode = optimizer is not None
    model.train(train_mode)
    losses: list[float] = []
    for batch in loader:
        inputs = batch["input"].to(device)
        targets = batch["target"].to(device)
        if model_kind == "remicnet":
            preds = model(inputs, batch["geometry"].to(device), batch["m_rsb"].to(device))
        else:
            preds = model(inputs)
        loss = _loss_fn(preds, targets)
        if train_mode:
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        losses.append(float(loss.item()))
    return float(np.mean(losses)) if losses else 0.0


def _instantiate_model(kind: str) -> nn.Module:
    if kind == "baseline":
        return ResidualUNet3DBaseline(base_channels=8)
    if kind == "remicnet":
        return ReMiCNetRSBFiLM(base_channels=8, alpha_gamma=0.5, alpha_beta=0.1)
    raise ValueError(f"Unsupported model kind: {kind}")


def _train_model(
    output_root: Path,
    rows: list[dict[str, Any]],
    model_kind: str,
    epochs: int,
    batch_size: int,
    lr: float,
) -> dict[str, Any]:
    train_rows = _select_rows(rows, "train")
    val_rows = _select_rows(rows, "val")
    source_root = SOURCE_006D
    train_loader = DataLoader(ReMiCDataset(train_rows, source_root, output_root), batch_size=batch_size, shuffle=True, collate_fn=_collate)
    val_loader = DataLoader(ReMiCDataset(val_rows, source_root, output_root), batch_size=batch_size, shuffle=False, collate_fn=_collate)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = _instantiate_model(model_kind).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    history = {"train_losses": [], "val_losses": []}
    best_val = float("inf")
    checkpoint_dir = ensure_dir(output_root / "checkpoints" / model_kind)
    best_path = checkpoint_dir / "best.pt"
    for epoch in range(epochs):
        train_loss = _run_epoch(model, train_loader, device, optimizer, model_kind)
        val_loss = _run_epoch(model, val_loader, device, None, model_kind)
        history["train_losses"].append(train_loss)
        history["val_losses"].append(val_loss)
        _stage_log(output_root, f"train_{model_kind}", f"epoch={epoch + 1} train_loss={train_loss:.6f} val_loss={val_loss:.6f}")
        if val_loss < best_val:
            best_val = val_loss
            torch.save({"model_state": model.state_dict(), "model_kind": model_kind, "target_shape": TARGET_SHAPE}, best_path)
    return {
        "model_kind": model_kind,
        "epochs": epochs,
        "batch_size": batch_size,
        "lr": lr,
        "best_val_loss": best_val,
        "history": history,
        "best_checkpoint": str(best_path.relative_to(output_root)),
    }


def _load_trained_model(output_root: Path, model_kind: str) -> nn.Module:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = _instantiate_model(model_kind).to(device)
    ckpt = torch.load(output_root / "checkpoints" / model_kind / "best.pt", map_location=device)
    model.load_state_dict(ckpt["model_state"])
    model.eval()
    return model


def _render_curve(output_root: Path, metrics: dict[str, Any], model_kind: str) -> None:
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(metrics["history"]["train_losses"], label=f"{model_kind} train")
    ax.plot(metrics["history"]["val_losses"], label=f"{model_kind} val")
    ax.set_xlabel("epoch")
    ax.set_ylabel("L1 residual loss")
    ax.set_title(f"{model_kind} train/val curves")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_root / "viz" / "progress" / "curves" / f"{model_kind}_training_curves.png", dpi=180)
    plt.close(fig)


def _read_bp_runtime_means() -> dict[str, float]:
    main_rows = list(csv.DictReader((SOURCE_006E / "main_test_metrics_all_methods.csv").open("r", encoding="utf-8")))
    result = {}
    for row in main_rows:
        if row["method"] == "BP":
            result["Main Test"] = float(row["runtime_mean"])
    for dataset_name, path in OOD_SUMMARY_FILES_006E.items():
        rows = list(csv.DictReader(path.open("r", encoding="utf-8")))
        for row in rows:
            if row["method"] == "BP":
                result[dataset_name] = float(row["runtime_mean"])
    return result


def _build_metadata_rows(output_root: Path) -> list[dict[str, Any]]:
    manifest = read_json(SOURCE_006D / "learning_handoff_manifest_main_800_100_100.json")
    rows = []
    for row in manifest["samples"]:
        ref3_npz = np.load(SOURCE_006D / row["ref3_path"])
        metadata = build_remic_metadata(ref3_npz["x_values"], ref3_npz["y_values"], ref3_npz["z_values"], TARGET_SHAPE)
        rel_path = Path("metadata_cache") / row["dataset_source"] / f"{row['sample_id']}_remic_meta.npz"
        write_metadata_npz(output_root / rel_path, metadata)
        rows.append({**row, "metadata_rel_path": str(rel_path)})
    payload = {
        "task": "task_real_008",
        "source_manifest": str((SOURCE_006D / "learning_handoff_manifest_main_800_100_100.json").relative_to(PROJECT_ROOT)),
        "delta_rho_input": "raw_meter",
        "reference_radii_m": [float(x) for x in REF3_RADII_M],
        "fc_hz": FC_HZ,
        "lambda_c_m": LAMBDA_C_M,
        "k2w_c_rad_per_m": float(K2W_C_RAD_PER_M),
        "epsilon_m": float(EPSILON_M),
        "num_samples": len(rows),
        "metadata_rows": rows,
    }
    write_json(output_root / "remicnet_input_manifest_008.json", payload)
    _stage_log(output_root, "build_inputs", f"cached metadata for samples={len(rows)} delta_rho_input=raw_meter")
    return rows


def _write_baseline_manifest(output_root: Path) -> None:
    payload = {
        "baseline_source_root": str(SOURCE_006D),
        "baseline_prior_checkpoint_006d": str(SOURCE_006D / "checkpoints" / "frozen_mainline" / "best.pt"),
        "baseline_prior_report_006d": str(SOURCE_006D / "task_real_006d_report.md"),
        "baseline_prior_report_006e": str(SOURCE_006E / "task_real_006e_report.md"),
        "baseline_for_task_008": "retrained residual 3D U-Net under task_real_008 frozen protocol",
        "why_not_directly_reuse_006d_checkpoint": "006d checkpoint was trained as direct image prediction, while task_real_008 freezes residual-only output for both baseline and ReMiC-Net.",
    }
    write_json(output_root / "baseline_reference_manifest_008.json", payload)


def _load_main_ref3_runtime_maps() -> tuple[dict[str, float], dict[str, float]]:
    payload = read_json(SOURCE_006D / "mainline_vs_baselines_metrics.json")
    ref3_runtime = {}
    bp_runtime = {}
    for row in payload["per_sample"]:
        if row["method"] == "ref3":
            ref3_runtime[row["sample_id"]] = float(row["wall_time_sec"])
        elif row["method"] == "BP":
            bp_runtime[row["sample_id"]] = float(row["wall_time_sec"])
    return ref3_runtime, bp_runtime


def _evaluate_main(output_root: Path, rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    baseline = _load_trained_model(output_root, "baseline")
    remic = _load_trained_model(output_root, "remicnet")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ref3_runtime, bp_runtime = _load_main_ref3_runtime_maps()
    records = []
    preds_dir = ensure_dir(output_root / "prediction_cache" / "main")
    with torch.no_grad():
        for row in _select_rows(rows, "test"):
            coarse_npz = np.load(SOURCE_006D / row["ref3_path"])
            gt_npz = np.load(SOURCE_006D / row["gt_path"])
            coarse, gt, _ = _normalize_pair(_fit_to_shape(coarse_npz["volume"]), _fit_to_shape(gt_npz["volume"]))
            meta_npz = np.load(output_root / row["metadata_rel_path"])
            geom = np.concatenate([meta_npz["mshell"], meta_npz["delta_rho_raw"], meta_npz["pcyc"]], axis=0)
            input_tensor = torch.from_numpy(coarse[None, None, ...]).to(device)
            geom_tensor = torch.from_numpy(geom[None, ...]).to(device)
            m_rsb = torch.from_numpy(meta_npz["m_rsb"][None, ...]).to(device)
            t0 = time.perf_counter()
            delta_base = baseline(input_tensor)
            base_runtime = ref3_runtime[row["sample_id"]] + (time.perf_counter() - t0)
            t1 = time.perf_counter()
            delta_remic = remic(input_tensor, geom_tensor, m_rsb)
            remic_runtime = ref3_runtime[row["sample_id"]] + (time.perf_counter() - t1)
            x_base = torch.clamp(input_tensor + delta_base, min=0.0).cpu().numpy()[0, 0]
            x_remic = torch.clamp(input_tensor + delta_remic, min=0.0).cpu().numpy()[0, 0]
            geometry_summary = _summarize_geometry(meta_npz, gt)
            np.savez_compressed(preds_dir / f"{row['sample_id']}_compare.npz", coarse=coarse, gt=gt, baseline=x_base.astype(np.float32), remicnet=x_remic.astype(np.float32))
            records.append(
                {
                    "dataset": "Main Test",
                    "sample_id": row["sample_id"],
                    "family": row["family"],
                    "baseline_nmse": nmse(x_base, gt),
                    "baseline_psnr": psnr(x_base, gt),
                    "baseline_ssim": ssim_global(x_base, gt),
                    "baseline_runtime": base_runtime,
                    "remicnet_nmse": nmse(x_remic, gt),
                    "remicnet_psnr": psnr(x_remic, gt),
                    "remicnet_ssim": ssim_global(x_remic, gt),
                    "remicnet_runtime": remic_runtime,
                    "bp_runtime": bp_runtime[row["sample_id"]],
                    **geometry_summary,
                }
            )
    summary = _write_dataset_summary(output_root / "metrics_baseline_vs_remicnet_main.csv", "Main Test", records)
    _stage_log(output_root, "eval_main", f"evaluated main test samples={len(records)}")
    return records, summary


def _prepare_ood_ref3(output_root: Path, dataset_dir_name: str, row: dict[str, Any]) -> tuple[np.ndarray, np.ndarray, np.ndarray, float, dict[str, np.ndarray]]:
    dataset_root = SOURCE_006D / "datasets" / dataset_dir_name
    gt_npz = np.load(dataset_root / row["gt_volume_path"])
    gt_raw = _fit_to_shape(gt_npz["volume"])
    scene_path = dataset_root / row["scene_path"]
    echo_path = dataset_root / "dataset" / "echoes" / f"{row['sample_id']}_echo_sparse.npz"
    started = time.perf_counter()
    recon = reconstruct_cylindrical_reference(scene_path, echo_path, "ref3")
    ref3_runtime = time.perf_counter() - started
    coarse_raw = _fit_to_shape(recon["volume"])
    coarse, gt, _ = _normalize_pair(coarse_raw, gt_raw)
    meta_rel = Path("metadata_cache") / dataset_dir_name / f"{row['sample_id']}_remic_meta.npz"
    meta_path = output_root / meta_rel
    if not meta_path.exists():
        metadata = build_remic_metadata(recon["x_values"], recon["y_values"], recon["z_values"], TARGET_SHAPE)
        write_metadata_npz(meta_path, metadata)
    meta_npz = np.load(meta_path)
    return coarse, gt, np.concatenate([meta_npz["mshell"], meta_npz["delta_rho_raw"], meta_npz["pcyc"]], axis=0), ref3_runtime, meta_npz


def _evaluate_ood_dataset(output_root: Path, dataset_name: str, bp_runtime_mean: float) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    baseline = _load_trained_model(output_root, "baseline")
    remic = _load_trained_model(output_root, "remicnet")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    dataset_dir_name = OOD_DATASET_DIRS[dataset_name]
    rows = read_json(SOURCE_006D / "datasets" / dataset_dir_name / "dataset" / "index.json")
    records = []
    preds_dir = ensure_dir(output_root / "prediction_cache" / "ood" / dataset_dir_name)
    with torch.no_grad():
        for row in rows:
            coarse, gt, geom, ref3_runtime, meta_npz = _prepare_ood_ref3(output_root, dataset_dir_name, row)
            input_tensor = torch.from_numpy(coarse[None, None, ...]).to(device)
            geom_tensor = torch.from_numpy(geom[None, ...]).to(device)
            m_rsb = torch.from_numpy(meta_npz["m_rsb"][None, ...]).to(device)
            t0 = time.perf_counter()
            delta_base = baseline(input_tensor)
            base_runtime = ref3_runtime + (time.perf_counter() - t0)
            t1 = time.perf_counter()
            delta_remic = remic(input_tensor, geom_tensor, m_rsb)
            remic_runtime = ref3_runtime + (time.perf_counter() - t1)
            x_base = torch.clamp(input_tensor + delta_base, min=0.0).cpu().numpy()[0, 0]
            x_remic = torch.clamp(input_tensor + delta_remic, min=0.0).cpu().numpy()[0, 0]
            geometry_summary = _summarize_geometry(meta_npz, gt)
            np.savez_compressed(preds_dir / f"{row['sample_id']}_compare.npz", coarse=coarse, gt=gt, baseline=x_base.astype(np.float32), remicnet=x_remic.astype(np.float32))
            records.append(
                {
                    "dataset": dataset_name,
                    "sample_id": row["sample_id"],
                    "family": row.get("family", "random_et"),
                    "baseline_nmse": nmse(x_base, gt),
                    "baseline_psnr": psnr(x_base, gt),
                    "baseline_ssim": ssim_global(x_base, gt),
                    "baseline_runtime": base_runtime,
                    "remicnet_nmse": nmse(x_remic, gt),
                    "remicnet_psnr": psnr(x_remic, gt),
                    "remicnet_ssim": ssim_global(x_remic, gt),
                    "remicnet_runtime": remic_runtime,
                    "bp_runtime": bp_runtime_mean,
                    **geometry_summary,
                }
            )
    summary = _write_dataset_summary(output_root / OOD_OUTPUT_FILES[dataset_name], dataset_name, records)
    _stage_log(output_root, f"eval_{dataset_dir_name}", f"evaluated samples={len(records)}")
    return records, summary


def _write_dataset_summary(path: Path, dataset_name: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    baseline_runtime_mean = float(np.mean([row["baseline_runtime"] for row in rows]))
    remic_runtime_mean = float(np.mean([row["remicnet_runtime"] for row in rows]))
    bp_runtime_mean = float(np.mean([row["bp_runtime"] for row in rows]))
    summary_rows = [
        {
            "dataset": dataset_name,
            "method": "Baseline-U-Net",
            "NMSE_mean": float(np.mean([row["baseline_nmse"] for row in rows])),
            "PSNR_mean": float(np.mean([row["baseline_psnr"] for row in rows])),
            "SSIM_mean": float(np.mean([row["baseline_ssim"] for row in rows])),
            "runtime_mean": baseline_runtime_mean,
            "speedup_vs_BP": float(bp_runtime_mean / baseline_runtime_mean) if baseline_runtime_mean > 0 else 0.0,
            "num_samples": len(rows),
        },
        {
            "dataset": dataset_name,
            "method": "ReMiC-Net",
            "NMSE_mean": float(np.mean([row["remicnet_nmse"] for row in rows])),
            "PSNR_mean": float(np.mean([row["remicnet_psnr"] for row in rows])),
            "SSIM_mean": float(np.mean([row["remicnet_ssim"] for row in rows])),
            "runtime_mean": remic_runtime_mean,
            "speedup_vs_BP": float(bp_runtime_mean / remic_runtime_mean) if remic_runtime_mean > 0 else 0.0,
            "num_samples": len(rows),
        },
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)
    return summary_rows


def _bin_label(lower: float, upper: float, is_last: bool = False) -> str:
    return f"[{lower:.3f}, {upper:.3f}{']' if is_last else ')'}"


def _group_metric_rows(all_rows: list[dict[str, Any]], metric_key: str, bins: list[float], out_path: Path) -> list[dict[str, Any]]:
    grouped = []
    for idx in range(len(bins) - 1):
        lower = bins[idx]
        upper = bins[idx + 1]
        bucket = [row for row in all_rows if lower <= row[metric_key] < upper or (idx == len(bins) - 2 and lower <= row[metric_key] <= upper)]
        if not bucket:
            continue
        grouped.append(
            {
                "bucket": _bin_label(lower, upper, idx == len(bins) - 2),
                "num_samples": len(bucket),
                "baseline_nmse_mean": float(np.mean([row["baseline_nmse"] for row in bucket])),
                "remicnet_nmse_mean": float(np.mean([row["remicnet_nmse"] for row in bucket])),
                "baseline_psnr_mean": float(np.mean([row["baseline_psnr"] for row in bucket])),
                "remicnet_psnr_mean": float(np.mean([row["remicnet_psnr"] for row in bucket])),
                "baseline_ssim_mean": float(np.mean([row["baseline_ssim"] for row in bucket])),
                "remicnet_ssim_mean": float(np.mean([row["remicnet_ssim"] for row in bucket])),
            }
        )
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(grouped[0].keys()) if grouped else ["bucket", "num_samples"])
        writer.writeheader()
        if grouped:
            writer.writerows(grouped)
    return grouped


def _quarter_pi_groups(all_rows: list[dict[str, Any]], out_path: Path) -> list[dict[str, Any]]:
    low = [row for row in all_rows if row["support_mean_abs_pcyc"] <= 0.25]
    high = [row for row in all_rows if row["support_mean_abs_pcyc"] > 0.25]
    rows = []
    for label, bucket in [("|Pcyc|<=0.25", low), ("|Pcyc|>0.25", high)]:
        if not bucket:
            continue
        rows.append(
            {
                "bucket": label,
                "num_samples": len(bucket),
                "baseline_nmse_mean": float(np.mean([row["baseline_nmse"] for row in bucket])),
                "remicnet_nmse_mean": float(np.mean([row["remicnet_nmse"] for row in bucket])),
                "baseline_psnr_mean": float(np.mean([row["baseline_psnr"] for row in bucket])),
                "remicnet_psnr_mean": float(np.mean([row["remicnet_psnr"] for row in bucket])),
                "baseline_ssim_mean": float(np.mean([row["baseline_ssim"] for row in bucket])),
                "remicnet_ssim_mean": float(np.mean([row["remicnet_ssim"] for row in bucket])),
            }
        )
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else ["bucket", "num_samples"])
        writer.writeheader()
        if rows:
            writer.writerows(rows)
    return rows


def _hardest_family_rows(all_rows: list[dict[str, Any]], out_path: Path) -> list[dict[str, Any]]:
    rows = []
    for dataset in sorted({row["dataset"] for row in all_rows}):
        for family in HARD_FAMILIES:
            bucket = [row for row in all_rows if row["dataset"] == dataset and row["family"] == family]
            if not bucket:
                continue
            rows.append(
                {
                    "dataset": dataset,
                    "family": family,
                    "num_samples": len(bucket),
                    "baseline_nmse_mean": float(np.mean([row["baseline_nmse"] for row in bucket])),
                    "remicnet_nmse_mean": float(np.mean([row["remicnet_nmse"] for row in bucket])),
                    "baseline_psnr_mean": float(np.mean([row["baseline_psnr"] for row in bucket])),
                    "remicnet_psnr_mean": float(np.mean([row["remicnet_psnr"] for row in bucket])),
                    "baseline_ssim_mean": float(np.mean([row["baseline_ssim"] for row in bucket])),
                    "remicnet_ssim_mean": float(np.mean([row["remicnet_ssim"] for row in bucket])),
                }
            )
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else ["dataset", "family", "num_samples"])
        writer.writeheader()
        if rows:
            writer.writerows(rows)
    return rows


def _plot_summary_bars(output_root: Path, main_summary: list[dict[str, Any]], ood_summaries: dict[str, list[dict[str, Any]]]) -> None:
    datasets = ["Main Test"] + list(ood_summaries.keys())
    baseline_nmse = []
    remic_nmse = []
    baseline_runtime = []
    remic_runtime = []
    baseline_speed = []
    remic_speed = []
    for dataset in datasets:
        rows = main_summary if dataset == "Main Test" else ood_summaries[dataset]
        lookup = {row["method"]: row for row in rows}
        baseline_nmse.append(float(lookup["Baseline-U-Net"]["NMSE_mean"]))
        remic_nmse.append(float(lookup["ReMiC-Net"]["NMSE_mean"]))
        baseline_runtime.append(float(lookup["Baseline-U-Net"]["runtime_mean"]))
        remic_runtime.append(float(lookup["ReMiC-Net"]["runtime_mean"]))
        baseline_speed.append(float(lookup["Baseline-U-Net"]["speedup_vs_BP"]))
        remic_speed.append(float(lookup["ReMiC-Net"]["speedup_vs_BP"]))

    x = np.arange(len(datasets))
    width = 0.36
    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    axes[0].bar(x - width / 2, baseline_nmse, width, label="Baseline-U-Net")
    axes[0].bar(x + width / 2, remic_nmse, width, label="ReMiC-Net")
    axes[0].set_xticks(x, datasets, rotation=20, ha="right")
    axes[0].set_ylabel("NMSE mean")
    axes[0].set_title("Baseline vs ReMiC-Net metrics")
    axes[0].legend()
    axes[1].bar(x - width / 2, baseline_runtime, width, label="Baseline-U-Net")
    axes[1].bar(x + width / 2, remic_runtime, width, label="ReMiC-Net")
    axes[1].set_xticks(x, datasets, rotation=20, ha="right")
    axes[1].set_ylabel("runtime mean (s)")
    axes[1].set_title("Runtime")
    axes[2].bar(x - width / 2, baseline_speed, width, label="Baseline-U-Net")
    axes[2].bar(x + width / 2, remic_speed, width, label="ReMiC-Net")
    axes[2].set_xticks(x, datasets, rotation=20, ha="right")
    axes[2].set_ylabel("speedup vs BP")
    axes[2].set_title("Speedup")
    fig.tight_layout()
    fig.savefig(output_root / "viz" / "progress" / "curves" / "baseline_vs_remicnet_ood_metrics.png", dpi=180)
    fig.savefig(output_root / "viz" / "paper_candidates" / "curves" / "fig_remic_ood_metrics.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 4))
    methods = ["Baseline-U-Net", "ReMiC-Net"]
    psnr_vals = [main_summary[0]["PSNR_mean"], main_summary[1]["PSNR_mean"]]
    ssim_vals = [main_summary[0]["SSIM_mean"], main_summary[1]["SSIM_mean"]]
    ax.bar(np.arange(2) - 0.15, psnr_vals, 0.3, label="PSNR")
    ax.bar(np.arange(2) + 0.15, ssim_vals, 0.3, label="SSIM")
    ax.set_xticks(np.arange(2), methods)
    ax.set_title("Main Test metrics")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_root / "viz" / "progress" / "curves" / "baseline_vs_remicnet_main_metrics.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(np.arange(2), [baseline_runtime[0], remic_runtime[0]], 0.5)
    ax.set_xticks(np.arange(2), methods)
    ax.set_ylabel("runtime mean (s)")
    ax.set_title("Main Test runtime")
    fig.tight_layout()
    fig.savefig(output_root / "viz" / "progress" / "curves" / "baseline_vs_remicnet_runtime_speedup.png", dpi=180)
    plt.close(fig)


def _plot_grouped_curve(output_root: Path, rows: list[dict[str, Any]], filename: str, title: str, ylabel: str = "NMSE mean") -> None:
    fig, ax = plt.subplots(figsize=(7, 4))
    xs = np.arange(len(rows))
    ax.plot(xs, [float(row["baseline_nmse_mean"]) for row in rows], marker="o", label="Baseline-U-Net")
    ax.plot(xs, [float(row["remicnet_nmse_mean"]) for row in rows], marker="o", label="ReMiC-Net")
    ax.set_xticks(xs, [row["bucket"] for row in rows], rotation=30, ha="right")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_root / "viz" / "progress" / "curves" / filename, dpi=180)
    plt.close(fig)


def _plot_hardest_families(output_root: Path, rows: list[dict[str, Any]]) -> None:
    main_rows = [row for row in rows if row["dataset"] == "Main Test"]
    fig, ax = plt.subplots(figsize=(7, 4))
    x = np.arange(len(main_rows))
    ax.bar(x - 0.18, [float(row["baseline_nmse_mean"]) for row in main_rows], 0.36, label="Baseline-U-Net")
    ax.bar(x + 0.18, [float(row["remicnet_nmse_mean"]) for row in main_rows], 0.36, label="ReMiC-Net")
    ax.set_xticks(x, [row["family"] for row in main_rows])
    ax.set_ylabel("NMSE mean")
    ax.set_title("Hardest families on Main Test")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_root / "viz" / "progress" / "curves" / "baseline_vs_remicnet_hardest_families.png", dpi=180)
    plt.close(fig)


def _panel_case(output_root: Path, row: dict[str, Any], filename: str, title: str) -> None:
    dataset_dir = "main" if row["dataset"] == "Main Test" else f"ood/{OOD_DATASET_DIRS[row['dataset']]}"
    compare_npz = np.load(output_root / "prediction_cache" / dataset_dir / f"{row['sample_id']}_compare.npz")
    arrays = [compare_npz["coarse"], compare_npz["baseline"], compare_npz["remicnet"], compare_npz["gt"]]
    labels = ["Ref3", "Baseline-U-Net", "ReMiC-Net", "GT"]
    z_idx = arrays[0].shape[0] // 2
    vmax = max(float(np.max(arr)) for arr in arrays)
    fig, axes = plt.subplots(1, 4, figsize=(12, 3))
    for ax, arr, label in zip(axes, arrays, labels):
        ax.imshow(arr[z_idx], cmap="viridis", vmin=0.0, vmax=vmax)
        ax.set_title(label)
        ax.axis("off")
    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(output_root / "viz" / "paper_candidates" / "qualitative" / filename, dpi=180)
    plt.close(fig)


def _render_report(
    output_root: Path,
    rows: list[dict[str, Any]],
    main_summary: list[dict[str, Any]],
    ood_summaries: dict[str, list[dict[str, Any]]],
) -> None:
    grouped_delta = list(csv.DictReader((output_root / "grouped_metrics_by_abs_delta_rho.csv").open("r", encoding="utf-8")))
    grouped_pcyc = list(csv.DictReader((output_root / "grouped_metrics_by_abs_pcyc.csv").open("r", encoding="utf-8")))
    hardest = list(csv.DictReader((output_root / "hardest_family_baseline_vs_remicnet.csv").open("r", encoding="utf-8")))
    best_case = max(rows, key=lambda item: item["baseline_nmse"] - item["remicnet_nmse"])
    worst_case = min(rows, key=lambda item: item["baseline_nmse"] - item["remicnet_nmse"])
    report = f"""# task_real_008_report

## Task Goal

Build and evaluate ReMiC-Net with RSB-FiLM on the frozen 800/100/100 datasets and compare it against a residual 3D U-Net baseline under the same ref3 backbone.

## Frozen Baseline Reused

- Prior frozen baseline reference root: `{SOURCE_006D}`
- Prior checkpoint audited: `{SOURCE_006D / 'checkpoints/frozen_mainline/best.pt'}`
- Direct reuse for the main comparison: no
- Reason: task_real_008 freezes residual-only output, while the prior 006d checkpoint was trained as direct image prediction. Baseline-U-Net was retrained here under the residual protocol for a controlled comparison.

## Protocol / Context Files Used

- `CONTEXT/real_cylindrical_master_document_rsb_film_updated20260510.md`
- `CONTEXT/model_structure_rsb_film_updated20260510.md`
- `CONTEXT/reference_surface_strategy_rsb_film_updated20260510.md`
- `CONTEXT/simulation_protocol_rsb_film_updated20260510.md`
- `CONTEXT/visualization_protocol.md`
- `PROMPTS/system_rules.md`
- `PROMPTS/review_checklist.md`

## Boundary Statement

- Data protocol: frozen 800/100/100 main split plus existing OOD sets only
- Physics backbone: `ref3` only
- Comparison scope: `Baseline-U-Net` vs `ReMiC-Net with RSB-FiLM` only
- `delta_rho_input = raw_meter`
- No support head, no generic FiLM main result, no physics-consistency, no new datasets

## ReMiC-Net Construction

- Main input: `X_ref3`
- Geometry branch input: `[Mshell, delta_rho_raw, Pcyc]`
- `Mshell`: 3-channel one-hot shell allocation map for ref3 radii `[0.00, 0.15, 0.30] m`
- `delta_rho_raw`: signed radial deviation in meter, used directly as the network input
- `Pcyc`: wrapped two-way phase deviation normalized by `pi`
- RSB-FiLM defaults: `epsilon_m=0.05`, `alpha_gamma=0.5`, `alpha_beta=0.1`
- Engineering note: the repository baseline trunk has a two-downsample 3D U-Net. RSB-FiLM was therefore applied to all available encoder, bottleneck, and decoder stages in that shallower trunk as the closest faithful implementation of the frozen placement rule.

## Input Metadata Construction

- Metadata source manifest: `exp/task_real_006d_800_formal/20260419_112717/learning_handoff_manifest_main_800_100_100.json`
- `fc = {FC_HZ:.1f} Hz`
- `lambda_c = {LAMBDA_C_M:.12f} m`
- `k_c^(2w) = {float(K2W_C_RAD_PER_M):.6f} rad/m`
- Cached metadata manifest: `{output_root / 'remicnet_input_manifest_008.json'}`

## Training Setup

- Dataset source: frozen main split from `006d`
- Epochs: 5
- Batch size: 4
- Optimizer: Adam
- Learning rate: 0.001
- Loss: residual L1
- Checkpoints:
  - baseline: `{output_root / 'checkpoints/baseline/best.pt'}`
  - remicnet: `{output_root / 'checkpoints/remicnet/best.pt'}`

## Main Test Comparison

{json.dumps(main_summary, indent=2, ensure_ascii=False)}

## OOD Comparison

{json.dumps(ood_summaries, indent=2, ensure_ascii=False)}

## Mismatch-Aware Diagnostic Results

- grouped by `|delta_rho|` uses support-mean `abs(delta_rho_raw)` per sample
- grouped by `|Pcyc|` uses support-mean `abs(Pcyc)` per sample
- `|Pcyc| <= 0.25` vs `> 0.25` uses support-mean phase-deviation grouping
- grouped delta rows: {json.dumps(grouped_delta, ensure_ascii=False)}
- grouped pcyc rows: {json.dumps(grouped_pcyc, ensure_ascii=False)}

## Hardest-Family Results

{json.dumps(hardest, ensure_ascii=False)}

## Visual Outputs

- `viz/progress/curves/baseline_vs_remicnet_main_metrics.png`
- `viz/progress/curves/baseline_vs_remicnet_ood_metrics.png`
- `viz/progress/curves/baseline_vs_remicnet_runtime_speedup.png`
- `viz/progress/curves/grouped_error_by_abs_delta_rho.png`
- `viz/progress/curves/grouped_error_by_abs_pcyc.png`
- `viz/progress/curves/grouped_error_by_pcyc_quarter_pi.png`
- `viz/progress/curves/baseline_vs_remicnet_hardest_families.png`
- `viz/paper_candidates/qualitative/remicnet_best_case_panel.png`
- `viz/paper_candidates/qualitative/remicnet_failure_case_panel.png`

## Git Update Summary

See `git_update_summary_008.md`.

## Remaining Issues

- This repository did not contain a previously trained residual-only baseline checkpoint, so baseline retraining was necessary.
- The current 3D U-Net trunk is shallower than the four-level description in the context docs; the implementation uses the closest compatible RSB-FiLM placement.
- OOD ref3 inputs were recomputed on demand because frozen OOD learning-cache volumes were not present as reusable files.

## Is ReMiC-Net Worth Keeping as Main Method?

Conditional. Keep it if the main/OOD metrics and mismatch-aware group curves consistently show lower NMSE at similar runtime than Baseline-U-Net, especially in higher `|delta_rho|` and higher `|Pcyc|` bins.

## Suggested Next Task

If ReMiC-Net shows consistent gains, the next task should be a controlled ablation on `Mshell`, `delta_rho_raw`, and `Pcyc` contributions without changing the frozen dataset or ref3 backbone.

## Key file paths for ChatGPT controller

- report: `{output_root / 'task_real_008_report.md'}`
- baseline manifest: `{output_root / 'baseline_reference_manifest_008.json'}`
- input manifest: `{output_root / 'remicnet_input_manifest_008.json'}`
- training metrics: `{output_root / 'metrics_remicnet_trainval_008.json'}`
- main metrics: `{output_root / 'metrics_baseline_vs_remicnet_main.csv'}`
- ood metrics:
  - `{output_root / 'metrics_baseline_vs_remicnet_unseen_param_ood.csv'}`
  - `{output_root / 'metrics_baseline_vs_remicnet_leave_one_family_out_ood.csv'}`
  - `{output_root / 'metrics_baseline_vs_remicnet_random_et_ood.csv'}`
"""
    write_text(output_root / "task_real_008_report.md", report)
    _panel_case(output_root, best_case, "remicnet_best_case_panel.png", "Best gain case")
    _panel_case(output_root, worst_case, "remicnet_failure_case_panel.png", "Worst gain case")


def _write_git_summary(output_root: Path, commit_hash: str | None = None) -> None:
    status = subprocess.run(["git", "status", "--short", "--branch"], cwd=PROJECT_ROOT, check=True, capture_output=True, text=True).stdout.strip()
    remotes = subprocess.run(["git", "remote", "-v"], cwd=PROJECT_ROOT, check=True, capture_output=True, text=True).stdout.strip()
    if commit_hash is None:
        commit_hash = subprocess.run(["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, check=True, capture_output=True, text=True).stdout.strip()
    summary = [
        "# git_update_summary_008",
        "",
        f"- commit_hash: {commit_hash}",
        f"- git_status: {status or 'clean'}",
        f"- remotes_present: {'yes' if remotes else 'no'}",
        f"- push_result: {'not attempted' if not remotes else 'pending'}",
    ]
    if remotes:
        summary.append("- remote_detail:")
        summary.extend([f"  {line}" for line in remotes.splitlines()])
    else:
        summary.append("- remote_detail: none")
        summary.append("- note: local commit only")
    write_text(output_root / "git_update_summary_008.md", "\n".join(summary) + "\n")


def _write_tree(output_root: Path) -> None:
    result = subprocess.run(["bash", "-lc", f"cd '{output_root}' && find . | sort"], check=True, capture_output=True, text=True)
    write_text(output_root / "tree.txt", result.stdout)


def stage_build_inputs(output_root: Path) -> list[dict[str, Any]]:
    _ensure_dirs(output_root)
    _write_baseline_manifest(output_root)
    return _build_metadata_rows(output_root)


def stage_train(output_root: Path) -> dict[str, Any]:
    rows = read_json(output_root / "remicnet_input_manifest_008.json")["metadata_rows"]
    baseline_metrics = _train_model(output_root, rows, "baseline", epochs=5, batch_size=4, lr=1.0e-3)
    remic_metrics = _train_model(output_root, rows, "remicnet", epochs=5, batch_size=4, lr=1.0e-3)
    payload = {
        "baseline": baseline_metrics,
        "remicnet": remic_metrics,
        "delta_rho_input": "raw_meter",
    }
    write_json(output_root / "metrics_remicnet_trainval_008.json", payload)
    write_text(
        output_root / "remicnet_config_008.yaml",
        "\n".join(
            [
                "model: ReMiC-Net with RSB-FiLM",
                "main_input: X_ref3",
                "geometry_input: [Mshell, delta_rho_raw, Pcyc]",
                "delta_rho_input: raw_meter",
                "fusion: RSB-FiLM",
                "epsilon_m: 0.05",
                "alpha_gamma: 0.5",
                "alpha_beta: 0.1",
                "loss: residual_l1",
                "output: residual_only",
            ]
        )
        + "\n",
    )
    _render_curve(output_root, baseline_metrics, "baseline")
    _render_curve(output_root, remic_metrics, "remicnet")
    return payload


def stage_eval(output_root: Path) -> dict[str, Any]:
    rows = read_json(output_root / "remicnet_input_manifest_008.json")["metadata_rows"]
    bp_runtime_means = _read_bp_runtime_means()
    all_rows, main_summary = _evaluate_main(output_root, rows)
    ood_summaries: dict[str, list[dict[str, Any]]] = {}
    for dataset_name in OOD_DATASET_DIRS:
        dataset_rows, summary_rows = _evaluate_ood_dataset(output_root, dataset_name, bp_runtime_means[dataset_name])
        all_rows.extend(dataset_rows)
        ood_summaries[dataset_name] = summary_rows
    _group_metric_rows(all_rows, "support_mean_abs_delta_rho", DELTA_BINS, output_root / "grouped_metrics_by_abs_delta_rho.csv")
    _group_metric_rows(all_rows, "support_mean_abs_pcyc", PCT_BINS, output_root / "grouped_metrics_by_abs_pcyc.csv")
    _quarter_pi_groups(all_rows, output_root / "grouped_metrics_by_pcyc_quarter_pi.csv")
    _hardest_family_rows(all_rows, output_root / "hardest_family_baseline_vs_remicnet.csv")
    _render_report(output_root, all_rows, main_summary, ood_summaries)
    write_json(output_root / "evaluation_manifest_008.json", {"main_summary": main_summary, "ood_summaries": ood_summaries, "num_rows": len(all_rows)})
    return {"main_summary": main_summary, "ood_summaries": ood_summaries, "all_rows": all_rows}


def stage_render(output_root: Path) -> None:
    main_summary = list(csv.DictReader((output_root / "metrics_baseline_vs_remicnet_main.csv").open("r", encoding="utf-8")))
    ood_summaries = {
        "Unseen-Parameter OOD": list(csv.DictReader((output_root / "metrics_baseline_vs_remicnet_unseen_param_ood.csv").open("r", encoding="utf-8"))),
        "Leave-One-Family-Out Focused OOD": list(csv.DictReader((output_root / "metrics_baseline_vs_remicnet_leave_one_family_out_ood.csv").open("r", encoding="utf-8"))),
        "Random-ET OOD": list(csv.DictReader((output_root / "metrics_baseline_vs_remicnet_random_et_ood.csv").open("r", encoding="utf-8"))),
    }
    grouped_delta = list(csv.DictReader((output_root / "grouped_metrics_by_abs_delta_rho.csv").open("r", encoding="utf-8")))
    grouped_pcyc = list(csv.DictReader((output_root / "grouped_metrics_by_abs_pcyc.csv").open("r", encoding="utf-8")))
    grouped_quarter = list(csv.DictReader((output_root / "grouped_metrics_by_pcyc_quarter_pi.csv").open("r", encoding="utf-8")))
    hardest = list(csv.DictReader((output_root / "hardest_family_baseline_vs_remicnet.csv").open("r", encoding="utf-8")))
    _plot_summary_bars(output_root, main_summary, ood_summaries)
    _plot_grouped_curve(output_root, grouped_delta, "grouped_error_by_abs_delta_rho.png", "Grouped by support mean |delta_rho|")
    _plot_grouped_curve(output_root, grouped_pcyc, "grouped_error_by_abs_pcyc.png", "Grouped by support mean |Pcyc|")
    _plot_grouped_curve(output_root, grouped_quarter, "grouped_error_by_pcyc_quarter_pi.png", "Quarter-pi mismatch grouping")
    _plot_hardest_families(output_root, hardest)
    _stage_log(output_root, "render_viz", "rendered baseline-vs-remic comparison figures")


def main() -> None:
    parser = argparse.ArgumentParser(description="task_real_008 pipeline")
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--stage", required=True, choices=["build_inputs", "train", "eval", "render", "git_update", "all"])
    args = parser.parse_args()
    output_root = Path(args.output_root)
    if args.stage in {"build_inputs", "all"}:
        stage_build_inputs(output_root)
    if args.stage in {"train", "all"}:
        stage_train(output_root)
    if args.stage in {"eval", "all"}:
        stage_eval(output_root)
    if args.stage in {"render", "all"}:
        stage_render(output_root)
    if args.stage in {"git_update", "all"}:
        _write_git_summary(output_root)
        _write_tree(output_root)


if __name__ == "__main__":
    main()
