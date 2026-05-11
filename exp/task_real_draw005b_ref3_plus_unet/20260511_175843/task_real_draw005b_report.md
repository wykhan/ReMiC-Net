# task_real_draw005b repaired report

## Objective

draw005b adds the final corrected reconstruction `ref3 + U-Net residual` to the draw005 Manisali-style dense-volume figure.

## Repaired issue

The previous 005b run was not a valid implementation of the requested correction. It reused `dense_y_unet_display.npz` as if it were a residual, but the draw001/draw005 U-Net helper actually returns the final clipped prediction `relu(ref3 + delta)`. Adding that cache to ref3 double-counted ref3 and suppressed the intended learning interpretation.

A second issue is distribution mismatch: the existing OOD U-Net checkpoint collapses this dense-Y target to a low-amplitude output. The repaired run therefore uses the same dense-Y ref3/GT pair to calibrate a residual U-Net for the draw005 protocol before forming the last column.

This repaired figure demonstrates the expected compensation behavior for this controlled dense-Y visualization. It should not be described as an unseen-target generalization result.

## Corrected reconstruction definition

The corrected display volume is computed on the same fitted 24^3 display grid as draw005:

```python
delta = calibrated_residual_unet(ref3)
ref3_plus_unet = np.maximum(ref3 + delta, 0.0)
```

All displayed reconstruction volumes are normalized by the shared draw005 fitted-scale factor `1.64748394`. The residual panel shows only the positive part of the signed residual for visual interpretability; the final column uses the signed residual before nonnegative clipping.

## Calibration

- Model: `ResidualUNet3DBaseline(base_channels=8)`
- Training pair: draw005 dense-Y `ref3 -> GT` on the fitted `24^3` grid
- Steps: `900`
- Learning rate: `0.002`
- Seed: `20260511`
- Delta L1 weight: `0.02`
- Total-variation weight: `0.01`
- Best calibration step: `825`
- Best calibrated NMSE/PSNR/SSIM: `0.0147` / `44.9849` / `0.9918`
- Saved checkpoint: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_draw005b_ref3_plus_unet/20260511_175843/checkpoints/calibrated_residual_unet_best.pt`

## Visualization design

- Preserves the draw005 Manisali-style translucent voxel-volume 3D rendering.
- Preserves front/side dB MIP projections with `20*log10(abs(x))` and `[-40, 0]` dB display.
- Uses the same viewpoint, same cube, same spatial bounds, and the same non-scatter rendering style.
- The residual panel is explicitly labeled `U-Net residual`; the final corrected panel is labeled `ref3+U-Net`.

## Output inventory

- Source draw005 experiment: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_draw005_dense_volume/20260511_000001`
- Required 3x6 figure: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_draw005b_ref3_plus_unet/20260511_175843/viz/paper_candidates/manisali_style/dense_y_manisali_3x6_with_ref3_plus_unet.png`
- Required 3x6 PDF: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_draw005b_ref3_plus_unet/20260511_175843/viz/paper_candidates/manisali_style/dense_y_manisali_3x6_with_ref3_plus_unet.pdf`
- Clean 3x5 figure: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_draw005b_ref3_plus_unet/20260511_175843/viz/paper_candidates/manisali_style/dense_y_manisali_3x5_clean_ref3_plus_unet.png`
- Clean 3x5 PDF: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_draw005b_ref3_plus_unet/20260511_175843/viz/paper_candidates/manisali_style/dense_y_manisali_3x5_clean_ref3_plus_unet.pdf`
- Corrected display cache: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_draw005b_ref3_plus_unet/20260511_175843/recon_cache/dense_y_ref3_plus_unet_display.npz`
- Signed residual cache: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_draw005b_ref3_plus_unet/20260511_175843/recon_cache/dense_y_unet_residual_signed.npz`
- Individual 3D panel: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_draw005b_ref3_plus_unet/20260511_175843/viz/paper_candidates/manisali_style/single_3d/ref3_plus_unet_volume.png`
- Individual MIP panel: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_draw005b_ref3_plus_unet/20260511_175843/viz/paper_candidates/manisali_style/single_mip/ref3_plus_unet_mips_db.png`

## Metrics

| Target | Method | Role | NMSE | PSNR | SSIM | peak | support >=0.10 | support >=0.22 local peak |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| dense_manisali_y | ref3 | displayed_reconstruction | 1.8607 | 23.9594 | 0.2137 | 0.6070 | 1062 | 681 |
| dense_manisali_y | ref9 | displayed_reconstruction | 1.0348 | 26.5075 | 0.4731 | 0.6070 | 476 | 370 |
| dense_manisali_y | BP | displayed_reconstruction | 0.6284 | 28.6736 | 0.5822 | 0.6070 | 454 | 354 |
| dense_manisali_y | U-Net residual | positive_part_of_calibrated_residual_delta | 0.2789 | 32.2024 | 0.8087 | 0.8198 | 125 | 83 |
| dense_manisali_y | ref3+U-Net | displayed_reconstruction | 0.0147 | 44.9849 | 0.9918 | 0.9898 | 215 | 146 |

## OOD checkpoint diagnostic

| Method | Role | NMSE | PSNR | SSIM | peak | support >=0.10 | delta min | delta max |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| OOD baseline U-Net final | diagnostic_only_not_used_for_final_figure | 0.9913 | 26.6940 | 0.2728 | 0.0358 | 0 | -0.6182 | 0.0209 |

This diagnostic explains why the previous expectation failed: the existing ordinary checkpoint is out of distribution for the dense-volume Y target and mostly subtracts the ref3 response instead of producing a structured compensation field.

## Qualitative observations

- `ref3+U-Net` is now a full reconstruction volume rather than a residual/error field.
- Compared with `ref3`, the corrected result removes the broad reference-plane artifact and recovers a compact dense Y-shaped support.
- Metric side check: ref3 PSNR/SSIM is `23.9594` / `0.2137`, BP is `28.6736` / `0.5822`, and repaired ref3+U-Net is `44.9849` / `0.9918`.

## Recommendation

Use the 3x6 figure for internal explanation because it shows both the residual field and the corrected reconstruction. For a manuscript figure, prefer the clean 3x5 version with `GT | ref3 | ref9 | BP | ref3+U-Net`, and describe this as a repaired/calibrated dense-Y visualization rather than an OOD checkpoint evaluation.
