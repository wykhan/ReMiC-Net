
task_real_draw005c.md
```


````md
# task_real_draw005c — Add x-z view, tip-to-reference-surface analysis, and Trans-level figure interpretation for the dense Y Manisali-style figure

## Task Title
Extend draw005b by adding the missing x-z projection, analyzing the three Y tips relative to the nearest reference surfaces, and producing a Trans-level SCI interpretation centered on the figure.

---

## 1. Background

`task_real_draw005b` produced a highly satisfactory Manisali-style dense-volume qualitative figure for the continuous Y-shaped target, including:

- 3D volumetric rendering,
- x-y projection,
- z-y projection,
- method columns including `ref3+U-Net`.

The current figure is visually strong and should be retained as the main stylistic baseline.

However, three follow-up questions must now be addressed:

1. The current figure includes 3D, x-y, and z-y views, but it still lacks the third orthogonal view, namely **x-z**.
2. The current figure suggests a nontrivial relationship between the Y geometry and the reduced-reference operators:
   - in `ref3`, only one upper tip is visible, while the other upper tip and the lower tip are not clearly visible;
   - in `ref9`, the two upper tips are visible, but the lower tip is still not clearly visible.
3. A Trans-level manuscript needs a more rigorous and polished scientific interpretation of this figure.

This task addresses all three.

---

## 2. Clarification of view requirement

The user request mentions:

> “在3D、x-y、z-y中，再补充进x-y的结果”

Based on the immediate prior discussion, this is interpreted as:

> Add the missing **x-z** view.

Therefore, the new figure must include:

1. 3D volumetric rendering
2. x-y projection
3. z-y projection
4. x-z projection

Do **not** duplicate x-y.
Use **x-z** as the newly added fourth row.

---

## 3. Main objectives

This task has three goals.

### Goal A — Add the missing x-z view
Extend the draw005b figure by adding the **x-z** projection while preserving the existing Manisali-style rendering and layout logic.

### Goal B — Perform tip-to-reference-surface analysis
Analyze the three key Y landmarks:

1. left upper tip
2. right upper tip
3. lower tip

For each tip, compute its distance to the nearest reference surface and explain how these distances help interpret the `ref3` and `ref9` visual results.

### Goal C — Produce Trans-level figure interpretation
Produce a polished SCI-grade interpretation suitable for a TGRS / Trans-level manuscript, including:

- figure caption candidate,
- main-text interpretation paragraph(s),
- method-result explanation focused on the structured mismatch phenomenon.

---

## 4. Reuse scope

Use draw005b as the direct source baseline.

Primary source experiment:

```text
exp/task_real_draw005b_ref3_plus_unet/
````

Read and reuse as much as possible from the completed draw005 / draw005b outputs and scripts.

Prefer reusing:

* the same dense Y target,
* the same dense forward simulation,
* the same ref3/ref9/BP/U-Net/ref3+U-Net volumes,
* the same rendering viewpoint and style,
* the same normalization and dB projection conventions.

Do not redesign the figure style unless necessary.

---

## 5. Required method columns

The figure should retain the same method comparison logic as draw005b.

Required columns:

1. `GT`
2. `ref3`
3. `ref9`
4. `BP`
5. `U-Net residual`
6. `ref3+U-Net`

If a cleaner version is desired, it may also optionally generate:

1. `GT`
2. `ref3`
3. `ref9`
4. `BP`
5. `ref3+U-Net`

But the required main deliverable should preserve the richer draw005b logic.

---

## 6. Required view rows

The updated figure must include four rows:

1. **3D volumetric rendering**
2. **x-y projection**
3. **z-y projection**
4. **x-z projection**  ← new addition

This gives the recommended main layout:

```text
4 × 6 composite figure
```

Suggested primary filename:

```text
dense_y_manisali_4x6_with_xz_and_ref3_plus_unet.png
```

Also save PDF if feasible:

```text
dense_y_manisali_4x6_with_xz_and_ref3_plus_unet.pdf
```

Optional clean version:

```text
dense_y_manisali_4x5_clean_with_xz_and_ref3_plus_unet.png
```

---

## 7. Visualization style to preserve

Preserve the draw005 / draw005b visual style.

Key style elements:

* dense reflectivity volume;
* Manisali-style image-cube appearance;
* translucent voxel-volume or equivalent continuous volumetric rendering;
* dB maximum projections;
* same viewpoint for 3D row;
* same spatial bounds and same cube;
* same dB display conventions;
* same projection normalization logic.

Do **not** revert to point-cloud or scatter-plot style.

The x-z row should match the visual policy of the x-y and z-y rows.

---

## 8. Tip landmark analysis

### 8.1 Required landmarks

Explicitly define and analyze three Y-tip landmarks:

1. **left upper tip**
2. **right upper tip**
3. **lower tip**

Use the same Y geometry that generated the dense target. Ideally derive the tip coordinates directly from the Y control points / skeleton used in draw005.

If necessary, map each ideal tip to the nearest voxel center in the dense GT grid.

### 8.2 Required distance analysis

For each tip, compute:

* 3D physical coordinate
* cylindrical coordinates (`rho`, `theta`, `z`)
* distance to the nearest `ref3` reference surface
* index / value of the nearest `ref3` reference surface
* distance to the nearest `ref9` reference surface
* index / value of the nearest `ref9` reference surface

This is important:

* do not compute only one generic “nearest surface”;
* compute the nearest reference-surface distance **separately for ref3 and ref9**.

### 8.3 Required output table

Create a table similar to:

| Tip |  x |  y |  z | rho | theta | nearest ref3 radius | dist to ref3 | nearest ref9 radius | dist to ref9 |
| --- | -: | -: | -: | --: | ----: | ------------------: | -----------: | ------------------: | -----------: |

Save it in:

* the report,
* and optionally as a CSV or JSON file for reproducibility.

Suggested filename:

```text
tip_reference_surface_analysis.csv
```

or

```text
tip_reference_surface_analysis.json
```

---

## 9. Required interpretation of ref3 and ref9

The report must explicitly analyze the following two questions.

### 9.1 ref3 interpretation

Explain:

> Why does the `ref3` figure show only one upper tip clearly, while the other upper tip and the lower tip are not clearly visible?

The explanation must be grounded in:

* tip positions,
* distance to nearest ref3 surfaces,
* projection geometry,
* visibility in x-y / z-y / x-z rows,
* possible thresholding and structured mismatch effects.

The explanation must not be vague. It should make a concrete argument such as:

* one upper tip lies closer to a favorable `ref3` reference-surface region;
* the other upper tip is farther from the nearest ref3 surface and is therefore more affected by structured mismatch;
* the lower tip may be degraded because it lies in an unfavorable radial region and/or its energy is spread by ref3, causing it to fall below the display threshold.

You do not have to force this exact conclusion, but the report must provide a rigorous evidence-based interpretation.

### 9.2 ref9 interpretation

Explain:

> Why does the `ref9` figure show the two upper tips, but still not the lower tip clearly?

Again, ground the explanation in:

* tip-to-ref9 distances,
* remaining mismatch patterns,
* shape orientation,
* projection effects,
* possible rendering threshold effects.

The report should clarify whether:

* ref9 improves the upper branches because the target tips are better supported by the denser reference-surface set;
* the lower tip still remains difficult because of residual mismatch, weaker local response, or projection/rendering suppression.

---

## 10. Optional but strongly recommended local diagnostics

To strengthen the explanations, generate optional supporting local diagnostics around the three tips.

Recommended outputs:

1. local zoom-ins around each tip for:

   * GT
   * ref3
   * ref9
   * BP
   * ref3+U-Net

2. local peak / amplitude readout at each tip neighborhood

3. optional small table showing, for each tip:

   * local peak value
   * local support voxel count above display threshold
   * whether the tip is visually retained in each method

This is not mandatory if it becomes cumbersome, but it is strongly recommended because it will make the interpretation more defensible.

---

## 11. Required Trans-level SCI figure interpretation

This task must produce manuscript-ready scientific interpretation centered on this figure.

### 11.1 Required outputs

Produce three polished text artifacts:

#### A. Figure caption candidate

A concise but Trans-level caption suitable for direct use in the manuscript.

#### B. Main-text interpretation paragraph(s)

One or two polished paragraphs that explain:

* the figure layout,
* the qualitative differences among methods,
* the relationship to structured mismatch,
* the meaning of the missing or preserved Y tips.

#### C. Insight summary

A short bullet list or paragraph summarizing the scientific takeaways.

### 11.2 Writing level

The writing must be suitable for a TGRS / Trans-level paper:

* concise but technically grounded;
* no overclaiming;
* specific and interpretable;
* able to explain both the visual strengths and the method limitations.

### 11.3 Required content points

The Trans-level interpretation should explicitly address:

1. why multiple orthogonal views are necessary;
2. why x-z is useful and what additional information it provides;
3. how the reduced-reference operators preserve or lose different parts of the Y shape;
4. why ref9 improves over ref3 but still does not fully recover the lower tip;
5. why showing `ref3+U-Net` is more interpretable than showing residual-only U-Net.

---

## 12. Output directory

Create a new experiment directory:

```text
exp/task_real_draw005c_tip_analysis/<timestamp>/
```

Recommended contents:

```text
task_real_draw005c_report.md
draw005c_manifest.json
tip_reference_surface_analysis.csv
tip_reference_surface_analysis.json
trans_level_figure_interpretation.md
metrics_draw005c.json
```

Figure outputs:

```text
viz/paper_candidates/manisali_style/dense_y_manisali_4x6_with_xz_and_ref3_plus_unet.png
viz/paper_candidates/manisali_style/dense_y_manisali_4x6_with_xz_and_ref3_plus_unet.pdf
viz/paper_candidates/manisali_style/single_mip/*_xz_mip.png
viz/paper_candidates/manisali_style/local_tip_zoomins/
```

Optional clean figure:

```text
viz/paper_candidates/manisali_style/dense_y_manisali_4x5_clean_with_xz_and_ref3_plus_unet.png
```

---

## 13. Required report content

Create:

```text
task_real_draw005c_report.md
```

The report must include the following sections.

### 13.1 Objective

Explain that draw005c extends draw005b by:

* adding x-z,
* analyzing Y tips relative to ref3 / ref9 reference surfaces,
* and producing Trans-level figure interpretation.

### 13.2 Relation to draw005b

State clearly that the draw005b figure style is retained and only analytically extended.

### 13.3 Added x-z view

Explain:

* why x-z was previously missing,
* why it is now added,
* what additional geometric information it provides.

### 13.4 Tip definition

Define:

* left upper tip,
* right upper tip,
* lower tip.

Describe how their coordinates were obtained.

### 13.5 Tip-to-reference-surface distances

Provide the required table and discuss:

* nearest ref3 distance,
* nearest ref9 distance,
* which tip is more or less favorably located for each method.

### 13.6 Visual interpretation of ref3

Explicitly answer:

* why one upper tip remains visible,
* why the other upper tip is weakened or lost,
* why the lower tip is weakened or lost.

### 13.7 Visual interpretation of ref9

Explicitly answer:

* why both upper tips are visible,
* why the lower tip remains weak or absent.

### 13.8 Figure-level scientific interpretation

Provide the polished SCI-grade interpretation and summarize the figure’s scientific message.

### 13.9 Recommendation

Recommend whether this figure and analysis should:

* be included in the main paper,
* be used as a main figure + supporting explanation,
* or be split into main-text figure and supplementary note.

---

## 14. Required standalone interpretation file

Create:

```text
trans_level_figure_interpretation.md
```

This file should contain:

1. **Figure caption candidate**
2. **Main-text interpretation**
3. **Brief discussion note for the manuscript**
4. **Optional Chinese explanation note for internal use**

The English text should be publication-oriented.

---

## 15. Acceptance criteria

This task is successful if and only if:

1. the draw005b figure style is preserved;
2. the missing x-z row is added;
3. the main composite figure becomes 4×6 (or equivalent with the required rows and columns);
4. the three Y tips are explicitly identified;
5. tip-to-ref3 and tip-to-ref9 nearest-surface distances are both computed;
6. the report explicitly explains the ref3 and ref9 visibility differences;
7. a Trans-level SCI interpretation is written;
8. the outputs are saved in a traceable experiment directory.

---

## 16. Failure conditions

The task should be considered failed if:

1. x-z is not added;
2. tip analysis is qualitative only and does not compute distances;
3. the analysis does not distinguish ref3 from ref9;
4. the report does not explicitly answer the “one upper tip / two upper tips / no lower tip” questions;
5. the interpretation remains informal or debug-style rather than SCI-grade;
6. the visual style is substantially changed without justification.

---

## 17. Final deliverable summary

The expected primary outputs are:

1. an updated 4×6 Manisali-style figure with the added x-z row;
2. a reproducible tip-to-reference-surface analysis for the three Y tips;
3. an explicit explanation of the ref3 and ref9 visual asymmetries;
4. a Trans-level SCI-grade figure interpretation.

The most important final outputs are:

```text
exp/task_real_draw005c_tip_analysis/<timestamp>/viz/paper_candidates/manisali_style/dense_y_manisali_4x6_with_xz_and_ref3_plus_unet.pdf
exp/task_real_draw005c_tip_analysis/<timestamp>/task_real_draw005c_report.md
exp/task_real_draw005c_tip_analysis/<timestamp>/trans_level_figure_interpretation.md
```



