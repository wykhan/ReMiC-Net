# task_real_006e_report

## 1. Task Goal

Complete the comprehensive six-method evaluation on the main test and all three OOD datasets without retraining or changing the dataset protocol.

## 2. Frozen Inputs Reused

- source root: `exp/task_real_006d_800_formal/20260419_112717`
- frozen checkpoint: `exp/task_real_006d_800_formal/20260419_112717/checkpoints/frozen_mainline/best.pt`
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

- methods: `Ref3, Ref5, Ref7, Ref9, BP, Ours`
- datasets: `Main Test, Unseen-Parameter OOD, Leave-One-Family-Out Focused OOD, Random-ET OOD`
- metrics: `NMSE / PSNR / SSIM / runtime / speedup_vs_BP`

## 6. Main Test Results

The main test all-method table is stored at `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006e_comprehensive_eval/20260419_190046/main_test_metrics_all_methods.csv`.

## 7. OOD Results

- unseen-parameter OOD: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006e_comprehensive_eval/20260419_190046/ood_unseen_param_metrics_all_methods.csv`
- leave-one-family-out focused OOD: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006e_comprehensive_eval/20260419_190046/ood_leave_one_family_out_metrics_all_methods.csv`
- random-ET OOD: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006e_comprehensive_eval/20260419_190046/ood_random_et_metrics_all_methods.csv`

## 8. Positioning of Ours vs Baselines

# positioning_summary

### Main Test

- Ours NMSE mean = `0.807482`
- Ours ranking by NMSE = `1/6`
- Ours is closest in quality to `Ref9` among the traditional references.
- Ours outperforms: `BP, Ref9, Ref7, Ref5, Ref3`
- Ours speedup_vs_BP = `5.188`
- Ours stays near the Ref3 runtime band if its runtime mean is closer to Ref3 than to BP.

### Unseen-Parameter OOD

- Ours NMSE mean = `0.723074`
- Ours ranking by NMSE = `1/6`
- Ours is closest in quality to `Ref9` among the traditional references.
- Ours outperforms: `BP, Ref9, Ref7, Ref5, Ref3`
- Ours speedup_vs_BP = `5.633`
- Ours stays near the Ref3 runtime band if its runtime mean is closer to Ref3 than to BP.

### Leave-One-Family-Out Focused OOD

- Ours NMSE mean = `0.977576`
- Ours ranking by NMSE = `1/6`
- Ours is closest in quality to `Ref9` among the traditional references.
- Ours outperforms: `BP, Ref9, Ref7, Ref5, Ref3`
- Ours speedup_vs_BP = `4.514`
- Ours stays near the Ref3 runtime band if its runtime mean is closer to Ref3 than to BP.

### Random-ET OOD

- Ours NMSE mean = `1.151614`
- Ours ranking by NMSE = `1/6`
- Ours is closest in quality to `Ref9` among the traditional references.
- Ours outperforms: `BP, Ref9, Ref7, Ref5, Ref3`
- Ours speedup_vs_BP = `3.905`
- Ours stays near the Ref3 runtime band if its runtime mean is closer to Ref3 than to BP.


## 9. Visual Outputs

- `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006e_comprehensive_eval/20260419_190046/viz/progress/curves/main_test_unified_metrics.png`
- `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006e_comprehensive_eval/20260419_190046/viz/progress/curves/ood_nmse_unified.png`
- `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006e_comprehensive_eval/20260419_190046/viz/progress/curves/ood_psnr_unified.png`
- `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006e_comprehensive_eval/20260419_190046/viz/progress/curves/ood_ssim_unified.png`
- `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006e_comprehensive_eval/20260419_190046/viz/progress/curves/runtime_speedup_across_datasets.png`
- `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006e_comprehensive_eval/20260419_190046/viz/progress/curves/frontier_main_and_ood.png`
- `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006e_comprehensive_eval/20260419_190046/viz/progress/curves/nmse_distribution_across_datasets.png`
- `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006e_comprehensive_eval/20260419_190046/viz/progress/curves/psnr_distribution_across_datasets.png`
- `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006e_comprehensive_eval/20260419_190046/viz/progress/curves/ssim_distribution_across_datasets.png`
- `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006e_comprehensive_eval/20260419_190046/viz/progress/curves/ood_unseen_param_case_panel.png`
- `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006e_comprehensive_eval/20260419_190046/viz/progress/curves/ood_leave_one_family_case_panel.png`
- `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006e_comprehensive_eval/20260419_190046/viz/progress/curves/ood_random_et_case_panel.png`

## 10. Remaining Issues

- This still builds on the 800-scale literature-matched dataset rather than the larger formal-scale target.
- Runtime is measured inside the current software stack and should be treated as controlled local timing rather than deployment timing.

## 11. Ready for Physics-Consistency Stage?

`conditional`

The evaluation matrix is now substantially more complete than in task_real_006d. Moving to task_real_007 is reasonable if the controller accepts the 800-scale frozen dataset as the controlled pre-physics baseline.

## 12. Suggested Next Task

`task_real_007`: introduce physics-consistency on top of the frozen 800-scale setup and compare against the fully evaluated six-method baseline matrix.

## Key file paths for ChatGPT controller

- report path: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006e_comprehensive_eval/20260419_190046/task_real_006e_report.md`
- all metrics path: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006e_comprehensive_eval/20260419_190046/mainline_vs_baselines_all_datasets.csv`
- per-sample path: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006e_comprehensive_eval/20260419_190046/per_sample_metrics_all_datasets.csv`
- positioning path: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006e_comprehensive_eval/20260419_190046/positioning_summary.md`
- curves path: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006e_comprehensive_eval/20260419_190046/viz/progress/curves`
- representative visuals path: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006e_comprehensive_eval/20260419_190046/viz/paper_candidates/qualitative`
- logs path: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006e_comprehensive_eval/20260419_190046/logs`
