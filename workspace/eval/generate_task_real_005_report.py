from __future__ import annotations

import argparse
from pathlib import Path

from workspace.common.io_utils import read_json, write_text


METHOD_ORDER = ["ref3", "ref5", "ref7", "ref9", "BP"]


def generate_report(output_root: Path) -> None:
    dataset_manifest = read_json(output_root / "dataset_manifest.json")
    baseline = read_json(output_root / "baseline_metrics_et.json")
    handoff = read_json(output_root / "learning_handoff_manifest.json")
    failures = read_json(output_root / "failure_case_index.json")
    agg = baseline["aggregate"]
    by_family = baseline["by_family"]
    failure_counts = baseline["failure_summary"]["counts_by_method"]
    hardest = handoff["family_priority_for_learning"][0]["family"]
    next_hard = handoff["family_priority_for_learning"][1]["family"]
    third_hard = handoff["family_priority_for_learning"][2]["family"]
    ready = "conditional"

    report = f"""# task_real_005_report

## 1. Task Goal

Build the first true-cylindrical shape-family ET dataset, run the frozen Variant B traditional front-end with `ref3/ref5/ref7/ref9/BP`, and produce the first ET main table, main figures, failure taxonomy, and learning handoff manifest.

## 2. ET Dataset Protocol Freeze Statement

`CONTEXT/et_dataset_protocol.md` is now created and frozen for Phase ET-1.
The mandatory family set is:

- `line`
- `cross`
- `L-shape`
- `double-line`
- `small_rect_edge`
- `point_cluster`

The executed ET-1 scale for `task_real_005` is the reduced but balanced per-family split:

- `train = 16`
- `val = 4`
- `test = 4`

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
- `exp/task_real_004c_variantB_confirmation/20260416_003500/task_real_004c_report.md`

## 4. Boundary Statement

This task only covers true cylindrical ET dataset generation, frozen Variant B and BP traditional baselines, failure taxonomy, visualization, and learning handoff preparation.
It does not train a network, impose physics consistency, revisit the front-end route, or integrate real echoes.

## 5. Manisali Borrowing Summary

Borrowed from the Manisali paper and codebase:

- the engineering separation of a physics-based first stage and a 3D U-Net second stage
- the dataset organization idea that stores a coarse physical reconstruction together with a voxel GT target
- the handoff structure needed for `ref3 coarse volume -> 3D U-Net -> GT amplitude`
- representative visualization style centered on 3D views, projections, and slice-based comparisons

Borrowed specifically from the inspected git project:

- `README.md`: two-stage problem framing and model/data split
- `src/src.py`: 3D U-Net I/O shape organization and stage separation
- `src/misc.py`: representative projection/scene visualization style

Not copied directly:

- the planar / near-field MIMO observation model
- the adjoint-style first-stage front-end
- the original paper's sensing geometry and random ET synthesis assumptions

Replacement in the current project:

- Manisali first stage is replaced here by the frozen cylindrical `Variant B` accelerated front-end
- BP remains the higher-quality traditional ET baseline
- Manisali second-stage and data-engineering thinking are retained only as the learning-handoff template

## 6. Dataset Summary

- Dataset name: `{dataset_manifest['dataset_name']}`
- Total samples: `{dataset_manifest['total_samples']}`
- Families: `{", ".join(dataset_manifest['family_names'])}`
- Counts by split: `{dataset_manifest['counts_by_split']}`
- Counts by family: `{dataset_manifest['counts_by_family']}`
- GT definition: `{dataset_manifest['gt_definition']}`
- Forward simulator: `{dataset_manifest['forward_simulator_entry']}`

## 7. Experiment Summary

- Built ET shape families as protocol-grid scatterer supports and saved per-sample GT amplitude volumes
- Generated true cylindrical sparse echoes via `workspace.sim.forward_cylindrical_point`
- Ran `ref3/ref5/ref7/ref9/BP` with the frozen Variant B front-end and unified amplitude-volume outputs
- Collected global averages, family-group averages, per-sample records, failure tags, representative visuals, and a learning handoff manifest

## 8. Key Metrics

| Method | NMSE mean | PSNR mean | SSIM mean | Wall time mean (s) | Speedup vs BP |
| --- | ---: | ---: | ---: | ---: | ---: |
| ref3 | {agg['ref3']['nmse_mean']:.4f} | {agg['ref3']['psnr_mean']:.4f} | {agg['ref3']['ssim_mean']:.4f} | {agg['ref3']['wall_time_mean_sec']:.4f} | {agg['ref3']['speedup_vs_bp']:.4f} |
| ref5 | {agg['ref5']['nmse_mean']:.4f} | {agg['ref5']['psnr_mean']:.4f} | {agg['ref5']['ssim_mean']:.4f} | {agg['ref5']['wall_time_mean_sec']:.4f} | {agg['ref5']['speedup_vs_bp']:.4f} |
| ref7 | {agg['ref7']['nmse_mean']:.4f} | {agg['ref7']['psnr_mean']:.4f} | {agg['ref7']['ssim_mean']:.4f} | {agg['ref7']['wall_time_mean_sec']:.4f} | {agg['ref7']['speedup_vs_bp']:.4f} |
| ref9 | {agg['ref9']['nmse_mean']:.4f} | {agg['ref9']['psnr_mean']:.4f} | {agg['ref9']['ssim_mean']:.4f} | {agg['ref9']['wall_time_mean_sec']:.4f} | {agg['ref9']['speedup_vs_bp']:.4f} |
| BP | {agg['BP']['nmse_mean']:.4f} | {agg['BP']['psnr_mean']:.4f} | {agg['BP']['ssim_mean']:.4f} | {agg['BP']['wall_time_mean_sec']:.4f} | {agg['BP']['speedup_vs_bp']:.4f} |

Family-level hardest `ref3` groups by mean NMSE:

1. `{hardest}` = {by_family[hardest]['ref3']['nmse_mean']:.4f}
2. `{next_hard}` = {by_family[next_hard]['ref3']['nmse_mean']:.4f}
3. `{third_hard}` = {by_family[third_hard]['ref3']['nmse_mean']:.4f}

## 9. Failure Taxonomy

Failure labels:

- `F1`: overall blur / global smearing
- `F2`: edge break / contour fracture
- `F3`: thin-structure disappearance
- `F4`: support fragmentation
- `F5`: local geometric shift
- `F6`: weak-return region suppression

Counts by method:

- `ref3`: F1={failure_counts['ref3']['F1']}, F2={failure_counts['ref3']['F2']}, F3={failure_counts['ref3']['F3']}, F4={failure_counts['ref3']['F4']}, F5={failure_counts['ref3']['F5']}, F6={failure_counts['ref3']['F6']}
- `ref5`: F1={failure_counts['ref5']['F1']}, F2={failure_counts['ref5']['F2']}, F3={failure_counts['ref5']['F3']}, F4={failure_counts['ref5']['F4']}, F5={failure_counts['ref5']['F5']}, F6={failure_counts['ref5']['F6']}
- `ref7`: F1={failure_counts['ref7']['F1']}, F2={failure_counts['ref7']['F2']}, F3={failure_counts['ref7']['F3']}, F4={failure_counts['ref7']['F4']}, F5={failure_counts['ref7']['F5']}, F6={failure_counts['ref7']['F6']}
- `ref9`: F1={failure_counts['ref9']['F1']}, F2={failure_counts['ref9']['F2']}, F3={failure_counts['ref9']['F3']}, F4={failure_counts['ref9']['F4']}, F5={failure_counts['ref9']['F5']}, F6={failure_counts['ref9']['F6']}
- `BP`: F1={failure_counts['BP']['F1']}, F2={failure_counts['BP']['F2']}, F3={failure_counts['BP']['F3']}, F4={failure_counts['BP']['F4']}, F5={failure_counts['BP']['F5']}, F6={failure_counts['BP']['F6']}

Interpretation:

- the main learning targets are thin-structure, contour, and fragmented-support failures rather than raw speed alone
- the most valuable ET learning battlefields are the families with the worst `ref3` averages, especially `{hardest}`, `{next_hard}`, and `{third_hard}`

## 10. Visual Outputs

- `viz/curves/runtime_vs_method_et.png`
- `viz/curves/speedup_vs_bp_et.png`
- `viz/curves/quality_vs_method_et.png`
- `viz/curves/metrics_by_family.png`
- `viz/curves/failure_mode_count_by_method.png`
- `viz/scene_3d/*`
- `viz/recon_compare/*`
- `viz/slices/*`

## 11. Readiness for Learning Stage

- shape-family ET dataset sufficient to start `task_real_006`? `{ready}`
- learning primary families: `{", ".join(handoff['recommended_primary_families'])}`
- sampling rebalance required immediately? `no`, because ET-1 is already family-balanced
- Variant B stable enough as ET traditional front-end? `conditional`
- `Ready for learning stage?` = `{ready}`

## 12. Suggested Next Task

`task_real_006`: use the ET handoff manifest to train and validate the two-stage `ref3 -> 3D U-Net -> GT amplitude` learning pipeline, prioritizing thin-structure and edge-fracture compensation.

## Key file paths for ChatGPT controller

- Report: `{output_root / 'task_real_005_report.md'}`
- Metrics: `{output_root / 'baseline_metrics_et.json'}`
- Curves: `{output_root / 'viz/curves/runtime_vs_method_et.png'}` and `{output_root / 'viz/curves/failure_mode_count_by_method.png'}`
- Representative visuals: `{output_root / 'viz/recon_compare'}` and `{output_root / 'viz/slices'}`
- Logs: `{output_root / 'logs'}`
- Learning handoff: `{output_root / 'learning_handoff_manifest.json'}`
"""
    write_text(output_root / "task_real_005_report.md", report)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the task_real_005 ET report.")
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()
    generate_report(Path(args.output_root))
    print("Generated task_real_005 report")


if __name__ == "__main__":
    main()
