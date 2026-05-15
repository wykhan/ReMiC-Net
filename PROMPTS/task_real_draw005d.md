
````md
# task_real_draw005d — Implement True BP and Redraw the Dense-Y Manisali-Style Figure

## Task Title
Implement a true cylindrical-aperture backprojection baseline and redraw the draw005c dense-Y Manisali-style figure.

---

## 1. Background

`task_real_draw005c` extended the dense-volume Manisali-style Y-target figure by adding the missing x-z view and tip-to-reference-surface analysis.

However, in the x-z view, the current `BP` result appears visibly thick / bloated. This raises an important concern:

> The current `BP` implementation may not be a true voxel-wise backprojection baseline. It may instead be a denser reference-surface reconstruction or another approximation in the reference-surface family.

This matters because the manuscript needs a trustworthy high-quality reference. If the method column labeled `BP` is not true BP, then the qualitative comparison and scientific interpretation may be misleading.

This task addresses that issue.

---

## 2. Main objective

Implement a **true cylindrical-aperture backprojection baseline** and redraw the draw005c figure using this true BP result.

The task must answer:

1. Is the x-z bloating in the current BP column caused by the pseudo-BP / dense-reference approximation?
2. Does true BP produce a sharper, less bloated reconstruction in x-z?
3. How do `ref3`, `ref9`, pseudo-BP, true BP, U-Net residual, and `ref3+U-Net` compare under the same dense-Y visualization protocol?

---

## 3. Important terminology

Use the following terms consistently.

### 3.1 Pseudo-BP
The current `BP` result from draw005 / draw005c should be treated as:

```text
pseudo-BP
````

unless code inspection proves that it is already a true BP.

If it is based on dense reference surfaces, a reference-surface engine, or another approximation, label it clearly as:

```text
pseudo-BP / dense-reference baseline
```

### 3.2 True BP

The new implementation in draw005d should be a direct voxel-wise backprojection:

```text
true BP
```

True BP must not be implemented as “more reference surfaces”.

True BP should directly use the measurement geometry and synthesize the image value of each voxel by phase-compensated summation over measured echo samples.

---

## 4. Required source experiment

Use the completed draw005c experiment as the figure and analysis baseline.

Primary source:

```text
exp/task_real_draw005c_tip_analysis/
```

Also reuse draw005b / draw005 outputs if needed:

```text
exp/task_real_draw005b_ref3_plus_unet/
exp/task_real_draw005_dense_volume/
```

Reuse the same:

* dense Y target;
* dense-volume echo;
* ref3 result;
* ref9 result;
* U-Net residual;
* ref3+U-Net result;
* visualization settings;
* projection views;
* tip analysis metadata.

Do not redesign the target.

---

## 5. True BP implementation requirements

### 5.1 New implementation

Add a true BP implementation in a clean, reusable location.

Suggested file:

```text
workspace/recon/cyl_true_bp_engine.py
```

or, if keeping it task-local:

```text
workspace/eval/task_real_draw005d_true_bp.py
```

A reusable recon module is preferred.

### 5.2 Mathematical definition

For each reconstruction voxel at position:

```text
p = (rho, theta, z)
```

or equivalent Cartesian coordinate:

```text
p = (x, y, z)
```

true BP should compute:

```text
x_hat(p) = sum over aperture samples and frequencies of y(a,h,k) * exp(+j k R(a,h,p))
```

or the project-consistent conjugate phase convention.

Where:

* `y(a,h,k)` is the measured synthetic echo;
* `R(a,h,p)` is the near-field propagation distance from aperture sample to voxel;
* `k` is the wavenumber;
* summation should use valid / active measurement cells;
* final displayed image should use magnitude or project-consistent intensity.

Use the same phase convention as the existing forward simulator and reconstruction code.

### 5.3 Geometry consistency

True BP must use the same geometry as the dense-volume forward operator from draw005:

* same protocol-v1 cylindrical aperture;
* same azimuth samples;
* same height samples;
* same frequency / wavenumber values;
* same measurement range function;
* same visibility / active measurement convention if applicable.

If the dense forward operator used sparse active echo cells, true BP must use the same active echo representation.

### 5.4 No reference-surface approximation

The true BP implementation must not call the reference-surface reconstruction engine as the core reconstruction.

It must not be:

* `refN` with larger N;
* interpolation among reference surfaces;
* reference-surface holographic approximation;
* dense-reference approximation.

It may reuse low-level geometry helpers, but not the reference-surface approximation itself.

### 5.5 Computational efficiency

The true BP implementation may be slower than ref3/ref9.

Use safe chunking:

* chunk over voxels, or
* chunk over measurement cells,
* avoid building a huge dense matrix if memory becomes large.

Record:

* number of reconstructed voxels;
* number of active measurements;
* number of frequencies;
* chunk size;
* runtime;
* memory-relevant choices.

---

## 6. Validation requirements

### 6.1 One-voxel sanity check

Validate true BP using a simple one-voxel or few-voxel dense target.

Recommended check:

1. create or reuse a tiny synthetic target with one nonzero voxel;
2. simulate echo using the dense-volume forward operator;
3. reconstruct with true BP;
4. verify that the peak appears near the correct voxel location.

Report:

* true target voxel coordinate;
* reconstructed peak coordinate;
* voxel localization error;
* peak-to-sidelobe observation if easy.

### 6.2 Compare pseudo-BP and true BP

For the dense-Y target, compare:

* pseudo-BP from draw005c;
* true BP from draw005d.

Compute at least:

* NMSE against GT;
* PSNR;
* SSIM;
* support voxel count at visualization threshold;
* x-z support thickness proxy;
* local peak values near the three Y tips.

---

## 7. Figure columns

The main draw005d figure should include seven columns:

1. `GT`
2. `ref3`
3. `ref9`
4. `pseudo-BP`
5. `true BP`
6. `U-Net residual`
7. `ref3+U-Net`

This gives the reader a direct comparison between the previous “BP” and the new true BP.

Optional clean version:

1. `GT`
2. `ref3`
3. `ref9`
4. `true BP`
5. `ref3+U-Net`

But the required primary figure is the seven-column comparison.

---

## 8. Figure rows / views

Use the same view structure as draw005c:

1. 3D volumetric rendering
2. x-y dB maximum projection
3. z-y dB maximum projection
4. x-z dB maximum projection

Recommended primary layout:

```text
4 × 7 composite figure
```

Suggested filename:

```text
dense_y_manisali_4x7_with_true_bp.png
```

Also save PDF:

```text
dense_y_manisali_4x7_with_true_bp.pdf
```

Optional clean figure:

```text
dense_y_manisali_4x5_clean_true_bp.png
dense_y_manisali_4x5_clean_true_bp.pdf
```

---

## 9. Visualization style

Preserve the draw005 / draw005b / draw005c style.

Use:

* dense-volume rendering;
* translucent voxel-volume or equivalent Manisali-style image-cube rendering;
* dB maximum projections;
* same cube;
* same spatial bounds;
* same viewpoint;
* same color and dB limits;
* same normalization rules.

Do not revert to scatter plots.

Do not manually tune true BP to look better than other methods.

The only intended change is the addition of true BP and the relabeling of old BP as pseudo-BP.

---

## 10. x-z bloating analysis

The report must specifically analyze the x-z bloating issue.

### 10.1 Required question

Explicitly answer:

> Is the x-z bloating in the previous BP column caused or aggravated by using pseudo-BP / dense-reference approximation instead of true BP?

### 10.2 Required evidence

Use at least two kinds of evidence:

1. visual comparison in the x-z projection;
2. quantitative support-thickness or local-width measurement.

### 10.3 Suggested thickness metric

For the x-z projection, compute a simple support-thickness proxy.

For example:

1. threshold the x-z dB projection at a fixed level, such as `-20 dB` or the project’s display threshold;
2. compute the support area in x-z;
3. compute width / height bounding-box statistics;
4. optionally compute average thickness around the Y trunk or tips.

Report this for:

* pseudo-BP;
* true BP;
* ref3;
* ref9;
* ref3+U-Net.

The metric does not need to be perfect, but it must support the visual analysis.

---

## 11. Tip-level analysis update

Reuse the draw005c tip analysis for:

1. left upper tip;
2. right upper tip;
3. lower tip.

Add true BP to the tip-level local diagnostics.

For each method:

* ref3;
* ref9;
* pseudo-BP;
* true BP;
* ref3+U-Net;

report if feasible:

* local peak near each tip;
* local support voxel count near each tip;
* whether the tip is visually retained;
* whether true BP improves the missing lower tip or sharpens upper tips.

---

## 12. Required report

Create:

```text
task_real_draw005d_report.md
```

The report must include the following sections.

### 12.1 Objective

State that draw005d implements a true BP baseline and redraws the dense-Y Manisali-style figure.

### 12.2 Why draw005d is needed

Explain:

* draw005c’s x-z BP result looked bloated;
* current BP may be pseudo-BP / dense-reference approximation;
* true BP is needed as a reliable high-quality reference.

### 12.3 Code inspection result

Inspect the current `BP` implementation and report whether it is:

* true BP, or
* pseudo-BP / dense-reference approximation.

Cite or describe the relevant code path in the report.

### 12.4 True BP implementation

Describe:

* file/function implemented;
* mathematical convention;
* input echo format;
* voxel grid;
* active measurement handling;
* chunking;
* runtime.

### 12.5 Validation

Report the one-voxel sanity check result:

* true voxel coordinate;
* reconstructed peak coordinate;
* localization error.

### 12.6 Main figure outputs

List all generated figures.

### 12.7 x-z bloating analysis

Compare pseudo-BP and true BP in x-z.

Discuss:

* whether true BP reduces bloating;
* whether the previous bloating was caused by pseudo-BP;
* whether any residual bloating is due to target thickness, projection, rendering threshold, or physical aperture resolution.

### 12.8 Tip-level analysis

Discuss whether true BP changes the visibility of:

* left upper tip;
* right upper tip;
* lower tip.

### 12.9 Manuscript recommendation

Recommend whether future paper figures should:

* use true BP instead of pseudo-BP;
* rename old BP as pseudo-BP;
* remove pseudo-BP from main figure;
* keep pseudo-BP only in supplementary analysis.

---

## 13. Required output directory

Create:

```text
exp/task_real_draw005d_true_bp/<timestamp>/
```

Recommended outputs:

```text
task_real_draw005d_report.md
draw005d_manifest.json
metrics_draw005d.json
true_bp_validation.json
xz_bloating_analysis.json
tip_analysis_with_true_bp.json
```

Figures:

```text
viz/paper_candidates/manisali_style/dense_y_manisali_4x7_with_true_bp.png
viz/paper_candidates/manisali_style/dense_y_manisali_4x7_with_true_bp.pdf
viz/paper_candidates/manisali_style/dense_y_manisali_4x5_clean_true_bp.png
viz/paper_candidates/manisali_style/dense_y_manisali_4x5_clean_true_bp.pdf
```

Single panels:

```text
viz/paper_candidates/manisali_style/single_3d/true_bp_volume.png
viz/paper_candidates/manisali_style/single_mip/true_bp_mips_db.png
```

Diagnostics:

```text
viz/diagnostics/xz_pseudo_bp_vs_true_bp.png
viz/diagnostics/tip_local_comparison_true_bp.png
```

---

## 14. Metrics

Compute metrics for:

1. ref3
2. ref9
3. pseudo-BP
4. true BP
5. U-Net residual
6. ref3+U-Net

Against GT, report:

* NMSE
* PSNR
* SSIM
* peak value
* support voxel count;
* x-z projection support area;
* x-z bounding-box width / height;
* optional Dice / IoU if already available.

Make clear that residual-only U-Net metrics are not final-reconstruction metrics.

---

## 15. Acceptance criteria

This task is successful if and only if:

1. the current BP implementation is inspected and classified;
2. a true BP implementation is created or verified;
3. true BP does not use the reference-surface approximation as its core algorithm;
4. true BP is run on the dense-Y echo;
5. the draw005c figure is redrawn with both pseudo-BP and true BP;
6. the x-z view is included;
7. x-z bloating is analyzed visually and quantitatively;
8. tip-level analysis is updated with true BP;
9. a report is written;
10. all outputs are saved under `exp/task_real_draw005d_true_bp/<timestamp>/`.

---

## 16. Failure conditions

The task should be considered failed if:

1. true BP is actually implemented as more reference surfaces;
2. the old BP column is not relabeled as pseudo-BP when appropriate;
3. the figure omits x-z;
4. the report does not address the x-z bloating question;
5. no validation is performed;
6. no quantitative x-z width / support diagnostic is provided;
7. visualization style changes substantially from draw005c without justification.

---

## 17. Final deliverable summary

The most important deliverables are:

```text
exp/task_real_draw005d_true_bp/<timestamp>/viz/paper_candidates/manisali_style/dense_y_manisali_4x7_with_true_bp.pdf
exp/task_real_draw005d_true_bp/<timestamp>/task_real_draw005d_report.md
exp/task_real_draw005d_true_bp/<timestamp>/xz_bloating_analysis.json
```

The scientific purpose of draw005d is to determine whether the x-z bloating in the previous BP panel was caused by the use of a pseudo-BP / dense-reference approximation, and to establish a trustworthy true BP baseline for future manuscript figures.

```


