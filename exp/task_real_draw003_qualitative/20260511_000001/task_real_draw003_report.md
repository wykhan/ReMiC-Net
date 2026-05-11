# task_real_draw003 report

## 1. Task objective

Draw003 upgrades the target itself to a thick, rotated, recognizable 3D Y object while keeping the method comparison fixed to ref3, ref9, BP, and the ordinary residual U-Net compensation on ref3.

## 2. Why draw002 was not yet sufficient

Draw002 improved rendering and annotation, but the Y target was still a thin point-built skeleton. That made the reader-facing figures less like a true 3D imaging object.

## 3. Thick-Y target design

- Construction: three cylindrical branch primitives represented by finite-thickness scatterer samples.
- Thickness: branch radius `0.010 m`, sampled with cross-section offsets.
- Rotation: x=18.0 deg, y=-22.0 deg, z=28.0 deg.
- Placement center: `[0.205, 0.035, 0.0]` m; object spans near and between ref3 reference radii.
- Scatterer count after grid deduplication: `299`.

## 4. Figure families implemented

- Family A: `exp/task_real_draw003_qualitative/20260511_000001/viz/paper_candidates/familyA`
- Family B: `exp/task_real_draw003_qualitative/20260511_000001/viz/paper_candidates/familyB`
- Family C: `exp/task_real_draw003_qualitative/20260511_000001/viz/paper_candidates/familyC`

## 5. Visualization choices

- Family A includes a perspective support rendering and a three-view MIP comparison.
- Family B uses rho-z max-over-theta projection with GT contour, ref3 reference-surface markers, and an ROI box.
- Family C uses the same ROI for reconstruction zoom, absolute error to GT, and correction/change relative to ref3.
- The learning panel is always the final compensated result `ref3 + U-Net`, not the residual alone.
- Reconstruction/MIP views use shared normalization and `log10(1 + A)` display. Error maps use shared absolute-error scaling within the figure.

## 6. Reader-interpretability assessment

The thick target is more object-like than the draw002 skeleton. The perspective view helps communicate that the object is rotated in 3D, while the MIP figure remains useful for method-by-method comparison. Family B and C are still needed because the object-readable views alone do not explain radial reference-surface mismatch.

## 7. Scientific interpretation

ref3 shows broad smeared support around the thick Y, while ref9 and BP are more localized. The ordinary `ref3 + U-Net` compensation visibly changes the ref3 output, but it should still be interpreted as a baseline compensation result rather than a ReMiC-Net claim. Object thickness helps expose shape distortion because blur and continuity loss are easier to see than on a one-voxel skeleton.

## 8. Recommendation for manuscript use

Use Family A as the main paper qualitative candidate if the paper needs an immediately recognizable object. Use Family B or C as the mechanism companion. A draw004 should replace ordinary `ref3 + U-Net` with the true ReMiC-Net / RSB-FiLM branch if the manuscript claim is structured mismatch compensation by ReMiC-Net.

## Metrics side check

| Target | Method | NMSE | PSNR | SSIM |
| --- | --- | ---: | ---: | ---: |
| thickY | ref3 | 1.5653 | 19.0217 | 0.0592 |
| thickY | ref9 | 2.0514 | 17.8471 | 0.0709 |
| thickY | BP | 1.8284 | 18.3470 | 0.0969 |
| thickY | ref3 + U-Net | 1.0100 | 20.9244 | 0.0903 |
