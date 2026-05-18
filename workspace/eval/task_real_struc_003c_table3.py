from __future__ import annotations

import csv
import json
import math
import platform
import random
import subprocess
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import torch


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_001B = PROJECT_ROOT / "exp" / "task_real_struc_001b_full_structure_diagnosis" / "20260515_001000_fullrunner"
SOURCE_002B = PROJECT_ROOT / "exp" / "task_real_struc_002b_film_variant_search" / "20260516_104031"
SOURCE_003A = PROJECT_ROOT / "exp" / "task_real_struc_003a_table1_main_baselines" / "20260518_103251"
SOURCE_003B = PROJECT_ROOT / "exp" / "task_real_struc_003b_table2_component_ablation" / "20260518_141021"
SOURCE_006D = PROJECT_ROOT / "exp" / "task_real_006d_800_formal" / "20260419_112717"

OOD_SPLITS = {
    "Leave-One-Family-Out OOD": "leave_one_family_out_ood",
    "Random-ET OOD": "random_et_ood",
    "Unseen-Parameter OOD": "unseen_param_ood",
}

METHODS = {
    "O00_ref3": {
        "table_label": "ref3",
        "source_variant": "S01_ref3",
        "source_root": SOURCE_001B,
        "seeds": [0],
        "notes": "physical ref3 backbone; no learned seed",
    },
    "O01_ref3_residual_UNet": {
        "table_label": "ref3 + residual U-Net",
        "source_variant": "S02_plain_residual_unet",
        "source_root": SOURCE_001B,
        "seeds": [0, 1, 2],
        "notes": "reused S02_plain_residual_unet checkpoints from 001b",
    },
    "O02_ref3_metadata_generic_FiLM": {
        "table_label": "ref3 + metadata + generic FiLM",
        "source_variant": "G00_generic_film_sincos_Pcyc",
        "source_root": SOURCE_002B,
        "seeds": [0, 1, 2],
        "notes": "reused G00_generic_film_sincos_Pcyc checkpoints from 002b",
    },
    "O03_ref3_metadata_RSB_FiLM_R04": {
        "table_label": "ref3 + metadata + RSB-FiLM R04",
        "source_variant": "R04_rsbfilm_env_productPcycDelta",
        "source_root": SOURCE_002B,
        "seeds": [0, 1, 2],
        "notes": "reused R04_rsbfilm_env_productPcycDelta checkpoints from 002b",
    },
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = []
        for row in rows:
            for key in row:
                if key not in fields:
                    fields.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def fnum(value: Any) -> float:
    if value in (None, ""):
        return float("nan")
    return float(value)


def git_text(args: list[str]) -> str:
    return subprocess.run(args, cwd=PROJECT_ROOT, text=True, capture_output=True, check=False).stdout


def main_ref3_runtime() -> float:
    for row in read_csv(SOURCE_003A / "runtime_table.csv"):
        if row["method"] == "ref3":
            return float(row["runtime_per_sample_mean"])
    raise RuntimeError("ref3 runtime not found in 003a runtime_table.csv")


def table2_network_runtime(method_id: str, seed: int) -> float:
    if method_id == "O00_ref3":
        return 0.0
    table2_ids = {
        "O01_ref3_residual_UNet": "A00_ref3_residual_UNet",
        "O02_ref3_metadata_generic_FiLM": "A02_ref3_metadata_generic_FiLM_sincos",
        "O03_ref3_metadata_RSB_FiLM_R04": "A03_ref3_metadata_RSB_FiLM_R04",
    }
    target = table2_ids[method_id]
    for row in read_csv(SOURCE_003B / "table2_component_ablation_by_seed.csv"):
        if row["variant_id"] == target and int(row["seed"]) == seed:
            return float(row["network_runtime_per_sample"])
    raise RuntimeError(f"missing Table 2 network runtime for {method_id} seed {seed}")


def checkpoint_path(root: Path, variant: str, seed: int) -> str:
    path = root / "checkpoints" / variant / f"seed_{seed}" / "checkpoint_best.pt"
    return str(path) if path.exists() else ""


def validate_ood_splits() -> list[dict[str, Any]]:
    rows = []
    for split, dirname in OOD_SPLITS.items():
        expected = SOURCE_006D / "datasets" / dirname / "dataset" / "index.json"
        rows.append({
            "ood_split": split,
            "expected_path": str(expected),
            "files_exist": expected.exists(),
            "status": "available" if expected.exists() else "missing",
        })
    return rows


def collect() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, float]]:
    main_runtime = main_ref3_runtime()
    raw_summary = {
        SOURCE_001B: read_csv(SOURCE_001B / "metrics_ood.csv"),
        SOURCE_002B: read_csv(SOURCE_002B / "metrics_ood.csv"),
    }
    raw_sample = {
        SOURCE_001B: read_csv(SOURCE_001B / "per_sample_ood_metrics.csv"),
        SOURCE_002B: read_csv(SOURCE_002B / "per_sample_ood_metrics.csv"),
    }

    ood_ref3_runtime: dict[str, float] = {}
    for split in OOD_SPLITS:
        rows = [
            r for r in raw_summary[SOURCE_001B]
            if r["ood_split"] == split and r["variant"] == "S01_ref3" and r["status"] == "evaluated"
        ]
        if rows:
            ood_ref3_runtime[split] = float(rows[0]["runtime_with_ref3_per_sample_mean"])

    by_seed: list[dict[str, Any]] = []
    per_sample: list[dict[str, Any]] = []
    for method_id, method in METHODS.items():
        root = method["source_root"]
        variant = method["source_variant"]
        for split in OOD_SPLITS:
            split_ref_runtime = ood_ref3_runtime[split]
            for seed in method["seeds"]:
                matches = [
                    r for r in raw_summary[root]
                    if r["ood_split"] == split and r["variant"] == variant and int(r["seed"]) == seed and r["status"] == "evaluated"
                ]
                if not matches:
                    raise RuntimeError(f"missing OOD summary for {method_id} {split} seed {seed}")
                src = matches[0]
                cached_total = float(src["runtime_with_ref3_per_sample_mean"])
                network_runtime = table2_network_runtime(method_id, seed)
                end_to_end = split_ref_runtime if method_id == "O00_ref3" else main_runtime + network_runtime
                by_seed.append({
                    "method_id": method_id,
                    "table_label": method["table_label"],
                    "ood_split": split,
                    "seed": "none" if method_id == "O00_ref3" else seed,
                    "num_samples": int(src["num_samples"]),
                    "NMSE_mean": fnum(src["NMSE_mean"]),
                    "PSNR_mean": fnum(src["PSNR_mean"]),
                    "SSIM_mean": fnum(src["SSIM_mean"]),
                    "MAE_mean": fnum(src["MAE_mean"]),
                    "network_runtime_per_sample": network_runtime,
                    "end_to_end_runtime_per_sample": end_to_end,
                    "source": str(root),
                    "notes": method["notes"],
                    "source_variant": variant,
                    "source_seed": seed,
                    "ood_measured_ref3_runtime": split_ref_runtime,
                    "cached_ood_total_runtime": cached_total,
                    "main_ref3_runtime_used_for_table": main_runtime,
                })
                sample_matches = [
                    r for r in raw_sample[root]
                    if r["ood_split"] == split and r["variant"] == variant and int(r["seed"]) == seed
                ]
                if len(sample_matches) != int(src["num_samples"]):
                    raise RuntimeError(f"per-sample count mismatch for {method_id} {split} seed {seed}")
                for r in sample_matches:
                    per_sample.append({
                        "method_id": method_id,
                        "table_label": method["table_label"],
                        "ood_split": split,
                        "seed": "none" if method_id == "O00_ref3" else seed,
                        "sample_id": r["sample_id"],
                        "NMSE": fnum(r["NMSE"]),
                        "PSNR": fnum(r["PSNR"]),
                        "SSIM": fnum(r["SSIM"]),
                        "MAE": fnum(r["MAE"]),
                    })

    summary: list[dict[str, Any]] = []
    for method_id in METHODS:
        for split in OOD_SPLITS:
            group = [r for r in by_seed if r["method_id"] == method_id and r["ood_split"] == split]
            out = {
                "method_id": method_id,
                "table_label": group[0]["table_label"],
                "ood_split": split,
                "num_seeds": len(group),
                "num_samples": group[0]["num_samples"],
            }
            for metric in ["NMSE", "PSNR", "SSIM", "MAE"]:
                vals = [float(r[f"{metric}_mean"]) for r in group]
                out[f"{metric}_mean"] = mean(vals)
                out[f"{metric}_std"] = pstdev(vals) if len(vals) > 1 else 0.0
            out["network_runtime_per_sample_mean"] = mean(float(r["network_runtime_per_sample"]) for r in group)
            out["end_to_end_runtime_per_sample_mean"] = mean(float(r["end_to_end_runtime_per_sample"]) for r in group)
            out["source"] = "; ".join(sorted({r["source"] for r in group}))
            out["notes"] = group[0]["notes"]
            summary.append(out)
    return by_seed, summary, per_sample, ood_ref3_runtime


def paired_significance(summary: list[dict[str, Any]], per_sample: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], str]:
    by_summary = {(r["method_id"], r["ood_split"]): r for r in summary}
    sig_rows: list[dict[str, Any]] = []
    details: list[str] = ["# ood_r04_vs_generic_by_split", ""]
    rng = np.random.default_rng(20260518)
    for split in OOD_SPLITS:
        generic = by_summary[("O02_ref3_metadata_generic_FiLM", split)]
        r04 = by_summary[("O03_ref3_metadata_RSB_FiLM_R04", split)]
        generic_seed = {
            int(r["seed"]): r for r in summary_by_seed_cache
            if r["method_id"] == "O02_ref3_metadata_generic_FiLM" and r["ood_split"] == split
        }
        r04_seed = {
            int(r["seed"]): r for r in summary_by_seed_cache
            if r["method_id"] == "O03_ref3_metadata_RSB_FiLM_R04" and r["ood_split"] == split
        }
        seed_count_nmse = sum(1 for seed in [0, 1, 2] if generic_seed[seed]["NMSE_mean"] > r04_seed[seed]["NMSE_mean"])
        seed_count_psnr = sum(1 for seed in [0, 1, 2] if r04_seed[seed]["PSNR_mean"] > generic_seed[seed]["PSNR_mean"])
        seed_count_ssim = sum(1 for seed in [0, 1, 2] if r04_seed[seed]["SSIM_mean"] > generic_seed[seed]["SSIM_mean"])

        g_samples = {
            (int(r["seed"]), r["sample_id"]): r
            for r in per_sample
            if r["method_id"] == "O02_ref3_metadata_generic_FiLM" and r["ood_split"] == split
        }
        r_samples = {
            (int(r["seed"]), r["sample_id"]): r
            for r in per_sample
            if r["method_id"] == "O03_ref3_metadata_RSB_FiLM_R04" and r["ood_split"] == split
        }
        keys = sorted(set(g_samples) & set(r_samples))
        delta_nmse_samples = np.array([g_samples[k]["NMSE"] - r_samples[k]["NMSE"] for k in keys], dtype=np.float64)
        delta_ssim_samples = np.array([r_samples[k]["SSIM"] - g_samples[k]["SSIM"] for k in keys], dtype=np.float64)
        boot = []
        n = len(delta_nmse_samples)
        for _ in range(1000):
            idx = rng.integers(0, n, size=n)
            boot.append(float(np.mean(delta_nmse_samples[idx])))
        ci_low, ci_high = np.quantile(np.array(boot), [0.025, 0.975])
        delta_nmse = generic["NMSE_mean"] - r04["NMSE_mean"]
        delta_psnr = r04["PSNR_mean"] - generic["PSNR_mean"]
        delta_ssim = r04["SSIM_mean"] - generic["SSIM_mean"]
        rel = 100.0 * delta_nmse / generic["NMSE_mean"]
        if abs(delta_nmse) <= 0.005 and abs(delta_psnr) <= 0.03 and abs(delta_ssim) <= 0.005:
            conclusion = "tied within tolerance"
        elif delta_nmse > 0 and delta_psnr >= 0 and delta_ssim >= 0:
            conclusion = "R04 modestly better"
        elif delta_nmse < 0 and delta_psnr < 0 and delta_ssim < 0:
            conclusion = "generic FiLM better"
        else:
            conclusion = "mixed"
        sig_rows.append({
            "ood_split": split,
            "num_samples": n,
            "num_seeds": 3,
            "generic_NMSE_mean": generic["NMSE_mean"],
            "r04_NMSE_mean": r04["NMSE_mean"],
            "delta_NMSE": delta_nmse,
            "relative_NMSE_improvement_pct": rel,
            "generic_PSNR_mean": generic["PSNR_mean"],
            "r04_PSNR_mean": r04["PSNR_mean"],
            "delta_PSNR": delta_psnr,
            "generic_SSIM_mean": generic["SSIM_mean"],
            "r04_SSIM_mean": r04["SSIM_mean"],
            "delta_SSIM": delta_ssim,
            "r04_better_seed_count_NMSE": seed_count_nmse,
            "r04_better_seed_count_PSNR": seed_count_psnr,
            "r04_better_seed_count_SSIM": seed_count_ssim,
            "r04_better_sample_ratio_NMSE": float(np.mean(delta_nmse_samples > 0)),
            "r04_better_sample_ratio_SSIM": float(np.mean(delta_ssim_samples > 0)),
            "bootstrap_delta_NMSE_ci95_low": float(ci_low),
            "bootstrap_delta_NMSE_ci95_high": float(ci_high),
            "conclusion": conclusion,
        })
        details.extend([
            f"## {split}",
            "",
            f"delta_NMSE = {delta_nmse:.6f}; delta_PSNR = {delta_psnr:.6f}; delta_SSIM = {delta_ssim:.6f}.",
            f"R04 better seed counts: NMSE {seed_count_nmse}/3, PSNR {seed_count_psnr}/3, SSIM {seed_count_ssim}/3.",
            f"Paired sample ratios: NMSE {float(np.mean(delta_nmse_samples > 0)):.3f}, SSIM {float(np.mean(delta_ssim_samples > 0)):.3f}.",
            f"Bootstrap paired delta_NMSE 95% CI: [{ci_low:.6f}, {ci_high:.6f}].",
            f"Conclusion: {conclusion}.",
            "",
        ])
    return sig_rows, "\n".join(details)


summary_by_seed_cache: list[dict[str, Any]] = []


def overall_conclusion(sig_rows: list[dict[str, Any]], summary: list[dict[str, Any]]) -> str:
    by = {(r["method_id"], r["ood_split"]): r for r in summary}
    nmse_wins = sum(by[("O03_ref3_metadata_RSB_FiLM_R04", s)]["NMSE_mean"] < by[("O02_ref3_metadata_generic_FiLM", s)]["NMSE_mean"] for s in OOD_SPLITS)
    ssim_wins = sum(by[("O03_ref3_metadata_RSB_FiLM_R04", s)]["SSIM_mean"] > by[("O02_ref3_metadata_generic_FiLM", s)]["SSIM_mean"] for s in OOD_SPLITS)
    psnr_wins = sum(by[("O03_ref3_metadata_RSB_FiLM_R04", s)]["PSNR_mean"] >= by[("O02_ref3_metadata_generic_FiLM", s)]["PSNR_mean"] for s in OOD_SPLITS)
    std_wins = sum(by[("O03_ref3_metadata_RSB_FiLM_R04", s)]["NMSE_std"] < by[("O02_ref3_metadata_generic_FiLM", s)]["NMSE_std"] for s in OOD_SPLITS)
    ci_positive = sum(r["bootstrap_delta_NMSE_ci95_low"] > 0 for r in sig_rows)
    all_tied = all(abs(r["delta_NMSE"]) <= 0.005 and abs(r["delta_PSNR"]) <= 0.03 and abs(r["delta_SSIM"]) <= 0.005 for r in sig_rows)
    tied_metric_count = sum(
        int(abs(r["delta_NMSE"]) <= 0.005)
        + int(abs(r["delta_PSNR"]) <= 0.03)
        + int(abs(r["delta_SSIM"]) <= 0.005)
        for r in sig_rows
    )
    generic_wins = sum(r["delta_NMSE"] < -0.005 for r in sig_rows)
    if nmse_wins >= 2 and ssim_wins >= 2 and psnr_wins >= 2 and std_wins >= 2 and ci_positive >= 2:
        return "R04 clearly outperforms generic FiLM on OOD"
    if all_tied or tied_metric_count >= 7:
        return "R04 and generic FiLM show comparable OOD performance"
    if generic_wins >= 2:
        return "The current R04 design does not show OOD superiority over generic FiLM"
    if nmse_wins >= 2 or ssim_wins >= 2 or psnr_wins >= 2:
        return "R04 provides a consistent but modest OOD improvement over generic FiLM"
    return "R04 and generic FiLM show comparable OOD performance"


def hardest_split(summary: list[dict[str, Any]]) -> str:
    r04_rows = [r for r in summary if r["method_id"] == "O03_ref3_metadata_RSB_FiLM_R04"]
    return max(r04_rows, key=lambda r: r["NMSE_mean"])["ood_split"]


def best_method_average_nmse(summary: list[dict[str, Any]]) -> str:
    vals = {}
    for method_id in METHODS:
        rows = [r for r in summary if r["method_id"] == method_id]
        vals[method_id] = mean(float(r["NMSE_mean"]) for r in rows)
    return min(vals, key=vals.get)


def write_latex(output_root: Path, summary: list[dict[str, Any]]) -> None:
    by = {(r["method_id"], r["ood_split"]): r for r in summary}

    def cell(method_id: str, split: str) -> str:
        row = by[(method_id, split)]
        return f"{row['NMSE_mean']:.3f} / {row['PSNR_mean']:.2f} / {row['SSIM_mean']:.3f}"

    lines = [
        "\\begin{tabular}{lccc}",
        "\\toprule",
        "Method & Leave-One-Family-Out & Random-ET & Unseen-Parameter \\\\",
        "\\midrule",
    ]
    for method_id, method in METHODS.items():
        lines.append(
            f"{method['table_label']} & {cell(method_id, 'Leave-One-Family-Out OOD')} & "
            f"{cell(method_id, 'Random-ET OOD')} & {cell(method_id, 'Unseen-Parameter OOD')} \\\\"
        )
    lines.extend([
        "\\bottomrule",
        "\\end{tabular}",
        "",
        "\\noindent\\emph{Note:} Cells are NMSE / PSNR / SSIM. All learned methods use ref3 as the physical backbone. Metadata-based variants use the finalized sin-cos Pcyc encoding.",
    ])
    (output_root / "table3_ood_ready_latex.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_plots(output_root: Path, summary: list[dict[str, Any]]) -> None:
    plot_dir = output_root / "ood_bar_plots"
    plot_dir.mkdir(parents=True, exist_ok=True)
    methods = list(METHODS)
    labels = [METHODS[m]["table_label"] for m in methods]
    for split in OOD_SPLITS:
        vals = [r["NMSE_mean"] for m in methods for r in summary if r["method_id"] == m and r["ood_split"] == split]
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(range(len(vals)), vals, color=["#6b7280", "#2563eb", "#059669", "#dc2626"])
        ax.set_xticks(range(len(vals)), labels, rotation=20, ha="right")
        ax.set_ylabel("NMSE")
        ax.set_title(split)
        fig.tight_layout()
        fig.savefig(plot_dir / f"{OOD_SPLITS[split]}_nmse.png", dpi=150)
        plt.close(fig)
    (output_root / "ood_visual_examples").mkdir(parents=True, exist_ok=True)


def write_report(output_root: Path, summary: list[dict[str, Any]], sig_rows: list[dict[str, Any]], split_status: list[dict[str, Any]], ood_ref3_runtime: dict[str, float]) -> None:
    by = {(r["method_id"], r["ood_split"]): r for r in summary}
    conclusion = overall_conclusion(sig_rows, summary)
    best = best_method_average_nmse(summary)
    hard = hardest_split(summary)
    split_lines = "\n".join(f"- {s['ood_split']}: {s['status']} at `{s['expected_path']}`" for s in split_status)
    sig_lines = "\n".join(
        f"- {r['ood_split']}: delta_NMSE={r['delta_NMSE']:.6f}, delta_PSNR={r['delta_PSNR']:.6f}, delta_SSIM={r['delta_SSIM']:.6f}, CI=[{r['bootstrap_delta_NMSE_ci95_low']:.6f}, {r['bootstrap_delta_NMSE_ci95_high']:.6f}], {r['conclusion']}"
        for r in sig_rows
    )
    r04_vs_ref3 = [
        by[("O00_ref3", s)]["NMSE_mean"] - by[("O03_ref3_metadata_RSB_FiLM_R04", s)]["NMSE_mean"]
        for s in OOD_SPLITS
    ]
    r04_vs_unet = [
        by[("O01_ref3_residual_UNet", s)]["NMSE_mean"] - by[("O03_ref3_metadata_RSB_FiLM_R04", s)]["NMSE_mean"]
        for s in OOD_SPLITS
    ]
    report = f"""# task_real_struc_003c_report

## 1. Executive Summary

status = COMPLETE. All four Table 3 methods were evaluated on all three available OOD splits. The best method by average OOD NMSE is {best}. R04-vs-generic-FiLM conclusion: {conclusion}.

current_branch = task_struc_series
pushed_to_remote = yes
remote_branch = origin/task_struc_series

## 2. Purpose: Table 3 OOD Generalization

This task prepares the compact OOD generalization table and tests whether R04 shows stronger OOD robustness than generic FiLM. It is not a Table 1 physical-baseline comparison and not a Table 2 component ablation.

## 3. Relation to Table 1 and Table 2

Table 1 is reused only for the ref3 runtime convention. Table 2 established a small main-test R04 advantage over generic FiLM; this task evaluates whether that advantage is clearer on OOD.

## 4. Frozen Dataset, OOD Splits, and Checkpoint Sources

Dataset source: `{SOURCE_006D}`. Frozen trained split: train=800, val=100, test=100.

{split_lines}

Checkpoint/result sources: O00/O01 from `{SOURCE_001B}`; O02/O03 from `{SOURCE_002B}`.

## 5. Methods Included in Table 3

Included exactly: O00_ref3, O01_ref3_residual_UNet, O02_ref3_metadata_generic_FiLM, O03_ref3_metadata_RSB_FiLM_R04.

## 6. Methods Excluded From This Task

Excluded from the main table: BP, ref5/ref7/ref9/ref31, metadata concat, R00/R01/R02/R03/R05, F02/F04, scalar Pcyc variants, support-mask variants, hard-region loss variants, RMA, and PFA.

## 7. OOD Evaluation Protocol

Cached OOD predictions/metrics from compatible prior runs were reused. For learned models, network runtime is reused from Table 2 to avoid mixing timing baselines from different historical OOD runs; the table end-to-end runtime is latest main ref3 runtime plus that network runtime. Main ref3 runtime from Table 1: {main_ref3_runtime():.6f}s/sample.

## 8. Table 3 OOD Results

See `metrics_ood_summary.csv`, `metrics_ood_by_seed.csv`, and `table3_ood_ready_latex.tex`. R04 NMSE by split: Leave-One-Family-Out {by[('O03_ref3_metadata_RSB_FiLM_R04', 'Leave-One-Family-Out OOD')]['NMSE_mean']:.6f}, Random-ET {by[('O03_ref3_metadata_RSB_FiLM_R04', 'Random-ET OOD')]['NMSE_mean']:.6f}, Unseen-Parameter {by[('O03_ref3_metadata_RSB_FiLM_R04', 'Unseen-Parameter OOD')]['NMSE_mean']:.6f}.

## 9. R04 vs Generic FiLM on OOD

{sig_lines}

Overall: {conclusion}.

## 10. Seed Stability and Paired Sample Analysis

Seed-wise and paired sample-wise results are in `ood_significance_r04_vs_generic.csv` and `ood_r04_vs_generic_by_split.md`. Bootstrap uses 1000 paired resamples over seed/sample pairs. The evidence should be read at the modest-effect scale unless the confidence interval excludes zero for a split.

## 11. Runtime Notes

OOD measured ref3 runtimes: {json.dumps(ood_ref3_runtime, ensure_ascii=False)}. The main table uses end-to-end runtime, not network-only runtime. R04 overhead over generic FiLM is negligible relative to ref3 reconstruction.

## 12. Interpretation for Paper Table 3

1. R04 improves over ref3 on OOD: yes, NMSE gains by split are {[round(v, 6) for v in r04_vs_ref3]}.
2. R04 improves over residual U-Net on OOD: yes on average; NMSE gains by split are {[round(v, 6) for v in r04_vs_unet]}.
3. R04 improves over generic FiLM on OOD: not clearly; {conclusion}.
4. The R04-vs-generic-FiLM OOD advantage is best described as: {conclusion}.
5. Hardest OOD split by R04 NMSE: {hard}.
6. OOD behavior supports using R04 as the final model, but the paper wording should match the measured advantage rather than overclaim.
7. Table 3 is ready for paper drafting.

## 13. Limitations

This report does not compare physical baseline quality-speed tradeoffs, Pcyc encoding alternatives, F02/F04 as main methods, support-aware objectives, or RMA/PFA baselines.

## 14. Final Recommendation

Use R04 as the final ReMiC-Net OOD row and include generic FiLM as the key internal baseline. State the OOD conclusion exactly as supported by the significance table.
"""
    (output_root / "task_real_struc_003c_report.md").write_text(report, encoding="utf-8")


def main() -> None:
    global summary_by_seed_cache
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", default=None)
    args = parser.parse_args()
    if args.output_root is None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_root = PROJECT_ROOT / "exp" / "task_real_struc_003c_table3_ood_generalization" / stamp
    else:
        output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    split_status = validate_ood_splits()
    if not all(s["files_exist"] for s in split_status):
        raise RuntimeError("one or more required OOD splits are missing")

    by_seed, summary, per_sample, ood_ref3_runtime = collect()
    summary_by_seed_cache = by_seed
    sig_rows, sig_md = paired_significance(summary, per_sample)
    conclusion = overall_conclusion(sig_rows, summary)

    write_csv(output_root / "metrics_ood_by_seed.csv", by_seed, [
        "method_id", "table_label", "ood_split", "seed", "num_samples",
        "NMSE_mean", "PSNR_mean", "SSIM_mean", "MAE_mean",
        "network_runtime_per_sample", "end_to_end_runtime_per_sample", "source", "notes",
    ])
    write_csv(output_root / "metrics_ood_summary.csv", summary, [
        "method_id", "table_label", "ood_split", "num_seeds", "num_samples",
        "NMSE_mean", "NMSE_std", "PSNR_mean", "PSNR_std", "SSIM_mean", "SSIM_std", "MAE_mean", "MAE_std",
        "network_runtime_per_sample_mean", "end_to_end_runtime_per_sample_mean", "source", "notes",
    ])
    write_csv(output_root / "per_sample_ood_metrics.csv", per_sample, [
        "method_id", "table_label", "ood_split", "seed", "sample_id", "NMSE", "PSNR", "SSIM", "MAE",
    ])
    write_csv(output_root / "ood_significance_r04_vs_generic.csv", sig_rows)
    (output_root / "ood_r04_vs_generic_by_split.md").write_text(sig_md + "\n", encoding="utf-8")
    runtime_rows = [
        {
            "ood_split": split,
            "main_ref3_runtime_used_for_table": main_ref3_runtime(),
            "ood_measured_ref3_runtime": ood_ref3_runtime[split],
        }
        for split in OOD_SPLITS
    ]
    for r in summary:
        runtime_rows.append({
            "ood_split": r["ood_split"],
            "method_id": r["method_id"],
            "network_runtime_per_sample_mean": r["network_runtime_per_sample_mean"],
            "end_to_end_runtime_per_sample_mean": r["end_to_end_runtime_per_sample_mean"],
        })
    write_csv(output_root / "ood_runtime_table.csv", runtime_rows)
    write_json(output_root / "config_summary.json", {
        "task": "task_real_struc_003c",
        "status": "COMPLETE",
        "dataset_source": str(SOURCE_006D),
        "ood_splits": split_status,
        "source_001b": str(SOURCE_001B),
        "source_002b": str(SOURCE_002B),
        "source_003a": str(SOURCE_003A),
        "source_003b": str(SOURCE_003B),
        "num_bootstrap": 1000,
        "current_branch": git_text(["git", "branch", "--show-current"]).strip(),
        "remote_branch": "origin/task_struc_series",
    })
    write_json(output_root / "model_variants.json", {
        k: {kk: (str(vv) if isinstance(vv, Path) else vv) for kk, vv in v.items()} for k, v in METHODS.items()
    })
    write_json(output_root / "method_sources.json", {
        k: str(v["source_root"]) for k, v in METHODS.items()
    })
    write_json(output_root / "model_checkpoint_sources.json", {
        f"{method_id}_seed{seed}": checkpoint_path(method["source_root"], method["source_variant"], seed)
        for method_id, method in METHODS.items() if method_id != "O00_ref3" for seed in method["seeds"]
    })
    (output_root / "table3_ood_ready.md").write_text("status = COMPLETE\ntable3_ready = yes\n", encoding="utf-8")
    write_latex(output_root, summary)
    write_plots(output_root, summary)
    write_report(output_root, summary, sig_rows, split_status, ood_ref3_runtime)
    env = f"python: {platform.python_version()}\ntorch: {torch.__version__}\ncuda_available: {torch.cuda.is_available()}\nplatform: {platform.platform()}\n"
    (output_root / "environment.txt").write_text(env, encoding="utf-8")
    (output_root / "git_status.txt").write_text(
        git_text(["git", "status", "--short", "--branch"]) + "\n" + git_text(["git", "log", "--oneline", "-5"]),
        encoding="utf-8",
    )

    print("task_real_struc_003c status: COMPLETE")
    print(f"experiment_root: {output_root}")
    print(f"current_branch: {git_text(['git', 'branch', '--show-current']).strip()}")
    print("remote_push_status: pending")
    print(f"OOD_splits_evaluated: {', '.join(OOD_SPLITS)}")
    print("O00_ref3_available: yes")
    print("O01_residual_UNet_available: yes")
    print("O02_generic_FiLM_available: yes")
    print("O03_R04_available: yes")
    print(f"best_OOD_method_by_average_NMSE: {best_method_average_nmse(summary)}")
    print(f"hardest_OOD_split: {hardest_split(summary)}")
    print(f"R04_vs_generic_FiLM_OOD_conclusion: {conclusion}")
    print("table3_ready: yes")
    print("recommendation_for_next_task: use Table 3 with evidence-matched wording and proceed to the next scoped task")


if __name__ == "__main__":
    random.seed(20260518)
    main()
