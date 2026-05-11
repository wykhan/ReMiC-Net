# task_real_005_report

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

- Dataset name: `task_real_005_shape_family_et_phase1`
- Total samples: `144`
- Families: `line, cross, L-shape, double-line, small_rect_edge, point_cluster`
- Counts by split: `{'train': 96, 'val': 24, 'test': 24}`
- Counts by family: `{'line': 24, 'cross': 24, 'L-shape': 24, 'double-line': 24, 'small_rect_edge': 24, 'point_cluster': 24}`
- GT definition: `voxel truth amplitude volume`
- Forward simulator: `workspace.sim.forward_cylindrical_point`

## 7. Experiment Summary

- Built ET shape families as protocol-grid scatterer supports and saved per-sample GT amplitude volumes
- Generated true cylindrical sparse echoes via `workspace.sim.forward_cylindrical_point`
- Ran `ref3/ref5/ref7/ref9/BP` with the frozen Variant B front-end and unified amplitude-volume outputs
- Collected global averages, family-group averages, per-sample records, failure tags, representative visuals, and a learning handoff manifest

## 8. Key Metrics

| Method | NMSE mean | PSNR mean | SSIM mean | Wall time mean (s) | Speedup vs BP |
| --- | ---: | ---: | ---: | ---: | ---: |
| ref3 | 6.4593 | 10.9748 | 0.0285 | 0.3311 | 5.9513 |
| ref5 | 3.4636 | 12.9886 | 0.0621 | 0.4455 | 4.4231 |
| ref7 | 3.1821 | 13.4254 | 0.0737 | 0.5599 | 3.5188 |
| ref9 | 2.7932 | 13.7603 | 0.0813 | 0.6733 | 2.9264 |
| BP | 2.6805 | 13.9988 | 0.1081 | 1.9703 | 1.0000 |

Family-level hardest `ref3` groups by mean NMSE:

1. `point_cluster` = 16.0039
2. `line` = 6.0356
3. `L-shape` = 4.7303

## 9. Failure Taxonomy

Failure labels:

- `F1`: overall blur / global smearing
- `F2`: edge break / contour fracture
- `F3`: thin-structure disappearance
- `F4`: support fragmentation
- `F5`: local geometric shift
- `F6`: weak-return region suppression

Counts by method:

- `ref3`: F1=49, F2=64, F3=25, F4=25, F5=36, F6=21
- `ref5`: F1=8, F2=86, F3=31, F4=13, F5=36, F6=27
- `ref7`: F1=6, F2=85, F3=35, F4=11, F5=32, F6=32
- `ref9`: F1=3, F2=90, F3=28, F4=12, F5=20, F6=22
- `BP`: F1=2, F2=56, F3=9, F4=16, F5=7, F6=9

Interpretation:

- the main learning targets are thin-structure, contour, and fragmented-support failures rather than raw speed alone
- the most valuable ET learning battlefields are the families with the worst `ref3` averages, especially `point_cluster`, `line`, and `L-shape`

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

- shape-family ET dataset sufficient to start `task_real_006`? `conditional`
- learning primary families: `point_cluster, line, L-shape`
- sampling rebalance required immediately? `no`, because ET-1 is already family-balanced
- Variant B stable enough as ET traditional front-end? `conditional`
- `Ready for learning stage?` = `conditional`

## 12. Suggested Next Task

`task_real_006`: use the ET handoff manifest to train and validate the two-stage `ref3 -> 3D U-Net -> GT amplitude` learning pipeline, prioritizing thin-structure and edge-fracture compensation.

## Key file paths for ChatGPT controller

- Report: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_005_shape_family_et/20260416_111500/task_real_005_report.md`
- Metrics: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_005_shape_family_et/20260416_111500/baseline_metrics_et.json`
- Curves: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_005_shape_family_et/20260416_111500/viz/curves/runtime_vs_method_et.png` and `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_005_shape_family_et/20260416_111500/viz/curves/failure_mode_count_by_method.png`
- Representative visuals: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_005_shape_family_et/20260416_111500/viz/recon_compare` and `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_005_shape_family_et/20260416_111500/viz/slices`
- Logs: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_005_shape_family_et/20260416_111500/logs`
- Learning handoff: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_005_shape_family_et/20260416_111500/learning_handoff_manifest.json`
