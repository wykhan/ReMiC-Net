# point_chain_report

## Task Goal

`task_real_002` validates the point-target physical chain under protocol v1:

`scene -> echo -> ref3/ref5/ref7/ref9/BP -> eval -> minimal learning smoke`

The task is a Phase 1 validation pass, not an extended-target main experiment and not a final paper result.

## Protocol Files Used

- `CONTEXT/real_cylindrical_master_document_with_physics_consistency.md`
- `CONTEXT/simulation_protocol.md`
- `CONTEXT/reference_surface_strategy.md`
- `CONTEXT/project_brief.md`
- `CONTEXT/experiment_matrix.md`
- `CONTEXT/dataset_protocol.md`
- `PROMPTS/system_rules.md`
- `PROMPTS/review_checklist.md`

## Point-Target Dataset Protocol Summary

- dataset mode executed here: `smoke`
- split sizes: `train=64`, `val=16`, `test=16`
- total generated samples: `96`
- scene types: single-point, double-point, and `3-5` point sparse scenes
- scatter rule: amplitude sampled from `[0.8, 1.2]`, phase fixed to zero
- GT definition: voxel-space amplitude volume on protocol-consistent local ROI grids

## Scene / Echo / Recon / Eval Chain

- Scene generator writes per-sample metadata with split, seed, point count, positions, amplitudes, and voxel indices
- Forward simulator follows protocol-v1 geometry and visibility rules, then writes sparse echo bundles plus echo metadata
- Traditional reconstruction entry points cover `ref3`, `ref5`, `ref7`, `ref9`, and `BP`
- Baseline evaluation reports magnitude NMSE, PSNR, SSIM, wall time, and runtime proxy
- Learning smoke uses `ref3` magnitude volumes as input and GT amplitude volumes as labels for a minimal 3D U-Net

## Baseline Result Summary

Evaluation was run on `8` smoke test samples to validate trends.

| Method | NMSE mean | PSNR mean | SSIM mean | Speedup vs BP |
| --- | ---: | ---: | ---: | ---: |
| ref3 | 138.8653 | 21.1746 | 0.0178 | 9.2746 |
| ref5 | 31.5337 | 24.9392 | 0.0644 | 6.1405 |
| ref7 | 28.4991 | 26.6603 | 0.1065 | 4.4503 |
| ref9 | 16.8751 | 27.4569 | 0.1288 | 3.4686 |
| BP | 8.2301 | 29.9514 | 0.2388 | 1.0000 |

Observed trend matches the expected physical direction: more reference surfaces improve quality while reducing speedup relative to BP.

## Learning Smoke Result Summary

- train loss: `0.0537 -> 0.0405 -> 0.0303`
- val loss: `0.0465 -> 0.0331 -> 0.0253`
- smoke conclusion: `RED_ref3 -> 3D U-Net -> GT amplitude` is trainable at minimal scale and improves over the initial coarse input on the saved sample visualization

## Issues Found

- The current smoke reconstructor is an analytic point-scene verifier and uses deterministic visibility subsampling during matched-filter accumulation for tractable runtime
- Runtime tables therefore include a reference-count proxy in addition to measured wall time
- SSIM is currently a repository-local global 3D implementation rather than a sliding-window external implementation

## Boundary Statement

This task did not enter shape-family ET experiments, Manisali-style random ET generation, physics consistency, real data ingestion, or final paper-scale ablations.

## Suggested Next Task

`task_real_003`: replace the smoke-time analytic reconstructor with a more faithful fast cylindrical reconstruction implementation, then expand point-target controlled validation and radial-mismatch analysis before moving into ET experiments.
