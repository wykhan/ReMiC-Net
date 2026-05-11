
# `PROMPTS/task_real_draw005b.md`

````md
# task_real_draw005b — Add ref3+U-Net Corrected Reconstruction to Dense-Volume Manisali-Style Figure

## Task Title
Add the final `ref3 + U-Net residual` reconstruction column to the draw005 Manisali-style dense-volume Y-target figure.

---

## 1. Background

`task_real_draw005` successfully produced a Manisali-style 3D overall imaging figure using:

- a dense Y-shaped reflectivity volume;
- a dense-volume forward operator;
- ref3 / ref9 / BP / ordinary U-Net baseline outputs;
- translucent voxel-volume 3D rendering;
- dB maximum-projection views.

The resulting figure style is satisfactory and should be retained.

However, there is one important issue:

> The current `U-Net` panel appears to show only the U-Net residual / compensation output, not the final corrected reconstruction.

For visual comparison in the manuscript, readers should see the final compensated image:

```text
U-Net corrected = ref3 + U-Net residual
````

Therefore, `task_real_draw005b` must add a new final column showing:

```text
ref3 + U-Net
```

or equivalently:

```text
ref3 + U-Net residual correction
```

---

## 2. Main objective

Reuse the outputs and pipeline of `task_real_draw005`, and generate a new Manisali-style composite figure with an additional final column:

```text
GT | ref3 | ref9 | BP | U-Net residual | ref3+U-Net
```

The last column must show the final corrected reconstruction:

```text
ref3_plus_unet = ref3 + unet_residual
```

This corrected result should be visually interpretable as a 3D reconstruction, not merely a residual/error field.

---

## 3. Required input experiment

Use the completed draw005 experiment as the source:

```text
exp/task_real_draw005_dense_volume/20260511_000001/
```

Read and reuse as much as possible from:

```text
exp/task_real_draw005_dense_volume/20260511_000001/draw005_manifest.json
exp/task_real_draw005_dense_volume/20260511_000001/recon_cache/
exp/task_real_draw005_dense_volume/20260511_000001/dataset/
workspace/eval/task_real_draw005_dense_volume.py
```

Do not rerun the whole experiment unless necessary.

If direct reuse is difficult, rerun the dense-volume target and reconstructions using the same settings as draw005.

---

## 4. Required method columns

The new composite figure must contain six columns:

1. `GT`
2. `ref3`
3. `ref9`
4. `BP`
5. `U-Net residual`
6. `ref3+U-Net`

The final column must be labeled clearly as one of:

```text
ref3+U-Net
```

or

```text
ref3 + U-Net residual
```

Preferred label:

```text
ref3+U-Net
```

---

## 5. Critical definition

### 5.1 U-Net residual

The existing U-Net output in draw005 should be treated as:

```text
u_net_residual
```

not as the final reconstruction.

### 5.2 Corrected output

Compute:

```python
ref3_plus_unet = ref3 + u_net_residual
```

Use the same fitted 24³ display grid as draw005.

### 5.3 Clipping / nonnegativity

After addition, apply a physically reasonable nonnegative display volume:

```python
ref3_plus_unet = np.maximum(ref3_plus_unet, 0.0)
```

If the existing evaluation protocol uses a different clipping or normalization convention, follow the existing protocol but document it clearly.

### 5.4 Normalization

Use the same normalization convention as draw005.

Preferred:

```text
normalize all display volumes by the GT peak
```

Do not independently auto-scale the final `ref3+U-Net` panel in a way that makes it visually incomparable.

---

## 6. Visualization style to preserve

The draw005 visual style is considered successful and should be retained.

Preserve the following style keywords:

* dense reflectivity volume;
* Manisali-style image-cube rendering;
* translucent voxel-volume renderer;
* multi-threshold translucent isosurfaces;
* low-opacity 3D cube;
* front/side dB maximum projections;
* `20*log10(abs(x))`;
* `[-40, 0] dB` projection display;
* same viewpoint;
* same spatial bounds;
* same cube;
* same method order.

Do not return to scatter plotting.

The main figure must not look like a point cloud.

---

## 7. Required output layout

Generate a new manuscript-oriented composite figure.

Preferred layout:

```text
columns:
GT | ref3 | ref9 | BP | U-Net residual | ref3+U-Net

rows:
row 1: 3D translucent volume rendering
row 2: front / top-like dB maximum projection
row 3: side-like dB maximum projection
```

This gives a:

```text
3 × 6 composite figure
```

Suggested main output filename:

```text
dense_y_manisali_3x6_with_ref3_plus_unet.png
```

Also save PDF if feasible:

```text
dense_y_manisali_3x6_with_ref3_plus_unet.pdf
```

---

## 8. Optional secondary figure

In addition to the required 3×6 figure, optionally generate a cleaner paper figure that omits the residual-only panel:

```text
GT | ref3 | ref9 | BP | ref3+U-Net
```

This would be a:

```text
3 × 5 manuscript-clean figure
```

Suggested filename:

```text
dense_y_manisali_3x5_clean_ref3_plus_unet.png
```

This optional 3×5 version may be more suitable for the final manuscript.

However, the required deliverable is the 3×6 figure.

---

## 9. Required experiment directory

Create a new output directory:

```text
exp/task_real_draw005b_ref3_plus_unet/<timestamp>/
```

Recommended fixed timestamp style if running in a controlled task:

```text
exp/task_real_draw005b_ref3_plus_unet/20260511_000001/
```

---

## 10. Required saved files

Save:

```text
task_real_draw005b_report.md
draw005b_manifest.json
metrics_draw005b.json
```

Save the computed corrected display volume:

```text
recon_cache/dense_y_ref3_plus_unet_display.npz
```

Save individual panels:

```text
viz/paper_candidates/manisali_style/single_3d/ref3_plus_unet_volume.png
viz/paper_candidates/manisali_style/single_mip/ref3_plus_unet_mips_db.png
```

Save the required composite figure:

```text
viz/paper_candidates/manisali_style/dense_y_manisali_3x6_with_ref3_plus_unet.png
```

Optional clean figure:

```text
viz/paper_candidates/manisali_style/dense_y_manisali_3x5_clean_ref3_plus_unet.png
```

---

## 11. Required metrics

Compute metrics for all displayed methods:

1. `ref3`
2. `ref9`
3. `BP`
4. `U-Net residual`
5. `ref3+U-Net`

For each, report:

* NMSE
* PSNR
* SSIM
* peak value
* support voxel count at the same threshold used in draw005
* support voxel count at `>= 0.10`, if this was used in draw005

Important:

`U-Net residual` metrics are not expected to be visually meaningful as reconstruction metrics.
Still record them for traceability, but mark them clearly as residual-only.

The key metric comparison is:

```text
ref3 vs ref3+U-Net
```

---

## 12. Required report content

Create:

```text
task_real_draw005b_report.md
```

The report must include the following sections.

### 12.1 Objective

State that draw005b adds the final corrected reconstruction:

```text
ref3 + U-Net residual
```

to the draw005 Manisali-style figure.

### 12.2 Relation to draw005

Explain that draw005 was visually successful but its last `U-Net` column represented residual compensation rather than the final reconstructed image.

### 12.3 Corrected reconstruction definition

Define explicitly:

```python
ref3_plus_unet = ref3 + u_net_residual
ref3_plus_unet = np.maximum(ref3_plus_unet, 0.0)
```

If a different exact implementation is used, document it.

### 12.4 Visualization design

State that draw005b preserves the draw005 Manisali-style rendering:

* translucent voxel-volume 3D rendering;
* dB MIP projections;
* same viewpoint;
* same cube;
* same color and normalization conventions.

### 12.5 Output inventory

List all generated figures and cache files.

### 12.6 Qualitative observations

Discuss:

* whether `ref3+U-Net` is visually more interpretable than residual-only U-Net;
* whether `ref3+U-Net` improves the Y-shape coherence over `ref3`;
* how `ref3+U-Net` compares visually with `ref9` and `BP`;
* whether the new final column is suitable for the manuscript.

### 12.7 Recommendation

Recommend whether the manuscript should use:

1. the 3×6 version with residual and corrected output, or
2. the clean 3×5 version with only final reconstruction outputs.

---

## 13. Acceptance criteria

This task is successful if and only if:

1. draw005 outputs are reused or exactly reproduced;
2. `ref3+U-Net` is computed explicitly;
3. the final column in the main composite figure is `ref3+U-Net`;
4. the residual-only U-Net panel is not mislabeled as a final reconstruction;
5. the draw005 Manisali-style rendering is preserved;
6. no scatter plot is used as the main 3D rendering;
7. a 3×6 composite figure is saved;
8. `ref3+U-Net` individual 3D and MIP figures are saved;
9. metrics are computed for `ref3+U-Net`;
10. a report is written.

---

## 14. Failure conditions

The task should be considered failed if:

1. the final column still shows only U-Net residual;
2. `ref3+U-Net` is not computed;
3. the main figure reverts to point-cloud/scatter rendering;
4. the visualization style differs substantially from draw005 without justification;
5. the report does not distinguish residual-only U-Net from final corrected reconstruction;
6. the corrected output is auto-scaled independently in a misleading way.

---

## 15. Final deliverable summary

The expected primary output is:

```text
exp/task_real_draw005b_ref3_plus_unet/<timestamp>/viz/paper_candidates/manisali_style/dense_y_manisali_3x6_with_ref3_plus_unet.png
```

The key scientific purpose is to make the learning-based correction visually interpretable by showing:

```text
ref3 + U-Net residual
```

rather than the residual field alone.

```


