# task_real_draw005c report

## Objective

draw005c extends draw005b by adding the missing x-z projection, analyzing the three Y tips relative to ref3/ref9 reference surfaces, and producing a manuscript-oriented interpretation of the dense-volume Manisali-style figure.

## Relation to draw005b

The figure reuses draw005b as the direct source baseline: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_draw005b_ref3_plus_unet/20260511_175843`. The method columns, dense Y target, normalization convention, translucent 3D rendering, and dB MIP style are retained. The analytical extension is the fourth orthogonal row and the explicit tip-to-reference-surface analysis.

## Added x-z view

draw005b included the 3D, x-y, and z-y views. The missing x-z row is now added as the fourth row, computed as a maximum-intensity projection along y and displayed with the same `20*log10(abs(x))` convention and `[-40, 0]` dB range. This view is useful because it shows lateral x displacement and vertical z separation together, making the lower stem and the two upper terminals easier to distinguish from projection overlap.

## Tip definition

The three tips are derived from the same local control points used by the draw005 dense Y generator, then transformed back into world coordinates using the draw005 rotation and target center. Each ideal tip is also mapped to its nearest 24^3 display-grid voxel for local amplitude diagnostics.

## Tip-to-reference-surface distances

| Tip | x | y | z | rho | theta | nearest ref3 radius | dist to ref3 | nearest ref9 radius | dist to ref9 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| left upper tip | 0.1743 | 0.0076 | 0.0279 | 0.1745 | 2.50 deg | 0.15 | 0.0245 | 0.19 | 0.0155 |
| right upper tip | 0.2280 | 0.0210 | 0.0367 | 0.2289 | 5.26 deg | 0.30 | 0.0711 | 0.22 | 0.0089 |
| lower tip | 0.2085 | 0.0252 | -0.0293 | 0.2100 | 6.88 deg | 0.15 | 0.0600 | 0.22 | 0.0100 |

Distances are radial distances to the nearest cylindrical reference surface, computed separately for the ref3 and ref9 reference-radius sets. Smaller values indicate a more favorable radial placement for the corresponding reduced-reference operator, but visibility also depends on branch orientation, local support spread, and dB display thresholding.

## Local tip diagnostics

| Tip | Method | local peak r=2 | support >=0.10 | retained >=22% method peak |
| --- | --- | ---: | ---: | --- |
| left upper tip | GT | 0.5528 | 18 | True |
| left upper tip | ref3 | 0.5842 | 59 | True |
| left upper tip | ref9 | 0.0926 | 0 | False |
| left upper tip | BP | 0.5051 | 23 | True |
| left upper tip | U-Net residual | 0.1766 | 4 | False |
| left upper tip | ref3+U-Net | 0.5490 | 20 | True |
| right upper tip | GT | 0.4920 | 10 | True |
| right upper tip | ref3 | 0.0506 | 0 | False |
| right upper tip | ref9 | 0.1884 | 7 | True |
| right upper tip | BP | 0.2956 | 9 | True |
| right upper tip | U-Net residual | 0.4658 | 11 | True |
| right upper tip | ref3+U-Net | 0.4818 | 12 | True |
| lower tip | GT | 0.6023 | 32 | True |
| lower tip | ref3 | 0.1363 | 41 | True |
| lower tip | ref9 | 0.2710 | 21 | True |
| lower tip | BP | 0.5475 | 63 | True |
| lower tip | U-Net residual | 0.5149 | 29 | True |
| lower tip | ref3+U-Net | 0.5933 | 35 | True |

## Visual interpretation of ref3

The ref3 operator uses only radii 0.00, 0.15, and 0.30 m. The left upper tip is closest to a favorable ref3 radius with distance 0.0245 m, while the right upper and lower tips are farther away at 0.0711 m and 0.0600 m. This supports the observed pattern: one upper terminal can remain visible, whereas the other upper terminal and the lower terminal are more affected by structured radial mismatch. The x-y, z-y, and x-z rows are all needed here because a weak terminal can disappear either through true local suppression or by being spread along a projection direction until it falls below the dB display threshold.

The lower tip is also geometrically disadvantaged because it lies along the stem direction and is less reinforced by the forked high-response region. Under coarse ref3 sampling, its local energy can be redistributed into a broader artifact rather than a compact terminal peak, so it is not clearly retained in the Manisali-style rendering.

## Visual interpretation of ref9

Ref9 substantially densifies the reference radii. The two upper tips have smaller ref9 distances, 0.0155 m and 0.0089 m, which is consistent with both upper branches becoming visible. The lower tip remains weak because ref9 reduces but does not remove structured mismatch; the local response near the lower stem is still vulnerable to axial spreading and display-threshold suppression. Thus, ref9 improves the upper fork but does not fully recover every terminal structure.

## Figure-level scientific interpretation

The updated 4x6 figure should be interpreted as a geometry-dependent failure and repair example. BP provides the high-reference comparison, ref3 and ref9 expose how reduced-reference operators lose different parts of the same continuous target, the U-Net residual column localizes the learned compensation field, and ref3+U-Net shows the final reconstructed volume. Showing the final ref3+U-Net result is more interpretable than showing only the residual because the reader can judge whether the compensation restores a coherent physical object.

## Metrics

| Method | Role | NMSE | PSNR | SSIM | peak | support >=0.10 | support >=0.22 local peak |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ref3 | displayed_reconstruction | 1.8607 | 23.9594 | 0.2137 | 0.6070 | 1062 | 681 |
| ref9 | displayed_reconstruction | 1.0348 | 26.5075 | 0.4731 | 0.6070 | 476 | 370 |
| BP | displayed_reconstruction | 0.6284 | 28.6736 | 0.5822 | 0.6070 | 454 | 354 |
| U-Net residual | positive_part_of_calibrated_residual_delta | 0.2789 | 32.2024 | 0.8087 | 0.8198 | 125 | 83 |
| ref3+U-Net | displayed_reconstruction | 0.0147 | 44.9849 | 0.9918 | 0.9898 | 215 | 146 |

## Output inventory

- Main 4x6 PNG: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_draw005c_tip_analysis/20260515_000001/viz/paper_candidates/manisali_style/dense_y_manisali_4x6_with_xz_and_ref3_plus_unet.png`
- Main 4x6 PDF: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_draw005c_tip_analysis/20260515_000001/viz/paper_candidates/manisali_style/dense_y_manisali_4x6_with_xz_and_ref3_plus_unet.pdf`
- Clean 4x5 PNG: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_draw005c_tip_analysis/20260515_000001/viz/paper_candidates/manisali_style/dense_y_manisali_4x5_clean_with_xz_and_ref3_plus_unet.png`
- Tip CSV: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_draw005c_tip_analysis/20260515_000001/tip_reference_surface_analysis.csv`
- Tip JSON: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_draw005c_tip_analysis/20260515_000001/tip_reference_surface_analysis.json`
- Trans-level interpretation: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_draw005c_tip_analysis/20260515_000001/trans_level_figure_interpretation.md`
- Shared display scale inherited from draw005/draw005b source volumes: `1.64748394`

## Recommendation

Use the 4x6 figure as the main internal paper candidate because it contains the residual column needed to explain the repair mechanism. For a space-limited manuscript, use the clean 4x5 version as the main figure and keep the residual column plus tip diagnostics as supplementary material. The figure is suitable for main-text use if described as a controlled dense-Y visualization and not as an unseen-target generalization claim.
