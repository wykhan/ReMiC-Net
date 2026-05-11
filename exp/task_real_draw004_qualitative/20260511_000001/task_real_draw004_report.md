# task_real_draw004 report

## Task objective

Generate an overall 3D qualitative imaging figure for a Manisali-inspired volumetric Y target, using GT, ref3, ref9, BP, and the ordinary residual U-Net baseline.

## Context files used

- `CONTEXT/manisali_inspired_target_protocol.md`
- `CONTEXT/remic_net_effect_figure_design_recommendations.md`
- `CONTEXT/visualization_protocol.md`

## Target design

- Target family: compact finite-thickness structured Y, inspired by the Manisali-style overall 3D imaging protocol rather than reproducing an external object.
- Point count after grid deduplication: `188`.
- rho range: `0.1743` to `0.2306` m.
- z range: `-0.0266` to `0.0379` m.
- theta span: `6.44` deg.
- Mean / max distance to nearest ref3 radius: `0.0544` / `0.0749` m.
- Scatter model: mild magnitude variation M1, phase P0.

## Draw003 issue avoided

- Raw GT patch shape: `[16, 10, 21]`.
- U-Net/display target shape: `[24, 24, 24]`.
- Raw GT nonzero voxels: `188`.
- Fitted GT nonzero voxels: `188`.
- Support lost during 24^3 fitting: `0`.
- Fits 24^3 without crop: `True`.

## Outputs

- Main 3x5 composite: `exp/task_real_draw004_qualitative/20260511_000001/viz/paper_candidates/qualitative/manisali_y_3x5.png`
- Individual 3D renders: `exp/task_real_draw004_qualitative/20260511_000001/viz/paper_candidates/qualitative/single_3d`
- Individual MIP panels: `exp/task_real_draw004_qualitative/20260511_000001/viz/paper_candidates/qualitative/single_mip`
- Progress copy: `exp/task_real_draw004_qualitative/20260511_000001/viz/progress/manisali_y_3x5.png`

## Visualization policy

- All methods use the same 24^3 display grid, the same GT-peak normalization, the same log10(1 + A) MIP display, and the same 3D support threshold `0.035`.
- The ordinary U-Net panel is the final compensated reconstruction from the task_real_008 residual U-Net baseline, not ReMiC-Net / RSB-FiLM.

## Metrics side check

| Target | Method | NMSE | PSNR | SSIM | peak | support voxels |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| manisali_y | ref3 | 2.1732 | 16.2366 | 0.1026 | 0.9615 | 3253 |
| manisali_y | ref9 | 1.0978 | 19.2022 | 0.2840 | 0.9615 | 2400 |
| manisali_y | BP | 0.7195 | 21.0370 | 0.4730 | 0.9615 | 1540 |
| manisali_y | U-Net | 0.9740 | 19.7217 | 0.0711 | 0.0766 | 190 |

## Interpretation

This figure is intended as an overall 3D qualitative visualization rather than a radial-mismatch diagnostic. The compact target keeps the bifurcation and both branches visible while staying within the 24^3 display volume without support loss, so the comparison is more suitable than draw003 for reader-facing overall imaging.
