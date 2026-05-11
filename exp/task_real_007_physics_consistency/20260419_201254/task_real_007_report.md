# task_real_007_report

## 1. Task Goal

Add a minimal sampled forward echo consistency loss on top of the frozen 800-scale baseline and compare Baseline-Ours vs Ours-PC-P1 on the frozen main test and three OOD datasets.

## 2. Frozen Baseline Reused

- baseline source root: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006d_800_formal/20260419_112717`
- baseline checkpoint: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006d_800_formal/20260419_112717/checkpoints/frozen_mainline/best.pt`
- six-method background reference: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006e_comprehensive_eval/20260419_190046/task_real_006e_report.md`

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

where `L_echo` is echo-domain NMSE on a fixed sparse subset of the original cylindrical measurements. The executed config is stored at `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007_physics_consistency/20260419_201254/consistency_config_P1.yaml`.

P2 was not executed in this run because the task only requires it as an optional enhancement after validating P1.

## 6. Training Matrix

- Baseline-Ours: reused only, not retrained
- Ours-PC-P1: trained from the baseline checkpoint with the added echo consistency term
- Ours-PC-P2: not executed

## 7. Main Test Comparison

- `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007_physics_consistency/20260419_201254/metrics_baseline_vs_pc_main.csv`

## 8. OOD Comparison

- `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007_physics_consistency/20260419_201254/metrics_baseline_vs_pc_unseen_param_ood.csv`
- `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007_physics_consistency/20260419_201254/metrics_baseline_vs_pc_leave_one_family_out_ood.csv`
- `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007_physics_consistency/20260419_201254/metrics_baseline_vs_pc_random_et_ood.csv`

## 9. Failure-Mode Improvement

- `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007_physics_consistency/20260419_201254/failure_mode_pc_improvement.csv`

## 10. Hardest-Family Improvement

- `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007_physics_consistency/20260419_201254/hardest_family_pc_improvement.csv`

## 11. Visual Outputs

- `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007_physics_consistency/20260419_201254/viz/progress/curves/baseline_vs_pc_main_metrics.png`
- `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007_physics_consistency/20260419_201254/viz/progress/curves/baseline_vs_pc_ood_metrics.png`
- `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007_physics_consistency/20260419_201254/viz/progress/curves/baseline_vs_pc_runtime_speedup.png`
- `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007_physics_consistency/20260419_201254/viz/progress/curves/baseline_vs_pc_failure_modes.png`
- `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007_physics_consistency/20260419_201254/viz/progress/curves/baseline_vs_pc_hardest_families.png`
- `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007_physics_consistency/20260419_201254/viz/progress/curves/baseline_vs_pc_frontier_ood.png`
- `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007_physics_consistency/20260419_201254/viz/paper_candidates/qualitative/pc_best_case_panel.png`
- `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007_physics_consistency/20260419_201254/viz/paper_candidates/qualitative/pc_failure_case_panel.png`

## 12. Git Update Summary

`/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007_physics_consistency/20260419_201254/git_update_summary.md`

## 13. Remaining Issues

- P2 was not executed.
- This comparison still inherits the 800-scale frozen protocol rather than a larger formal-scale dataset.

## 14. Is Physics-Consistency Worth Keeping?

`conditional`

P1 should be kept if it improves at least one of the main/OOD aggregates or materially reduces `F2/F3/F4` on the hardest families without changing runtime materially. The final CSVs determine that conclusion directly.

## 15. Suggested Next Task

If P1 is beneficial, continue to the next controlled refinement or write it into the main method section; otherwise keep it as an ablation-side branch and retain the frozen baseline as the main method.

### Key file paths for ChatGPT controller

- report path: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007_physics_consistency/20260419_201254/task_real_007_report.md`
- baseline reference path: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007_physics_consistency/20260419_201254/baseline_reference_manifest_007.json`
- consistency config path: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007_physics_consistency/20260419_201254/consistency_config_P1.yaml`
- metrics path: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007_physics_consistency/20260419_201254/metrics_baseline_vs_pc_main.csv`, `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007_physics_consistency/20260419_201254/metrics_baseline_vs_pc_unseen_param_ood.csv`, `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007_physics_consistency/20260419_201254/metrics_baseline_vs_pc_leave_one_family_out_ood.csv`, `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007_physics_consistency/20260419_201254/metrics_baseline_vs_pc_random_et_ood.csv`
- failure-mode path: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007_physics_consistency/20260419_201254/failure_mode_pc_improvement.csv`
- family path: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007_physics_consistency/20260419_201254/hardest_family_pc_improvement.csv`
- curves path: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007_physics_consistency/20260419_201254/viz/progress/curves`
- representative visuals path: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007_physics_consistency/20260419_201254/viz/paper_candidates/qualitative`
- git summary path: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007_physics_consistency/20260419_201254/git_update_summary.md`
- logs path: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_007_physics_consistency/20260419_201254/logs`
