# task_real_004_report

## 1. Task Goal

Implement a protocol-v1 accelerated cylindrical reference-surface reconstruction engine aligned to the Tan MATLAB prototype, then rerun controlled true-3D cylindrical point validation with wall-time, quality, and radial-mismatch evidence.

## 2. Protocol / Context Files Used

- `CONTEXT/real_cylindrical_master_document_with_physics_consistency.md`
- `CONTEXT/simulation_protocol.md`
- `CONTEXT/reference_surface_strategy.md`
- `CONTEXT/dataset_protocol.md`
- `CONTEXT/project_brief.md`
- `CONTEXT/experiment_matrix.md`
- `PROMPTS/system_rules.md`
- `PROMPTS/review_checklist.md`
- `exp/task_real_003_faithful_point_validation/20260415_165500/task_real_003_report.md`

## 3. Boundary Statement

This task stayed inside controlled point-target validation. It did not enter shape-family ET, Manisali-style ET, real echoes, physics consistency, or protocol-v2 work.

## 4. Implementation Summary

- Added `workspace.recon.cyl_fast_reference_engine` as the new accelerated main path.
- The new engine follows the MATLAB ordering: height FFT -> azimuth FFT -> reference-surface matching in transformed space -> height inverse FFT -> cylindrical-to-Cartesian geometry correction.
- `ref3/ref5/ref7/ref9/BP` now share one engine and differ only by the reference-surface library size.
- Added accelerated evaluation, radial-mismatch analysis, visualization, and task scripts.

## 5. MATLAB Audit Summary

- MATLAB executable used: `~/software/MATLAB_R2018b/bin/matlab`
- Source audited: `reference_plane_matlab_Tan/points_4_202406.m` with helper files `ftx.m`, `fty.m`, `iftx.m`, `ifty.m`
- Ran `scripts/run_matlab_reference_plane_audit.sh`, which executed a synthetic single-point replay of the MATLAB fast chain and wrote `matlab_engine_notes.md`
- Audit outputs:
  - `doc/task_real_004_algorithm_audit.md`
  - `doc/matlab_to_python_mapping.md`
  - `matlab_engine_notes.md`

## 6. Dataset Summary

- Dataset name: `task_real_004_controlled_accelerated_point_set`
- Total samples: `46`
- Groups:
  - `rho_sweep = 31`
  - `azimuth_control = 9`
  - `height_control = 6`
- Proof of origin:
  - `dataset_manifest.json`
  - `dataset_protocol_snapshot.md`
  - `data_origin_statement.md`

## 7. Experiment Summary

- Rebuilt the controlled dataset and true cylindrical sparse echoes.
- Ran accelerated `ref3/ref5/ref7/ref9/BP` reconstruction on all `46` samples.
- Measured three runtime repeats per sample and aggregated mean/std/median wall time.
- Generated runtime, speedup, quality, and radial-mismatch curves.
- Rendered standardized GT scene views, method comparisons, and slice/error figures.

## 8. Key Metrics

| Method | Ref count | NMSE mean | PSNR mean | SSIM mean | Wall time mean (s) | Speedup vs BP |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ref3 | 3 | 33.2641 | 6.3925 | 0.0039 | 0.1401 | 8.2348 |
| ref5 | 5 | 18.6611 | 8.7006 | 0.0069 | 0.2085 | 5.5360 |
| ref7 | 7 | 15.5008 | 9.4746 | 0.0082 | 0.2818 | 4.0951 |
| ref9 | 9 | 15.9071 | 9.7849 | 0.0096 | 0.3507 | 3.2910 |
| BP | 31 | 9.7924 | 12.0033 | 0.0223 | 1.1540 | 1.0000 |

Observed runtime ordering is clean: `ref3 < ref5 < ref7 < ref9 < BP`.

Observed quality trend is preserved on `rho_sweep` and `height_control`, and BP remains best overall. A small non-monotonic crossover between `ref7` and `ref9` remains on some azimuth-edge controls near the wrap boundary.

## 9. Visual Outputs

- `viz/curves/runtime_vs_method_accelerated.png`
- `viz/curves/speedup_vs_bp_accelerated.png`
- `viz/curves/nmse_vs_rho_target_accelerated.png`
- `viz/curves/error_vs_radial_mismatch_accelerated.png`
- `viz/recon_compare/rho_015_compare.png`
- `viz/recon_compare/az_outer_negpi_compare.png`
- `viz/scene_3d/rho_015_gt_3d.png`
- `viz/scene_3d/z_outer_high_gt_views.png`
- `viz/slices/rho_015_ref3_slices.png`
- `viz/slices/az_outer_negpi_BP_slices.png`

## 10. Issues / Limitations

- The accelerated engine is now genuine in the sense that wall time scales directly with the reference-library size, but the current Python port still uses local active azimuth-height windows rather than dense global `1101 x 501` tensors.
- `ref9` is not strictly better than `ref7` on every azimuth-edge control sample; the remaining instability is concentrated near angle wrap cases.
- Geometry correction uses linear interpolation over reduced reference sets instead of the original MATLAB full-library sinc stencil.

## 11. Ready for ET?

- `Current accelerated engine truly fast?` Yes. The wall-time gradient is strong and consistent, with `ref3` about `8.23x` faster than BP.
- `Can the speed-quality story serve as the ET front-end skeleton?` Yes, for the main speed story and controlled radial-mismatch evidence.
- `Is `reference_surface_strategy_v1` still weak at small radius?` Yes. The `rho_sweep` and radial-mismatch curves still show stronger error sensitivity around mismatch-heavy settings.
- `Should shape-family ET start immediately?` Conditionally yes. The front-end is now usable, but the azimuth-edge `ref7/ref9` crossover should be cleaned before treating the trend as fully publication-stable.

## 12. Suggested Next Task

Stabilize the azimuth-wrap edge cases in the accelerated geometry-correction path, then launch shape-family ET with the current accelerated engine as the fixed traditional baseline.

## Key file paths for ChatGPT controller

- Report: `../exp/task_real_004_accelerated_point_validation/20260415_190000/task_real_004_report.md`
- Metrics: `../exp/task_real_004_accelerated_point_validation/20260415_190000/baseline_metrics_accelerated.json`
- Runtime table: `../exp/task_real_004_accelerated_point_validation/20260415_190000/runtime_table_accelerated.csv`
- Radial mismatch metrics: `../exp/task_real_004_accelerated_point_validation/20260415_190000/radial_mismatch_metrics_accelerated.json`
- Curves: `../exp/task_real_004_accelerated_point_validation/20260415_190000/viz/curves/runtime_vs_method_accelerated.png` and `../exp/task_real_004_accelerated_point_validation/20260415_190000/viz/curves/error_vs_radial_mismatch_accelerated.png`
- Representative visuals: `../exp/task_real_004_accelerated_point_validation/20260415_190000/viz/recon_compare/rho_015_compare.png` and `../exp/task_real_004_accelerated_point_validation/20260415_190000/viz/slices/az_outer_negpi_BP_slices.png`
- Logs: `../exp/task_real_004_accelerated_point_validation/20260415_190000/logs/run_point_accelerated_baselines.log`, `../exp/task_real_004_accelerated_point_validation/20260415_190000/logs/run_accelerated_radial_mismatch_analysis.log`, `../exp/task_real_004_accelerated_point_validation/20260415_190000/logs/render_point_viz_accelerated.log`, `../exp/task_real_004_accelerated_point_validation/20260415_190000/logs/run_matlab_reference_plane_audit.log`
- MATLAB audit config/output: `../scripts/run_matlab_reference_plane_audit.sh`, `../exp/task_real_004_accelerated_point_validation/20260415_190000/matlab_engine_notes.md`
