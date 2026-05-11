# task_real_006b_report

## 1. Task Goal

Freeze the single mainline method and place it on the unified `ref3/ref5/ref7/ref9/BP` speed-quality curve.

## 2. Formal-Scale Dataset Completion Statement

Executed dataset counts:

- shape-family full: `{'train': 576, 'val': 144, 'test': 144}`
- random ET full resource: `{'train': 192, 'val': 48, 'test': 48}`

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

- Shape-family total samples: `864`
- Random ET total samples: `288`
- Frozen mainline handoff samples: `864`
- Hardest families: `['point_cluster', 'line', 'L-shape']`

## 7. Key Metrics

Frozen Mainline overall:

- learned NMSE = `0.8281`
- learned PSNR = `30.9922`
- learned SSIM = `0.6265`
- runtime = `0.3919 s`
- speedup vs BP = `5.2514`

## 8. Mainline vs Baselines Positioning

Overall unified table is written to `mainline_vs_baselines_table.csv`.
On the current executed scale, Frozen Mainline is quality-closest to `BP` among the traditional baselines, while keeping runtime near the `ref3` regime.

## 9. Family-Level Results

- point_cluster: ref3=11.3377, learned=1.0151, gain=10.3227; line: ref3=5.0251, learned=0.7919, gain=4.2333; L-shape: ref3=5.3249, learned=0.7937, gain=4.5312

Family table:

- `family_metrics_mainline_vs_baselines.csv`

## 10. Failure-Mode Results

- F2: 66 -> 23; F3: 37 -> 1; F4: 29 -> 0

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

- Reached master-document target scale? `no`
- Frozen Mainline usable as formal mainline? `yes`
- Frozen Mainline closest traditional tier on the current curve: `BP`
- `Ready for physics-consistency stage?` = `conditional`

## 14. Suggested Next Task

`task_real_007`: add physics-consistency / echo-consistency on top of Frozen Mainline and quantify whether it moves the unified frontier further toward BP on the hardest families.

## Key file paths for ChatGPT controller

- Report: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006b_fullscale_mainline/20260417_000500/task_real_006b_report.md`
- Checkpoints: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006b_fullscale_mainline/20260417_000500/checkpoints`
- Metrics: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006b_fullscale_mainline/20260417_000500/metrics_frozen_mainline.json`
- Mainline vs baseline table: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006b_fullscale_mainline/20260417_000500/mainline_vs_baselines_table.csv`
- Family table: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006b_fullscale_mainline/20260417_000500/family_metrics_mainline_vs_baselines.csv`
- Failure-mode table: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006b_fullscale_mainline/20260417_000500/failure_mode_mainline_vs_baselines.csv`
- Curves: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006b_fullscale_mainline/20260417_000500/viz/curves`
- Representative visuals: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006b_fullscale_mainline/20260417_000500/viz/recon_compare` and `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006b_fullscale_mainline/20260417_000500/viz/slices`
- Logs: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006b_fullscale_mainline/20260417_000500/logs`
