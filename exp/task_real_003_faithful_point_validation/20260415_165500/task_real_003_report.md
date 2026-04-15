# task_real_003_report

## 1. Task Goal

Replace the previous point-scene analytic verifier with a more faithful echo-driven cylindrical reconstruction path, then establish controlled radial mismatch evidence before entering extended-target work.

## 2. Protocol / Context Files Used

- `CONTEXT/real_cylindrical_master_document_with_physics_consistency.md`
- `CONTEXT/simulation_protocol.md`
- `CONTEXT/reference_surface_strategy.md`
- `CONTEXT/dataset_protocol.md`
- `CONTEXT/project_brief.md`
- `CONTEXT/experiment_matrix.md`
- `PROMPTS/system_rules.md`
- `PROMPTS/review_checklist.md`

## 3. Boundary Statement

This task stayed inside point-target validation. It did not enter shape-family ET, Manisali-style ET, real echoes, physics consistency, or final paper-scale claims.

## 4. Implementation Summary

- Added `workspace.data.radial_control_dataset_builder` to create a controlled true-3D cylindrical point dataset with rho sweep, azimuth control, and height control
- Reused `workspace.sim.forward_cylindrical_point` for true cylindrical forward simulation
- Added `workspace.recon.faithful_cylindrical_fast_recon` and `workspace.recon.faithful_reference_recon`
- Main change vs `task_real_002`:
  - old path: point-scene analytic verifier using scene points directly plus deterministic visibility subsampling
  - new path: reconstruction starts from saved sparse echo tensors, builds dense active windows, applies height/azimuth FFT preprocessing, then performs echo-driven matched filtering on protocol-consistent local Cartesian ROIs
- The new implementation is more faithful to the protocol, but still not a production-grade accelerated FFT reference-surface engine

## 5. Dataset Summary

- Dataset name: `task_real_003_controlled_radial_point_set`
- Total samples: `46`
- Groups:
  - `rho_sweep = 31`
  - `azimuth_control = 9`
  - `height_control = 6`
- Proof of origin:
  - [dataset_manifest.json](/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_003_faithful_point_validation/20260415_165500/dataset_manifest.json:1)
  - [dataset_protocol_snapshot.md](/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_003_faithful_point_validation/20260415_165500/dataset_protocol_snapshot.md:1)
  - [data_origin_statement.md](/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_003_faithful_point_validation/20260415_165500/data_origin_statement.md:1)

## 6. Experiment Summary

- Ran true cylindrical forward simulation on all `46` controlled samples
- Ran faithful `ref3/ref5/ref7/ref9/BP` reconstruction on all samples
- Computed faithful metrics and wall time tables
- Computed `error vs rho_target` and `error vs radial mismatch`
- Rendered standardized scene, reconstruction, curve, and slice figures

## 7. Key Metrics

| Method | NMSE mean | PSNR mean | SSIM mean | Wall time mean (s) | Speedup vs BP |
| --- | ---: | ---: | ---: | ---: | ---: |
| ref3 | 37.4449 | 5.9577 | 0.0078 | 2.0467 | 0.9994 |
| ref5 | 23.5087 | 7.7892 | 0.0108 | 2.0374 | 1.0040 |
| ref7 | 16.8945 | 9.1972 | 0.0149 | 2.0128 | 1.0162 |
| ref9 | 15.4104 | 9.9319 | 0.0199 | 2.0263 | 1.0095 |
| BP | 5.7846 | 13.3836 | 0.0449 | 2.0455 | 1.0000 |

Observed quality trend is still correct: more reference surfaces improve quality and BP remains best.

Observed runtime trend is not yet sufficient for the final fast-imaging claim: wall time remains too similar across methods.

## 8. Visual Outputs

- Curves:
  - [runtime_vs_method.png](/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_003_faithful_point_validation/20260415_165500/viz/curves/runtime_vs_method.png:1)
  - [quality_vs_method.png](/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_003_faithful_point_validation/20260415_165500/viz/curves/quality_vs_method.png:1)
  - [nmse_vs_rho_target.png](/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_003_faithful_point_validation/20260415_165500/viz/curves/nmse_vs_rho_target.png:1)
  - [psnr_vs_rho_target.png](/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_003_faithful_point_validation/20260415_165500/viz/curves/psnr_vs_rho_target.png:1)
  - [ssim_vs_rho_target.png](/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_003_faithful_point_validation/20260415_165500/viz/curves/ssim_vs_rho_target.png:1)
  - [error_vs_radial_mismatch.png](/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_003_faithful_point_validation/20260415_165500/viz/curves/error_vs_radial_mismatch.png:1)
- Representative recon compare:
  - [rho_015_compare.png](/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_003_faithful_point_validation/20260415_165500/viz/recon_compare/rho_015_compare.png:1)
  - [rho_030_compare.png](/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_003_faithful_point_validation/20260415_165500/viz/recon_compare/rho_030_compare.png:1)
  - [az_outer_negpi_compare.png](/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_003_faithful_point_validation/20260415_165500/viz/recon_compare/az_outer_negpi_compare.png:1)
- Representative scene views:
  - [rho_015_gt_3d.png](/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_003_faithful_point_validation/20260415_165500/viz/scene_3d/rho_015_gt_3d.png:1)
  - [rho_015_gt_views.png](/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_003_faithful_point_validation/20260415_165500/viz/scene_3d/rho_015_gt_views.png:1)
- Representative slice/error view:
  - [rho_015_ref3_slices.png](/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_003_faithful_point_validation/20260415_165500/viz/slices/rho_015_ref3_slices.png:1)

## 9. Issues / Limitations

- The current faithful implementation is more protocol-faithful than `task_real_002`, but it is still not a fully accelerated fast cylindrical reference-surface implementation
- Runtime separation between `ref3/ref5/ref7/ref9/BP` is weak, so the speed story is not yet trustworthy enough for ET main experiments
- Metric scale is based on small local point-target ROIs; this is appropriate for controlled mismatch analysis but not yet the final paper front-end benchmark
- Current SSIM remains a repository-local global 3D statistic rather than a sliding-window implementation

## 10. Suggested Next Task

`task_real_004`: implement a more genuinely accelerated cylindrical reference-surface recon path with stronger wall-time separation from BP, then rerun controlled point validation before entering shape-family ET.

## Key file paths for ChatGPT controller

- Report:
  - [task_real_003_report.md](/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_003_faithful_point_validation/20260415_165500/task_real_003_report.md:1)
- Metrics:
  - [baseline_metrics_faithful.json](/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_003_faithful_point_validation/20260415_165500/baseline_metrics_faithful.json:1)
  - [radial_mismatch_metrics.json](/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_003_faithful_point_validation/20260415_165500/radial_mismatch_metrics.json:1)
  - [runtime_table_faithful.csv](/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_003_faithful_point_validation/20260415_165500/runtime_table_faithful.csv:1)
  - [quality_table_faithful.csv](/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_003_faithful_point_validation/20260415_165500/quality_table_faithful.csv:1)
- Curves:
  - [runtime_vs_method.png](/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_003_faithful_point_validation/20260415_165500/viz/curves/runtime_vs_method.png:1)
  - [error_vs_radial_mismatch.png](/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_003_faithful_point_validation/20260415_165500/viz/curves/error_vs_radial_mismatch.png:1)
- Representative visuals:
  - [rho_015_compare.png](/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_003_faithful_point_validation/20260415_165500/viz/recon_compare/rho_015_compare.png:1)
  - [rho_015_ref3_slices.png](/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_003_faithful_point_validation/20260415_165500/viz/slices/rho_015_ref3_slices.png:1)
- Logs:
  - [run_point_faithful_baselines.log](/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_003_faithful_point_validation/20260415_165500/logs/run_point_faithful_baselines.log:1)
  - [run_radial_mismatch_analysis.log](/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_003_faithful_point_validation/20260415_165500/logs/run_radial_mismatch_analysis.log:1)
  - [render_point_viz.log](/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_003_faithful_point_validation/20260415_165500/logs/render_point_viz.log:1)
