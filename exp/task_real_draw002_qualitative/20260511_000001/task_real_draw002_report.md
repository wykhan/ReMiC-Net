# task_real_draw002 report

## 1. Task objective

Draw002 is a second-round redesign focused on reader-readable qualitative figures. It keeps the draw001 scientific target but separates shape-readable views from mechanism-diagnostic views.

## 2. Summary of draw001 limitation

Draw001 relied on rho-z max-over-theta projections. That preserved radial mismatch information, but readers could not immediately recognize the Y-shaped or random extended targets, and the compensation region was not sufficiently explicit.

## 3. Figure families implemented

- Figure Family A: `exp/task_real_draw002_qualitative/20260511_000001/viz/paper_candidates/familyA`
- Figure Family B: `exp/task_real_draw002_qualitative/20260511_000001/viz/paper_candidates/familyB`
- Figure Family C: `exp/task_real_draw002_qualitative/20260511_000001/viz/paper_candidates/familyC`
- No point-target primary qualitative panel was produced.

## 4. Target definitions

- Y-shaped target: reused from draw001 for continuity; it contains a thin trunk and two branches at inter-reference radii.
- Random connected extended target: reused from draw001 for continuity; it contains irregular connected/semi-connected clusters and sparse bridges.
- No geometry change was made relative to draw001; the redesign is in rendering and annotation.

## 5. Visualization choices

- Family A uses three orthogonal MIP views (xy, xz, yz) for each target and method so the target shape is recognizable.
- Family B uses rho-z max-over-theta projections with GT contour overlays, ref3 reference-surface markers, and cyan ROI boxes.
- Family C zooms into a deliberate ROI around the Y bifurcation/fork region, then shows reconstruction, absolute error to GT, and correction magnitude relative to ref3.
- Shape and mechanism panels use shared per-target normalization and log10(1 + A) rendering for dynamic-range control.
- Error maps use absolute amplitude error with one shared color scale within the figure.

## 6. Reader-interpretability assessment

- Family A is the most reader-readable: the Y structure and irregular connected target can be recognized before studying method differences.
- Family B is the best mechanism bridge: it preserves rho while adding GT context and ref3 reference surfaces.
- Family C is the strongest reviewer-facing compensation figure for the Y target because the ROI is tied to the bifurcation and branch-continuity failure mode.

## 7. Scientific interpretation

The ref3 panels show broader radial spread and weaker structural localization than ref9/BP in the diagnostic views. Ref9 generally moves closer to BP by reducing the reference-surface approximation gap. The ordinary U-Net baseline changes the ref3 output but does not consistently recover the BP-like structure in these reader-facing panels; this is important because draw002 intentionally keeps U-Net distinct from ReMiC-Net/RSB-FiLM.

## 8. Recommendation for manuscript use

Use Family A as the primary qualitative reconstruction figure, and use Family B or C as a mechanism-oriented companion figure. A draw003 follow-up should focus on a true ReMiC-Net/RSB-FiLM compensation figure or a shell-wise error/improvement figure if the manuscript needs a stronger compensation claim than the ordinary U-Net baseline can support.

## Metrics side check

| Target | Method | NMSE | PSNR | SSIM |
| --- | --- | ---: | ---: | ---: |
| y | ref3 | 48.3438 | 15.0874 | 0.0015 |
| y | ref9 | 7.7489 | 23.0384 | 0.0662 |
| y | BP | 5.5094 | 24.5197 | 0.1044 |
| y | U-Net | 1.5265 | 30.0939 | 0.3465 |
| random_ext | ref3 | 20.2693 | 19.3685 | 0.0061 |
| random_ext | ref9 | 3.1984 | 27.3877 | 0.1730 |
| random_ext | BP | 2.8561 | 27.8792 | 0.2061 |
| random_ext | U-Net | 1.4227 | 30.9058 | 0.4064 |
