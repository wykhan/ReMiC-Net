# task_real_draw005 report

## Objective

This task replaces the draw004 point-scatterer-looking rendering with a dense reflectivity-volume target and a Manisali-style 3D qualitative figure.

## Manisali figure-9 rendering study

- Paper source: `doc/（U1）Efficient physics-based learned reconstruction methods for real-time 3D near-field MIMO radar imaging.pdf`.
- Source repository inspected: `wykhan/Efficient-Learned-3D-Near-Field-MIMO-Imaging`, especially `src/misc.py`.
- Manisali Fig. 9 uses five method columns, a first-row 3D image-cube view in linear scale, then front/side max projections in dB scale.
- Their public code renders the 3D cube with Plotly `go.Volume`, low opacity around `0.2`, and multiple translucent isosurfaces; max projections use `jet`, `20*log10(abs(x))`, and `[-40, 0]` dB color limits.
- Plotly is not installed in this execution environment, so the static PNG uses a matplotlib multi-threshold translucent voxel-volume renderer with the same low-opacity cube and dB projection policy.
- The 3D row uses per-panel relative isosurface thresholds so weak baseline outputs are still visible; absolute amplitude differences remain recorded in the metrics table.

## Dense-volume forward operator

- Implemented as `simulate_dense_volume` in `workspace/eval/task_real_draw005_dense_volume.py`.
- The primary object is a 24^3 dense reflectivity array, not a hand-authored point list.
- The forward model directly iterates over nonzero dense voxels and sums each voxel contribution into the protocol-v1 sparse cylindrical echo tensor.
- A derived scene JSON is written only to reuse the existing ref3/ref9/BP reconstruction patch machinery.
- Dense volume path: `exp/task_real_draw005_dense_volume/20260511_000001/dataset/dense_volumes/draw005_dense_manisali_y_dense_volume.npz`.
- Nonzero dense voxels after thresholding: `278` (`2.01%` of the 24^3 grid).
- Echo active measurement cells: `8294`.
- Dense forward wall time: `10.34` sec.

## Target validation

- rho range: `0.1677` to `0.2341` m.
- theta span: `8.12` deg.
- Mean / max distance to nearest ref3 radius: `0.0543` / `0.0742` m.
- Raw GT patch shape: `[17, 11, 23]`.
- Fitted display shape: `[24, 24, 24]`.
- Support lost during 24^3 fitting: `0`.
- Fits without crop: `True`.

## Outputs

- Main Manisali-style composite: `exp/task_real_draw005_dense_volume/20260511_000001/viz/paper_candidates/manisali_style/dense_y_manisali_3x5.png`
- Individual 3D volume renders: `exp/task_real_draw005_dense_volume/20260511_000001/viz/paper_candidates/manisali_style/single_3d`
- Individual dB MIP panels: `exp/task_real_draw005_dense_volume/20260511_000001/viz/paper_candidates/manisali_style/single_mip`
- Manifest: `exp/task_real_draw005_dense_volume/20260511_000001/draw005_manifest.json`

## Metrics side check

| Target | Method | NMSE | PSNR | SSIM | peak | support >=0.10 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| dense_manisali_y | ref3 | 1.8607 | 23.9594 | 0.2137 | 0.6070 | 1062 |
| dense_manisali_y | ref9 | 1.0348 | 26.5075 | 0.4731 | 0.6070 | 476 |
| dense_manisali_y | BP | 0.6284 | 28.6736 | 0.5822 | 0.6070 | 454 |
| dense_manisali_y | U-Net | 0.9928 | 26.6874 | 0.2586 | 0.0217 | 0 |

## Interpretation

The GT panel is now a connected volumetric object rather than a scatter cloud. The first row follows the Manisali-style image-cube idea, while the second and third rows provide the same dB max-projection checks used in Fig. 9. The ordinary U-Net panel remains a baseline compensation result, not a ReMiC-Net / RSB-FiLM result.
