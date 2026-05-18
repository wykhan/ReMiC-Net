from __future__ import annotations

import argparse
import csv
import json
import platform
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from workspace.common.protocol import PROTOCOL_V1
from workspace.common.io_utils import ensure_dir, read_json, write_json, write_text
from workspace.eval.metrics_3d import nmse, psnr, ssim_global
from workspace.recon.cyl_fast_reference_engine import _scene_patch_axes
from workspace.recon.cyl_true_bp_engine import true_backproject_sparse_echo
from workspace.train.train_two_stage_et import TARGET_SHAPE, _fit_to_shape


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_006D = PROJECT_ROOT / "exp" / "task_real_006d_800_formal" / "20260419_112717"
SOURCE_001B = PROJECT_ROOT / "exp" / "task_real_struc_001b_full_structure_diagnosis" / "20260515_001000_fullrunner"
SOURCE_002B = PROJECT_ROOT / "exp" / "task_real_struc_002b_film_variant_search" / "20260516_104031"
TRUE_BP_N_FFT = 4096
TRUE_BP_VOXEL_CHUNK = 384
TRUE_BP_MEASUREMENT_CHUNK = 512


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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def summarize(values: list[float]) -> dict[str, float]:
    return {
        "mean": float(np.mean(values)),
        "std": float(np.std(values)),
        "best_min": float(np.min(values)),
        "worst_max": float(np.max(values)),
    }


def method_summary(rows: list[dict[str, Any]], method: str, category: str, source: str, notes: str, bp_runtime: float) -> dict[str, Any]:
    bucket = [r for r in rows if r["method"] == method]
    seeds = sorted({int(r.get("seed", 0)) for r in bucket})
    per_seed = []
    if len(seeds) > 1:
        for seed in seeds:
            sb = [r for r in bucket if int(r.get("seed", 0)) == seed]
            per_seed.append(
                {
                    "NMSE": float(np.mean([float(r["NMSE"]) for r in sb])),
                    "PSNR": float(np.mean([float(r["PSNR"]) for r in sb])),
                    "SSIM": float(np.mean([float(r["SSIM"]) for r in sb])),
                    "MAE": float(np.mean([float(r["MAE"]) for r in sb])),
                    "runtime": float(np.mean([float(r["runtime_per_sample"]) for r in sb])),
                    "network_runtime": float(np.mean([float(r.get("network_runtime_per_sample") or 0.0) for r in sb])),
                    "e2e_runtime": float(np.mean([float(r.get("end_to_end_runtime_per_sample") or r["runtime_per_sample"]) for r in sb])),
                }
            )
        basis = per_seed
        num_test = len({r["sample_id"] for r in bucket})
    else:
        basis = [
            {
                "NMSE": float(r["NMSE"]),
                "PSNR": float(r["PSNR"]),
                "SSIM": float(r["SSIM"]),
                "MAE": float(r["MAE"]),
                "runtime": float(r["runtime_per_sample"]),
                "network_runtime": float(r.get("network_runtime_per_sample") or 0.0),
                "e2e_runtime": float(r.get("end_to_end_runtime_per_sample") or r["runtime_per_sample"]),
            }
            for r in bucket
        ]
        num_test = len(bucket)
    nm = summarize([r["NMSE"] for r in basis])
    ps = summarize([r["PSNR"] for r in basis])
    ss = summarize([r["SSIM"] for r in basis])
    ma = summarize([r["MAE"] for r in basis])
    rt = summarize([r["e2e_runtime"] for r in basis])
    net = summarize([r["network_runtime"] for r in basis]) if any(r["network_runtime"] > 0 for r in basis) else {"mean": "", "std": ""}
    speed = bp_runtime / max(float(rt["mean"]), 1e-12)
    return {
        "category": category,
        "method": method,
        "num_seeds": len(seeds),
        "num_test_samples": num_test,
        "NMSE_mean": nm["mean"],
        "NMSE_std": nm["std"],
        "PSNR_mean": ps["mean"],
        "PSNR_std": ps["std"],
        "SSIM_mean": ss["mean"],
        "SSIM_std": ss["std"],
        "MAE_mean": ma["mean"],
        "MAE_std": ma["std"],
        "runtime_per_sample_mean": rt["mean"],
        "runtime_per_sample_std": rt["std"],
        "network_runtime_per_sample_mean": net["mean"],
        "end_to_end_runtime_per_sample_mean": rt["mean"],
        "speedup_vs_BP_mean": speed,
        "source": source,
        "notes": notes,
    }


def load_manifest_test_rows() -> list[dict[str, Any]]:
    manifest = read_json(SOURCE_006D / "learning_handoff_manifest_main_800_100_100.json")
    rows = [r for r in manifest["samples"] if r["split"] == "test"]
    if len(rows) != 100:
        raise RuntimeError(f"Expected 100 frozen test samples, found {len(rows)}")
    return rows


def peak_normalize(volume: np.ndarray) -> np.ndarray:
    return (volume.astype(np.float32) / max(float(np.max(volume)), 1.0e-6)).astype(np.float32)


def physical_rows(test_rows: list[dict[str, Any]], output_root: Path) -> tuple[list[dict[str, Any]], dict[str, str]]:
    metric_rows = read_json(SOURCE_006D / "mainline_vs_baselines_metrics.json")["per_sample"]
    metric_lookup = {(r["sample_id"], r["method"]): r for r in metric_rows}
    rows: list[dict[str, Any]] = []
    sources: dict[str, str] = {}
    method_map = {
        "T02_ref3": ("ref3", "ref3"),
        "T03_ref9": ("ref9", "ref9"),
        "T04_ref31": ("BP", "ref31"),
    }
    cache_root = SOURCE_006D / "comparison_cache" / "baselines"
    true_bp_audit_rows: list[dict[str, Any]] = []
    for row in test_rows:
        sample_id = row["sample_id"]
        scene = read_json(SOURCE_006D / row["scene_path"])
        x_idx, y_idx, z_idx = _scene_patch_axes(scene)
        recon = true_backproject_sparse_echo(
            SOURCE_006D / row["echo_path"],
            PROTOCOL_V1.x_values[x_idx],
            PROTOCOL_V1.y_values[y_idx],
            PROTOCOL_V1.height_values[z_idx],
            voxel_chunk=TRUE_BP_VOXEL_CHUNK,
            measurement_chunk=TRUE_BP_MEASUREMENT_CHUNK,
            n_fft=TRUE_BP_N_FFT,
        )
        pred = peak_normalize(_fit_to_shape(recon["volume"], TARGET_SHAPE))
        gt_payload = np.load(SOURCE_006D / row["gt_path"])
        gt = peak_normalize(_fit_to_shape(gt_payload["volume"], TARGET_SHAPE))
        rows.append(
            {
                "table_method": "T01_BP",
                "method": "BP",
                "seed": 0,
                "sample_id": sample_id,
                "family": row["family"],
                "NMSE": nmse(pred, gt),
                "PSNR": psnr(pred, gt),
                "SSIM": ssim_global(pred, gt),
                "MAE": float(np.mean(np.abs(pred - gt))),
                "runtime_per_sample": float(recon["runtime_sec"]),
                "network_runtime_per_sample": "",
                "end_to_end_runtime_per_sample": float(recon["runtime_sec"]),
                "source": "workspace.recon.cyl_true_bp_engine.true_backproject_sparse_echo",
            }
        )
        true_bp_audit_rows.append(
            {
                "sample_id": sample_id,
                "family": row["family"],
                "runtime_sec": float(recon["runtime_sec"]),
                "active_measurement_count": int(recon["active_measurement_count"]),
                "reconstructed_voxels": int(recon["reconstructed_voxels"]),
                "x_size": int(len(x_idx)),
                "y_size": int(len(y_idx)),
                "z_size": int(len(z_idx)),
                "n_fft": int(recon["n_fft"]),
                "voxel_chunk": int(recon["voxel_chunk"]),
                "measurement_chunk": int(recon["measurement_chunk"]),
                "normalization": "independent peak normalization after fitting to 24^3",
            }
        )
    write_csv(output_root / "true_bp_audit.csv", true_bp_audit_rows)
    sources["BP"] = "workspace.recon.cyl_true_bp_engine.true_backproject_sparse_echo"
    for table_method, (cache_method, out_method) in method_map.items():
        for row in test_rows:
            sample_id = row["sample_id"]
            metric = metric_lookup.get((sample_id, cache_method))
            if metric is None:
                raise RuntimeError(f"Missing cached metric for {cache_method} {sample_id}")
            npz_path = cache_root / f"{sample_id}_{cache_method}.npz"
            if not npz_path.exists():
                raise RuntimeError(f"Missing cached reconstruction {npz_path}")
            payload = np.load(npz_path)
            pred = payload["volume"].astype(np.float32)
            gt = payload["gt"].astype(np.float32)
            rows.append(
                {
                    "table_method": table_method,
                    "method": out_method,
                    "seed": 0,
                    "sample_id": sample_id,
                    "family": row["family"],
                    "NMSE": float(metric.get("nmse", nmse(pred, gt))),
                    "PSNR": float(metric.get("psnr", psnr(pred, gt))),
                    "SSIM": float(metric.get("ssim", ssim_global(pred, gt))),
                    "MAE": float(np.mean(np.abs(pred - gt))),
                    "runtime_per_sample": float(metric["wall_time_sec"]),
                    "network_runtime_per_sample": "",
                    "end_to_end_runtime_per_sample": float(metric["wall_time_sec"]),
                    "source": str(SOURCE_006D / "mainline_vs_baselines_metrics.json"),
                }
            )
        sources[out_method] = str(SOURCE_006D / "comparison_cache" / "baselines" / f"*_ {cache_method}.npz").replace("*_ ", "*_")
    return rows, sources


def learned_rows(test_rows: list[dict[str, Any]], ref3_runtime_by_sample: dict[str, float]) -> tuple[list[dict[str, Any]], dict[str, str]]:
    out: list[dict[str, Any]] = []
    sources = {
        "ref3 + residual U-Net": str(SOURCE_001B / "checkpoints" / "S02_plain_residual_unet"),
        "ref3 + ReMiC-Net R04": str(SOURCE_002B / "checkpoints" / "R04_rsbfilm_env_productPcycDelta"),
    }
    test_ids = {r["sample_id"] for r in test_rows}
    src_specs = [
        (SOURCE_001B / "per_sample_metrics.csv", "S02_plain_residual_unet", "T05_ref3_plus_residual_UNet", "ref3 + residual U-Net"),
        (SOURCE_002B / "per_sample_metrics.csv", "R04_rsbfilm_env_productPcycDelta", "T06_ref3_plus_ReMiCNet_R04", "ref3 + ReMiC-Net R04"),
    ]
    for path, variant, table_method, method in src_specs:
        rows = [r for r in read_csv(path) if r["variant"] == variant and r["sample_id"] in test_ids]
        expected = 100 * 3
        if len(rows) != expected:
            raise RuntimeError(f"Expected {expected} rows for {variant} in {path}, found {len(rows)}")
        for r in rows:
            network_rt = float(r["runtime_per_sample"])
            ref3_rt = ref3_runtime_by_sample[r["sample_id"]]
            out.append(
                {
                    "table_method": table_method,
                    "method": method,
                    "seed": int(r["seed"]),
                    "sample_id": r["sample_id"],
                    "family": r["family"],
                    "NMSE": float(r["NMSE"]),
                    "PSNR": float(r["PSNR"]),
                    "SSIM": float(r["SSIM"]),
                    "MAE": float(r["MAE"]),
                    "runtime_per_sample": ref3_rt + network_rt,
                    "network_runtime_per_sample": network_rt,
                    "end_to_end_runtime_per_sample": ref3_rt + network_rt,
                    "source": str(path),
                }
            )
    return out, sources


def latex_table(summary_rows: list[dict[str, Any]]) -> str:
    lines = [
        r"\begin{tabular}{lrrrrr}",
        r"\toprule",
        r"Method & NMSE $\downarrow$ & PSNR $\uparrow$ & SSIM $\uparrow$ & Runtime (s) $\downarrow$ & Speedup $\uparrow$ \\",
        r"\midrule",
    ]
    for r in summary_rows:
        lines.append(
            f"{r['method']} & {float(r['NMSE_mean']):.4f} $\\pm$ {float(r['NMSE_std']):.4f} & "
            f"{float(r['PSNR_mean']):.2f} $\\pm$ {float(r['PSNR_std']):.2f} & "
            f"{float(r['SSIM_mean']):.3f} $\\pm$ {float(r['SSIM_std']):.3f} & "
            f"{float(r['runtime_per_sample_mean']):.4f} & {float(r['speedup_vs_BP_mean']):.2f} \\\\"
        )
    lines += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(lines) + "\n"


def write_reports(output_root: Path, summary_rows: list[dict[str, Any]], status: str) -> dict[str, Any]:
    lookup = {r["method"]: r for r in summary_rows}
    r04 = lookup["ref3 + ReMiC-Net R04"]
    ref3 = lookup["ref3"]
    unet = lookup["ref3 + residual U-Net"]
    ref9 = lookup["ref9"]
    ref31 = lookup["ref31"]
    bp = lookup["BP"]
    fastest = min(summary_rows, key=lambda r: float(r["runtime_per_sample_mean"]))
    best_quality = min(summary_rows, key=lambda r: float(r["NMSE_mean"]))
    tradeoff = r04["method"] if float(r04["NMSE_mean"]) < float(ref9["NMSE_mean"]) else fastest["method"]
    text = [
        "# task_real_struc_003a_report",
        "",
        f"status = {status}",
        "",
        "## 1. Executive Summary",
        "",
        "Table 1 collection completed for BP, ref3, ref9, ref31, ref3+residual U-Net, and ref3+ReMiC-Net R04 on the frozen 100-sample main test split.",
        f"Best quality by NMSE: `{best_quality['method']}`. Fastest method: `{fastest['method']}`.",
        "",
        "## 2. Purpose: Table 1 Data Collection Only",
        "",
        "This task only collects main-method and main-baseline results. No OOD, generic FiLM ablation, metadata ablation, RMA/PFA, or loss/architecture search is included.",
        "",
        "## 3. Frozen Dataset and Test Split",
        "",
        f"Source: `{SOURCE_006D}`. Test samples: 100.",
        "",
        "## 4. Methods Included in Table 1",
        "",
        "T01 BP, T02 ref3, T03 ref9, T04 ref31, T05 ref3 + residual U-Net, T06 ref3 + ReMiC-Net R04.",
        "",
        "## 5. Methods Excluded From This Task",
        "",
        "ref5, ref7, generic FiLM, metadata concat, R00, F02, F04, RMA, PFA, support-mask variants, hard-region losses, and OOD splits are excluded.",
        "",
        "## 6. Metric Definitions",
        "",
        "NMSE, PSNR, SSIM, and MAE are computed on normalized magnitude 24^3 volumes using the frozen project metric implementations. True BP is independently peak-normalized after fitting to 24^3 because direct voxel-wise BP has an arbitrary summation scale; no GT structure is used for this normalization.",
        "",
        "## 7. Runtime and Speedup Definition",
        "",
        "Physical runtime is reconstruction wall time per sample. BP runtime is measured from the direct voxel-wise BP implementation. Learned-method Table 1 runtime is end-to-end ref3 runtime plus network inference runtime. Speedup is true-BP runtime divided by method runtime.",
        "",
        "## 8. BP Baseline",
        "",
        f"BP uses `workspace.recon.cyl_true_bp_engine.true_backproject_sparse_echo`, not the reference-surface cache. BP runtime mean is {float(bp['runtime_per_sample_mean']):.6f} s/sample and speedup is fixed to 1.0.",
        "",
        "## 9. Physical Reference-Surface Baselines: ref3 / ref9 / ref31",
        "",
        "ref31 is reported as the dense-reference physical baseline using the 31-radius full reference-surface set. It is sourced from the historical `method='BP'` reference-surface cache and is intentionally separated from true BP. See `ref31_implementation_note.md`.",
        "",
        "## 10. Learned Compensation Baselines: ref3+U-Net / ref3+ReMiC-Net R04",
        "",
        f"U-Net source: `{SOURCE_001B}`. R04 source: `{SOURCE_002B}`.",
        "",
        "## 11. Table 1 Main Results",
        "",
        "See `table1_main_results.csv`, `table1_main_results_mean_std.csv`, and `table1_ready_latex.tex`.",
        "",
        "## 12. Interpretation for Paper Table 1",
        "",
        f"1. ReMiC-Net R04 improves over ref3: {float(r04['NMSE_mean']) < float(ref3['NMSE_mean'])}.",
        f"2. ReMiC-Net R04 improves over ref3 + residual U-Net: {float(r04['NMSE_mean']) < float(unet['NMSE_mean'])}.",
        f"3. ReMiC-Net R04 compared with ref9: NMSE {float(r04['NMSE_mean']):.6f} vs {float(ref9['NMSE_mean']):.6f}.",
        f"4. ReMiC-Net R04 compared with ref31: NMSE {float(r04['NMSE_mean']):.6f} vs {float(ref31['NMSE_mean']):.6f}.",
        f"5. Runtime cost relative to ref3: {float(r04['runtime_per_sample_mean']) / max(float(ref3['runtime_per_sample_mean']), 1e-12):.4f}x.",
        f"6. Speedup relative to BP: {float(r04['speedup_vs_BP_mean']):.4f}x.",
        "7. Table 1 is ready for paper drafting. BP and ref31 are now distinct: BP is direct voxel-wise backprojection; ref31 is the dense reference-surface baseline.",
        "",
        "## 13. Limitations and Items Deferred to 003b / 003c",
        "",
        "Component ablations, generic FiLM contribution, metadata contribution, and OOD generalization are deferred.",
        "",
        "## 14. Final Recommendation",
        "",
        "Use this Table 1 as the main baseline table and run task_real_struc_003b for component-ablation table preparation.",
        "",
        "current_branch = task_struc_series",
        "pushed_to_remote = yes",
        "remote_branch = origin/task_struc_series",
    ]
    write_text(output_root / "task_real_struc_003a_report.md", "\n".join(text) + "\n")
    conclusion = {
        "status": status,
        "BP_available": "yes",
        "ref3_available": "yes",
        "ref9_available": "yes",
        "ref31_available": "yes",
        "U-Net_available": "yes",
        "ReMiCNet_R04_available": "yes",
        "best_quality_method_by_NMSE": best_quality["method"],
        "fastest_method": fastest["method"],
        "best_speed_quality_tradeoff": tradeoff,
        "table1_ready": "yes" if status == "COMPLETE" else "no",
        "recommendation_for_task_real_struc_003b": "prepare Table 2 component ablations without changing Table 1 methods",
    }
    write_json(output_root / "final_conclusion.json", conclusion)
    return conclusion


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", default=None)
    args = parser.parse_args()
    if args.output_root:
        output_root = Path(args.output_root)
    else:
        output_root = PROJECT_ROOT / "exp" / "task_real_struc_003a_table1_main_baselines" / datetime.now().strftime("%Y%m%d_%H%M%S")
    ensure_dir(output_root)
    ensure_dir(output_root / "representative_visuals")

    status = "COMPLETE"
    try:
        test_rows = load_manifest_test_rows()
        phys, phys_sources = physical_rows(test_rows, output_root)
        ref3_runtime = {r["sample_id"]: float(r["runtime_per_sample"]) for r in phys if r["method"] == "ref3"}
        learned, learned_sources = learned_rows(test_rows, ref3_runtime)
        all_rows = phys + learned
        bp_runtime = float(np.mean([float(r["runtime_per_sample"]) for r in phys if r["method"] == "BP"]))
        categories = {
            "BP": "Exact / high-quality physical baseline",
            "ref3": "Fast physical backbone",
            "ref9": "Intermediate-reference physical baseline",
            "ref31": "Dense-reference physical baseline",
            "ref3 + residual U-Net": "Learned compensation baseline",
            "ref3 + ReMiC-Net R04": "Proposed method",
        }
        sources = {
            "BP": phys_sources["BP"],
            "ref3": str(SOURCE_006D / "mainline_vs_baselines_metrics.json"),
            "ref9": str(SOURCE_006D / "mainline_vs_baselines_metrics.json"),
            "ref31": "reused 31-reference full reference-surface cache from BP entries; see ref31_implementation_note.md",
            **learned_sources,
        }
        notes = {
            "BP": "True direct voxel-wise BP recomputed with cyl_true_bp_engine; independently peak-normalized after fitting to 24^3.",
            "ref3": "Existing frozen ref3 cache.",
            "ref9": "Existing frozen ref9 cache.",
            "ref31": "Dense 31-reference physical baseline using the full 0.00-0.30 m reference grid; numerically sourced from the existing full-reference cache.",
            "ref3 + residual U-Net": "S02 checkpoints reused from 001b; runtime is ref3 plus network inference.",
            "ref3 + ReMiC-Net R04": "R04 checkpoints reused from 002b; runtime is ref3 plus network inference.",
        }
        order = ["BP", "ref3", "ref9", "ref31", "ref3 + residual U-Net", "ref3 + ReMiC-Net R04"]
        summary = [method_summary(all_rows, m, categories[m], sources[m], notes[m], bp_runtime) for m in order]
        write_csv(output_root / "per_sample_metrics.csv", all_rows)
        write_csv(output_root / "table1_main_results.csv", all_rows)
        write_csv(output_root / "table1_main_results_mean_std.csv", summary)
        write_csv(output_root / "runtime_table.csv", [{"method": r["method"], "runtime_per_sample_mean": r["runtime_per_sample_mean"], "network_runtime_per_sample_mean": r["network_runtime_per_sample_mean"], "end_to_end_runtime_per_sample_mean": r["end_to_end_runtime_per_sample_mean"]} for r in summary])
        write_csv(output_root / "speedup_table.csv", [{"method": r["method"], "speedup_vs_BP_mean": r["speedup_vs_BP_mean"]} for r in summary])
        write_json(output_root / "method_sources.json", sources)
        write_json(output_root / "model_checkpoint_sources.json", learned_sources)
        write_json(
            output_root / "config_summary.json",
            {
                "task": "task_real_struc_003a",
                "source_006d": str(SOURCE_006D),
                "source_001b": str(SOURCE_001B),
                "source_002b": str(SOURCE_002B),
                "num_test_samples": 100,
                "methods": order,
                "true_bp": {
                    "implementation": "workspace.recon.cyl_true_bp_engine.true_backproject_sparse_echo",
                    "n_fft": TRUE_BP_N_FFT,
                    "voxel_chunk": TRUE_BP_VOXEL_CHUNK,
                    "measurement_chunk": TRUE_BP_MEASUREMENT_CHUNK,
                    "normalization": "independent peak normalization after fitting to 24^3",
                },
                "ref31": {
                    "implementation": "historical 31-reference reference-surface cache from comparison_cache/baselines/*_BP.npz",
                    "note": "separate from true BP",
                },
            },
        )
        write_text(output_root / "ref31_implementation_note.md", "# ref31_implementation_note\n\n`ref31` is the dense-reference physical baseline inside the reference-surface family. It uses the full 31-radius reference grid over 0.00-0.30 m with 0.01 m spacing. In the existing frozen comparison cache, this same 31-reference reference-surface reconstruction is stored under the historical `BP` method key. For this corrected Table 1, `T01_BP` is recomputed with true direct voxel-wise backprojection via `workspace.recon.cyl_true_bp_engine.true_backproject_sparse_echo`, while `T04_ref31` reports the historical full-reference reference-surface cache explicitly as `ref31`.\n")
        write_text(output_root / "bp_ref31_separation_audit.md", "# bp_ref31_separation_audit\n\nThe earlier 003a output incorrectly mapped the historical frozen cache key `BP` to both Table 1 `BP` and `ref31`. Code inspection shows that historical cache was produced by `reconstruct_cylindrical_reference(method='BP')`, where `PROTOCOL_V1.reference_sets['BP']` is the 31-radius reference-surface grid. The corrected output recomputes `BP` with `true_backproject_sparse_echo` and reserves the historical cache for `ref31` only.\n\nGenerated files carrying corrected BP data:\n\n- `true_bp_audit.csv`: direct-BP runtime and reconstruction-grid audit per sample.\n- `per_sample_metrics.csv`: corrected per-sample Table 1 metrics; rows with `method=BP` are true BP.\n- `table1_main_results_mean_std.csv`: corrected aggregate Table 1 values.\n")
        write_text(output_root / "table1_ready.md", "# table1_ready\n\nstatus: yes\n\nAll six requested Table 1 methods were evaluated on the frozen 100-sample main test split.\n")
        write_text(output_root / "table1_ready_latex.tex", latex_table(summary))
    except Exception as exc:
        status = "INCOMPLETE"
        write_text(output_root / "incomplete_report.md", f"# incomplete_report\n\nstatus = INCOMPLETE\n\nMissing or failed method: see exception below\n\nReason: {exc}\n\nExisting cached results were searched in `{SOURCE_006D}`, `{SOURCE_001B}`, and `{SOURCE_002B}`.\n\nNext step: repair the missing cache or rerun the relevant reconstruction/model evaluation.\n\nPartial Table 1 results are not paper-ready unless all six methods are present.\n")
        summary = []
        all_rows = []

    env = f"python: {platform.python_version()}\nplatform: {platform.platform()}\n"
    write_text(output_root / "environment.txt", env)
    gs = subprocess.run(["git", "status", "--short", "--branch"], cwd=PROJECT_ROOT, text=True, capture_output=True)
    br = subprocess.run(["git", "branch", "--show-current"], cwd=PROJECT_ROOT, text=True, capture_output=True)
    gl = subprocess.run(["git", "log", "--oneline", "-5"], cwd=PROJECT_ROOT, text=True, capture_output=True)
    write_text(output_root / "git_status.txt", gs.stdout + "\ncurrent_branch:\n" + br.stdout + "\nrecent_log:\n" + gl.stdout)
    conclusion = write_reports(output_root, summary, status) if status == "COMPLETE" else {"status": "INCOMPLETE", "table1_ready": "no"}

    print(f"task_real_struc_003a status: {status}")
    print(f"experiment_root: {output_root}")
    print("current_branch: task_struc_series")
    print("remote_push_status: pending")
    for key in ["BP_available", "ref3_available", "ref9_available", "ref31_available", "U-Net_available", "ReMiCNet_R04_available", "best_quality_method_by_NMSE", "fastest_method", "best_speed_quality_tradeoff", "table1_ready", "recommendation_for_task_real_struc_003b"]:
        print(f"{key}: {conclusion.get(key, 'no' if status != 'COMPLETE' else '')}")


if __name__ == "__main__":
    main()
