# task_real_draw005d report

## Objective

draw005d implements a direct cylindrical-aperture true BP baseline and redraws the dense-Y Manisali-style figure with both the previous pseudo-BP column and the new true BP column.

## Why draw005d is needed

The draw005c x-z projection showed a visibly thick BP result. Because the existing code path labels `method='BP'` but reconstructs through the reference-surface engine, a direct voxel-wise BP baseline is needed before using this column as a high-quality manuscript reference.

## Code inspection result

`workspace/recon/cyl_fast_reference_engine.py::reconstruct_cylindrical_reference` obtains `refs = PROTOCOL_V1.reference_sets[method]`. For `method='BP'`, `ProtocolV1.reference_sets` maps BP to `rho_ref_full`, then `_reference_surface_stack(...)` and `sinc_geometry_correction(...)` produce the Cartesian volume. Therefore the old BP column is a dense-reference pseudo-BP baseline, not true voxel-wise BP.

## True BP implementation

`workspace/recon/cyl_true_bp_engine.py::true_backproject_sparse_echo` directly evaluates the project-consistent phase-compensated sum `sum y(a,h,k) exp(+j k R(a,h,p))` for each Cartesian voxel. It uses the sparse active echo cells written by the dense-volume forward simulator, the protocol-v1 azimuth/height/frequency samples, and the same `measurement_range` helper. A zero-padded inverse FFT over frequency is used only to interpolate the same k-domain summation as a range profile; no reference surfaces or geometry-correction stack are used.

- Dense-Y runtime: `7.28` sec
- Active measurement cells: `8294`
- Frequencies: `181`
- Reconstructed voxels: `13824`
- Voxel chunk / measurement chunk: `384` / `512`
- FFT range bins: `4096`
- Estimated peak memory: `268.19` MB

## Validation

The one-voxel sanity check used target coordinate `(0.2075, 0.0225, 0.002)` m. The reconstructed peak was at `(0.2075, 0.0225, 0.002)` m, giving localization error `0.000000` m. The peak-to-second-largest ratio was `1.1874`.

## Main figure outputs

- 4x7 main figure: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_draw005d_true_bp/20260515_000001/viz/paper_candidates/manisali_style/dense_y_manisali_4x7_with_true_bp.png`
- 4x7 main PDF: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_draw005d_true_bp/20260515_000001/viz/paper_candidates/manisali_style/dense_y_manisali_4x7_with_true_bp.pdf`
- 4x5 clean figure: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_draw005d_true_bp/20260515_000001/viz/paper_candidates/manisali_style/dense_y_manisali_4x5_clean_true_bp.png`
- x-z diagnostic: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_draw005d_true_bp/20260515_000001/viz/diagnostics/xz_pseudo_bp_vs_true_bp.png`

## x-z bloating analysis

At the fixed -20 dB x-z projection threshold, pseudo-BP has support area `270` pixels and bounding box `17x21`. True BP has support area `293` pixels and bounding box `22x21`. In the 3D volume, true BP uses fewer voxels above 0.10 (`282`) than pseudo-BP (`454`), but the x-z projection support at this dB threshold is not smaller.

Therefore, the previous x-z bloating should not be attributed solely to the dense-reference pseudo-BP approximation. True BP improves the physics baseline and reduces volumetric support, but the x-z projection still broadens under the finite aperture, finite tube radius, projection collapse, and the chosen dB threshold. The dense-reference pseudo-BP label remains necessary for correctness, but the x-z thickness is a mixed effect rather than a pure pseudo-BP artifact.

| Method | x-z support area | bbox width | bbox height | bbox area | fill ratio |
| --- | ---: | ---: | ---: | ---: | ---: |
| ref3 | 327 | 17 | 21 | 357 | 0.9160 |
| ref9 | 249 | 17 | 20 | 340 | 0.7324 |
| pseudo-BP | 270 | 17 | 21 | 357 | 0.7563 |
| true BP | 293 | 22 | 21 | 462 | 0.6342 |
| ref3+U-Net | 91 | 14 | 19 | 266 | 0.3421 |

## Tip-level analysis

| Tip | x | y | z | rho | theta | nearest ref3 radius | dist to ref3 | nearest ref9 radius | dist to ref9 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| left upper tip | 0.1743 | 0.0076 | 0.0279 | 0.1745 | 2.50 deg | 0.15 | 0.0245 | 0.19 | 0.0155 |
| right upper tip | 0.2280 | 0.0210 | 0.0367 | 0.2289 | 5.26 deg | 0.30 | 0.0711 | 0.22 | 0.0089 |
| lower tip | 0.2085 | 0.0252 | -0.0293 | 0.2100 | 6.88 deg | 0.15 | 0.0600 | 0.22 | 0.0100 |

| Tip | Method | local peak r=2 | support >=0.10 | retained >=22% method peak |
| --- | --- | ---: | ---: | --- |
| left upper tip | GT | 0.5528 | 18 | True |
| left upper tip | ref3 | 0.5842 | 59 | True |
| left upper tip | ref9 | 0.0926 | 0 | False |
| left upper tip | pseudo-BP | 0.5051 | 23 | True |
| left upper tip | U-Net residual | 0.1766 | 4 | False |
| left upper tip | ref3+U-Net | 0.5490 | 20 | True |
| right upper tip | GT | 0.4920 | 10 | True |
| right upper tip | ref3 | 0.0506 | 0 | False |
| right upper tip | ref9 | 0.1884 | 7 | True |
| right upper tip | pseudo-BP | 0.2956 | 9 | True |
| right upper tip | U-Net residual | 0.4658 | 11 | True |
| right upper tip | ref3+U-Net | 0.4818 | 12 | True |
| lower tip | GT | 0.6023 | 32 | True |
| lower tip | ref3 | 0.1363 | 41 | True |
| lower tip | ref9 | 0.2710 | 21 | True |
| lower tip | pseudo-BP | 0.5475 | 63 | True |
| lower tip | U-Net residual | 0.5149 | 29 | True |
| lower tip | ref3+U-Net | 0.5933 | 35 | True |
| left upper tip | true BP | 0.3270 | 42 | True |
| right upper tip | true BP | 0.2325 | 24 | True |
| lower tip | true BP | 0.2668 | 36 | True |

True BP is added to the same local-tip diagnostic used in draw005c. The result should be interpreted together with the x-z diagnostic: true BP provides a direct physical baseline for whether each Y terminal is locally focused, while ref3/ref9 expose reference-radius mismatch and ref3+U-Net shows learned compensation.

## Metrics

| Method | Role | NMSE | PSNR | SSIM | peak | support >=0.10 | support >=0.22 local peak |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ref3 | displayed_reconstruction | 1.8607 | 23.9594 | 0.2137 | 0.6070 | 1062 | 681 |
| ref9 | displayed_reconstruction | 1.0348 | 26.5075 | 0.4731 | 0.6070 | 476 | 370 |
| pseudo-BP | dense_reference_pseudo_bp | 0.6284 | 28.6736 | 0.5822 | 0.6070 | 454 | 354 |
| true BP | voxelwise_phase_compensated_backprojection | 0.5703 | 29.0952 | 0.5904 | 0.3270 | 282 | 371 |
| U-Net residual | positive_part_of_calibrated_residual_delta | 0.2789 | 32.2024 | 0.8087 | 0.8198 | 125 | 83 |
| ref3+U-Net | displayed_reconstruction | 0.0147 | 44.9849 | 0.9918 | 0.9898 | 215 | 146 |

## Manuscript recommendation

Future paper figures should use true BP when the column is meant to represent a high-quality physics baseline. The old BP column should be renamed pseudo-BP or dense-reference BP. For the main paper, keep true BP and ref3+U-Net in the clean comparison; retain pseudo-BP in supplementary analysis when discussing why the previous x-z panel appeared bloated.
