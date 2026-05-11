# task_real_004b_report

## 1. Task Goal

Harden the accelerated cylindrical reference-surface front-end before ET by stress-testing seam behavior, comparing active-window and dense-global tensor modes, comparing linear and MATLAB-inspired sinc geometry correction, and making an explicit default-engine decision.

## 2. Protocol / Context Files Used

- `CONTEXT/real_cylindrical_master_document_with_physics_consistency.md`
- `CONTEXT/simulation_protocol.md`
- `CONTEXT/reference_surface_strategy.md`
- `CONTEXT/dataset_protocol.md`
- `CONTEXT/project_brief.md`
- `CONTEXT/experiment_matrix.md`
- `PROMPTS/system_rules.md`
- `PROMPTS/review_checklist.md`
- `exp/task_real_004_accelerated_point_validation/20260415_190000/task_real_004_report.md`
- `doc/task_real_004_algorithm_audit.md`
- `doc/matlab_to_python_mapping.md`

## 3. Boundary Statement

This task stayed inside pre-ET hardening. It did not enter shape-family ET, real echoes, physics consistency, or protocol-v2 work.

## 4. Implementation Summary

- Added `workspace.data.azimuth_edge_stress_builder` for a seam-focused true cylindrical stress set.
- Upgraded `workspace.recon.cyl_fast_reference_engine` to support:
  - `tensor_mode = active | dense_global`
  - `geom_mode = linear | sinc`
- Added `workspace.recon.geometry_correction` with:
  - direct linear correction
  - MATLAB-inspired full-library sinc-stencil correction
- Added wrap ablation, stability analysis, visualization, and report-generation modules.

## 5. Stress Dataset Summary

- Dataset name: `task_real_004b_azimuth_edge_stress_set`
- Total samples: `6`
- Radius groups: inner / mid / outer
- Height groups: mid / high / low
- Seam offsets: `-pi`, `-pi+du`, `-pi+2du`, `pi-2du`, `pi-du`, `pi`

## 6. A/B/C/D Variant Definition

- `A`: active windows + linear geometry correction
- `B`: active windows + full-library sinc geometry correction
- `C`: dense global tensor + linear geometry correction
- `D`: dense global tensor + full-library sinc geometry correction

## 7. Key Metrics

- Monotonicity violations (`ref9` worse than `ref7` on NMSE):
  - `A`: 2 / 6
  - `B`: 1 / 6
  - `C`: 4 / 6
  - `D`: 4 / 6
- Edge-subset `ref9` NMSE:
  - `A`: 14.2090
  - `B`: 10.5699
  - `C`: 52.9643
  - `D`: 49.5695
- `ref9` runtime / estimated peak memory:
  - `A`: 0.3868 s / 15.36 MB
  - `B`: 0.3772 s / 16.63 MB
  - `C`: 44.5347 s / 1561.31 MB
  - `D`: 48.5992 s / 1691.77 MB

## 8. Visual Outputs

- `viz/curves/monotonicity_violations_by_variant.png`
- `viz/curves/wrap_symmetry_error_by_variant.png`
- `viz/curves/edge_nmse_by_variant.png`
- `viz/curves/edge_psnr_by_variant.png`
- `viz/curves/runtime_by_variant.png`
- `viz/curves/memory_by_variant.png`
- `viz/curves/error_vs_radial_mismatch_edge_subset.png`
- representative compare figures under `viz/recon_compare/`
- representative slice / difference figures under `viz/slices/`

## 9. Root Cause Analysis

- Primary root cause: `geometry correction`.
- Decision logic: `geometry correction dominates if switching A->B reduces violations more than A->C; dense global is only default-worthy if it adds clear stability gains over B.`
- In practice the decisive evidence is whether geometry-only improvement (`A->B`) or tensor-only improvement (`A->C`) removes more `ref7/ref9` violations and symmetry asymmetry.

## 10. Engineering Decision

- Default accelerated engine: `B` = active windows + full-library sinc geometry correction.
- Dense global mode: keep as `audit mode`, not default, unless it clearly outperforms the chosen active-window variant on stability without unacceptable runtime cost.
- Geometry correction: promote sinc correction to default only if the chosen best variant is `B` or `D`.

## 11. Issues / Limitations

- The sinc correction is MATLAB-inspired, but still uses a linear expansion to the full radial library before the final local stencil.
- Memory reporting is an estimated peak based on dominant tensor allocations, not an OS-traced absolute peak RSS.
- The stress set is intentionally seam-focused and should not replace the broader controlled point validation suite.

## 12. Ready for ET?

- `ref7/ref9` crossing primary cause: `geometry correction`
- full-library sinc stencil worth defaulting? `yes`
- dense global tensor worth defaulting? `no`
- front-end publication-stable? `conditional`
- ready for shape-family ET? `conditional`

## 13. Suggested Next Task

Freeze the chosen default front-end configuration, rerun the broader controlled point suite once with that configuration, then start shape-family ET on the hardened baseline.

## Key file paths for ChatGPT controller

- Report: `../exp/task_real_004b_wrap_hardening/20260415_210500/task_real_004b_report.md`
- Metrics: `../exp/task_real_004b_wrap_hardening/20260415_210500/wrap_stability_metrics.json`
- Runtime / memory: `../exp/task_real_004b_wrap_hardening/20260415_210500/runtime_memory_by_variant.csv`
- Curves: `../exp/task_real_004b_wrap_hardening/20260415_210500/viz/curves/runtime_by_variant.png` and `../exp/task_real_004b_wrap_hardening/20260415_210500/viz/curves/wrap_symmetry_error_by_variant.png`
- Representative visuals: `../exp/task_real_004b_wrap_hardening/20260415_210500/viz/recon_compare/inner_mid_negpi_exact_ref9_variant_compare.png` and `../exp/task_real_004b_wrap_hardening/20260415_210500/viz/slices/mid_high_negpi_p1_ref9_variant_slices.png`
- Logs: `../exp/task_real_004b_wrap_hardening/20260415_210500/logs/run_azimuth_edge_stress_set.log`, `../exp/task_real_004b_wrap_hardening/20260415_210500/logs/run_wrap_ablation_variants.log`, `../exp/task_real_004b_wrap_hardening/20260415_210500/logs/run_wrap_stability_analysis.log`, `../exp/task_real_004b_wrap_hardening/20260415_210500/logs/render_wrap_viz.log`
