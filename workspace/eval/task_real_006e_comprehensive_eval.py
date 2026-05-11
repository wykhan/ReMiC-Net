from __future__ import annotations

import argparse
import csv
import json
import shutil
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import torch

from workspace.common.io_utils import ensure_dir, read_json, write_json, write_text
from workspace.eval.metrics_3d import nmse, psnr, ssim_global
from workspace.recon.cyl_fast_reference_engine import reconstruct_cylindrical_reference
from workspace.train.train_two_stage_et import TARGET_SHAPE, _fit_to_shape, _normalize_pair


PROJECT_ROOT = Path("/home/superws/2026_Projects/Codex_reference_plane_real")
DEFAULT_SOURCE_ROOT = PROJECT_ROOT / "exp" / "task_real_006d_800_formal" / "20260419_112717"
DISPLAY_METHODS = ["Ref3", "Ref5", "Ref7", "Ref9", "BP", "Ours"]
METHOD_TO_INTERNAL = {"Ref3": "ref3", "Ref5": "ref5", "Ref7": "ref7", "Ref9": "ref9", "BP": "BP", "Ours": "Ours"}
DATASET_ORDER = ["Main Test", "Unseen-Parameter OOD", "Leave-One-Family-Out Focused OOD", "Random-ET OOD"]
OOD_DATASET_TO_DIR = {
    "Unseen-Parameter OOD": "unseen_param_ood",
    "Leave-One-Family-Out Focused OOD": "leave_one_family_out_ood",
    "Random-ET OOD": "random_et_ood",
}
OOD_DATASET_TO_CSV = {
    "Unseen-Parameter OOD": "ood_unseen_param_metrics_all_methods.csv",
    "Leave-One-Family-Out Focused OOD": "ood_leave_one_family_out_metrics_all_methods.csv",
    "Random-ET OOD": "ood_random_et_metrics_all_methods.csv",
}


def _stage_log(output_root: Path, stage: str, text: str) -> None:
    log_dir = ensure_dir(output_root / "logs")
    with (log_dir / f"{stage}.log").open("a", encoding="utf-8") as handle:
        handle.write(text.rstrip() + "\n")


def _ensure_dirs(output_root: Path) -> None:
    for rel in [
        "logs",
        "viz/progress/curves",
        "viz/progress/recon_compare",
        "viz/progress/slices",
        "viz/paper_candidates/curves",
        "viz/paper_candidates/qualitative",
        "viz/paper_candidates/tables_as_figs",
        "viz/paper_candidates/supplementary",
        "viz/manifest",
        "comparison_cache",
    ]:
        ensure_dir(output_root / rel)


def _load_model(source_root: Path) -> torch.nn.Module:
    from workspace.models.unet3d_small import UNet3DSmall

    model = UNet3DSmall(base_channels=8)
    ckpt = torch.load(source_root / "checkpoints" / "frozen_mainline" / "best.pt", map_location="cpu")
    model.load_state_dict(ckpt["model_state"])
    model.eval()
    return model


def build_evaluation_manifest(output_root: Path, source_root: Path) -> dict[str, Any]:
    manifest = {
        "task": "task_real_006e",
        "source_task": "task_real_006d",
        "source_root": str(source_root),
        "frozen_checkpoint": str(source_root / "checkpoints" / "frozen_mainline" / "best.pt"),
        "methods": DISPLAY_METHODS,
        "datasets": DATASET_ORDER,
        "metrics": ["NMSE", "PSNR", "SSIM", "runtime", "speedup_vs_BP"],
        "boundary_statement": "Evaluation only. No retraining, no dataset changes, no protocol changes, no physics-consistency.",
    }
    write_json(output_root / "evaluation_manifest_006e.json", manifest)
    _stage_log(output_root, "build_manifest", json.dumps(manifest, ensure_ascii=False))
    return manifest


def _aggregate(records: list[dict[str, Any]], bp_runtime_mean: float) -> dict[str, Any]:
    nmse_values = np.array([row["nmse"] for row in records], dtype=np.float64)
    psnr_values = np.array([row["psnr"] for row in records], dtype=np.float64)
    ssim_values = np.array([row["ssim"] for row in records], dtype=np.float64)
    runtime_values = np.array([row["runtime"] for row in records], dtype=np.float64)
    return {
        "NMSE_mean": float(np.mean(nmse_values)),
        "NMSE_std": float(np.std(nmse_values)),
        "NMSE_median": float(np.median(nmse_values)),
        "PSNR_mean": float(np.mean(psnr_values)),
        "PSNR_std": float(np.std(psnr_values)),
        "PSNR_median": float(np.median(psnr_values)),
        "SSIM_mean": float(np.mean(ssim_values)),
        "SSIM_std": float(np.std(ssim_values)),
        "SSIM_median": float(np.median(ssim_values)),
        "runtime_mean": float(np.mean(runtime_values)),
        "runtime_std": float(np.std(runtime_values)),
        "runtime_median": float(np.median(runtime_values)),
        "speedup_vs_BP": float(bp_runtime_mean / np.mean(runtime_values)) if np.mean(runtime_values) > 0 else 0.0,
        "num_samples": len(records),
    }


def _write_metrics_csv(path: Path, dataset_name: str, grouped: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    bp_runtime_mean = float(np.mean([row["runtime"] for row in grouped["BP"]]))
    rows = []
    for method in DISPLAY_METHODS:
        stats = _aggregate(grouped[method], bp_runtime_mean)
        rows.append({"dataset": dataset_name, "method": method, **stats})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "dataset",
                "method",
                "NMSE_mean",
                "NMSE_std",
                "NMSE_median",
                "PSNR_mean",
                "PSNR_std",
                "PSNR_median",
                "SSIM_mean",
                "SSIM_std",
                "SSIM_median",
                "runtime_mean",
                "runtime_std",
                "runtime_median",
                "speedup_vs_BP",
                "num_samples",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    return rows


def evaluate_main_test(source_root: Path, output_root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    payload = read_json(source_root / "mainline_vs_baselines_metrics.json")
    per_sample = []
    for row in payload["per_sample"]:
        family = row.get("family", "unknown")
        method = row["method"]
        display_method = {
            "ref3": "Ref3",
            "ref5": "Ref5",
            "ref7": "Ref7",
            "ref9": "Ref9",
            "BP": "BP",
            "ref3+learning": "Ours",
        }[method]
        per_sample.append(
            {
                "dataset": "Main Test",
                "family": family,
                "sample_id": row["sample_id"],
                "method": display_method,
                "nmse": float(row["nmse"]),
                "psnr": float(row["psnr"]),
                "ssim": float(row["ssim"]),
                "runtime": float(row["wall_time_sec"]),
            }
        )
    grouped = defaultdict(list)
    for row in per_sample:
        grouped[row["method"]].append(row)
    summary_rows = _write_metrics_csv(output_root / "main_test_metrics_all_methods.csv", "Main Test", grouped)
    _stage_log(output_root, "run_main_test_all_methods_eval", f"main test evaluated samples={len(per_sample)}")
    return per_sample, summary_rows


def _evaluate_ood_dataset(source_root: Path, output_root: Path, dataset_name: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    dataset_dir = source_root / "datasets" / OOD_DATASET_TO_DIR[dataset_name]
    rows = read_json(dataset_dir / "dataset" / "index.json")
    cache_dir = ensure_dir(output_root / "comparison_cache" / OOD_DATASET_TO_DIR[dataset_name])
    model = _load_model(source_root)
    per_sample = []
    with torch.no_grad():
        for item in rows:
            gt_npz = np.load(dataset_dir / item["gt_volume_path"])
            gt = _fit_to_shape(gt_npz["volume"], TARGET_SHAPE)
            scene_path = dataset_dir / item["scene_path"]
            echo_path = dataset_dir / "dataset" / "echoes" / f"{item['sample_id']}_echo_sparse.npz"
            baseline_volumes: dict[str, np.ndarray] = {}
            baseline_runtime: dict[str, float] = {}
            for display_method in ["Ref3", "Ref5", "Ref7", "Ref9", "BP"]:
                internal_method = METHOD_TO_INTERNAL[display_method]
                t0 = time.perf_counter()
                result = reconstruct_cylindrical_reference(scene_path, echo_path, internal_method)
                runtime_val = time.perf_counter() - t0
                volume = _fit_to_shape(result["volume"], TARGET_SHAPE)
                volume, gt_norm = _normalize_pair(volume, gt)
                baseline_volumes[display_method] = volume
                baseline_runtime[display_method] = runtime_val
                np.savez_compressed(cache_dir / f"{item['sample_id']}_{display_method}.npz", volume=volume, gt=gt_norm)
                per_sample.append(
                    {
                        "dataset": dataset_name,
                        "family": item.get("family", "random_et"),
                        "sample_id": item["sample_id"],
                        "method": display_method,
                        "nmse": nmse(volume, gt_norm),
                        "psnr": psnr(volume, gt_norm),
                        "ssim": ssim_global(volume, gt_norm),
                        "runtime": runtime_val,
                    }
                )
            ref3_norm = baseline_volumes["Ref3"]
            gt_norm = _normalize_pair(ref3_norm, gt)[1]
            input_tensor = torch.from_numpy(ref3_norm[None, None, ...])
            t1 = time.perf_counter()
            pred = model(input_tensor).numpy()[0, 0]
            ours_runtime = baseline_runtime["Ref3"] + (time.perf_counter() - t1)
            per_sample.append(
                {
                    "dataset": dataset_name,
                    "family": item.get("family", "random_et"),
                    "sample_id": item["sample_id"],
                    "method": "Ours",
                    "nmse": nmse(pred, gt_norm),
                    "psnr": psnr(pred, gt_norm),
                    "ssim": ssim_global(pred, gt_norm),
                    "runtime": ours_runtime,
                }
            )
            np.savez_compressed(cache_dir / f"{item['sample_id']}_Ours.npz", volume=pred.astype(np.float32), gt=gt_norm.astype(np.float32))
    grouped = defaultdict(list)
    for row in per_sample:
        grouped[row["method"]].append(row)
    summary_rows = _write_metrics_csv(output_root / OOD_DATASET_TO_CSV[dataset_name], dataset_name, grouped)
    _stage_log(output_root, f"eval_{OOD_DATASET_TO_DIR[dataset_name]}", f"{dataset_name} evaluated samples={len(rows)}")
    return per_sample, summary_rows


def _write_per_sample_csv(output_root: Path, rows: list[dict[str, Any]]) -> None:
    with (output_root / "per_sample_metrics_all_datasets.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["dataset", "family", "sample_id", "method", "nmse", "psnr", "ssim", "runtime"])
        writer.writeheader()
        writer.writerows(rows)


def _write_all_dataset_summary(output_root: Path, rows: list[dict[str, Any]]) -> None:
    with (output_root / "mainline_vs_baselines_all_datasets.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "dataset",
                "method",
                "NMSE_mean",
                "NMSE_std",
                "NMSE_median",
                "PSNR_mean",
                "PSNR_std",
                "PSNR_median",
                "SSIM_mean",
                "SSIM_std",
                "SSIM_median",
                "runtime_mean",
                "runtime_std",
                "runtime_median",
                "speedup_vs_BP",
                "num_samples",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def run_eval_for_dataset(source_root: Path, output_root: Path, dataset_name: str) -> None:
    if dataset_name == "Main Test":
        per_sample, summary = evaluate_main_test(source_root, output_root)
    else:
        per_sample, summary = _evaluate_ood_dataset(source_root, output_root, dataset_name)
    existing_rows = []
    if (output_root / "per_sample_metrics_all_datasets.csv").exists():
        existing_rows.extend(list(csv.DictReader((output_root / "per_sample_metrics_all_datasets.csv").open("r", encoding="utf-8"))))
    existing_rows.extend(per_sample)
    _write_per_sample_csv(output_root, existing_rows)

    summary_path = output_root / "mainline_vs_baselines_all_datasets.csv"
    merged = []
    if summary_path.exists():
        merged.extend(list(csv.DictReader(summary_path.open("r", encoding="utf-8"))))
        merged = [row for row in merged if row["dataset"] != dataset_name]
    merged.extend(summary)
    merged.sort(key=lambda row: (DATASET_ORDER.index(row["dataset"]), DISPLAY_METHODS.index(row["method"])))
    _write_all_dataset_summary(output_root, merged)


def merge_all_dataset_metrics(output_root: Path) -> None:
    rows = list(csv.DictReader((output_root / "mainline_vs_baselines_all_datasets.csv").open("r", encoding="utf-8")))
    rows.sort(key=lambda row: (DATASET_ORDER.index(row["dataset"]), DISPLAY_METHODS.index(row["method"])))
    _write_all_dataset_summary(output_root, rows)
    _stage_log(output_root, "merge_all_dataset_metrics", f"merged_rows={len(rows)}")


def _position_for_dataset(rows: list[dict[str, Any]], dataset_name: str) -> str:
    subset = [row for row in rows if row["dataset"] == dataset_name]
    subset.sort(key=lambda row: float(row["NMSE_mean"]))
    ours = next(row for row in subset if row["method"] == "Ours")
    better_than = [row["method"] for row in subset if float(row["NMSE_mean"]) > float(ours["NMSE_mean"])]
    faster_than = [row["method"] for row in subset if row["method"] != "BP" and float(row["runtime_mean"]) < float(next(r["runtime_mean"] for r in subset if r["method"] == "BP"))]
    closest = min(
        [row for row in subset if row["method"] not in {"Ours", "BP"}],
        key=lambda row: abs(float(row["NMSE_mean"]) - float(ours["NMSE_mean"])),
    )["method"]
    return (
        f"### {dataset_name}\n\n"
        f"- Ours NMSE mean = `{float(ours['NMSE_mean']):.6f}`\n"
        f"- Ours ranking by NMSE = `{1 + subset.index(ours)}/{len(subset)}`\n"
        f"- Ours is closest in quality to `{closest}` among the traditional references.\n"
        f"- Ours outperforms: `{', '.join(better_than)}`\n"
        f"- Ours speedup_vs_BP = `{float(ours['speedup_vs_BP']):.3f}`\n"
        f"- Ours stays near the Ref3 runtime band if its runtime mean is closer to Ref3 than to BP.\n"
    )


def build_positioning_summary(output_root: Path) -> None:
    rows = list(csv.DictReader((output_root / "mainline_vs_baselines_all_datasets.csv").open("r", encoding="utf-8")))
    sections = ["# positioning_summary", ""]
    for dataset_name in DATASET_ORDER:
        sections.append(_position_for_dataset(rows, dataset_name))
    text = "\n".join(sections).strip() + "\n"
    write_text(output_root / "positioning_summary.md", text)
    _stage_log(output_root, "build_positioning_summary", "completed")


def _metric_rows(output_root: Path) -> list[dict[str, Any]]:
    return list(csv.DictReader((output_root / "mainline_vs_baselines_all_datasets.csv").open("r", encoding="utf-8")))


def _per_sample_rows(output_root: Path) -> list[dict[str, Any]]:
    return list(csv.DictReader((output_root / "per_sample_metrics_all_datasets.csv").open("r", encoding="utf-8")))


def _save_fig(fig: plt.Figure, progress_path: Path, paper_path: Path | None = None) -> None:
    fig.tight_layout()
    fig.savefig(progress_path, dpi=170)
    if paper_path is not None:
        fig.savefig(paper_path, dpi=170)
    plt.close(fig)


def _render_metric_grid(rows: list[dict[str, Any]], metric_key: str, title: str, output_path: Path) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    for ax, dataset_name in zip(axes.ravel(), DATASET_ORDER):
        subset = [row for row in rows if row["dataset"] == dataset_name]
        vals = [float(next(row[metric_key] for row in subset if row["method"] == method)) for method in DISPLAY_METHODS]
        ax.bar(DISPLAY_METHODS, vals, color=["#7d8597", "#8d99ae", "#90be6d", "#43aa8b", "#577590", "#f9844a"])
        ax.set_title(dataset_name)
        ax.tick_params(axis="x", rotation=20)
    fig.suptitle(title)
    _save_fig(fig, output_path)


def _render_distribution(rows: list[dict[str, Any]], metric_key: str, title: str, output_path: Path) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    for ax, dataset_name in zip(axes.ravel(), DATASET_ORDER):
        subset = [row for row in rows if row["dataset"] == dataset_name]
        data = [np.array([float(row[metric_key]) for row in subset if row["method"] == method], dtype=np.float64) for method in DISPLAY_METHODS]
        ax.boxplot(data, labels=DISPLAY_METHODS, showfliers=False)
        ax.set_title(dataset_name)
        ax.tick_params(axis="x", rotation=20)
    fig.suptitle(title)
    _save_fig(fig, output_path)


def _load_compare_volume(npz_path: Path) -> tuple[np.ndarray, np.ndarray]:
    payload = np.load(npz_path)
    key = "volume" if "volume" in payload else "pred"
    return payload[key], payload["gt"]


def _render_case_panel(cache_dir: Path, sample_id: str, title: str, output_path: Path) -> None:
    volumes = {}
    gt = None
    for method in DISPLAY_METHODS:
        npz_path = cache_dir / f"{sample_id}_{method}.npz"
        vol, gt_val = _load_compare_volume(npz_path)
        volumes[method] = vol
        gt = gt_val
    assert gt is not None
    vmax = float(np.max(gt)) if float(np.max(gt)) > 0 else 1.0
    z_idx = gt.shape[2] // 2
    fig, axes = plt.subplots(2, 4, figsize=(14, 7))
    panels = [("GT", gt)] + [(method, volumes[method]) for method in DISPLAY_METHODS] + [("AbsErr(Ours)", np.abs(volumes["Ours"] - gt))]
    for ax, (label, volume) in zip(axes.ravel(), panels):
        cmap = "inferno" if "AbsErr" in label else "viridis"
        vmax_local = None if "AbsErr" in label else vmax
        ax.imshow(volume[:, :, z_idx], cmap=cmap, vmin=0.0 if "AbsErr" not in label else None, vmax=vmax_local)
        ax.set_title(label)
        ax.axis("off")
    fig.suptitle(title)
    _save_fig(fig, output_path)


def render_visuals(output_root: Path) -> None:
    metric_rows = _metric_rows(output_root)
    per_sample_rows = _per_sample_rows(output_root)
    progress_curves = ensure_dir(output_root / "viz" / "progress" / "curves")
    paper_curves = ensure_dir(output_root / "viz" / "paper_candidates" / "curves")
    qual_dir = ensure_dir(output_root / "viz" / "paper_candidates" / "qualitative")

    # Main test metrics
    main_rows = [row for row in metric_rows if row["dataset"] == "Main Test"]
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.2))
    for ax, key in zip(axes, ["NMSE_mean", "PSNR_mean", "SSIM_mean"]):
        vals = [float(next(row[key] for row in main_rows if row["method"] == method)) for method in DISPLAY_METHODS]
        ax.bar(DISPLAY_METHODS, vals)
        ax.set_title(key.replace("_mean", ""))
        ax.tick_params(axis="x", rotation=20)
    _save_fig(fig, progress_curves / "main_test_unified_metrics.png", paper_curves / "fig_main_metrics.png")

    _render_metric_grid(metric_rows, "NMSE_mean", "OOD NMSE unified", progress_curves / "ood_nmse_unified.png")
    _render_metric_grid(metric_rows, "PSNR_mean", "OOD PSNR unified", progress_curves / "ood_psnr_unified.png")
    _render_metric_grid(metric_rows, "SSIM_mean", "OOD SSIM unified", progress_curves / "ood_ssim_unified.png")

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2))
    x = np.arange(len(DATASET_ORDER))
    for idx, method in enumerate(DISPLAY_METHODS):
        runtimes = [float(next(row["runtime_mean"] for row in metric_rows if row["dataset"] == ds and row["method"] == method)) for ds in DATASET_ORDER]
        speedups = [float(next(row["speedup_vs_BP"] for row in metric_rows if row["dataset"] == ds and row["method"] == method)) for ds in DATASET_ORDER]
        axes[0].plot(x, runtimes, marker="o", label=method)
        axes[1].plot(x, speedups, marker="o", label=method)
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(DATASET_ORDER, rotation=20)
    axes[0].set_title("Runtime mean")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(DATASET_ORDER, rotation=20)
    axes[1].set_title("Speedup vs BP")
    axes[0].legend(ncol=3, fontsize=8)
    _save_fig(fig, progress_curves / "runtime_speedup_across_datasets.png")

    fig, ax = plt.subplots(figsize=(8, 5))
    for method in DISPLAY_METHODS:
        runtimes = np.array([float(next(row["runtime_mean"] for row in metric_rows if row["dataset"] == ds and row["method"] == method)) for ds in DATASET_ORDER])
        qualities = np.array([float(next(row["NMSE_mean"] for row in metric_rows if row["dataset"] == ds and row["method"] == method)) for ds in DATASET_ORDER])
        ax.scatter(runtimes, qualities, s=55, label=method)
        ax.annotate(method, (float(np.mean(runtimes)), float(np.mean(qualities))))
    ax.set_xlabel("Runtime mean")
    ax.set_ylabel("NMSE mean")
    ax.set_title("Frontier main and OOD")
    ax.grid(alpha=0.25)
    ax.legend(ncol=3, fontsize=8)
    _save_fig(fig, progress_curves / "frontier_main_and_ood.png", paper_curves / "fig_main_frontier.png")

    _render_distribution(per_sample_rows, "nmse", "NMSE distribution across datasets", progress_curves / "nmse_distribution_across_datasets.png")
    _render_distribution(per_sample_rows, "psnr", "PSNR distribution across datasets", progress_curves / "psnr_distribution_across_datasets.png")
    _render_distribution(per_sample_rows, "ssim", "SSIM distribution across datasets", progress_curves / "ssim_distribution_across_datasets.png")

    # OOD qualitative panels
    for dataset_name, png_name in [
        ("Unseen-Parameter OOD", "ood_unseen_param_case_panel.png"),
        ("Leave-One-Family-Out Focused OOD", "ood_leave_one_family_case_panel.png"),
        ("Random-ET OOD", "ood_random_et_case_panel.png"),
    ]:
        subset = [row for row in per_sample_rows if row["dataset"] == dataset_name and row["method"] == "Ours"]
        best = max(
            subset,
            key=lambda row: float(next(r["nmse"] for r in per_sample_rows if r["dataset"] == dataset_name and r["method"] == "Ref3" and r["sample_id"] == row["sample_id"])) - float(row["nmse"]),
        )
        cache_dir = output_root / "comparison_cache" / OOD_DATASET_TO_DIR[dataset_name]
        _render_case_panel(cache_dir, best["sample_id"], dataset_name, progress_curves / png_name)
    shutil.copyfile(progress_curves / "ood_unseen_param_case_panel.png", qual_dir / "fig_ood_case_best.png")
    shutil.copyfile(progress_curves / "ood_random_et_case_panel.png", qual_dir / "fig_ood_case_failure.png")
    shutil.copyfile(progress_curves / "ood_nmse_unified.png", paper_curves / "fig_ood_metrics.png")

    # manifest
    write_json(
        output_root / "viz" / "manifest" / "paper_candidates_manifest.json",
        {
            "paper_candidate_figures": [
                "fig_main_frontier.png",
                "fig_main_metrics.png",
                "fig_ood_metrics.png",
                "fig_ood_case_best.png",
                "fig_ood_case_failure.png",
            ]
        },
    )
    _stage_log(output_root, "render_006e_comprehensive_eval_viz", "completed")


def generate_report(output_root: Path, source_root: Path) -> None:
    metric_rows = _metric_rows(output_root)
    positioning = (output_root / "positioning_summary.md").read_text(encoding="utf-8")
    report = f"""# task_real_006e_report

## 1. Task Goal

Complete the comprehensive six-method evaluation on the main test and all three OOD datasets without retraining or changing the dataset protocol.

## 2. Frozen Inputs Reused

- source root: `{source_root}`
- frozen checkpoint: `{source_root / 'checkpoints/frozen_mainline/best.pt'}`
- frozen main dataset and all three OOD datasets from task_real_006d

## 3. Protocol / Context Files Used

- `CONTEXT/real_cylindrical_master_document_with_physics_consistency.md`
- `CONTEXT/simulation_protocol.md`
- `CONTEXT/reference_surface_strategy.md`
- `CONTEXT/dataset_protocol.md`
- `CONTEXT/et_dataset_protocol.md`
- `CONTEXT/et_dataset_protocol_800.md`
- `CONTEXT/visualization_protocol.md`
- `exp/task_real_006d_800_formal/20260419_112717/task_real_006d_report.md`

## 4. Boundary Statement

This task is evaluation-only. No retraining, no checkpoint replacement, no dataset modification, and no physics-consistency terms were introduced.

## 5. Evaluation Matrix

- methods: `{', '.join(DISPLAY_METHODS)}`
- datasets: `{', '.join(DATASET_ORDER)}`
- metrics: `NMSE / PSNR / SSIM / runtime / speedup_vs_BP`

## 6. Main Test Results

The main test all-method table is stored at `{output_root / 'main_test_metrics_all_methods.csv'}`.

## 7. OOD Results

- unseen-parameter OOD: `{output_root / 'ood_unseen_param_metrics_all_methods.csv'}`
- leave-one-family-out focused OOD: `{output_root / 'ood_leave_one_family_out_metrics_all_methods.csv'}`
- random-ET OOD: `{output_root / 'ood_random_et_metrics_all_methods.csv'}`

## 8. Positioning of Ours vs Baselines

{positioning}

## 9. Visual Outputs

- `{output_root / 'viz/progress/curves/main_test_unified_metrics.png'}`
- `{output_root / 'viz/progress/curves/ood_nmse_unified.png'}`
- `{output_root / 'viz/progress/curves/ood_psnr_unified.png'}`
- `{output_root / 'viz/progress/curves/ood_ssim_unified.png'}`
- `{output_root / 'viz/progress/curves/runtime_speedup_across_datasets.png'}`
- `{output_root / 'viz/progress/curves/frontier_main_and_ood.png'}`
- `{output_root / 'viz/progress/curves/nmse_distribution_across_datasets.png'}`
- `{output_root / 'viz/progress/curves/psnr_distribution_across_datasets.png'}`
- `{output_root / 'viz/progress/curves/ssim_distribution_across_datasets.png'}`
- `{output_root / 'viz/progress/curves/ood_unseen_param_case_panel.png'}`
- `{output_root / 'viz/progress/curves/ood_leave_one_family_case_panel.png'}`
- `{output_root / 'viz/progress/curves/ood_random_et_case_panel.png'}`

## 10. Remaining Issues

- This still builds on the 800-scale literature-matched dataset rather than the larger formal-scale target.
- Runtime is measured inside the current software stack and should be treated as controlled local timing rather than deployment timing.

## 11. Ready for Physics-Consistency Stage?

`conditional`

The evaluation matrix is now substantially more complete than in task_real_006d. Moving to task_real_007 is reasonable if the controller accepts the 800-scale frozen dataset as the controlled pre-physics baseline.

## 12. Suggested Next Task

`task_real_007`: introduce physics-consistency on top of the frozen 800-scale setup and compare against the fully evaluated six-method baseline matrix.

## Key file paths for ChatGPT controller

- report path: `{output_root / 'task_real_006e_report.md'}`
- all metrics path: `{output_root / 'mainline_vs_baselines_all_datasets.csv'}`
- per-sample path: `{output_root / 'per_sample_metrics_all_datasets.csv'}`
- positioning path: `{output_root / 'positioning_summary.md'}`
- curves path: `{output_root / 'viz/progress/curves'}`
- representative visuals path: `{output_root / 'viz/paper_candidates/qualitative'}`
- logs path: `{output_root / 'logs'}`
"""
    write_text(output_root / "task_real_006e_report.md", report)


def update_project_logs(output_root: Path) -> None:
    changelog = PROJECT_ROOT / "CHANGELOG_DEV.md"
    debug = PROJECT_ROOT / "debug.md"
    with changelog.open("a", encoding="utf-8") as handle:
        handle.write(
            "\n## 2026-04-19 task_real_006e\n\n"
            "- Added comprehensive six-method evaluation completion on main test and all three OOD datasets.\n"
            f"- Artifacts: `{output_root}`.\n"
        )
    with debug.open("a", encoding="utf-8") as handle:
        handle.write(
            "\n## 2026-04-19 task_real_006e\n\n"
            f"- output_root: `{output_root}`\n"
            "- comprehensive evaluation completed across 4 datasets and 6 methods.\n"
        )


def finalize_tree(output_root: Path) -> None:
    entries = sorted(str(path) for path in output_root.rglob("*"))
    write_text(output_root / "tree.txt", "\n".join(entries) + "\n")


def run_stage(output_root: Path, source_root: Path, stage: str, dataset_name: str | None) -> None:
    if stage == "manifest":
        build_evaluation_manifest(output_root, source_root)
    elif stage == "eval_dataset":
        assert dataset_name is not None
        run_eval_for_dataset(source_root, output_root, dataset_name)
    elif stage == "merge":
        merge_all_dataset_metrics(output_root)
    elif stage == "positioning":
        build_positioning_summary(output_root)
    elif stage == "viz":
        render_visuals(output_root)
    elif stage == "report":
        generate_report(output_root, source_root)
        update_project_logs(output_root)
        finalize_tree(output_root)
    elif stage == "all":
        build_evaluation_manifest(output_root, source_root)
        for ds in DATASET_ORDER:
            run_eval_for_dataset(source_root, output_root, ds)
        merge_all_dataset_metrics(output_root)
        build_positioning_summary(output_root)
        render_visuals(output_root)
        generate_report(output_root, source_root)
        update_project_logs(output_root)
        finalize_tree(output_root)
    else:
        raise ValueError(stage)


def main() -> None:
    parser = argparse.ArgumentParser(description="task_real_006e comprehensive evaluation")
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--source-root", default=str(DEFAULT_SOURCE_ROOT))
    parser.add_argument("--stage", required=True, choices=["manifest", "eval_dataset", "merge", "positioning", "viz", "report", "all"])
    parser.add_argument("--dataset-name", default=None)
    args = parser.parse_args()
    output_root = Path(args.output_root)
    source_root = Path(args.source_root)
    _ensure_dirs(output_root)
    run_stage(output_root, source_root, args.stage, args.dataset_name)
    print(f"task_real_006e stage={args.stage} completed output_root={output_root}")


if __name__ == "__main__":
    main()
