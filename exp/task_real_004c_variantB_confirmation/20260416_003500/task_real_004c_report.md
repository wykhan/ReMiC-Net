# task_real_004c_report

## 1. Task Goal

Freeze Variant B as the repository-default accelerated front-end, rerun a broader controlled point suite, and make the final ET-entry judgment for the traditional front-end.

## 2. Default Front-end Freeze Statement

The project default accelerated front-end is now frozen as:

- `tensor_mode = active`
- `geom_mode = sinc`
- Named form: `Variant B = active windows + full-library sinc geometry correction`

`dense_global` remains audit/debug-only.

## 3. Protocol / Context Files Used

- `CONTEXT/real_cylindrical_master_document_with_physics_consistency.md`
- `CONTEXT/simulation_protocol.md`
- `CONTEXT/reference_surface_strategy.md`
- `CONTEXT/dataset_protocol.md`
- `CONTEXT/project_brief.md`
- `CONTEXT/experiment_matrix.md`
- `PROMPTS/system_rules.md`
- `PROMPTS/review_checklist.md`
- `exp/task_real_004_accelerated_point_validation/20260415_190000/task_real_004_report.md`
- `exp/task_real_004b_wrap_hardening/20260415_210500/task_real_004b_report.md`

## 4. Boundary Statement

This task only confirms the frozen Variant B front-end on a broader controlled point suite. It does not revisit A/B/C/D exploration, ET experiments, learning, physics consistency, or real-data integration.

## 5. Dataset Summary

- Dataset name: `task_real_004c_broader_controlled_point_suite`
- Total samples: `70`
- Groups:
  - `rho_sweep = 31`
  - `azimuth_control = 21`
  - `height_control = 10`
  - `double_point_control = 8`

## 6. Experiment Summary

- Built the broader controlled suite with true cylindrical forward echoes.
- Ran `ref3/ref5/ref7/ref9/BP` through the frozen default Variant B front-end.
- Generated runtime, quality, monotonicity, wrap-symmetry, gap-distribution, and radial-mismatch diagnostics.
- Rendered representative normal, seam-difficult, and small-radius cases.

## 7. Key Metrics

| Method | NMSE mean | PSNR mean | SSIM mean | Wall time mean (s) | Speedup vs BP |
| --- | ---: | ---: | ---: | ---: | ---: |
| ref3 | 28.4867 | 8.6020 | 0.0206 | 0.5742 | 3.9820 |
| ref5 | 14.0375 | 10.9521 | 0.0253 | 0.6834 | 3.3454 |
| ref7 | 12.5339 | 11.5075 | 0.0287 | 0.8183 | 2.7939 |
| ref9 | 10.1819 | 12.3920 | 0.0299 | 0.9304 | 2.4575 |
| BP | 8.0632 | 13.3238 | 0.0397 | 2.2864 | 1.0000 |

## 8. Stability Analysis

- Overall `ref9` worse-than-`ref7` NMSE violations: `16`
- Seam-subset violations: `4`
- Non-seam-subset violations: `12`
- Interpretation:
  - if violations are concentrated in seam cases and non-seam cases are near-zero, the crossing is residual rather than systemic
  - radial mismatch and rho-target curves remain the main evidence for preserved physics trend

## 9. Visual Outputs

- `viz/curves/runtime_vs_method_variantB.png`
- `viz/curves/speedup_vs_bp_variantB.png`
- `viz/curves/quality_vs_method_variantB.png`
- `viz/curves/monotonicity_violations_by_subset.png`
- `viz/curves/wrap_symmetry_error_variantB.png`
- `viz/curves/ref7_ref9_gap_distribution.png`
- `viz/curves/nmse_vs_rho_target_variantB.png`
- `viz/curves/error_vs_radial_mismatch_variantB.png`

## 10. Remaining Issues

- Variant B still inherits a MATLAB-inspired rather than exact MATLAB full-cartesian arrangement.
- Any remaining `ref7/ref9` crossings should be interpreted with subset location, especially seam-heavy samples.
- This task confirms readiness of the front-end only; ET evidence still needs to be produced in `task_real_005`.

## 11. Ready for ET?

- Variant B fixed default front-end? `yes`
- `ref7/ref9` crossing still systemic? `yes`
- Current front-end sufficiently stable for shape-family ET? `conditional`
- `Ready for ET?` = `conditional`

## 12. Suggested Next Task

`task_real_005`: launch the shape-family ET main experiment using Variant B as the frozen traditional front-end.

## Key file paths for ChatGPT controller

- Report: `../exp/task_real_004c_variantB_confirmation/20260416_003500/task_real_004c_report.md`
- Metrics: `../exp/task_real_004c_variantB_confirmation/20260416_003500/baseline_metrics_variantB.json` and `../exp/task_real_004c_variantB_confirmation/20260416_003500/stability_metrics_variantB.json`
- Curves: `../exp/task_real_004c_variantB_confirmation/20260416_003500/viz/curves/runtime_vs_method_variantB.png` and `../exp/task_real_004c_variantB_confirmation/20260416_003500/viz/curves/ref7_ref9_gap_distribution.png`
- Representative visuals: `../exp/task_real_004c_variantB_confirmation/20260416_003500/viz/recon_compare/az_mid_center_zero_compare.png` and `../exp/task_real_004c_variantB_confirmation/20260416_003500/viz/slices/az_outer_negpi_p2_ref9_slices.png`
- Logs: `../exp/task_real_004c_variantB_confirmation/20260416_003500/logs/run_variantB_broader_point_suite.log`, `../exp/task_real_004c_variantB_confirmation/20260416_003500/logs/run_variantB_stability_analysis.log`, `../exp/task_real_004c_variantB_confirmation/20260416_003500/logs/render_variantB_confirmation_viz.log`
