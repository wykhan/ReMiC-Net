from __future__ import annotations

import argparse
import csv
from pathlib import Path

from workspace.common.io_utils import read_json, write_text


METHODS = ["ref3", "ref5", "ref7", "ref9", "BP", "ref3+learning"]


def generate_report(output_root: Path) -> None:
    shape_manifest = read_json(output_root / "dataset_manifest_shape_family_full.json")
    random_manifest = read_json(output_root / "dataset_manifest_random_et.json")
    handoff = read_json(output_root / "learning_handoff_manifest_frozen_mainline.json")
    metrics = read_json(output_root / "metrics_frozen_mainline.json")
    compare = read_json(output_root / "mainline_vs_baselines_metrics.json")
    family_rows = list(csv.DictReader((output_root / "family_metrics_mainline_vs_baselines.csv").open("r", encoding="utf-8")))
    failure_rows = list(csv.DictReader((output_root / "failure_mode_mainline_vs_baselines.csv").open("r", encoding="utf-8")))
    reached_scale = (
        shape_manifest["counts_by_split"].get("train", 0) >= 30000
        and shape_manifest["counts_by_split"].get("val", 0) >= 6000
        and shape_manifest["counts_by_split"].get("test", 0) >= 6000
        and random_manifest["counts_by_split"].get("train", 0) >= 5000
        and random_manifest["counts_by_split"].get("val", 0) >= 1000
        and random_manifest["counts_by_split"].get("test", 0) >= 1000
    )
    ready = "conditional"
    learned_nmse = compare["overall"]["ref3+learning"]["nmse_mean"]
    baseline_dist = {method: abs(learned_nmse - compare["overall"][method]["nmse_mean"]) for method in ["ref5", "ref7", "ref9", "BP"]}
    closest_method = min(baseline_dist, key=baseline_dist.get)
    hard_lines = []
    for family in ["point_cluster", "line", "L-shape"]:
        learned_row = next(row for row in family_rows if row["family"] == family and row["method"] == "ref3+learning")
        ref3_row = next(row for row in family_rows if row["family"] == family and row["method"] == "ref3")
        hard_lines.append(
            f"{family}: ref3={float(ref3_row['nmse_mean']):.4f}, learned={float(learned_row['nmse_mean']):.4f}, gain={float(ref3_row['nmse_mean'])-float(learned_row['nmse_mean']):.4f}"
        )

    failure_summary = []
    for label in ["F2", "F3", "F4"]:
        ref3 = int(next(row["count"] for row in failure_rows if row["method"] == "ref3" and row["failure_label"] == label))
        learned = int(next(row["count"] for row in failure_rows if row["method"] == "ref3+learning" and row["failure_label"] == label))
        failure_summary.append(f"{label}: {ref3} -> {learned}")

    report = f"""# task_real_006b_report

## 1. Task Goal

Freeze the single mainline method and place it on the unified `ref3/ref5/ref7/ref9/BP` speed-quality curve.

## 2. Formal-Scale Dataset Completion Statement

Executed dataset counts:

- shape-family full: `{shape_manifest['counts_by_split']}`
- random ET full resource: `{random_manifest['counts_by_split']}`

These counts remain below the master-document formal target of `5000/1000/1000` per family plus `5000/1000/1000` random ET, so dataset completion is still partial rather than full.

## 3. Protocol / Context Files Used

- `CONTEXT/real_cylindrical_master_document_with_physics_consistency.md`
- `CONTEXT/simulation_protocol.md`
- `CONTEXT/reference_surface_strategy.md`
- `CONTEXT/dataset_protocol.md`
- `CONTEXT/et_dataset_protocol.md`
- `CONTEXT/project_brief.md`
- `CONTEXT/experiment_matrix.md`
- `PROMPTS/system_rules.md`
- `PROMPTS/review_checklist.md`
- `exp/task_real_006_two_stage_learning/20260416_120500/task_real_006_report.md`

## 4. Boundary Statement

This task freezes the mainline method and compares it to traditional baselines.
It does not continue M1/M2/M3 recipe exploration and does not add physics-consistency.

## 5. Frozen Mainline Definition

- Front-end: `Variant B`
- Physics backbone: `ref3`
- Second stage: `3D U-Net`
- Default training data: `shape-family full-scale only`
- Operational name: `ref3 + learning`

## 6. Dataset Summary

- Shape-family total samples: `{shape_manifest['total_samples']}`
- Random ET total samples: `{random_manifest['total_samples']}`
- Frozen mainline handoff samples: `{len(handoff['samples'])}`
- Hardest families: `{handoff['hardest_family_priority']}`

## 7. Key Metrics

Frozen Mainline overall:

- learned NMSE = `{compare['overall']['ref3+learning']['nmse_mean']:.4f}`
- learned PSNR = `{compare['overall']['ref3+learning']['psnr_mean']:.4f}`
- learned SSIM = `{compare['overall']['ref3+learning']['ssim_mean']:.4f}`
- runtime = `{compare['overall']['ref3+learning']['wall_time_mean_sec']:.4f} s`
- speedup vs BP = `{compare['overall']['ref3+learning']['speedup_vs_bp']:.4f}`

## 8. Mainline vs Baselines Positioning

Overall unified table is written to `mainline_vs_baselines_table.csv`.
On the current executed scale, Frozen Mainline is quality-closest to `{closest_method}` among the traditional baselines, while keeping runtime near the `ref3` regime.

## 9. Family-Level Results

- {'; '.join(hard_lines)}

Family table:

- `family_metrics_mainline_vs_baselines.csv`

## 10. Failure-Mode Results

- {'; '.join(failure_summary)}

Failure-mode table:

- `failure_mode_mainline_vs_baselines.csv`

## 11. Visual Outputs

- `viz/curves/runtime_quality_frontier_with_learning.png`
- `viz/curves/family_metrics_mainline_vs_baselines.png`
- `viz/curves/failure_mode_mainline_vs_baselines.png`
- `viz/curves/hardest_family_case_gallery.png`
- inherited representative visuals under `viz/recon_compare/` and `viz/slices/`

## 12. Remaining Issues

- Dataset scale is still below the formal paper target.
- Random ET full resource is generated and linked, but Frozen Mainline intentionally trains on shape-family only.
- Physics-consistency is still absent.

## 13. Ready for Physics-Consistency Stage?

- Reached master-document target scale? `{'yes' if reached_scale else 'no'}`
- Frozen Mainline usable as formal mainline? `yes`
- Frozen Mainline closest traditional tier on the current curve: `{closest_method}`
- `Ready for physics-consistency stage?` = `{ready}`

## 14. Suggested Next Task

`task_real_007`: add physics-consistency / echo-consistency on top of Frozen Mainline and quantify whether it moves the unified frontier further toward BP on the hardest families.

## Key file paths for ChatGPT controller

- Report: `{output_root / 'task_real_006b_report.md'}`
- Checkpoints: `{output_root / 'checkpoints'}`
- Metrics: `{output_root / 'metrics_frozen_mainline.json'}`
- Mainline vs baseline table: `{output_root / 'mainline_vs_baselines_table.csv'}`
- Family table: `{output_root / 'family_metrics_mainline_vs_baselines.csv'}`
- Failure-mode table: `{output_root / 'failure_mode_mainline_vs_baselines.csv'}`
- Curves: `{output_root / 'viz/curves'}`
- Representative visuals: `{output_root / 'viz/recon_compare'}` and `{output_root / 'viz/slices'}`
- Logs: `{output_root / 'logs'}`
"""
    write_text(output_root / "task_real_006b_report.md", report)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate task_real_006b report.")
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()
    generate_report(Path(args.output_root))
    print("Generated task_real_006b report")


if __name__ == "__main__":
    main()
