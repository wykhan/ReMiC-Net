# task_real_draw001 — Round-1 Effect Figure Drawing Experiment

## Task Title
Round-1 qualitative figure drawing experiment for ReMiC-Net paper effect figures

## Background
This repository contains the project for real cylindrical physics-guided learned 3D imaging.

A blueprint file already exists in the repository:

- `remic_net_effect_figure_design_recommendations.md`

This file should be treated as the primary blueprint for effect-figure planning.  
The current task is to start the **first round of figure-drawing experiments** for the SCI manuscript.

The goal is **not** to beautify figures first, but to produce a scientifically useful first round of qualitative comparison results that can help decide which figure design is most valuable for the paper.

---

## Frozen decision for this task
For this task, the method named **“U-Net”** must be interpreted as:

- **the current main learning method’s ordinary U-Net baseline version**
- not ReMiC-Net with extra conditioning
- not the stronger FiLM / RSB-FiLM / ReMiC-Net branch
- not a future improved variant

This task is specifically for comparing:

1. `ref3`
2. `ref9`
3. `BP`
4. `U-Net` (ordinary U-Net baseline)

---

## Main goal
Based on the blueprint file `remic_net_effect_figure_design_recommendations.md`, select one figure type suitable for the **first-round qualitative comparison experiment**.

The preferred figure type for this round is:

### Selected figure type
**Multi-method qualitative comparison figure**

More concretely:

- rows = target types
- columns = methods

Recommended layout:

- **3 rows × 4 columns**
- rows:
  1. two isolated points
  2. Y-shaped target
  3. random extended target
- columns:
  1. ref3
  2. ref9
  3. BP
  4. U-Net

This first-round figure should help judge whether this qualitative figure family is useful enough to be retained in the paper.

---

## Required target types

### 1) Two isolated points
Construct one sample containing **two independent point targets**.

Requirements:
- the two points must be spatially separated
- one point should be located **on or near a reference surface**
- the other point should be located **far from the nearest reference surface**
- avoid placing them too close in azimuth/height such that they visually merge
- this sample should be designed to reveal structured mismatch sensitivity with respect to reference-surface approximation

Purpose:
- compare localization sharpness
- compare defocus / blur
- compare whether the learning method compensates mismatch better than ref3

---

### 2) Y-shaped target
Construct one sample with a **Y-shaped extended target**.

Requirements:
- thin branches are preferred
- keep the fork / bifurcation structure clear
- avoid making the target too thick, otherwise structural differences may be visually hidden
- ensure the shape is sufficiently extended so that structure preservation can be observed

Purpose:
- compare branch continuity
- compare tip sharpness
- compare whether small structural details are preserved
- compare whether ref3 induces visible distortion that may be compensated by learning

---

### 3) Random extended target
Construct one sample of a **random extended target** in a style similar in spirit to the extended targets used in Manisali-style demonstrations.

Requirements:
- irregular shape
- connected or semi-connected extended structure
- moderate complexity
- not overly sparse like a point set
- not too large and dense to the point that all methods look similar
- keep this sample representative of “extended-target” behavior rather than simple point behavior

Purpose:
- provide a more realistic qualitative test
- examine shape fidelity and clutter/artifact behavior
- help assess whether the learning method’s advantage extends beyond point targets

Important note:
- do **not** copy copyrighted figure artwork
- instead generate a new synthetic random extended target inspired only by the general style of irregular extended targets

---

## Methods to run
For **each** of the three target types above, generate reconstructions using:

1. `ref3`
2. `ref9`
3. `BP`
4. `U-Net`

Thus the required minimum output is:

- 3 target types × 4 methods = **12 qualitative reconstruction images**

---

## Figure production requirements

### A. Single-image outputs
For each target type and each method, save an individual figure.

Naming suggestion:
- `point_ref3.*`
- `point_ref9.*`
- `point_bp.*`
- `point_unet.*`
- `y_ref3.*`
- ...
- `random_ext_unet.*`

Preferred formats:
- `.png` for convenient inspection
- optionally `.pdf` if plotting pipeline makes this easy

---

### B. Composite figure
Assemble the 12 images into one composite figure:

- **3 rows × 4 columns**
- rows correspond to target type
- columns correspond to method

Suggested row labels:
- Two isolated points
- Y-shaped target
- Random extended target

Suggested column labels:
- ref3
- ref9
- BP
- U-Net

This composite figure is a primary deliverable.

Suggested filename:
- `qualitative_comparison_3x4.png`
- optionally `qualitative_comparison_3x4.pdf`

---

### C. Normalization / display consistency
For each target type:
- use a **consistent display normalization across all four methods**
- do not let each panel auto-scale independently if that would make cross-method visual comparison misleading
- if needed, also save one “same-color-scale” version explicitly

If there is a strong reason to provide both:
- same-scale version
- individually optimized display version

then save both, but the **same-scale comparison** is the priority.

---

### D. Ground-truth handling
If easy and scientifically useful, also save the ground-truth image for each target type.

This can be either:
- saved separately, or
- optionally assembled into an auxiliary 3×5 figure with the first column as GT

However, for this task, the **minimum required composite figure is still 3×4**.  
GT is recommended but optional.

---

### E. Optional zoom-ins
If the first-round outputs suggest that important differences are subtle, optionally produce local zoom-in crops for:
- the two-point sample
- the Y-shaped bifurcation region

This is optional in this round, not mandatory.

---

## Scientific intent of this task
This is a **paper-figure exploration task**, not a benchmark task.

The purpose is to determine:
1. whether this figure family is worth keeping in the paper
2. whether the selected target designs make the differences between methods visible
3. which target type is most informative
4. whether ref3 vs ref9 vs BP vs U-Net produces the expected qualitative hierarchy
5. whether further follow-up figures (zoom-in, error map, profile plots, etc.) are justified

Therefore, besides generating images, provide a short scientific interpretation.

---

## What to read before implementation
Before coding or plotting, read and use:

1. `remic_net_effect_figure_design_recommendations.md`
2. any current project protocol documents needed to stay consistent with the repo’s imaging/reconstruction setup
3. existing code for `ref3`, `ref9`, `BP`, and the ordinary U-Net baseline

If the blueprint file is missing or inconsistent, stop and report clearly.

---

## Expected implementation strategy
Use the existing repository codebase if possible.

Try to reuse:
- target generation utilities
- reconstruction runners
- model inference scripts
- visualization utilities

If some small helper scripts are missing, create minimal additional scripts in a clean and traceable way.

Avoid large refactors unless absolutely necessary.

---

## Reproducibility requirements
Save all outputs under a new experiment directory, e.g.:

- `exp/task_real_draw001_<timestamp>/`

Recommended contents:

- `task_real_draw001_report.md`
- `sample_specs.json`
- `render_config.json`
- `qualitative_comparison_3x4.png`
- optional auxiliary figures
- all 12 single-panel images
- any scripts created specifically for this task
- logs if relevant

The report should clearly record:
- what target definitions were used
- where the two points were placed
- how the Y-shape was parameterized
- how the random extended target was generated
- which model checkpoint was used for U-Net
- what visualization normalization was used
- key qualitative observations

---

## Required report content
Create:

- `exp/task_real_draw001_<timestamp>/task_real_draw001_report.md`

The report must include:

### 1. Task objective
Explain that this is the first-round effect-figure drawing experiment for the manuscript.

### 2. Figure type selected from blueprint
State that the selected first-round figure type is a multi-method qualitative comparison figure.

### 3. Target construction summary
Describe each of:
- two isolated points
- Y-shaped target
- random extended target

### 4. Methods used
List:
- ref3
- ref9
- BP
- U-Net baseline

### 5. Output inventory
List all major generated figures and files.

### 6. Qualitative observations
Discuss, at minimum:
- whether ref3 degradation is visible
- whether ref9 is closer to BP
- whether U-Net improves over ref3
- whether advantages differ between point and extended targets
- which target type is most informative for the paper

### 7. Recommendation for next round
Recommend one of:
- keep this figure family and refine it
- keep but redesign target definitions
- drop this figure family and switch to another blueprint figure

---

## Acceptance criteria
This task is successful if and only if:

1. the blueprint file is read and used as guidance
2. three target types are generated:
   - two isolated points
   - Y-shaped target
   - random extended target
3. four methods are run on each:
   - ref3
   - ref9
   - BP
   - U-Net baseline
4. at least 12 single-panel reconstruction images are saved
5. one composite **3×4** comparison figure is saved
6. a report is written
7. outputs are placed in a traceable experiment directory under `exp/`

---

## Important caveats
- Do not substitute U-Net with a stronger model variant.
- Do not silently change the target definitions to easier cases.
- Do not over-beautify figures at the cost of scientific comparability.
- Do not use per-panel normalization that destroys fair visual comparison unless also providing a same-scale version.
- Do not copy Manisali’s exact figure artwork; only imitate the general idea of an irregular synthetic extended target.

---

## Final deliverable summary
The final expected deliverables are:

1. a reproducible experiment folder under `exp/task_real_draw001_<timestamp>/`
2. 12 single-panel qualitative reconstruction images
3. one 3×4 composite comparison figure
4. one markdown report with observations and next-step recommendation
