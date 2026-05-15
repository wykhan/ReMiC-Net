from __future__ import annotations

import argparse
import csv
import json
import platform
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import torch

from workspace.common.io_utils import ensure_dir, read_json, write_json, write_text
from workspace.common.remic_metadata import REF3_RADII_M, build_remic_metadata
from workspace.eval.task_real_008_pipeline import _fit_to_shape, _normalize_pair


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_006D = PROJECT_ROOT / "exp" / "task_real_006d_800_formal" / "20260419_112717"
SOURCE_001A = PROJECT_ROOT / "exp" / "task_real_struc_001_remicnet_core_structure_diagnosis" / "20260515_000001"
TARGET_SHAPE = (24, 24, 24)
OOD_DIRS = {
    "Leave-One-Family-Out OOD": SOURCE_006D / "datasets" / "leave_one_family_out_ood",
    "Random-ET OOD": SOURCE_006D / "datasets" / "random_et_ood",
    "Unseen-Parameter OOD": SOURCE_006D / "datasets" / "unseen_param_ood",
}


VARIANTS = [
    ("S01_ref3", "ref3 physical baseline"),
    ("S02_plain_residual_unet", "plain residual 3D U-Net"),
    ("S03_concat_Mshell", "concat [X_ref3, Mshell]"),
    ("S04_concat_Mshell_delta", "concat [X_ref3, Mshell, delta_rho]"),
    ("S05_concat_Mshell_delta_Pcyc", "concat [X_ref3, Mshell, delta_rho, Pcyc]"),
    ("S06_geometry_branch_bottleneck_concat", "geometry branch bottleneck concat"),
    ("S07_generic_film_middeep", "generic FiLM"),
    ("S08_rsbfilm_middeep_default", "RSB-FiLM default"),
    ("S09_concat_Mshell_delta_Pcyc_sincos", "concat periodic Pcyc sin/cos"),
    ("S10_geometry_branch_bottleneck_concat_Pcyc_sincos", "geometry branch with periodic Pcyc"),
    ("S11_rsbfilm_Pcyc_sincos", "RSB-FiLM with periodic Pcyc geometry input"),
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


def stats(prefix: str, arr: np.ndarray) -> dict[str, Any]:
    arr = arr.astype(np.float64)
    return {
        f"{prefix}_min": float(np.min(arr)),
        f"{prefix}_max": float(np.max(arr)),
        f"{prefix}_mean": float(np.mean(arr)),
        f"{prefix}_std": float(np.std(arr)),
        f"{prefix}_nan_count": int(np.isnan(arr).sum()),
        f"{prefix}_inf_count": int(np.isinf(arr).sum()),
    }


def verify_full_split(output_root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    manifest_path = SOURCE_006D / "learning_handoff_manifest_main_800_100_100.json"
    if not manifest_path.exists():
        return [], {"available": False, "reason": f"missing {manifest_path}"}
    manifest = read_json(manifest_path)
    rows = manifest["samples"]
    counts = {split: sum(1 for row in rows if row["split"] == split) for split in ["train", "val", "test"]}
    ok = counts == {"train": 800, "val": 100, "test": 100}
    payload = {"available": ok, "counts": counts, "manifest": str(manifest_path)}
    write_json(output_root / "full_split_verification.json", payload)
    return rows, payload


def metadata_audit(output_root: Path, rows: list[dict[str, Any]]) -> None:
    stat_rows = []
    shell_channel_sums = np.zeros(3, dtype=np.float64)
    onehot_bad = 0
    total_voxels = 0
    deltas = []
    pcycs = []
    support_alignment = []
    boundary_counts = []
    for row in rows:
        ref3_npz = np.load(SOURCE_006D / row["ref3_path"])
        gt_npz = np.load(SOURCE_006D / row["gt_path"])
        x_ref3, gt, _ = _normalize_pair(_fit_to_shape(ref3_npz["volume"]), _fit_to_shape(gt_npz["volume"]))
        meta = build_remic_metadata(ref3_npz["x_values"], ref3_npz["y_values"], ref3_npz["z_values"], TARGET_SHAPE)
        mshell = meta["mshell"]
        delta = meta["delta_rho_raw"][0]
        pcyc = meta["pcyc"][0]
        rho = meta["rho"][0]
        shell_sum = mshell.sum(axis=0)
        onehot_bad += int(np.count_nonzero(np.abs(shell_sum - 1.0) > 1.0e-5))
        total_voxels += int(shell_sum.size)
        shell_channel_sums += mshell.reshape(3, -1).sum(axis=1)
        deltas.append(delta.ravel())
        pcycs.append(pcyc.ravel())
        support = gt > max(float(gt.max()) * 0.05, 1.0e-6)
        ref_support = x_ref3 > max(float(x_ref3.max()) * 0.05, 1.0e-6)
        support_alignment.append(float(np.count_nonzero(support & ref_support) / max(np.count_nonzero(support | ref_support), 1)))
        boundary = np.logical_or(np.abs(rho - 0.075) <= 0.010, np.abs(rho - 0.225) <= 0.010)
        boundary_counts.append(int(np.count_nonzero(boundary)))
        stat_rows.append(
            {
                "sample_id": row["sample_id"],
                "split": row["split"],
                "family": row["family"],
                **stats("X_ref3", x_ref3),
                **stats("GT", gt),
                **stats("delta_rho", delta),
                **stats("Pcyc", pcyc),
                "Pcyc_abs_le_0p25_ratio": float(np.mean(np.abs(pcyc) <= 0.25)),
                "Pcyc_abs_gt_0p25_ratio": float(np.mean(np.abs(pcyc) > 0.25)),
                "support_alignment_iou_ref3_vs_gt": support_alignment[-1],
                "shell_boundary_voxel_count": boundary_counts[-1],
            }
        )
    delta_all = np.concatenate(deltas)
    pcyc_all = np.concatenate(pcycs)
    write_csv(output_root / "metadata_stats.csv", stat_rows)
    ensure_dir(output_root / "metadata_histograms")
    for name, values in [("delta_rho", delta_all), ("Pcyc", pcyc_all), ("abs_Pcyc", np.abs(pcyc_all))]:
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.hist(values, bins=80)
        ax.set_title(name)
        fig.tight_layout()
        fig.savefig(output_root / "metadata_histograms" / f"{name}_hist.png", dpi=160)
        plt.close(fig)
    shell_stats = "\n".join([f"- Mshell channel {idx} sum: {val:.0f}" for idx, val in enumerate(shell_channel_sums)])
    report = f"""# metadata_audit_report

Full split samples audited: {len(rows)}

## One-Hot Validity

- total voxels checked: {total_voxels}
- one-hot invalid voxels: {onehot_bad}

## Mshell Channel Sums

{shell_stats}

## delta_rho

- min/max/mean/std: {float(delta_all.min()):.6f} / {float(delta_all.max()):.6f} / {float(delta_all.mean()):.6f} / {float(delta_all.std()):.6f}

## Pcyc

- min/max/mean/std: {float(pcyc_all.min()):.6f} / {float(pcyc_all.max()):.6f} / {float(pcyc_all.mean()):.6f} / {float(pcyc_all.std()):.6f}
- abs(Pcyc)<=0.25 ratio: {float(np.mean(np.abs(pcyc_all) <= 0.25)):.6f}
- abs(Pcyc)>0.25 ratio: {float(np.mean(np.abs(pcyc_all) > 0.25)):.6f}

## Spatial Alignment

- mean ref3/GT support IoU: {float(np.mean(support_alignment)):.6f}
- min ref3/GT support IoU: {float(np.min(support_alignment)):.6f}

## Shell Boundary

- mean shell-boundary voxel count: {float(np.mean(boundary_counts)):.2f}

## NaN / Inf

See `metadata_stats.csv`; all audited fields include NaN/Inf counts.
"""
    write_text(output_root / "metadata_audit_report.md", report)


def ood_investigation(output_root: Path) -> None:
    rows = []
    for name, path in OOD_DIRS.items():
        index = path / "dataset" / "index.json"
        manifest_candidates = list(path.glob("**/index.json"))
        rows.append(
            {
                "ood_split": name,
                "dataset_dir": str(path),
                "available": path.exists(),
                "index_exists": index.exists(),
                "index_candidates": ";".join(str(p) for p in manifest_candidates[:3]),
                "status": "available_but_not_evaluated_in_001b_incomplete_run" if path.exists() else "unavailable",
                "reason": "Full S01-S11 50-epoch multi-seed training was not completed, so OOD evaluation could not be meaningfully run." if path.exists() else f"missing {path}",
            }
        )
    write_csv(output_root / "metrics_ood.csv", rows)


def copy_001a_metrics(output_root: Path) -> dict[str, Any]:
    metrics_path = SOURCE_001A / "metrics_overall.csv"
    rows = []
    if metrics_path.exists():
        with metrics_path.open("r", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        write_csv(output_root / "metrics_001a_smoke_reference.csv", rows)
    return {row["variant"]: row for row in rows}


def write_failure_and_metric_audits(output_root: Path, smoke: dict[str, Any]) -> None:
    s03 = smoke.get("S03_concat_Mshell", {})
    s05 = smoke.get("S05_concat_Mshell_delta_Pcyc", {})
    lines = [
        "# failure_audit_S03_S05",
        "",
        "001a observed collapse for S03 and S05 under 48/12/24 samples and 2 epochs.",
        "",
        f"- S03 001a NMSE/SSIM: {s03.get('NMSE', 'missing')} / {s03.get('SSIM', 'missing')}",
        f"- S05 001a NMSE/SSIM: {s05.get('NMSE', 'missing')} / {s05.get('SSIM', 'missing')}",
        "",
        "## Current 001b Status",
        "",
        "Full corrective retraining was not completed, so the task cannot answer whether S03/S05 still fail after full training.",
        "",
        "## Preliminary Causes To Test",
        "",
        "- Metadata scale: delta_rho is in meters while Mshell and Pcyc are dimensionless; scale imbalance must be tested during full training.",
        "- Pcyc wrap discontinuity: S09-S11 are required to test sin/cos periodic encoding.",
        "- Channel normalization: concat variants mix sparse one-hot maps with continuous image and phase channels.",
        "- Undertraining: 001a used only 2 epochs; this remains a plausible cause until 50-epoch curves are available.",
    ]
    write_text(output_root / "failure_audit_S03_S05.md", "\n".join(lines) + "\n")
    write_csv(
        output_root / "input_channel_scale_table.csv",
        [
            {"channel": "X_ref3", "scale": "normalized per sample by max(ref3, GT)", "range_expected": "[0, 1]"},
            {"channel": "Mshell", "scale": "one-hot", "range_expected": "{0, 1}"},
            {"channel": "delta_rho", "scale": "meters, signed", "range_expected": "approximately [-0.075, 0.075]"},
            {"channel": "Pcyc", "scale": "wrapped phase / pi", "range_expected": "[-1, 1] with wrap discontinuity"},
            {"channel": "sin(pi*Pcyc), cos(pi*Pcyc)", "scale": "periodic corrective encoding", "range_expected": "[-1, 1]"},
        ],
    )
    write_csv(
        output_root / "prediction_value_stats_S03_S05.csv",
        [
            {"variant": "S03_concat_Mshell", "source": "001a_smoke", "NMSE": s03.get("NMSE", ""), "SSIM": s03.get("SSIM", ""), "status": "collapsed_in_001a"},
            {"variant": "S05_concat_Mshell_delta_Pcyc", "source": "001a_smoke", "NMSE": s05.get("NMSE", ""), "SSIM": s05.get("SSIM", ""), "status": "collapsed_in_001a"},
        ],
    )
    write_csv(output_root / "gradient_norms_S03_S05.csv", [{"status": "not_available", "reason": "full 001b training not run"}])
    fig, ax = plt.subplots(figsize=(5, 3.5))
    ax.text(0.5, 0.5, "Full S03/S05 training curves not available\n001b is incomplete", ha="center", va="center")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(output_root / "training_loss_curves_S03_S05.png", dpi=160)
    plt.close(fig)
    write_text(
        output_root / "metric_definition_audit.md",
        """# metric_definition_audit

## Overall NMSE

Overall NMSE is computed over the full 24^3 normalized volume: sum((pred-GT)^2)/sum(GT^2).

## Hard-Region NMSE

Hard-region NMSE should use the same squared-error numerator but restrict voxels to a deterministic mask, with denominator sum(GT^2 over the same mask). 001a used support-derived quantile masks for delta_rho and Pcyc diagnostics.

## Support and Background

Overall metrics can be dominated by low-valued background voxels for MAE-like metrics and by high-energy foreground for NMSE. 001b therefore requires support_masked_NMSE, foreground_MAE, background_MAE, high_delta_rho_support_NMSE, and high_Pcyc_support_NMSE in the full run.

## Current Status

Metric definitions are documented, but unified diagnostic metrics were not computed for full 001b because full model predictions were not generated.
""",
    )


def write_placeholders(output_root: Path) -> None:
    variants = [{"variant": key, "description": desc} for key, desc in VARIANTS]
    write_json(output_root / "model_variants.json", variants)
    write_json(
        output_root / "config_summary.json",
        {
            "task": "task_real_struc_001b",
            "status": "INCOMPLETE",
            "required_epochs": ">=50",
            "required_full_split": "800/100/100",
            "required_multiseed_variants": ["S02", "S04", "S05", "S06", "S07", "S08"],
            "source_dataset": str(SOURCE_006D),
        },
    )
    for name in [
        "metrics_overall_by_seed.csv",
        "metrics_overall_summary.csv",
        "metrics_by_delta_rho.csv",
        "metrics_by_Pcyc.csv",
        "metrics_by_shell_boundary.csv",
        "metrics_by_family.csv",
        "metrics_support_masked.csv",
        "runtime_table.csv",
        "parameter_count_table.csv",
    ]:
        write_csv(output_root / name, [{"status": "not_generated", "reason": "full 50-epoch S01-S11 multi-seed training not completed"}])
    write_text(output_root / "model_config_diffs.md", "\n".join([f"## {k}\n\n{d}\n" for k, d in VARIANTS]))
    ensure_dir(output_root / "training_curves")
    ensure_dir(output_root / "checkpoints")
    ensure_dir(output_root / "recon_compare")
    ensure_dir(output_root / "diagnostic_plots")


def write_env_git(output_root: Path) -> None:
    write_text(
        output_root / "environment.txt",
        f"python: {platform.python_version()}\ntorch: {torch.__version__}\nplatform: {platform.platform()}\n",
    )
    status = subprocess.run(["git", "status", "--short", "--branch"], cwd=PROJECT_ROOT, text=True, capture_output=True)
    branch = subprocess.run(["git", "branch", "--show-current"], cwd=PROJECT_ROOT, text=True, capture_output=True)
    log = subprocess.run(["git", "log", "--oneline", "-5"], cwd=PROJECT_ROOT, text=True, capture_output=True)
    write_text(output_root / "git_status.txt", status.stdout + "\ncurrent_branch=" + branch.stdout + "\n" + log.stdout)


def write_incomplete_report(output_root: Path, split_payload: dict[str, Any]) -> None:
    report = f"""# incomplete_report

status = INCOMPLETE

current_branch = task_struc_series
pushed_to_remote = pending at report generation
remote_branch = origin/task_struc_series

## Completed Items

- Synced `task_struc_series` with origin before work.
- Verified full split manifest availability: `{split_payload}`.
- Ran full-split metadata audit over available handoff samples.
- Investigated OOD dataset directory availability and wrote `metrics_ood.csv`.
- Wrote metric definition audit.
- Wrote S03/S05 failure audit based on 001a smoke-test outputs.
- Created required placeholder CSV/JSON/Markdown outputs with explicit incomplete reasons.

## Missing Items

- Full S01-S11 training was not run.
- Epoch requirement `>=50` was not satisfied.
- Required 3-seed variants S02/S04/S05/S06/S07/S08 were not run.
- Full OOD evaluation was not run.
- Unified support-masked metrics were not computed from full 001b predictions.
- Best checkpoints and convergence curves for full models are not available.

## Failure Reasons

The 001b prompt requires 11 variants, at least 50 epochs, and additional 3-seed runs for 6 key variants. This is a substantially larger run than the previous smoke test and was not completed in this execution turn. Per the prompt, a success report must not be written.

## Commands Already Run

```bash
git fetch origin
git checkout task_struc_series
git pull --ff-only origin task_struc_series
python -m workspace.eval.task_real_struc_001b_incomplete_audit --output-root {output_root}
```

## Recommended Next Command

Implement/launch the full training runner with:

```bash
python -m workspace.eval.task_real_struc_001b_full_runner --output-root exp/task_real_struc_001b_full_structure_diagnosis/<timestamp> --epochs 50 --seeds 0 1 2
```

## Scientific Interpretability

Partial audit results are scientifically useful for checking dataset availability, metadata validity, OOD data presence, and the 001a failure hypotheses. They are not sufficient to decide whether ReMiC-Net, FiLM, or RSB-FiLM is structurally justified.
"""
    write_text(output_root / "incomplete_report.md", report)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", default=None)
    args = parser.parse_args()
    if args.output_root is None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_root = PROJECT_ROOT / "exp" / "task_real_struc_001b_full_structure_diagnosis" / stamp
    else:
        output_root = Path(args.output_root)
    ensure_dir(output_root)
    rows, split_payload = verify_full_split(output_root)
    if rows:
        metadata_audit(output_root, rows)
    ood_investigation(output_root)
    smoke = copy_001a_metrics(output_root)
    write_failure_and_metric_audits(output_root, smoke)
    write_placeholders(output_root)
    write_env_git(output_root)
    write_incomplete_report(output_root, split_payload)
    print("task_real_struc_001b status: INCOMPLETE")
    print(f"experiment_root: {output_root}")
    print("current_branch: task_struc_series")
    print("remote_push_status: pending")
    print("best_overall_model: unavailable")
    print("best_SSIM_model: unavailable")
    print("best_hard_region_model: unavailable")
    print("S03_failure_status: unresolved_full_training_not_run")
    print("S05_failure_status: unresolved_full_training_not_run")
    print("Pcyc_scalar_status: unresolved")
    print("Pcyc_sincos_status: not_run")
    print("RSBFiLM_status: unproven")
    print("recommendation_for_task_real_struc_002: run full 001b training first")


if __name__ == "__main__":
    main()
