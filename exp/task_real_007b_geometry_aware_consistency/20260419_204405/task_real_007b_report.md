# task_real_007b_report

## 1. Task Goal

Upgrade the `task_real_007` sampled consistency into a geometry-aware support-weighted consistency and compare Baseline-Ours vs Ours-PC-P1 vs Ours-PC-P2A on the frozen 800-scale protocol.

## 2. Frozen Baseline / P1 Reused

- baseline source root: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006d_800_formal/20260419_112717`
- baseline checkpoint: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006d_800_formal/20260419_112717/checkpoints/frozen_mainline/best.pt`
- P1 source root: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007_physics_consistency/20260419_201254`
- P1 checkpoint: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007_physics_consistency/20260419_201254/checkpoints/pc_p1/best.pt`

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

where `L_echo_geo` is computed on the same sparse cylindrical measurement subset as P1, but with a dynamic prediction-derived support mask. Voxels above a support threshold are assigned higher support weights, a one-voxel dilation defines a lightweight geometry neighborhood, and measurement-domain weights are derived from support-weighted projected energy. The executed config is stored at `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007b_geometry_aware_consistency/20260419_204405/consistency_config_P2A.yaml`.

P2B was not executed in this run. `scripts/run_pc_training_P2B.sh` is present only as a controlled placeholder because P2A already provides the required mandatory extension and this round is not a recipe search task.

## 6. Training Matrix

- Baseline-Ours: reused only
- Ours-PC-P1: reused only
- Ours-PC-P2A: trained from the frozen `task_real_007` P1 checkpoint
- Ours-PC-P2B: not executed

## 7. Main Test Comparison

- `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007b_geometry_aware_consistency/20260419_204405/metrics_baseline_p1_p2_main.csv`

## 8. OOD Comparison

- `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007b_geometry_aware_consistency/20260419_204405/metrics_baseline_p1_p2_unseen_param_ood.csv`
- `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007b_geometry_aware_consistency/20260419_204405/metrics_baseline_p1_p2_leave_one_family_out_ood.csv`
- `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007b_geometry_aware_consistency/20260419_204405/metrics_baseline_p1_p2_random_et_ood.csv`

## 9. Failure-Mode Improvement

- `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007b_geometry_aware_consistency/20260419_204405/failure_mode_p2_improvement.csv`

## 10. Hardest-Family Improvement

- `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007b_geometry_aware_consistency/20260419_204405/hardest_family_p2_improvement.csv`

## 11. Visual Outputs

- `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007b_geometry_aware_consistency/20260419_204405/viz/progress/curves/baseline_p1_p2_main_metrics.png`
- `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007b_geometry_aware_consistency/20260419_204405/viz/progress/curves/baseline_p1_p2_ood_metrics.png`
- `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007b_geometry_aware_consistency/20260419_204405/viz/progress/curves/baseline_p1_p2_runtime_speedup.png`
- `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007b_geometry_aware_consistency/20260419_204405/viz/progress/curves/baseline_p1_p2_failure_modes.png`
- `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007b_geometry_aware_consistency/20260419_204405/viz/progress/curves/baseline_p1_p2_hardest_families.png`
- `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007b_geometry_aware_consistency/20260419_204405/viz/progress/curves/baseline_p1_p2_frontier_ood.png`
- `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007b_geometry_aware_consistency/20260419_204405/viz/paper_candidates/qualitative/p2_best_case_panel.png`
- `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007b_geometry_aware_consistency/20260419_204405/viz/paper_candidates/qualitative/p2_failure_case_panel.png`

## 12. Git Update Summary

`/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007b_geometry_aware_consistency/20260419_204405/git_update_summary_007b.md`

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

- report path: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007b_geometry_aware_consistency/20260419_204405/task_real_007b_report.md`
- baseline/P1 reference path: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007b_geometry_aware_consistency/20260419_204405/baseline_p1_reference_manifest_007b.json`
- consistency config path: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007b_geometry_aware_consistency/20260419_204405/consistency_config_P2A.yaml`
- metrics path: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007b_geometry_aware_consistency/20260419_204405/metrics_baseline_p1_p2_main.csv`, `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007b_geometry_aware_consistency/20260419_204405/metrics_baseline_p1_p2_unseen_param_ood.csv`, `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007b_geometry_aware_consistency/20260419_204405/metrics_baseline_p1_p2_leave_one_family_out_ood.csv`, `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007b_geometry_aware_consistency/20260419_204405/metrics_baseline_p1_p2_random_et_ood.csv`
- failure-mode path: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007b_geometry_aware_consistency/20260419_204405/failure_mode_p2_improvement.csv`
- family path: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007b_geometry_aware_consistency/20260419_204405/hardest_family_p2_improvement.csv`
- curves path: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007b_geometry_aware_consistency/20260419_204405/viz/progress/curves`
- representative visuals path: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007b_geometry_aware_consistency/20260419_204405/viz/paper_candidates/qualitative`
- git summary path: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007b_geometry_aware_consistency/20260419_204405/git_update_summary_007b.md`
- logs path: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007b_geometry_aware_consistency/20260419_204405/logs`
