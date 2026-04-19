from __future__ import annotations

import argparse
import csv
import json
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
DATASET_MAP = {
    "Main Test": {
        "type": "baseline",
        "metrics_csv": DEFAULT_EVAL006E_ROOT / "main_test_metrics_all_methods.csv",
        "dataset_dir": DEFAULT_BASELINE_ROOT / "datasets" / "main_800_100_100",
        "split": "test",
    },
    "Unseen-Parameter OOD": {
        "type": "ood",
        "metrics_csv": DEFAULT_EVAL006E_ROOT / "ood_unseen_param_metrics_all_methods.csv",
        "dataset_dir": DEFAULT_BASELINE_ROOT / "datasets" / "unseen_param_ood",
        "split": "test",
    },
    "Leave-One-Family-Out Focused OOD": {
        "type": "ood",
        "metrics_csv": DEFAULT_EVAL006E_ROOT / "ood_leave_one_family_out_metrics_all_methods.csv",
        "dataset_dir": DEFAULT_BASELINE_ROOT / "datasets" / "leave_one_family_out_ood",
        "split": "test",
    },
    "Random-ET OOD": {
        "type": "ood",
        "metrics_csv": DEFAULT_EVAL006E_ROOT / "ood_random_et_metrics_all_methods.csv",
        "dataset_dir": DEFAULT_BASELINE_ROOT / "datasets" / "random_et_ood",
        "split": "test",
    },
}
HARD_FAMILIES = ["point_cluster", "line", "L-shape"]


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


def _stage_log(output_root: Path, stage: str, text: str) -> None:
    log_dir = ensure_dir(output_root / "logs")
    with (log_dir / f"{stage}.log").open("a", encoding="utf-8") as handle:
        handle.write(text.rstrip() + "\n")


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


def write_baseline_manifest(output_root: Path, baseline_root: Path, eval006e_root: Path) -> dict[str, Any]:
    baseline_manifest = {
        "baseline_source_root": str(baseline_root),
        "baseline_checkpoint": str(baseline_root / "checkpoints" / "frozen_mainline" / "best.pt"),
        "baseline_report_006d": str(baseline_root / "task_real_006d_report.md"),
        "baseline_report_006e": str(eval006e_root / "task_real_006e_report.md"),
        "baseline_all_metrics_006e": str(eval006e_root / "mainline_vs_baselines_all_datasets.csv"),
    }
    write_json(output_root / "baseline_reference_manifest_007.json", baseline_manifest)
    return baseline_manifest


def _load_pc_model(output_root: Path) -> torch.nn.Module:
    model = UNet3DSmall(base_channels=8)
    ckpt = torch.load(output_root / "checkpoints" / "pc_p1" / "best.pt", map_location="cpu")
    model.load_state_dict(ckpt["model_state"])
    model.eval()
    return model


def _baseline_runtime_lookup(eval006e_root: Path) -> dict[tuple[str, str, str], float]:
    rows = list(csv.DictReader((eval006e_root / "per_sample_metrics_all_datasets.csv").open("r", encoding="utf-8")))
    return {(row["dataset"], row["sample_id"], row["method"]): float(row["runtime"]) for row in rows}


def _baseline_ours_lookup(eval006e_root: Path) -> dict[tuple[str, str], dict[str, float]]:
    rows = list(csv.DictReader((eval006e_root / "per_sample_metrics_all_datasets.csv").open("r", encoding="utf-8")))
    result = {}
    for row in rows:
        if row["method"] == "Ours":
            result[(row["dataset"], row["sample_id"])] = {
                "nmse": float(row["nmse"]),
                "psnr": float(row["psnr"]),
                "ssim": float(row["ssim"]),
                "runtime": float(row["runtime"]),
            }
    return result


def _baseline_bp_speed(eval006e_root: Path) -> dict[str, float]:
    rows = list(csv.DictReader((eval006e_root / "mainline_vs_baselines_all_datasets.csv").open("r", encoding="utf-8")))
    return {row["dataset"]: float(row["runtime_mean"]) for row in rows if row["method"] == "BP"}


def evaluate_pc_dataset(output_root: Path, baseline_root: Path, eval006e_root: Path, dataset_name: str) -> dict[str, Any]:
    dataset_info = DATASET_MAP[dataset_name]
    dataset_dir = dataset_info["dataset_dir"]
    rows = read_json(dataset_dir / "dataset" / "index.json")
    split_rows = [row for row in rows if row["split"] == dataset_info["split"]]
    model = _load_pc_model(output_root)
    baseline_lookup = _baseline_ours_lookup(eval006e_root)
    runtime_lookup = _baseline_runtime_lookup(eval006e_root)
    bp_runtime_mean = _baseline_bp_speed(eval006e_root)[dataset_name]
    records = []
    failure_counts = {"Baseline-Ours": {"F2": 0, "F3": 0, "F4": 0}, "Ours-PC-P1": {"F2": 0, "F3": 0, "F4": 0}}
    hardest_metrics = []
    pred_dir = ensure_dir(output_root / "predictions" / dataset_name.replace(" ", "_").lower())
    with torch.no_grad():
        for item in split_rows:
            gt_npz = np.load(dataset_dir / item["gt_volume_path"])
            coarse_npz = np.load(baseline_root / next(row["ref3_path"] for row in read_json(baseline_root / "learning_handoff_manifest_main_800_100_100.json")["samples"] if row["sample_id"] == item["sample_id"]) ) if dataset_name=="Main Test" else None
            # Rebuild coarse from saved ref3 prediction cache where available.
            if dataset_name == "Main Test":
                coarse_volume = coarse_npz["volume"]
            else:
                cache_key = {
                    "Unseen-Parameter OOD": "unseen_param_ood",
                    "Leave-One-Family-Out Focused OOD": "leave_one_family_out_ood",
                    "Random-ET OOD": "random_et_ood",
                }[dataset_name]
                coarse_path = eval006e_root / "comparison_cache" / cache_key / f"{item['sample_id']}_Ref3.npz"
                coarse_volume = np.load(coarse_path)["volume"]
            gt = _fit_to_shape(gt_npz["volume"], TARGET_SHAPE)
            coarse = _fit_to_shape(coarse_volume, TARGET_SHAPE)
            coarse, gt = _normalize_pair(coarse, gt)
            input_tensor = torch.from_numpy(coarse[None, None, ...])
            t0 = time.perf_counter()
            pred = model(input_tensor).numpy()[0, 0]
            pred_runtime = time.perf_counter() - t0
            np.savez_compressed(pred_dir / f"{item['sample_id']}_pc_pred.npz", pred=pred.astype(np.float32), coarse=coarse.astype(np.float32), gt=gt.astype(np.float32))
            baseline_stats = baseline_lookup[(dataset_name, item["sample_id"])]
            ref3_runtime = runtime_lookup[(dataset_name, item["sample_id"], "Ref3")]
            pc_runtime = ref3_runtime + pred_runtime
            records.append(
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
                }
            )
            records.append(
                {
                    "dataset": dataset_name,
                    "sample_id": item["sample_id"],
                    "family": item.get("family", "random_et"),
                    "model": "Ours-PC-P1",
                    "NMSE": nmse(pred, gt),
                    "PSNR": psnr(pred, gt),
                    "SSIM": ssim_global(pred, gt),
                    "runtime": pc_runtime,
                    "speedup_vs_BP": bp_runtime_mean / pc_runtime if pc_runtime > 0 else 0.0,
                }
            )
            base_fail = _failure_tags(coarse if dataset_name != "Main Test" else coarse, gt, item.get("family", "random_et"), baseline_stats["nmse"])
            pc_fail = _failure_tags(pred, gt, item.get("family", "random_et"), nmse(pred, gt))
            for label in ["F2", "F3", "F4"]:
                if label in base_fail["tags"]:
                    failure_counts["Baseline-Ours"][label] += 1
                if label in pc_fail["tags"]:
                    failure_counts["Ours-PC-P1"][label] += 1
            if item.get("family", "random_et") in HARD_FAMILIES:
                hardest_metrics.append(
                    {
                        "dataset": dataset_name,
                        "family": item["family"],
                        "baseline_nmse": baseline_stats["nmse"],
                        "pc_nmse": nmse(pred, gt),
                        "baseline_psnr": baseline_stats["psnr"],
                        "pc_psnr": psnr(pred, gt),
                        "baseline_ssim": baseline_stats["ssim"],
                        "pc_ssim": ssim_global(pred, gt),
                    }
                )
    grouped = {"Baseline-Ours": [], "Ours-PC-P1": []}
    for row in records:
        grouped[row["model"]].append(row)
    summary_rows = []
    for model_name, values in grouped.items():
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
    return {"summary_rows": summary_rows, "per_sample": records, "failure_counts": failure_counts, "hardest_metrics": hardest_metrics}


def _write_dataset_summary(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["dataset", "model", "NMSE_mean", "NMSE_std", "PSNR_mean", "PSNR_std", "SSIM_mean", "SSIM_std", "runtime_mean", "runtime_std", "speedup_vs_BP", "num_samples"])
        writer.writeheader()
        writer.writerows(rows)


def run_eval(output_root: Path, baseline_root: Path, eval006e_root: Path, scope: str) -> None:
    datasets = ["Main Test"] if scope == "main" else [name for name in DATASET_MAP if name != "Main Test"]
    all_summaries = []
    all_per_sample = []
    all_failure_rows = []
    all_family_rows = []
    for dataset_name in datasets:
        payload = evaluate_pc_dataset(output_root, baseline_root, eval006e_root, dataset_name)
        all_summaries.extend(payload["summary_rows"])
        all_per_sample.extend(payload["per_sample"])
        for model_name, counts in payload["failure_counts"].items():
            for label in ["F2", "F3", "F4"]:
                all_failure_rows.append({"dataset": dataset_name, "model": model_name, "failure_label": label, "count": counts[label]})
        all_family_rows.extend(payload["hardest_metrics"])
    mapping = {
        "Main Test": "metrics_baseline_vs_pc_main.csv",
        "Unseen-Parameter OOD": "metrics_baseline_vs_pc_unseen_param_ood.csv",
        "Leave-One-Family-Out Focused OOD": "metrics_baseline_vs_pc_leave_one_family_out_ood.csv",
        "Random-ET OOD": "metrics_baseline_vs_pc_random_et_ood.csv",
    }
    for dataset_name in datasets:
        rows = [row for row in all_summaries if row["dataset"] == dataset_name]
        _write_dataset_summary(output_root / mapping[dataset_name], rows)
    _merge_csv_rows(
        output_root / "failure_mode_pc_improvement.csv",
        ["dataset", "model", "failure_label", "count"],
        all_failure_rows,
        ["dataset", "model", "failure_label"],
    )
    _merge_csv_rows(
        output_root / "hardest_family_pc_improvement.csv",
        ["dataset", "family", "baseline_nmse", "pc_nmse", "baseline_psnr", "pc_psnr", "baseline_ssim", "pc_ssim"],
        all_family_rows,
        ["dataset", "family", "baseline_nmse", "pc_nmse", "baseline_psnr", "pc_psnr", "baseline_ssim", "pc_ssim"],
    )
    with (output_root / f"per_sample_pc_{scope}.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["dataset", "sample_id", "family", "model", "NMSE", "PSNR", "SSIM", "runtime", "speedup_vs_BP"])
        writer.writeheader()
        writer.writerows(all_per_sample)
    _stage_log(output_root, f"run_pc_eval_{scope}", f"datasets={datasets}")


def render_viz(output_root: Path) -> None:
    progress = ensure_dir(output_root / "viz" / "progress" / "curves")
    paper = ensure_dir(output_root / "viz" / "paper_candidates" / "curves")
    qual = ensure_dir(output_root / "viz" / "paper_candidates" / "qualitative")
    all_rows = []
    for filename in [
        "metrics_baseline_vs_pc_main.csv",
        "metrics_baseline_vs_pc_unseen_param_ood.csv",
        "metrics_baseline_vs_pc_leave_one_family_out_ood.csv",
        "metrics_baseline_vs_pc_random_et_ood.csv",
    ]:
        all_rows.extend(list(csv.DictReader((output_root / filename).open("r", encoding="utf-8"))))

    # baseline vs pc main metrics
    main_rows = [row for row in all_rows if row["dataset"] == "Main Test"]
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.2))
    for ax, key in zip(axes, ["NMSE_mean", "PSNR_mean", "SSIM_mean"]):
        vals = [float(next(row[key] for row in main_rows if row["model"] == model)) for model in ["Baseline-Ours", "Ours-PC-P1"]]
        ax.bar(["Baseline", "PC-P1"], vals)
        ax.set_title(key.replace("_mean", ""))
    fig.tight_layout()
    fig.savefig(progress / "baseline_vs_pc_main_metrics.png", dpi=170)
    plt.close(fig)

    # ood metrics
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.3))
    ood_names = ["Unseen-Parameter OOD", "Leave-One-Family-Out Focused OOD", "Random-ET OOD"]
    for ax, key in zip(axes, ["NMSE_mean", "PSNR_mean", "SSIM_mean"]):
        x = np.arange(len(ood_names))
        baseline = [float(next(row[key] for row in all_rows if row["dataset"] == ds and row["model"] == "Baseline-Ours")) for ds in ood_names]
        pc = [float(next(row[key] for row in all_rows if row["dataset"] == ds and row["model"] == "Ours-PC-P1")) for ds in ood_names]
        ax.bar(x - 0.18, baseline, width=0.36, label="Baseline")
        ax.bar(x + 0.18, pc, width=0.36, label="PC-P1")
        ax.set_xticks(x)
        ax.set_xticklabels(["Unseen", "LeaveOne", "RandomET"], rotation=15)
        ax.set_title(key.replace("_mean", ""))
    axes[0].legend()
    fig.tight_layout()
    fig.savefig(progress / "baseline_vs_pc_ood_metrics.png", dpi=170)
    fig.savefig(paper / "fig_pc_ood_metrics.png", dpi=170)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
    datasets = ["Main Test"] + ood_names
    x = np.arange(len(datasets))
    for model_name in ["Baseline-Ours", "Ours-PC-P1"]:
        runtimes = [float(next(row["runtime_mean"] for row in all_rows if row["dataset"] == ds and row["model"] == model_name)) for ds in datasets]
        speedups = [float(next(row["speedup_vs_BP"] for row in all_rows if row["dataset"] == ds and row["model"] == model_name)) for ds in datasets]
        axes[0].plot(x, runtimes, marker="o", label=model_name)
        axes[1].plot(x, speedups, marker="o", label=model_name)
    for ax in axes:
        ax.set_xticks(x)
        ax.set_xticklabels(["Main", "Unseen", "LeaveOne", "RandomET"], rotation=15)
        ax.legend()
    axes[0].set_title("Runtime")
    axes[1].set_title("Speedup vs BP")
    fig.tight_layout()
    fig.savefig(progress / "baseline_vs_pc_runtime_speedup.png", dpi=170)
    plt.close(fig)

    failure_rows = list(csv.DictReader((output_root / "failure_mode_pc_improvement.csv").open("r", encoding="utf-8")))
    fig, ax = plt.subplots(figsize=(10, 4.5))
    labels = ["F2", "F3", "F4"]
    x = np.arange(len(labels))
    width = 0.2
    for idx, dataset_name in enumerate(datasets):
        base = [int(next(row["count"] for row in failure_rows if row["dataset"] == dataset_name and row["model"] == "Baseline-Ours" and row["failure_label"] == label)) for label in labels]
        pc = [int(next(row["count"] for row in failure_rows if row["dataset"] == dataset_name and row["model"] == "Ours-PC-P1" and row["failure_label"] == label)) for label in labels]
        ax.plot(x, np.array(base) - np.array(pc), marker="o", label=dataset_name)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_title("Baseline vs PC failure mode improvement")
    ax.legend(ncol=2, fontsize=8)
    fig.tight_layout()
    fig.savefig(progress / "baseline_vs_pc_failure_modes.png", dpi=170)
    plt.close(fig)

    family_rows = list(csv.DictReader((output_root / "hardest_family_pc_improvement.csv").open("r", encoding="utf-8")))
    fig, ax = plt.subplots(figsize=(10, 4.5))
    family_names = HARD_FAMILIES
    x = np.arange(len(family_names))
    baseline = [float(np.mean([float(row["baseline_nmse"]) for row in family_rows if row["family"] == family])) for family in family_names]
    pc = [float(np.mean([float(row["pc_nmse"]) for row in family_rows if row["family"] == family])) for family in family_names]
    ax.bar(x - 0.18, baseline, width=0.36, label="Baseline")
    ax.bar(x + 0.18, pc, width=0.36, label="PC-P1")
    ax.set_xticks(x)
    ax.set_xticklabels(family_names, rotation=20)
    ax.set_title("Baseline vs PC hardest families")
    ax.legend()
    fig.tight_layout()
    fig.savefig(progress / "baseline_vs_pc_hardest_families.png", dpi=170)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.5, 5))
    for model_name in ["Baseline-Ours", "Ours-PC-P1"]:
        runtimes = [float(next(row["runtime_mean"] for row in all_rows if row["dataset"] == ds and row["model"] == model_name)) for ds in datasets]
        nmse_vals = [float(next(row["NMSE_mean"] for row in all_rows if row["dataset"] == ds and row["model"] == model_name)) for ds in datasets]
        ax.scatter(runtimes, nmse_vals, s=60, label=model_name)
        ax.plot(runtimes, nmse_vals, alpha=0.5)
    ax.set_xlabel("Runtime")
    ax.set_ylabel("NMSE mean")
    ax.set_title("Baseline vs PC frontier OOD")
    ax.legend()
    fig.tight_layout()
    fig.savefig(progress / "baseline_vs_pc_frontier_ood.png", dpi=170)
    plt.close(fig)

    # qualitative using main dataset predictions
    per_main = list(csv.DictReader((output_root / "per_sample_pc_main.csv").open("r", encoding="utf-8")))
    best = max(
        [row for row in per_main if row["model"] == "Ours-PC-P1"],
        key=lambda row: float(next(r["NMSE"] for r in per_main if r["model"] == "Baseline-Ours" and r["sample_id"] == row["sample_id"])) - float(row["NMSE"]),
    )
    failure = max([row for row in per_main if row["model"] == "Ours-PC-P1"], key=lambda row: float(row["NMSE"]))
    source_root = DEFAULT_BASELINE_ROOT
    for key, target in [(best["sample_id"], qual / "pc_best_case_panel.png"), (failure["sample_id"], qual / "pc_failure_case_panel.png")]:
        baseline_pred = np.load(source_root / "predictions" / "frozen_mainline" / f"{key}_M2_pred.npz")
        pc_pred = np.load(output_root / "predictions" / "main_test" / f"{key}_pc_pred.npz")
        fig, axes = plt.subplots(1, 4, figsize=(12, 3.5))
        z_idx = baseline_pred["gt"].shape[2] // 2
        panels = [("GT", baseline_pred["gt"]), ("Baseline", baseline_pred["pred"]), ("PC-P1", pc_pred["pred"]), ("AbsErr(PC)", np.abs(pc_pred["pred"] - baseline_pred["gt"]))]
        for ax, (label, volume) in zip(axes, panels):
            cmap = "inferno" if "Err" in label else "viridis"
            ax.imshow(volume[:, :, z_idx], cmap=cmap)
            ax.set_title(label)
            ax.axis("off")
        fig.tight_layout()
        fig.savefig(target, dpi=170)
        plt.close(fig)


def git_update(output_root: Path) -> dict[str, Any]:
    files_to_add = [
        "workspace/train/physics_consistency.py",
        "workspace/train/train_pc_p1.py",
        "workspace/eval/task_real_007_pc_comparison.py",
        "scripts/run_pc_training_P1.sh",
        "scripts/run_pc_training_P2.sh",
        "scripts/run_pc_eval_main.sh",
        "scripts/run_pc_eval_ood.sh",
        "scripts/render_pc_comparison_viz.sh",
        "scripts/update_git_and_record_007.sh",
        "CHANGELOG_DEV.md",
        "debug.md",
    ]
    subprocess.run(["git", "add", *files_to_add], cwd=PROJECT_ROOT, check=True)
    commit_proc = subprocess.run(["git", "commit", "-m", "task_real_007: add physics-consistency controlled comparison"], cwd=PROJECT_ROOT, text=True, capture_output=True)
    if commit_proc.returncode not in (0, 1):
        raise RuntimeError(commit_proc.stderr)
    commit_hash = subprocess.run(["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, text=True, capture_output=True, check=True).stdout.strip()
    status = subprocess.run(["git", "status", "--short"], cwd=PROJECT_ROOT, text=True, capture_output=True, check=True).stdout
    remote_result = subprocess.run(["git", "remote"], cwd=PROJECT_ROOT, text=True, capture_output=True, check=True).stdout.strip().splitlines()
    pushed = False
    push_message = "local commit only"
    if remote_result:
        push_proc = subprocess.run(["git", "push"], cwd=PROJECT_ROOT, text=True, capture_output=True)
        pushed = push_proc.returncode == 0
        push_message = "push succeeded" if pushed else f"push failed: {push_proc.stderr.strip() or push_proc.stdout.strip()}"
    summary = {
        "commit_hash": commit_hash,
        "git_status": status,
        "push_result": push_message,
    }
    write_text(
        output_root / "git_update_summary.md",
        "\n".join(
            [
                "# git_update_summary",
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
    return summary


def generate_report(output_root: Path, baseline_root: Path, eval006e_root: Path, git_summary: dict[str, Any] | None) -> None:
    main_rows = list(csv.DictReader((output_root / "metrics_baseline_vs_pc_main.csv").open("r", encoding="utf-8")))
    unseen_rows = list(csv.DictReader((output_root / "metrics_baseline_vs_pc_unseen_param_ood.csv").open("r", encoding="utf-8")))
    leave_rows = list(csv.DictReader((output_root / "metrics_baseline_vs_pc_leave_one_family_out_ood.csv").open("r", encoding="utf-8")))
    random_rows = list(csv.DictReader((output_root / "metrics_baseline_vs_pc_random_et_ood.csv").open("r", encoding="utf-8")))
    report = f"""# task_real_007_report

## 1. Task Goal

Add a minimal sampled forward echo consistency loss on top of the frozen 800-scale baseline and compare Baseline-Ours vs Ours-PC-P1 on the frozen main test and three OOD datasets.

## 2. Frozen Baseline Reused

- baseline source root: `{baseline_root}`
- baseline checkpoint: `{baseline_root / 'checkpoints/frozen_mainline/best.pt'}`
- six-method background reference: `{eval006e_root / 'task_real_006e_report.md'}`

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

## 4. Boundary Statement

This task only compares Baseline-Ours vs Ours-PC-P1. No six-method rerun, no new data, no front-end replacement, and no new backbone were introduced.

## 5. Physics-Consistency Design

P1 uses sampled forward echo consistency:

`L_total = L_image + lambda_pc * L_echo`

where `L_echo` is echo-domain NMSE on a fixed sparse subset of the original cylindrical measurements. The executed config is stored at `{output_root / 'consistency_config_P1.yaml'}`.

P2 was not executed in this run because the task only requires it as an optional enhancement after validating P1.

## 6. Training Matrix

- Baseline-Ours: reused only, not retrained
- Ours-PC-P1: trained from the baseline checkpoint with the added echo consistency term
- Ours-PC-P2: not executed

## 7. Main Test Comparison

- `{output_root / 'metrics_baseline_vs_pc_main.csv'}`

## 8. OOD Comparison

- `{output_root / 'metrics_baseline_vs_pc_unseen_param_ood.csv'}`
- `{output_root / 'metrics_baseline_vs_pc_leave_one_family_out_ood.csv'}`
- `{output_root / 'metrics_baseline_vs_pc_random_et_ood.csv'}`

## 9. Failure-Mode Improvement

- `{output_root / 'failure_mode_pc_improvement.csv'}`

## 10. Hardest-Family Improvement

- `{output_root / 'hardest_family_pc_improvement.csv'}`

## 11. Visual Outputs

- `{output_root / 'viz/progress/curves/baseline_vs_pc_main_metrics.png'}`
- `{output_root / 'viz/progress/curves/baseline_vs_pc_ood_metrics.png'}`
- `{output_root / 'viz/progress/curves/baseline_vs_pc_runtime_speedup.png'}`
- `{output_root / 'viz/progress/curves/baseline_vs_pc_failure_modes.png'}`
- `{output_root / 'viz/progress/curves/baseline_vs_pc_hardest_families.png'}`
- `{output_root / 'viz/progress/curves/baseline_vs_pc_frontier_ood.png'}`
- `{output_root / 'viz/paper_candidates/qualitative/pc_best_case_panel.png'}`
- `{output_root / 'viz/paper_candidates/qualitative/pc_failure_case_panel.png'}`

## 12. Git Update Summary

`{output_root / 'git_update_summary.md'}`

## 13. Remaining Issues

- P2 was not executed.
- This comparison still inherits the 800-scale frozen protocol rather than a larger formal-scale dataset.

## 14. Is Physics-Consistency Worth Keeping?

`conditional`

P1 should be kept if it improves at least one of the main/OOD aggregates or materially reduces `F2/F3/F4` on the hardest families without changing runtime materially. The final CSVs determine that conclusion directly.

## 15. Suggested Next Task

If P1 is beneficial, continue to the next controlled refinement or write it into the main method section; otherwise keep it as an ablation-side branch and retain the frozen baseline as the main method.

### Key file paths for ChatGPT controller

- report path: `{output_root / 'task_real_007_report.md'}`
- baseline reference path: `{output_root / 'baseline_reference_manifest_007.json'}`
- consistency config path: `{output_root / 'consistency_config_P1.yaml'}`
- metrics path: `{output_root / 'metrics_baseline_vs_pc_main.csv'}`, `{output_root / 'metrics_baseline_vs_pc_unseen_param_ood.csv'}`, `{output_root / 'metrics_baseline_vs_pc_leave_one_family_out_ood.csv'}`, `{output_root / 'metrics_baseline_vs_pc_random_et_ood.csv'}`
- failure-mode path: `{output_root / 'failure_mode_pc_improvement.csv'}`
- family path: `{output_root / 'hardest_family_pc_improvement.csv'}`
- curves path: `{output_root / 'viz/progress/curves'}`
- representative visuals path: `{output_root / 'viz/paper_candidates/qualitative'}`
- git summary path: `{output_root / 'git_update_summary.md'}`
- logs path: `{output_root / 'logs'}`
"""
    write_text(output_root / "task_real_007_report.md", report)


def finalize_tree(output_root: Path) -> None:
    entries = sorted(str(path) for path in output_root.rglob("*"))
    write_text(output_root / "tree.txt", "\n".join(entries) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="task_real_007 pc comparison")
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--baseline-root", default=str(DEFAULT_BASELINE_ROOT))
    parser.add_argument("--eval006e-root", default=str(DEFAULT_EVAL006E_ROOT))
    parser.add_argument("--stage", required=True, choices=["baseline_manifest", "eval_main", "eval_ood", "viz", "git", "report"])
    args = parser.parse_args()
    output_root = Path(args.output_root)
    baseline_root = Path(args.baseline_root)
    eval006e_root = Path(args.eval006e_root)
    _ensure_dirs(output_root)
    git_summary = None
    if args.stage == "baseline_manifest":
        write_baseline_manifest(output_root, baseline_root, eval006e_root)
    elif args.stage == "eval_main":
        run_eval(output_root, baseline_root, eval006e_root, "main")
    elif args.stage == "eval_ood":
        run_eval(output_root, baseline_root, eval006e_root, "ood")
    elif args.stage == "viz":
        render_viz(output_root)
    elif args.stage == "git":
        git_summary = git_update(output_root)
    elif args.stage == "report":
        summary = None
        if (output_root / "git_update_summary.md").exists():
            summary = {"path": str(output_root / "git_update_summary.md")}
        generate_report(output_root, baseline_root, eval006e_root, summary)
        finalize_tree(output_root)
    print(f"task_real_007 stage={args.stage} completed output_root={output_root}")


if __name__ == "__main__":
    main()
