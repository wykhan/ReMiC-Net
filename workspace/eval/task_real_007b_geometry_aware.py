from __future__ import annotations

import argparse
import csv
import subprocess
import time
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import torch

from workspace.common.io_utils import ensure_dir, read_json, write_json, write_text
from workspace.eval.eval_et_baselines_variantB import _failure_tags
from workspace.eval.metrics_3d import nmse, psnr, ssim_global
from workspace.models.unet3d_small import UNet3DSmall
from workspace.train.train_two_stage_et import TARGET_SHAPE, _fit_to_shape, _normalize_pair


PROJECT_ROOT = Path("/home/superws/2026_Projects/Codex_reference_plane_real")
DEFAULT_BASELINE_ROOT = PROJECT_ROOT / "exp" / "task_real_006d_800_formal" / "20260419_112717"
DEFAULT_EVAL006E_ROOT = PROJECT_ROOT / "exp" / "task_real_006e_comprehensive_eval" / "20260419_190046"
DEFAULT_P1_ROOT = PROJECT_ROOT / "exp" / "task_real_007_physics_consistency" / "20260419_201254"
DATASET_MAP = {
    "Main Test": {
        "dataset_dir": DEFAULT_BASELINE_ROOT / "datasets" / "main_800_100_100",
        "split": "test",
        "scope_key": "main",
    },
    "Unseen-Parameter OOD": {
        "dataset_dir": DEFAULT_BASELINE_ROOT / "datasets" / "unseen_param_ood",
        "split": "test",
        "scope_key": "unseen_param_ood",
    },
    "Leave-One-Family-Out Focused OOD": {
        "dataset_dir": DEFAULT_BASELINE_ROOT / "datasets" / "leave_one_family_out_ood",
        "split": "test",
        "scope_key": "leave_one_family_out_ood",
    },
    "Random-ET OOD": {
        "dataset_dir": DEFAULT_BASELINE_ROOT / "datasets" / "random_et_ood",
        "split": "test",
        "scope_key": "random_et_ood",
    },
}
HARD_FAMILIES = ["point_cluster", "line", "L-shape"]
MODEL_ORDER = ["Baseline-Ours", "Ours-PC-P1", "Ours-PC-P2A"]


def _ensure_dirs(output_root: Path) -> None:
    for rel in [
        "logs",
        "checkpoints",
        "viz/progress/curves",
        "viz/paper_candidates/curves",
        "viz/paper_candidates/qualitative",
        "viz/manifest",
        "predictions",
    ]:
        ensure_dir(output_root / rel)


def _stage_log(output_root: Path, stage: str, text: str) -> None:
    log_dir = ensure_dir(output_root / "logs")
    with (log_dir / f"{stage}.log").open("a", encoding="utf-8") as handle:
        handle.write(text.rstrip() + "\n")


def _merge_csv_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]], key_fields: list[str]) -> None:
    merged: dict[tuple[Any, ...], dict[str, Any]] = {}
    if path.exists():
        with path.open("r", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                merged[tuple(row[field] for field in key_fields)] = row
    for row in rows:
        merged[tuple(row[field] for field in key_fields)] = row
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(merged[key] for key in sorted(merged))


def write_reference_manifest(output_root: Path, baseline_root: Path, eval006e_root: Path, p1_root: Path) -> dict[str, Any]:
    manifest = {
        "baseline_source_root": str(baseline_root),
        "baseline_checkpoint": str(baseline_root / "checkpoints" / "frozen_mainline" / "best.pt"),
        "p1_source_root": str(p1_root),
        "p1_checkpoint": str(p1_root / "checkpoints" / "pc_p1" / "best.pt"),
        "report_006d": str(baseline_root / "task_real_006d_report.md"),
        "report_006e": str(eval006e_root / "task_real_006e_report.md"),
        "report_007": str(p1_root / "task_real_007_report.md"),
    }
    write_json(output_root / "baseline_p1_reference_manifest_007b.json", manifest)
    return manifest


def _load_model(ckpt_path: Path) -> torch.nn.Module:
    model = UNet3DSmall(base_channels=8)
    ckpt = torch.load(ckpt_path, map_location="cpu")
    model.load_state_dict(ckpt["model_state"])
    model.eval()
    return model


def _baseline_runtime_lookup(eval006e_root: Path) -> dict[tuple[str, str, str], float]:
    rows = list(csv.DictReader((eval006e_root / "per_sample_metrics_all_datasets.csv").open("r", encoding="utf-8")))
    return {(row["dataset"], row["sample_id"], row["method"]): float(row["runtime"]) for row in rows}


def _baseline_ours_lookup(eval006e_root: Path) -> dict[tuple[str, str], dict[str, float]]:
    rows = list(csv.DictReader((eval006e_root / "per_sample_metrics_all_datasets.csv").open("r", encoding="utf-8")))
    payload = {}
    for row in rows:
        if row["method"] == "Ours":
            payload[(row["dataset"], row["sample_id"])] = {
                "nmse": float(row["nmse"]),
                "psnr": float(row["psnr"]),
                "ssim": float(row["ssim"]),
                "runtime": float(row["runtime"]),
            }
    return payload


def _bp_runtime_lookup(eval006e_root: Path) -> dict[str, float]:
    rows = list(csv.DictReader((eval006e_root / "mainline_vs_baselines_all_datasets.csv").open("r", encoding="utf-8")))
    return {row["dataset"]: float(row["runtime_mean"]) for row in rows if row["method"] == "BP"}


def _dataset_rows(dataset_name: str, baseline_root: Path) -> list[dict[str, Any]]:
    dataset_dir = DATASET_MAP[dataset_name]["dataset_dir"]
    index_rows = read_json(dataset_dir / "dataset" / "index.json")
    return [row for row in index_rows if row["split"] == DATASET_MAP[dataset_name]["split"]]


def _coarse_volume(dataset_name: str, sample_id: str, baseline_root: Path, eval006e_root: Path) -> np.ndarray:
    if dataset_name == "Main Test":
        manifest = read_json(baseline_root / "learning_handoff_manifest_main_800_100_100.json")
        ref3_rel = next(row["ref3_path"] for row in manifest["samples"] if row["sample_id"] == sample_id)
        return np.load(baseline_root / ref3_rel)["volume"]
    cache_key = DATASET_MAP[dataset_name]["scope_key"]
    return np.load(eval006e_root / "comparison_cache" / cache_key / f"{sample_id}_Ref3.npz")["volume"]


def _predict(model: torch.nn.Module, coarse: np.ndarray) -> tuple[np.ndarray, float]:
    input_tensor = torch.from_numpy(coarse[None, None, ...])
    t0 = time.perf_counter()
    pred = model(input_tensor).numpy()[0, 0]
    return pred, time.perf_counter() - t0


def evaluate_dataset(
    output_root: Path,
    baseline_root: Path,
    eval006e_root: Path,
    p1_root: Path,
    dataset_name: str,
) -> dict[str, Any]:
    rows = _dataset_rows(dataset_name, baseline_root)
    p1_model = _load_model(p1_root / "checkpoints" / "pc_p1" / "best.pt")
    p2_model = _load_model(output_root / "checkpoints" / "pc_p2a" / "best.pt")
    baseline_lookup = _baseline_ours_lookup(eval006e_root)
    runtime_lookup = _baseline_runtime_lookup(eval006e_root)
    bp_runtime_mean = _bp_runtime_lookup(eval006e_root)[dataset_name]
    pred_dir = ensure_dir(output_root / "predictions" / DATASET_MAP[dataset_name]["scope_key"])

    per_sample = []
    failure_counts = {model: {"F2": 0, "F3": 0, "F4": 0} for model in MODEL_ORDER}
    hardest_rows = []

    with torch.no_grad():
        for item in rows:
            gt_npz = np.load(DATASET_MAP[dataset_name]["dataset_dir"] / item["gt_volume_path"])
            coarse_volume = _coarse_volume(dataset_name, item["sample_id"], baseline_root, eval006e_root)
            gt = _fit_to_shape(gt_npz["volume"], TARGET_SHAPE)
            coarse = _fit_to_shape(coarse_volume, TARGET_SHAPE)
            coarse, gt = _normalize_pair(coarse, gt)

            p1_pred, p1_net_runtime = _predict(p1_model, coarse)
            p2_pred, p2_net_runtime = _predict(p2_model, coarse)
            np.savez_compressed(
                pred_dir / f"{item['sample_id']}_p2_compare.npz",
                coarse=coarse.astype(np.float32),
                gt=gt.astype(np.float32),
                p1_pred=p1_pred.astype(np.float32),
                p2_pred=p2_pred.astype(np.float32),
            )

            baseline_stats = baseline_lookup[(dataset_name, item["sample_id"])]
            ref3_runtime = runtime_lookup[(dataset_name, item["sample_id"], "Ref3")]
            model_rows = [
                {
                    "dataset": dataset_name,
                    "sample_id": item["sample_id"],
                    "family": item.get("family", "random_et"),
                    "model": "Baseline-Ours",
                    "NMSE": baseline_stats["nmse"],
                    "PSNR": baseline_stats["psnr"],
                    "SSIM": baseline_stats["ssim"],
                    "runtime": baseline_stats["runtime"],
                    "speedup_vs_BP": bp_runtime_mean / baseline_stats["runtime"] if baseline_stats["runtime"] > 0 else 0.0,
                    "pred_volume": None,
                },
                {
                    "dataset": dataset_name,
                    "sample_id": item["sample_id"],
                    "family": item.get("family", "random_et"),
                    "model": "Ours-PC-P1",
                    "NMSE": nmse(p1_pred, gt),
                    "PSNR": psnr(p1_pred, gt),
                    "SSIM": ssim_global(p1_pred, gt),
                    "runtime": ref3_runtime + p1_net_runtime,
                    "speedup_vs_BP": bp_runtime_mean / (ref3_runtime + p1_net_runtime) if ref3_runtime + p1_net_runtime > 0 else 0.0,
                    "pred_volume": p1_pred,
                },
                {
                    "dataset": dataset_name,
                    "sample_id": item["sample_id"],
                    "family": item.get("family", "random_et"),
                    "model": "Ours-PC-P2A",
                    "NMSE": nmse(p2_pred, gt),
                    "PSNR": psnr(p2_pred, gt),
                    "SSIM": ssim_global(p2_pred, gt),
                    "runtime": ref3_runtime + p2_net_runtime,
                    "speedup_vs_BP": bp_runtime_mean / (ref3_runtime + p2_net_runtime) if ref3_runtime + p2_net_runtime > 0 else 0.0,
                    "pred_volume": p2_pred,
                },
            ]
            per_sample.extend([{k: v for k, v in row.items() if k != "pred_volume"} for row in model_rows])
            for row in model_rows:
                pred_for_failure = coarse if row["model"] == "Baseline-Ours" else row["pred_volume"]
                fail = _failure_tags(pred_for_failure, gt, item.get("family", "random_et"), row["NMSE"])
                for label in ["F2", "F3", "F4"]:
                    if label in fail["tags"]:
                        failure_counts[row["model"]][label] += 1
            if item.get("family", "random_et") in HARD_FAMILIES:
                hardest_rows.append(
                    {
                        "dataset": dataset_name,
                        "family": item["family"],
                        "baseline_nmse": baseline_stats["nmse"],
                        "p1_nmse": nmse(p1_pred, gt),
                        "p2a_nmse": nmse(p2_pred, gt),
                        "baseline_psnr": baseline_stats["psnr"],
                        "p1_psnr": psnr(p1_pred, gt),
                        "p2a_psnr": psnr(p2_pred, gt),
                        "baseline_ssim": baseline_stats["ssim"],
                        "p1_ssim": ssim_global(p1_pred, gt),
                        "p2a_ssim": ssim_global(p2_pred, gt),
                    }
                )
    summary_rows = []
    for model_name in MODEL_ORDER:
        values = [row for row in per_sample if row["model"] == model_name and row["dataset"] == dataset_name]
        summary_rows.append(
            {
                "dataset": dataset_name,
                "model": model_name,
                "NMSE_mean": float(np.mean([row["NMSE"] for row in values])),
                "NMSE_std": float(np.std([row["NMSE"] for row in values])),
                "PSNR_mean": float(np.mean([row["PSNR"] for row in values])),
                "PSNR_std": float(np.std([row["PSNR"] for row in values])),
                "SSIM_mean": float(np.mean([row["SSIM"] for row in values])),
                "SSIM_std": float(np.std([row["SSIM"] for row in values])),
                "runtime_mean": float(np.mean([row["runtime"] for row in values])),
                "runtime_std": float(np.std([row["runtime"] for row in values])),
                "speedup_vs_BP": float(np.mean([row["speedup_vs_BP"] for row in values])),
                "num_samples": len(values),
            }
        )
    return {
        "summary_rows": summary_rows,
        "per_sample": per_sample,
        "failure_counts": failure_counts,
        "hardest_rows": hardest_rows,
    }


def _write_dataset_summary(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["dataset", "model", "NMSE_mean", "NMSE_std", "PSNR_mean", "PSNR_std", "SSIM_mean", "SSIM_std", "runtime_mean", "runtime_std", "speedup_vs_BP", "num_samples"])
        writer.writeheader()
        writer.writerows(rows)


def run_eval(output_root: Path, baseline_root: Path, eval006e_root: Path, p1_root: Path, scope: str) -> None:
    datasets = ["Main Test"] if scope == "main" else [name for name in DATASET_MAP if name != "Main Test"]
    all_summaries = []
    all_per_sample = []
    all_failure_rows = []
    all_hardest_rows = []
    for dataset_name in datasets:
        payload = evaluate_dataset(output_root, baseline_root, eval006e_root, p1_root, dataset_name)
        all_summaries.extend(payload["summary_rows"])
        all_per_sample.extend(payload["per_sample"])
        for model_name, counts in payload["failure_counts"].items():
            for label in ["F2", "F3", "F4"]:
                all_failure_rows.append({"dataset": dataset_name, "model": model_name, "failure_label": label, "count": counts[label]})
        all_hardest_rows.extend(payload["hardest_rows"])

    mapping = {
        "Main Test": "metrics_baseline_p1_p2_main.csv",
        "Unseen-Parameter OOD": "metrics_baseline_p1_p2_unseen_param_ood.csv",
        "Leave-One-Family-Out Focused OOD": "metrics_baseline_p1_p2_leave_one_family_out_ood.csv",
        "Random-ET OOD": "metrics_baseline_p1_p2_random_et_ood.csv",
    }
    for dataset_name in datasets:
        rows = [row for row in all_summaries if row["dataset"] == dataset_name]
        _write_dataset_summary(output_root / mapping[dataset_name], rows)
    _merge_csv_rows(
        output_root / "failure_mode_p2_improvement.csv",
        ["dataset", "model", "failure_label", "count"],
        all_failure_rows,
        ["dataset", "model", "failure_label"],
    )
    _merge_csv_rows(
        output_root / "hardest_family_p2_improvement.csv",
        ["dataset", "family", "baseline_nmse", "p1_nmse", "p2a_nmse", "baseline_psnr", "p1_psnr", "p2a_psnr", "baseline_ssim", "p1_ssim", "p2a_ssim"],
        all_hardest_rows,
        ["dataset", "family", "baseline_nmse", "p1_nmse", "p2a_nmse", "baseline_psnr", "p1_psnr", "p2a_psnr", "baseline_ssim", "p1_ssim", "p2a_ssim"],
    )
    with (output_root / f"per_sample_p2_{scope}.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["dataset", "sample_id", "family", "model", "NMSE", "PSNR", "SSIM", "runtime", "speedup_vs_BP"])
        writer.writeheader()
        writer.writerows(all_per_sample)
    _stage_log(output_root, f"run_p2_eval_{scope}", f"datasets={datasets}")


def _all_summary_rows(output_root: Path) -> list[dict[str, Any]]:
    rows = []
    for fn in [
        "metrics_baseline_p1_p2_main.csv",
        "metrics_baseline_p1_p2_unseen_param_ood.csv",
        "metrics_baseline_p1_p2_leave_one_family_out_ood.csv",
        "metrics_baseline_p1_p2_random_et_ood.csv",
    ]:
        rows.extend(list(csv.DictReader((output_root / fn).open("r", encoding="utf-8"))))
    return rows


def render_viz(output_root: Path, baseline_root: Path) -> None:
    progress = ensure_dir(output_root / "viz" / "progress" / "curves")
    paper_curves = ensure_dir(output_root / "viz" / "paper_candidates" / "curves")
    qual = ensure_dir(output_root / "viz" / "paper_candidates" / "qualitative")
    all_rows = _all_summary_rows(output_root)
    datasets = ["Main Test", "Unseen-Parameter OOD", "Leave-One-Family-Out Focused OOD", "Random-ET OOD"]
    labels = ["Main", "Unseen", "LeaveOne", "RandomET"]

    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.2))
    main_rows = [row for row in all_rows if row["dataset"] == "Main Test"]
    for ax, key in zip(axes, ["NMSE_mean", "PSNR_mean", "SSIM_mean"]):
        vals = [float(next(row[key] for row in main_rows if row["model"] == model)) for model in MODEL_ORDER]
        ax.bar(["Baseline", "P1", "P2A"], vals)
        ax.set_title(key.replace("_mean", ""))
    fig.tight_layout()
    fig.savefig(progress / "baseline_p1_p2_main_metrics.png", dpi=170)
    plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(13.8, 4.3))
    x = np.arange(len(datasets))
    for ax, key in zip(axes, ["NMSE_mean", "PSNR_mean", "SSIM_mean"]):
        for offset, model_name in zip([-0.24, 0.0, 0.24], MODEL_ORDER):
            vals = [float(next(row[key] for row in all_rows if row["dataset"] == ds and row["model"] == model_name)) for ds in datasets]
            ax.bar(x + offset, vals, width=0.22, label=model_name if ax is axes[0] else None)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=15)
        ax.set_title(key.replace("_mean", ""))
    axes[0].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(progress / "baseline_p1_p2_ood_metrics.png", dpi=170)
    fig.savefig(paper_curves / "fig_p2_ood_metrics.png", dpi=170)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2))
    x = np.arange(len(datasets))
    for model_name in MODEL_ORDER:
        runtimes = [float(next(row["runtime_mean"] for row in all_rows if row["dataset"] == ds and row["model"] == model_name)) for ds in datasets]
        speedups = [float(next(row["speedup_vs_BP"] for row in all_rows if row["dataset"] == ds and row["model"] == model_name)) for ds in datasets]
        axes[0].plot(x, runtimes, marker="o", label=model_name)
        axes[1].plot(x, speedups, marker="o", label=model_name)
    for ax in axes:
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=15)
        ax.legend(fontsize=8)
    axes[0].set_title("Runtime")
    axes[1].set_title("Speedup vs BP")
    fig.tight_layout()
    fig.savefig(progress / "baseline_p1_p2_runtime_speedup.png", dpi=170)
    plt.close(fig)

    failure_rows = list(csv.DictReader((output_root / "failure_mode_p2_improvement.csv").open("r", encoding="utf-8")))
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    x = np.arange(3)
    failure_labels = ["F2", "F3", "F4"]
    for idx, focus_model in enumerate(["Ours-PC-P1", "Ours-PC-P2A"]):
        ax = axes[idx]
        for dataset_name in datasets:
            base = np.array([int(next(row["count"] for row in failure_rows if row["dataset"] == dataset_name and row["model"] == "Baseline-Ours" and row["failure_label"] == label)) for label in failure_labels])
            target = np.array([int(next(row["count"] for row in failure_rows if row["dataset"] == dataset_name and row["model"] == focus_model and row["failure_label"] == label)) for label in failure_labels])
            ax.plot(x, base - target, marker="o", label=dataset_name)
        ax.set_xticks(x)
        ax.set_xticklabels(failure_labels)
        ax.set_title(f"Baseline vs {focus_model.split('-')[-1]}")
    axes[0].legend(ncol=2, fontsize=8)
    fig.tight_layout()
    fig.savefig(progress / "baseline_p1_p2_failure_modes.png", dpi=170)
    plt.close(fig)

    family_rows = list(csv.DictReader((output_root / "hardest_family_p2_improvement.csv").open("r", encoding="utf-8")))
    fig, ax = plt.subplots(figsize=(10, 4.5))
    x = np.arange(len(HARD_FAMILIES))
    baseline = [np.mean([float(row["baseline_nmse"]) for row in family_rows if row["family"] == family]) for family in HARD_FAMILIES]
    p1 = [np.mean([float(row["p1_nmse"]) for row in family_rows if row["family"] == family]) for family in HARD_FAMILIES]
    p2 = [np.mean([float(row["p2a_nmse"]) for row in family_rows if row["family"] == family]) for family in HARD_FAMILIES]
    ax.bar(x - 0.24, baseline, width=0.22, label="Baseline")
    ax.bar(x + 0.0, p1, width=0.22, label="P1")
    ax.bar(x + 0.24, p2, width=0.22, label="P2A")
    ax.set_xticks(x)
    ax.set_xticklabels(HARD_FAMILIES, rotation=18)
    ax.set_title("Hardest families")
    ax.legend()
    fig.tight_layout()
    fig.savefig(progress / "baseline_p1_p2_hardest_families.png", dpi=170)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.6, 5))
    for model_name in MODEL_ORDER:
        runtimes = [float(next(row["runtime_mean"] for row in all_rows if row["dataset"] == ds and row["model"] == model_name)) for ds in datasets]
        nmse_vals = [float(next(row["NMSE_mean"] for row in all_rows if row["dataset"] == ds and row["model"] == model_name)) for ds in datasets]
        ax.scatter(runtimes, nmse_vals, s=60, label=model_name)
        ax.plot(runtimes, nmse_vals, alpha=0.5)
    ax.set_xlabel("Runtime")
    ax.set_ylabel("NMSE mean")
    ax.set_title("Baseline / P1 / P2A frontier")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(progress / "baseline_p1_p2_frontier_ood.png", dpi=170)
    plt.close(fig)

    per_main = list(csv.DictReader((output_root / "per_sample_p2_main.csv").open("r", encoding="utf-8")))
    p2_rows = [row for row in per_main if row["model"] == "Ours-PC-P2A"]
    best = max(
        p2_rows,
        key=lambda row: float(next(r["NMSE"] for r in per_main if r["model"] == "Ours-PC-P1" and r["sample_id"] == row["sample_id"])) - float(row["NMSE"]),
    )
    failure = max(p2_rows, key=lambda row: float(row["NMSE"]))
    for sample_id, target in [(best["sample_id"], qual / "p2_best_case_panel.png"), (failure["sample_id"], qual / "p2_failure_case_panel.png")]:
        baseline_pred = np.load(baseline_root / "predictions" / "frozen_mainline" / f"{sample_id}_M2_pred.npz")
        compare = np.load(output_root / "predictions" / "main" / f"{sample_id}_p2_compare.npz")
        fig, axes = plt.subplots(1, 5, figsize=(14.5, 3.5))
        z_idx = baseline_pred["gt"].shape[2] // 2
        panels = [
            ("GT", baseline_pred["gt"]),
            ("Baseline", baseline_pred["pred"]),
            ("P1", compare["p1_pred"]),
            ("P2A", compare["p2_pred"]),
            ("AbsErr(P2A)", np.abs(compare["p2_pred"] - baseline_pred["gt"])),
        ]
        for ax, (label, volume) in zip(axes, panels):
            ax.imshow(volume[:, :, z_idx], cmap="inferno" if "Err" in label else "viridis")
            ax.set_title(label)
            ax.axis("off")
        fig.tight_layout()
        fig.savefig(target, dpi=170)
        plt.close(fig)


def git_update(output_root: Path) -> dict[str, Any]:
    files_to_add = [
        "workspace/train/physics_consistency.py",
        "workspace/train/train_pc_p2a.py",
        "workspace/eval/task_real_007b_geometry_aware.py",
        "scripts/run_pc_training_P2A.sh",
        "scripts/run_pc_training_P2B.sh",
        "scripts/run_p2_eval_main.sh",
        "scripts/run_p2_eval_ood.sh",
        "scripts/render_p2_comparison_viz.sh",
        "scripts/update_git_and_record_007b.sh",
        "CHANGELOG_DEV.md",
        "debug.md",
    ]
    subprocess.run(["git", "add", *files_to_add], cwd=PROJECT_ROOT, check=True)
    commit_proc = subprocess.run(["git", "commit", "-m", "task_real_007b: add geometry-aware consistency refinement"], cwd=PROJECT_ROOT, text=True, capture_output=True)
    if commit_proc.returncode not in (0, 1):
        raise RuntimeError(commit_proc.stderr)
    commit_hash = subprocess.run(["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, text=True, capture_output=True, check=True).stdout.strip()
    status = subprocess.run(["git", "status", "--short"], cwd=PROJECT_ROOT, text=True, capture_output=True, check=True).stdout
    remotes = subprocess.run(["git", "remote"], cwd=PROJECT_ROOT, text=True, capture_output=True, check=True).stdout.strip().splitlines()
    push_message = "local commit only"
    if remotes:
        push_proc = subprocess.run(["git", "push"], cwd=PROJECT_ROOT, text=True, capture_output=True)
        push_message = "push succeeded" if push_proc.returncode == 0 else f"push failed: {push_proc.stderr.strip() or push_proc.stdout.strip()}"
    write_text(
        output_root / "git_update_summary_007b.md",
        "\n".join(
            [
                "# git_update_summary_007b",
                "",
                f"- commit_hash: `{commit_hash}`",
                f"- push_result: `{push_message}`",
                "",
                "## git status",
                "",
                "```text",
                status.rstrip(),
                "```",
            ]
        )
        + "\n",
    )
    return {"commit_hash": commit_hash, "git_status": status, "push_result": push_message}


def generate_report(output_root: Path, baseline_root: Path, eval006e_root: Path, p1_root: Path) -> None:
    report = f"""# task_real_007b_report

## 1. Task Goal

Upgrade the `task_real_007` sampled consistency into a geometry-aware support-weighted consistency and compare Baseline-Ours vs Ours-PC-P1 vs Ours-PC-P2A on the frozen 800-scale protocol.

## 2. Frozen Baseline / P1 Reused

- baseline source root: `{baseline_root}`
- baseline checkpoint: `{baseline_root / 'checkpoints/frozen_mainline/best.pt'}`
- P1 source root: `{p1_root}`
- P1 checkpoint: `{p1_root / 'checkpoints/pc_p1/best.pt'}`

## 3. Protocol / Context Files Used

- `CONTEXT/real_cylindrical_master_document_with_physics_consistency.md`
- `CONTEXT/simulation_protocol.md`
- `CONTEXT/reference_surface_strategy.md`
- `CONTEXT/dataset_protocol.md`
- `CONTEXT/et_dataset_protocol.md`
- `CONTEXT/et_dataset_protocol_800.md`
- `CONTEXT/visualization_protocol.md`
- `exp/task_real_006d_800_formal/20260419_112717/task_real_006d_report.md`
- `exp/task_real_006e_comprehensive_eval/20260419_190046/task_real_006e_report.md`
- `exp/task_real_007_physics_consistency/20260419_201254/task_real_007_report.md`

## 4. Boundary Statement

This task keeps the frozen 800-scale data protocol, keeps Variant B + ref3 + UNet3DSmall unchanged, and only refines the consistency loss weighting. No six-method rerun, no new dataset, and no backbone replacement were introduced.

## 5. Geometry-Aware Consistency Design

P2A uses:

`L_total = L_image + lambda_pc * L_echo_geo`

where `L_echo_geo` is computed on the same sparse cylindrical measurement subset as P1, but with a dynamic prediction-derived support mask. Voxels above a support threshold are assigned higher support weights, a one-voxel dilation defines a lightweight geometry neighborhood, and measurement-domain weights are derived from support-weighted projected energy. The executed config is stored at `{output_root / 'consistency_config_P2A.yaml'}`.

P2B was not executed in this run. `scripts/run_pc_training_P2B.sh` is present only as a controlled placeholder because P2A already provides the required mandatory extension and this round is not a recipe search task.

## 6. Training Matrix

- Baseline-Ours: reused only
- Ours-PC-P1: reused only
- Ours-PC-P2A: trained from the frozen `task_real_007` P1 checkpoint
- Ours-PC-P2B: not executed

## 7. Main Test Comparison

- `{output_root / 'metrics_baseline_p1_p2_main.csv'}`

## 8. OOD Comparison

- `{output_root / 'metrics_baseline_p1_p2_unseen_param_ood.csv'}`
- `{output_root / 'metrics_baseline_p1_p2_leave_one_family_out_ood.csv'}`
- `{output_root / 'metrics_baseline_p1_p2_random_et_ood.csv'}`

## 9. Failure-Mode Improvement

- `{output_root / 'failure_mode_p2_improvement.csv'}`

## 10. Hardest-Family Improvement

- `{output_root / 'hardest_family_p2_improvement.csv'}`

## 11. Visual Outputs

- `{output_root / 'viz/progress/curves/baseline_p1_p2_main_metrics.png'}`
- `{output_root / 'viz/progress/curves/baseline_p1_p2_ood_metrics.png'}`
- `{output_root / 'viz/progress/curves/baseline_p1_p2_runtime_speedup.png'}`
- `{output_root / 'viz/progress/curves/baseline_p1_p2_failure_modes.png'}`
- `{output_root / 'viz/progress/curves/baseline_p1_p2_hardest_families.png'}`
- `{output_root / 'viz/progress/curves/baseline_p1_p2_frontier_ood.png'}`
- `{output_root / 'viz/paper_candidates/qualitative/p2_best_case_panel.png'}`
- `{output_root / 'viz/paper_candidates/qualitative/p2_failure_case_panel.png'}`

## 12. Git Update Summary

`{output_root / 'git_update_summary_007b.md'}`

## 13. Remaining Issues

- P2B was not executed.
- The comparison still inherits the frozen 800-scale protocol rather than a larger formal-scale dataset.
- Runtime remains controlled local timing inside the current software stack.

## 14. Is Geometry-Aware Consistency Worth Keeping?

`conditional`

P2A should be kept only if it improves at least one aggregate metric or strengthens failure-mode suppression relative to P1 without material runtime cost. The final decision should follow the CSV tables generated in this task.

## 15. Suggested Next Task

If P2A is beneficial, fold it into the main physics-consistency branch and consider a narrowly scoped P2B boundary-emphasis follow-up only on the hardest residual failures.

### Key file paths for ChatGPT controller

- report path: `{output_root / 'task_real_007b_report.md'}`
- baseline/P1 reference path: `{output_root / 'baseline_p1_reference_manifest_007b.json'}`
- consistency config path: `{output_root / 'consistency_config_P2A.yaml'}`
- metrics path: `{output_root / 'metrics_baseline_p1_p2_main.csv'}`, `{output_root / 'metrics_baseline_p1_p2_unseen_param_ood.csv'}`, `{output_root / 'metrics_baseline_p1_p2_leave_one_family_out_ood.csv'}`, `{output_root / 'metrics_baseline_p1_p2_random_et_ood.csv'}`
- failure-mode path: `{output_root / 'failure_mode_p2_improvement.csv'}`
- family path: `{output_root / 'hardest_family_p2_improvement.csv'}`
- curves path: `{output_root / 'viz/progress/curves'}`
- representative visuals path: `{output_root / 'viz/paper_candidates/qualitative'}`
- git summary path: `{output_root / 'git_update_summary_007b.md'}`
- logs path: `{output_root / 'logs'}`
"""
    write_text(output_root / "task_real_007b_report.md", report)


def finalize_tree(output_root: Path) -> None:
    entries = sorted(str(path) for path in output_root.rglob("*"))
    write_text(output_root / "tree.txt", "\n".join(entries) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="task_real_007b geometry-aware consistency")
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--baseline-root", default=str(DEFAULT_BASELINE_ROOT))
    parser.add_argument("--eval006e-root", default=str(DEFAULT_EVAL006E_ROOT))
    parser.add_argument("--p1-root", default=str(DEFAULT_P1_ROOT))
    parser.add_argument("--stage", required=True, choices=["reference_manifest", "eval_main", "eval_ood", "viz", "git", "report"])
    args = parser.parse_args()
    output_root = Path(args.output_root)
    baseline_root = Path(args.baseline_root)
    eval006e_root = Path(args.eval006e_root)
    p1_root = Path(args.p1_root)
    _ensure_dirs(output_root)
    if args.stage == "reference_manifest":
        write_reference_manifest(output_root, baseline_root, eval006e_root, p1_root)
    elif args.stage == "eval_main":
        run_eval(output_root, baseline_root, eval006e_root, p1_root, "main")
    elif args.stage == "eval_ood":
        run_eval(output_root, baseline_root, eval006e_root, p1_root, "ood")
    elif args.stage == "viz":
        render_viz(output_root, baseline_root)
    elif args.stage == "git":
        git_update(output_root)
    elif args.stage == "report":
        generate_report(output_root, baseline_root, eval006e_root, p1_root)
        finalize_tree(output_root)
    print(f"task_real_007b stage={args.stage} completed output_root={output_root}")


if __name__ == "__main__":
    main()
