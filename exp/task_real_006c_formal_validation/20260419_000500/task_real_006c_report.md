# task_real_006c_report

## 1. Task Goal

Validate whether the current Frozen Mainline result is credible enough to justify entering the physics-consistency stage.

## 2. Formal-Scale Dataset Completion Statement

- shape-family current counts: `{'train': 576, 'val': 144, 'test': 144}`
- shape-family target counts: `{'train': 30000, 'val': 6000, 'test': 6000}`
- random ET current counts: `{'train': 192, 'val': 48, 'test': 48}`
- random ET target counts: `{'train': 5000, 'val': 1000, 'test': 1000}`
- formal-scale dataset completed? `no`

This task fails at the formal-scale gate because the required `5000/1000/1000` per-family and `5000/1000/1000` random-ET targets were not reached.

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
- `exp/task_real_006b_fullscale_mainline/20260417_000500/task_real_006b_report.md`

## 4. Boundary Statement

No new training or formal-scale comparison was run because task_real_006c explicitly forbids training before formal-scale dataset completion.

## 5. Frozen Mainline Definition

- Front-end: `Variant B`
- Physics backbone: `ref3`
- Second stage: `3D U-Net`
- Default training data: `shape-family main training`

## 6. Dataset Summary

- current shape-family total samples: `864`
- current random ET total samples: `288`
- current grand total samples: `1152`
- required grand total samples: `49000`

## 7. Split Integrity / Leakage Check

- duplicate scene-hash count: `0`
- duplicate parameter-signature count: `158`
- nearest train-test distance mean: `0.228101`
- nearest train-test distance min: `0.060051`

These checks were completed on the currently available shape-family dataset, but they do not satisfy the formal-scale requirement by themselves.

## 8. Model Audit Summary

- total params: `85017`
- trainable params: `85017`
- input shape: `[1, 1, 24, 24, 24]`
- output shape: `[1, 1, 24, 24, 24]`
- memory / FLOPs audit: not fully measured in this CPU-side audit

## 9. Formal-Scale Mainline vs Baselines

Not run.
Reason: formal-scale dataset completion failed, and task_real_006c forbids training/comparison before that gate is passed.

## 10. OOD / Generalization Results

Not run.
Reason: formal-scale dataset completion failed, and task_real_006c forbids downstream validation before that gate is passed.

## 11. Visual Outputs

- `viz/progress/curves/dataset_scale_completion.png`
- `viz/progress/curves/train_test_nearest_neighbor_distance.png`
- `viz/progress/curves/parameter_coverage_train_vs_test.png`
- placeholder not-run figures for the remaining formal validation outputs

## 12. Remaining Issues

- The primary blocker is formal-scale dataset completion.
- Only about `20 GB` remained on the current filesystem at audit time.
- Extrapolating from the current dataset footprint, full formal-scale data generation would require far more storage and compute than are currently available in this workspace.

## 13. Ready for Physics-Consistency Stage?

- formal-scale data truly completed? `no`
- train/test leakage found in the currently available shape-family set? `no exact-duplicate evidence`
- current 3D U-Net parameter count: `85017`
- Frozen Mainline OOD superiority verified on formal-scale data? `no`
- formal-scale BP-tier positioning verified? `no`
- `Ready for Physics-Consistency Stage?` = `no`

## 14. Suggested Next Task

Do not start `task_real_007` yet.
First resolve the formal-scale data-generation blocker by provisioning sufficient storage / compute and completing the required ET dataset scale.

## Key file paths for ChatGPT controller

- Report: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006c_formal_validation/20260419_000500/task_real_006c_report.md`
- Manifests: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006c_formal_validation/20260419_000500/dataset_manifest_shape_family_formal.json` and `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006c_formal_validation/20260419_000500/dataset_manifest_random_et_formal.json`
- Split integrity: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006c_formal_validation/20260419_000500/split_integrity_report.md`, `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006c_formal_validation/20260419_000500/duplicate_check.json`, `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006c_formal_validation/20260419_000500/nearest_neighbor_overlap.csv`
- Model audit: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006c_formal_validation/20260419_000500/model_audit.json` and `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006c_formal_validation/20260419_000500/model_summary.txt`
- Metrics: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006c_formal_validation/20260419_000500/metrics_frozen_mainline_formal.json`
- OOD: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006c_formal_validation/20260419_000500/ood_unseen_param_metrics.csv`, `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006c_formal_validation/20260419_000500/ood_leave_one_family_out_metrics.csv`, `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006c_formal_validation/20260419_000500/ood_random_et_metrics.csv`
- Curves: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006c_formal_validation/20260419_000500/viz/progress/curves`
- Representative visuals: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006c_formal_validation/20260419_000500/viz/paper_candidates` and `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006c_formal_validation/20260419_000500/viz/progress`
- Logs: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006c_formal_validation/20260419_000500/logs`
