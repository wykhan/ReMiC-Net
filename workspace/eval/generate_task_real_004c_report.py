from __future__ import annotations

import argparse
from pathlib import Path

from workspace.common.io_utils import read_json, write_text


def generate_report(output_root: Path) -> None:
    dataset_manifest = read_json(output_root / "dataset_manifest.json")
    baseline = read_json(output_root / "baseline_metrics_variantB.json")
    stability = read_json(output_root / "stability_metrics_variantB.json")
    agg = baseline["aggregate"]
    mono = {row["subset"]: row for row in stability["monotonicity_by_subset"]}
    all_viol = mono["all_samples"]["nmse_violation_count"]
    seam_viol = mono["seam_subset"]["nmse_violation_count"]
    nonseam_viol = mono["non_seam_subset"]["nmse_violation_count"]
    ready = "yes" if all_viol == 0 else "conditional"
    report = f"""# task_real_004c_report

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

- Dataset name: `{dataset_manifest['dataset_name']}`
- Total samples: `{dataset_manifest['total_samples']}`
- Groups:
  - `rho_sweep = {dataset_manifest['counts_by_group']['rho_sweep']}`
  - `azimuth_control = {dataset_manifest['counts_by_group']['azimuth_control']}`
  - `height_control = {dataset_manifest['counts_by_group']['height_control']}`
  - `double_point_control = {dataset_manifest['counts_by_group']['double_point_control']}`

## 6. Experiment Summary

- Built the broader controlled suite with true cylindrical forward echoes.
- Ran `ref3/ref5/ref7/ref9/BP` through the frozen default Variant B front-end.
- Generated runtime, quality, monotonicity, wrap-symmetry, gap-distribution, and radial-mismatch diagnostics.
- Rendered representative normal, seam-difficult, and small-radius cases.

## 7. Key Metrics

| Method | NMSE mean | PSNR mean | SSIM mean | Wall time mean (s) | Speedup vs BP |
| --- | ---: | ---: | ---: | ---: | ---: |
| ref3 | {agg['ref3']['nmse_mean']:.4f} | {agg['ref3']['psnr_mean']:.4f} | {agg['ref3']['ssim_mean']:.4f} | {agg['ref3']['wall_time_mean_sec']:.4f} | {agg['ref3']['speedup_vs_bp']:.4f} |
| ref5 | {agg['ref5']['nmse_mean']:.4f} | {agg['ref5']['psnr_mean']:.4f} | {agg['ref5']['ssim_mean']:.4f} | {agg['ref5']['wall_time_mean_sec']:.4f} | {agg['ref5']['speedup_vs_bp']:.4f} |
| ref7 | {agg['ref7']['nmse_mean']:.4f} | {agg['ref7']['psnr_mean']:.4f} | {agg['ref7']['ssim_mean']:.4f} | {agg['ref7']['wall_time_mean_sec']:.4f} | {agg['ref7']['speedup_vs_bp']:.4f} |
| ref9 | {agg['ref9']['nmse_mean']:.4f} | {agg['ref9']['psnr_mean']:.4f} | {agg['ref9']['ssim_mean']:.4f} | {agg['ref9']['wall_time_mean_sec']:.4f} | {agg['ref9']['speedup_vs_bp']:.4f} |
| BP | {agg['BP']['nmse_mean']:.4f} | {agg['BP']['psnr_mean']:.4f} | {agg['BP']['ssim_mean']:.4f} | {agg['BP']['wall_time_mean_sec']:.4f} | {agg['BP']['speedup_vs_bp']:.4f} |

## 8. Stability Analysis

- Overall `ref9` worse-than-`ref7` NMSE violations: `{all_viol}`
- Seam-subset violations: `{seam_viol}`
- Non-seam-subset violations: `{nonseam_viol}`
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
- `ref7/ref9` crossing still systemic? `{"yes" if nonseam_viol > 0 else "no"}`
- Current front-end sufficiently stable for shape-family ET? `{ready}`
- `Ready for ET?` = `{ready}`

## 12. Suggested Next Task

`task_real_005`: launch the shape-family ET main experiment using Variant B as the frozen traditional front-end.

## Key file paths for ChatGPT controller

- Report: `{output_root / 'task_real_004c_report.md'}`
- Metrics: `{output_root / 'baseline_metrics_variantB.json'}` and `{output_root / 'stability_metrics_variantB.json'}`
- Curves: `{output_root / 'viz/curves/runtime_vs_method_variantB.png'}` and `{output_root / 'viz/curves/ref7_ref9_gap_distribution.png'}`
- Representative visuals: `{output_root / 'viz/recon_compare/az_mid_center_zero_compare.png'}` and `{output_root / 'viz/slices/az_outer_negpi_p2_ref9_slices.png'}`
- Logs: `{output_root / 'logs/run_variantB_broader_point_suite.log'}`, `{output_root / 'logs/run_variantB_stability_analysis.log'}`, `{output_root / 'logs/render_variantB_confirmation_viz.log'}`
"""
    write_text(output_root / "task_real_004c_report.md", report)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate task_real_004c report.")
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()
    generate_report(Path(args.output_root))
    print("Generated task_real_004c report")


if __name__ == "__main__":
    main()
