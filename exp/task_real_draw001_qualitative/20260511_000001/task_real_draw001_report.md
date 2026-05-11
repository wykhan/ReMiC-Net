# task_real_draw001 report

## Outputs

- Primary 3x4 composite: `exp/task_real_draw001_qualitative/20260511_000001/viz/paper_candidates/qualitative/qualitative_comparison_3x4.png`
- GT auxiliary composite: `exp/task_real_draw001_qualitative/20260511_000001/viz/paper_candidates/qualitative/qualitative_comparison_3x5_with_gt.png`
- Single panels: `exp/task_real_draw001_qualitative/20260511_000001/viz/paper_candidates/qualitative/single_images`
- Manifest: `exp/task_real_draw001_qualitative/20260511_000001/draw001_manifest.json`

## Method scope

- `U-Net` is the ordinary residual 3D U-Net baseline from task_real_008.
- It is not the RSB-FiLM/ReMiC-Net branch.
- Panels use rho-z max-over-theta projections to retain the radial reference-surface dimension.
- Each target row uses one shared GT-peak color scale across ref3/ref9/BP/U-Net.
- Rendering uses `log10(1 + A)` after shared per-row normalization to keep the point-target dynamic range inspectable.

## Projection side check

| Target | Method | peak rho (m) | peak z (m) | peak value |
| --- | --- | ---: | ---: | ---: |
| point | ref3 | 0.1609 | 0.1880 | 5994 |
| point | ref9 | 0.2109 | 0.1880 | 9675 |
| point | BP | 0.2047 | 0.1880 | 1.066e+04 |
| point | U-Net | 0.1484 | 0.1880 | 3.06e+05 |
| y | ref3 | 0.2391 | 0.0525 | 1 |
| y | ref9 | 0.2203 | 0.1694 | 0.9941 |
| y | BP | 0.2266 | 0.1110 | 0.9183 |
| y | U-Net | 0.2391 | 0.1840 | 0.1999 |
| random_ext | ref3 | 0.2484 | -0.1560 | 0.8037 |
| random_ext | ref9 | 0.1953 | 0.1348 | 0.9171 |
| random_ext | BP | 0.2047 | 0.1348 | 0.9171 |
| random_ext | U-Net | 0.2484 | -0.1560 | 0.4039 |

## Scientific interpretation

This first-round figure family is useful as a qualitative screening tool because the rho-z display keeps the radial mismatch axis visible while still fitting the requested 3x4 multi-method layout.

The two-point row is the most direct diagnostic for reference-surface mismatch: one scatterer is on the rho=0.15 m ref3 surface and the other is between rho=0.15 m and rho=0.30 m. It should be used to judge localization sharpness and inter-reference defocus.

The Y-shaped target is the most useful structure-preservation case. The fork and branch tips make it easier to see whether a method preserves continuity or smears thin geometry along rho.

The random extended target provides a broader clutter/artifact check, but it is less mechanism-specific than the first two rows. It is better suited as a supplementary qualitative row unless its artifacts are visibly distinctive in follow-up rounds.

For the next round, a shell-wise figure or local zoom around the two-point inter-reference scatterer and the Y bifurcation would be a stronger paper candidate than adding more random targets.
