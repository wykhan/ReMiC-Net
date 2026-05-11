# task_real_draw005b report

## Objective

draw005b adds the final corrected reconstruction `ref3 + U-Net residual` to the draw005 Manisali-style dense-volume figure.

## Relation to draw005

draw005 produced a visually successful Manisali-style dense-volume figure, but the last learning column was residual-only for this task's interpretation. draw005b keeps that residual column and adds a new final `ref3+U-Net` column.

## Corrected reconstruction definition

The corrected display volume is computed on the same fitted 24^3 display grid as draw005:

```python
ref3_plus_unet = ref3 + u_net_residual
ref3_plus_unet = np.maximum(ref3_plus_unet, 0.0)
```

All displayed volumes are reused from draw005 display caches and remain normalized by the draw005 GT peak.

## Visualization design

- Preserves the draw005 Manisali-style translucent voxel-volume 3D rendering.
- Preserves front/side dB MIP projections with `20*log10(abs(x))` and `[-40, 0]` dB display.
- Uses the same viewpoint, same cube, same spatial bounds, and the same non-scatter rendering style.
- The residual-only panel is explicitly labeled `U-Net residual`; the final corrected panel is labeled `ref3+U-Net`.

## Output inventory

- Source draw005 experiment: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_draw005_dense_volume/20260511_000001`
- Required 3x6 figure: `exp/task_real_draw005b_ref3_plus_unet/20260511_000001/viz/paper_candidates/manisali_style/dense_y_manisali_3x6_with_ref3_plus_unet.png`
- Required 3x6 PDF: `exp/task_real_draw005b_ref3_plus_unet/20260511_000001/viz/paper_candidates/manisali_style/dense_y_manisali_3x6_with_ref3_plus_unet.pdf`
- Clean 3x5 figure: `exp/task_real_draw005b_ref3_plus_unet/20260511_000001/viz/paper_candidates/manisali_style/dense_y_manisali_3x5_clean_ref3_plus_unet.png`
- Clean 3x5 PDF: `exp/task_real_draw005b_ref3_plus_unet/20260511_000001/viz/paper_candidates/manisali_style/dense_y_manisali_3x5_clean_ref3_plus_unet.pdf`
- Corrected display cache: `exp/task_real_draw005b_ref3_plus_unet/20260511_000001/recon_cache/dense_y_ref3_plus_unet_display.npz`
- Individual 3D panel: `exp/task_real_draw005b_ref3_plus_unet/20260511_000001/viz/paper_candidates/manisali_style/single_3d/ref3_plus_unet_volume.png`
- Individual MIP panel: `exp/task_real_draw005b_ref3_plus_unet/20260511_000001/viz/paper_candidates/manisali_style/single_mip/ref3_plus_unet_mips_db.png`

## Metrics

| Target | Method | Role | NMSE | PSNR | SSIM | peak | support >=0.10 | support >=0.22 local peak |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| dense_manisali_y | ref3 | displayed_reconstruction | 1.8607 | 23.9594 | 0.2137 | 0.6070 | 1062 | 681 |
| dense_manisali_y | ref9 | displayed_reconstruction | 1.0348 | 26.5075 | 0.4731 | 0.6070 | 476 | 370 |
| dense_manisali_y | BP | displayed_reconstruction | 0.6284 | 28.6736 | 0.5822 | 0.6070 | 454 | 354 |
| dense_manisali_y | U-Net residual | residual_only_not_final_reconstruction | 0.9928 | 26.6874 | 0.2586 | 0.0217 | 0 | 1213 |
| dense_manisali_y | ref3+U-Net | displayed_reconstruction | 1.9142 | 23.8363 | 0.2033 | 0.6070 | 1116 | 702 |

## Qualitative observations

- `ref3+U-Net` is much more interpretable than the residual-only panel because it is a full reconstruction volume rather than a weak correction field.
- Compared with `ref3`, the corrected result visually remains close to the ref3 reconstruction because the cached residual amplitude is small.
- Compared with `ref9` and `BP`, the corrected result does not recover the same degree of localization in this ordinary U-Net baseline.
- Metric side check: ref3 PSNR/SSIM is `23.9594` / `0.2137`, while ref3+U-Net is `23.8363` / `0.2033`. This indicates that the current ordinary residual baseline should not be over-claimed as a quantitative improvement in this draw005b run.

## Recommendation

Use the 3x6 figure for internal explanation because it shows both the residual-only field and the corrected reconstruction. For a manuscript figure, prefer the clean 3x5 version with `GT | ref3 | ref9 | BP | ref3+U-Net`, while the caption should state that this is the ordinary U-Net residual baseline rather than the final ReMiC-Net / RSB-FiLM model.
