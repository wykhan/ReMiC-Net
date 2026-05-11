from __future__ import annotations

import argparse
from pathlib import Path

from workspace.common.io_utils import read_json, write_text


VARIANT_LABELS = {
    "A": "active windows + linear geometry correction",
    "B": "active windows + full-library sinc geometry correction",
    "C": "dense global tensor + linear geometry correction",
    "D": "dense global tensor + full-library sinc geometry correction",
}


def _best_variant(metrics: dict) -> tuple[str, str]:
    monotonicity = {row["variant"]: row["nmse_violation_count"] for row in metrics["monotonicity"]}
    edge_nmse = {variant: metrics["edge_metrics"][variant]["ref9"]["nmse_mean"] for variant in metrics["edge_metrics"]}
    runtime = read_json(Path(metrics["_output_root"]) / "wrap_variant_metrics.json")["aggregate"]
    scores = []
    for variant in VARIANT_LABELS:
        scores.append((monotonicity[variant], edge_nmse[variant], runtime[variant]["ref9"]["wall_time_mean_sec"], variant))
    best = sorted(scores)[0][-1]
    rationale = (
        "geometry correction dominates if switching A->B reduces violations more than A->C; "
        "dense global is only default-worthy if it adds clear stability gains over B."
    )
    return best, rationale


def generate_report(output_root: Path) -> None:
    wrap_metrics = read_json(output_root / "wrap_stability_metrics.json")
    wrap_metrics["_output_root"] = str(output_root)
    variant_metrics = read_json(output_root / "wrap_variant_metrics.json")
    dataset_manifest = read_json(output_root / "dataset_manifest.json")
    runtime_rows = variant_metrics["aggregate"]
    monotonicity = {row["variant"]: row for row in wrap_metrics["monotonicity"]}
    best_variant, rationale = _best_variant(wrap_metrics)
    root_cause = "joint"
    if monotonicity["B"]["nmse_violation_count"] < monotonicity["C"]["nmse_violation_count"]:
        root_cause = "geometry correction"
    elif monotonicity["C"]["nmse_violation_count"] < monotonicity["B"]["nmse_violation_count"]:
        root_cause = "tensor mode"

    dense_note = "\n".join(
        [
            "# dense_global_mode_notes",
            "",
            "- Dense global mode keeps the full protocol tensor shape `1101 x 181 x 501`.",
            "- It is intended for strict MATLAB / audit mode and wrap-hardening comparisons.",
            f"- Variant C ref9 mean runtime: {runtime_rows['C']['ref9']['wall_time_mean_sec']:.4f} s",
            f"- Variant D ref9 mean runtime: {runtime_rows['D']['ref9']['wall_time_mean_sec']:.4f} s",
        ]
    )
    write_text(output_root / "dense_global_mode_notes.md", dense_note)

    report = f"""# task_real_004b_report

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
- Total samples: `{dataset_manifest['total_samples']}`
- Radius groups: inner / mid / outer
- Height groups: mid / high / low
- Seam offsets: `-pi`, `-pi+du`, `-pi+2du`, `pi-2du`, `pi-du`, `pi`

## 6. A/B/C/D Variant Definition

- `A`: {VARIANT_LABELS['A']}
- `B`: {VARIANT_LABELS['B']}
- `C`: {VARIANT_LABELS['C']}
- `D`: {VARIANT_LABELS['D']}

## 7. Key Metrics

- Monotonicity violations (`ref9` worse than `ref7` on NMSE):
  - `A`: {monotonicity['A']['nmse_violation_count']} / {monotonicity['A']['total_samples']}
  - `B`: {monotonicity['B']['nmse_violation_count']} / {monotonicity['B']['total_samples']}
  - `C`: {monotonicity['C']['nmse_violation_count']} / {monotonicity['C']['total_samples']}
  - `D`: {monotonicity['D']['nmse_violation_count']} / {monotonicity['D']['total_samples']}
- Edge-subset `ref9` NMSE:
  - `A`: {wrap_metrics['edge_metrics']['A']['ref9']['nmse_mean']:.4f}
  - `B`: {wrap_metrics['edge_metrics']['B']['ref9']['nmse_mean']:.4f}
  - `C`: {wrap_metrics['edge_metrics']['C']['ref9']['nmse_mean']:.4f}
  - `D`: {wrap_metrics['edge_metrics']['D']['ref9']['nmse_mean']:.4f}
- `ref9` runtime / estimated peak memory:
  - `A`: {runtime_rows['A']['ref9']['wall_time_mean_sec']:.4f} s / {runtime_rows['A']['ref9']['estimated_peak_memory_mb']:.2f} MB
  - `B`: {runtime_rows['B']['ref9']['wall_time_mean_sec']:.4f} s / {runtime_rows['B']['ref9']['estimated_peak_memory_mb']:.2f} MB
  - `C`: {runtime_rows['C']['ref9']['wall_time_mean_sec']:.4f} s / {runtime_rows['C']['ref9']['estimated_peak_memory_mb']:.2f} MB
  - `D`: {runtime_rows['D']['ref9']['wall_time_mean_sec']:.4f} s / {runtime_rows['D']['ref9']['estimated_peak_memory_mb']:.2f} MB

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

- Primary root cause: `{root_cause}`.
- Decision logic: `{rationale}`
- In practice the decisive evidence is whether geometry-only improvement (`A->B`) or tensor-only improvement (`A->C`) removes more `ref7/ref9` violations and symmetry asymmetry.

## 10. Engineering Decision

- Default accelerated engine: `{best_variant}` = {VARIANT_LABELS[best_variant]}.
- Dense global mode: keep as `audit mode`, not default, unless it clearly outperforms the chosen active-window variant on stability without unacceptable runtime cost.
- Geometry correction: promote sinc correction to default only if the chosen best variant is `B` or `D`.

## 11. Issues / Limitations

- The sinc correction is MATLAB-inspired, but still uses a linear expansion to the full radial library before the final local stencil.
- Memory reporting is an estimated peak based on dominant tensor allocations, not an OS-traced absolute peak RSS.
- The stress set is intentionally seam-focused and should not replace the broader controlled point validation suite.

## 12. Ready for ET?

- `ref7/ref9` crossing primary cause: `{root_cause}`
- full-library sinc stencil worth defaulting? `{"yes" if best_variant in {"B","D"} else "no"}`
- dense global tensor worth defaulting? `{"yes" if best_variant in {"C","D"} else "no"}`
- front-end publication-stable? `{"yes" if monotonicity[best_variant]["nmse_violation_count"] == 0 else "conditional"}`
- ready for shape-family ET? `{"yes" if monotonicity[best_variant]["nmse_violation_count"] == 0 else "conditional"}`

## 13. Suggested Next Task

Freeze the chosen default front-end configuration, rerun the broader controlled point suite once with that configuration, then start shape-family ET on the hardened baseline.

## Key file paths for ChatGPT controller

- Report: `{output_root / 'task_real_004b_report.md'}`
- Metrics: `{output_root / 'wrap_stability_metrics.json'}`
- Runtime / memory: `{output_root / 'runtime_memory_by_variant.csv'}`
- Curves: `{output_root / 'viz/curves/runtime_by_variant.png'}` and `{output_root / 'viz/curves/wrap_symmetry_error_by_variant.png'}`
- Representative visuals: `{output_root / 'viz/recon_compare/inner_mid_negpi_exact_ref9_variant_compare.png'}` and `{output_root / 'viz/slices/mid_high_negpi_p1_ref9_variant_slices.png'}`
- Logs: `{output_root / 'logs/run_azimuth_edge_stress_set.log'}`, `{output_root / 'logs/run_wrap_ablation_variants.log'}`, `{output_root / 'logs/run_wrap_stability_analysis.log'}`, `{output_root / 'logs/render_wrap_viz.log'}`
"""
    write_text(output_root / "task_real_004b_report.md", report)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate task_real_004b report.")
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()
    generate_report(Path(args.output_root))
    print("Generated task_real_004b report")


if __name__ == "__main__":
    main()
