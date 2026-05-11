from __future__ import annotations

import argparse
import csv
from pathlib import Path

from workspace.common.io_utils import read_json, write_text


def _load_optional(output_root: Path, name: str) -> dict | None:
    path = output_root / name
    return read_json(path) if path.exists() else None


def generate_report(output_root: Path) -> None:
    shape_manifest = read_json(output_root / "dataset_manifest_shape_family_full.json")
    random_manifest = read_json(output_root / "dataset_manifest_random_et.json")
    handoff = read_json(output_root / "learning_handoff_manifest_full.json")
    m1 = _load_optional(output_root, "metrics_M1.json")
    m2 = _load_optional(output_root, "metrics_M2.json")
    m3 = _load_optional(output_root, "metrics_M3.json")
    ready = "conditional"
    reached_scale = False

    family_rows = []
    if (output_root / "family_metrics.csv").exists():
        family_rows = list(csv.DictReader((output_root / "family_metrics.csv").open("r", encoding="utf-8")))
    hard_family_summary = []
    for family in ["point_cluster", "line", "L-shape"]:
        match = next((row for row in family_rows if row["mode"] == "M1" and row["family"] == family), None)
        if match is not None:
            hard_family_summary.append(f"{family}: nmse_gain={float(match['ref3_nmse_mean']) - float(match['learned_nmse_mean']):.4f}")

    def overall_line(metrics: dict | None, mode: str) -> str:
        if metrics is None:
            return f"| {mode} | not run | not run | not run | not run |"
        overall = metrics["overall"]
        return (
            f"| {mode} | {overall['learned_nmse_mean']:.4f} | {overall['learned_psnr_mean']:.4f} | "
            f"{overall['learned_ssim_mean']:.4f} | {overall['nmse_gain_vs_ref3']:.4f} |"
        )

    report = f"""# task_real_006_report

## 1. Task Goal

Train the first formal two-stage ET learning pipeline under the frozen cylindrical Variant B front-end:
`ref3 coarse volume -> 3D U-Net -> GT amplitude`.

## 2. Dataset Scale Upgrade Statement

This task expands beyond the ET-1 reduced set from `task_real_005`.
Completed executed scale:

- shape-family full dataset counts by split: `{shape_manifest['counts_by_split']}`
- random ET supplement counts by split: `{random_manifest['counts_by_split']}`

This is still below the master-document target of `5000/1000/1000` per family plus `5000/1000/1000` random ET, so the present run should be interpreted as the first substantial ET-2 formal training pass under local resource limits rather than the final paper-scale dataset.

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
- `exp/task_real_005_shape_family_et/20260416_111500/task_real_005_report.md`

## 4. Boundary Statement

This task trains and evaluates the second-stage learning pipeline only.
It does not revisit the frozen traditional front-end, add physics-consistency losses, use complex supervision, or integrate real echoes.

## 5. Manisali Borrowing Summary

Borrowed from the Manisali paper and repository:

- coarse-to-GT two-stage decomposition
- 3D U-Net second stage fed by a physics-based first-stage volume
- dataset organization that stores first-stage inputs, GT targets, and reusable checkpoints/visuals
- projection/slice-oriented qualitative reporting style

Borrowed concretely from the inspected repository:

- `src/src.py`: 3D U-Net input-output organization and the first-stage-to-network handoff concept
- `src/misc.py`: max-projection, scene-visualization, and reporting style
- `README.md`: checkpoint-oriented usage framing and model/data separation

Not copied directly:

- the planar / near-field MIMO sensing model
- the adjoint observation-matrix first stage
- their exact tensor shape conventions and TensorFlow implementation

Replacement in this project:

- Manisali first stage is replaced by frozen cylindrical `Variant B ref3`
- Manisali second-stage and dataset-engineering ideas are retained and adapted to the current PyTorch ET pipeline

## 6. Training Matrix

- `M0`: inherited bare `ref3` non-learning baseline
- `M1`: shape-family full + random ET supplement
- `M2`: shape-family full only
- `M3`: `M1` with hard-family emphasis on `point_cluster / line / L-shape`

## 7. Dataset Summary

- Shape-family dataset: `{shape_manifest['total_samples']}` samples
- Random ET dataset: `{random_manifest['total_samples']}` samples
- Full handoff total samples: `{len(handoff['samples'])}`
- Hard-family priority: `{handoff['hardest_family_priority']}`

## 8. Key Metrics

| Mode | Learned NMSE | Learned PSNR | Learned SSIM | NMSE gain vs ref3 |
| --- | ---: | ---: | ---: | ---: |
{overall_line(m1, 'M1')}
{overall_line(m2, 'M2')}
{overall_line(m3, 'M3')}

## 9. Family-Level Results

Primary hard-family summary from `M1`:

- {'; '.join(hard_family_summary) if hard_family_summary else 'not available'}

The hardest families from `task_real_005` remain the main learning battlefield: `point_cluster`, `line`, and `L-shape`.

## 10. Failure-Mode Improvement

The main monitored failure labels are `F2`, `F3`, and `F4`.
See:

- `failure_mode_improvement.csv`
- `viz/curves/failure_mode_improvement.png`

These files quantify whether learned outputs reduce contour fracture, thin-structure disappearance, and support fragmentation relative to bare `ref3`.

## 11. Visual Outputs

- `viz/curves/train_val_loss_M1.png`
- `viz/curves/train_val_loss_M2.png`
- `viz/curves/train_val_loss_M3.png`
- `viz/curves/quality_gain_vs_ref3.png`
- `viz/curves/family_metrics_learning.png`
- `viz/curves/failure_mode_improvement.png`
- `viz/recon_compare/*`
- `viz/slices/*`

## 12. Remaining Issues

- The executed ET-2 dataset is still below the master-document formal target scale.
- The second stage currently uses amplitude-only supervision and a compact U-Net, not a larger paper-tuned architecture.
- Physics-consistency loss is still absent and belongs to the next task.

## 13. Ready for Physics-Consistency Stage?

- Reached master-document target scale? `{'yes' if reached_scale else 'no'}`
- `ref3 + 3D U-Net` usable as first formal mainline? `{'yes' if m1 is not None and m1['overall']['nmse_gain_vs_ref3'] > 0 else 'conditional'}`
- Hardest families improved? `{'yes' if hard_family_summary else 'conditional'}`
- `Ready for physics-consistency stage?` = `{ready}`

## 14. Suggested Next Task

`task_real_007`: add physics-consistency / echo-consistency to the trained cylindrical two-stage baseline and test whether it further reduces `F2/F3/F4` on the hardest ET families.

## Key file paths for ChatGPT controller

- Report: `{output_root / 'task_real_006_report.md'}`
- Checkpoints: `{output_root / 'checkpoints'}`
- Metrics: `{output_root / 'metrics_M1.json'}`, `{output_root / 'metrics_M2.json'}`, `{output_root / 'metrics_M3.json'}`
- Family tables: `{output_root / 'family_metrics.csv'}`
- Failure-mode table: `{output_root / 'failure_mode_improvement.csv'}`
- Curves: `{output_root / 'viz/curves'}`
- Representative visuals: `{output_root / 'viz/recon_compare'}` and `{output_root / 'viz/slices'}`
- Logs: `{output_root / 'logs'}`
"""
    write_text(output_root / "task_real_006_report.md", report)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate task_real_006 report.")
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()
    generate_report(Path(args.output_root))
    print("Generated task_real_006 report")


if __name__ == "__main__":
    main()
