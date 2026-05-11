# task_real_draw002 — Reader-Readable Qualitative Figure Redesign

## Task Title
Second-round paper-figure drawing experiment for reader-readable qualitative reconstruction and mismatch-compensation visualization

---

## Background

The previous task `task_real_draw001` successfully produced a first-round qualitative comparison figure and verified that the overall figure family is scientifically useful. However, the main limitation of `task_real_draw001` is **readability for readers and reviewers**.

The draw001 figure used:

- `rho-z max-over-theta` projections
- rows = target types
- columns = methods

This was useful as an internal diagnostic view, but it is **not sufficiently intuitive as a manuscript figure**, because:

1. readers cannot directly recognize the target shape
2. readers may not understand that the displayed image is a projection in cylindrical coordinates
3. readers may not see where “structured mismatch compensation” happens
4. readers may not know how to interpret the Y-shaped target or the random extended target from the compressed projection alone
5. point-target qualitative panels are not visually reader-friendly and should not be used as the primary manuscript figure family

Therefore, the current task is to redesign the qualitative figure family so that:

- a reader can **first understand what target is being imaged**
- a reader can **then see how different methods differ**
- a reviewer can **clearly identify where ref3 fails and where U-Net compensates**
- the final figure family becomes closer to a **paper-ready candidate**

---

## Relationship to previous task

Use the outputs and lessons from:

- `PROMPTS/task_real_draw001.md`
- `exp/task_real_draw001_qualitative/...`

In particular:

- keep the same interpretation of `U-Net`
- reuse the successful target-design logic where appropriate
- preserve the insight that `rho-z` views are useful for mechanism diagnosis
- improve readability rather than simply duplicating draw001

Important:

This task is a **follow-up redesign task**, not a complete reset.

---

## Frozen definition of methods

For this task, the compared methods must remain exactly:

1. `ref3`
2. `ref9`
3. `BP`
4. `U-Net`

Where:

- `U-Net` means the **ordinary residual 3D U-Net baseline**
- it is **not** the RSB-FiLM / ReMiC-Net branch
- it is **not** a stronger follow-up variant
- it should be consistent with the baseline definition already used in draw001

Do not silently change the learning method.

---

## Main goal

Redesign the qualitative figure outputs so that they become **reader-readable** and **reviewer-readable**.

The key redesign principle is:

> Readers should first see the target shape clearly, and only then see the structured mismatch and compensation mechanism.

Therefore, the new figure family should separate:

1. **shape-readable qualitative reconstruction views**
2. **mechanism-oriented mismatch-diagnosis views**

The manuscript figure should no longer rely on `rho-z` projection alone.

---

## Core scientific objective

This task should answer the following visual questions clearly:

1. What does the target actually look like?
2. How does `ref3` distort or degrade the target?
3. How close are `ref9` and `BP` to the target structure?
4. How much does `U-Net` recover the structure relative to `ref3`?
5. Where exactly is the compensation happening?
6. Is the compensation visually meaningful in terms of shape continuity / branch preservation / artifact suppression / radial correction?

---

## Target selection for draw002

### Keep as primary targets
Use the following two target classes as the **main targets** for draw002:

1. **Y-shaped target**
2. **Random connected extended target**

Reason:
- these are the most useful reader-facing extended-target cases
- they better support the paper’s main story than isolated points
- they are more appropriate for qualitative reconstruction figures

### Point target policy
Do **not** use the two-point target as the primary qualitative panel in the main draw002 figure family.

The point target may optionally be used only as:
- a supplementary diagnostic figure
- a radial profile / peak-shift analysis figure
- an appendix/internal figure if needed

But it is **not** the main focus of draw002.

---

## Required figure families

This task must generate **three figure families**.

---

# Figure Family A — Shape-readable reconstruction figure

## Purpose
This is the primary reader-facing manuscript figure.

Its purpose is to let a reader immediately understand:
- what the target looks like
- which method preserves the shape best
- what kind of degradation ref3 causes

## Required content
For each of the two primary targets:
- Y-shaped target
- random connected extended target

generate a shape-readable comparison across:

- GT
- ref3
- ref9
- BP
- U-Net

## Recommended visualization style
Use one of the following, preferring the most readable option supported by the codebase:

### Preferred
- **3D isosurface rendering**
or
- **3D volume rendering**

### Acceptable fallback
- **multi-view MIP / projection views**
  such as:
  - view 1: x-y projection
  - view 2: x-z projection
  - view 3: y-z projection
or the cylindrical equivalents if needed

### Important requirement
The chosen rendering must allow a human reader to visually recognize:
- the Y-shaped structure
- the irregular extended structure

If a single-view rendering is not sufficiently informative, use a compact multi-view display.

## Layout suggestion
For each target, preferred column layout:

- GT
- ref3
- ref9
- BP
- U-Net

If using multi-view rendering, keep the method layout clear and consistent.

## Output requirement
Produce at least one **paper-candidate figure** for Figure Family A.

Suggested filenames:
- `familyA_shape_readable_y.png`
- `familyA_shape_readable_random_ext.png`
- optionally one combined figure:
  - `familyA_shape_readable_combined.png`

---

# Figure Family B — Mechanism-oriented mismatch-diagnosis figure

## Purpose
This figure explains **why** the methods differ, especially:
- reference-surface mismatch
- radial smearing / displacement
- structure recovery by U-Net

This figure should reuse the useful idea from draw001:
- `rho-z`-style diagnostic projection

But the redesign must make it much more interpretable.

## Required content
At minimum, do this for the **Y-shaped target**.
Optionally also do it for the random extended target if the result is informative.

## Required panel content
For each selected target, show:
- GT
- ref3
- ref9
- BP
- U-Net

using a diagnostic projection such as:
- `rho-z max-over-theta projection`

## Mandatory readability upgrades
Compared with draw001, this figure must include **reader aids**, such as:

1. **GT contour / skeleton overlay**
2. **reference-surface markers** (e.g., ref3 radii lines)
3. **local ROI boxes** indicating important regions
4. optional arrows or text annotations indicating:
   - radial smearing
   - mismatch region
   - branch distortion
   - recovered branch / recovered continuity

At least items 1 and 2 are mandatory.

## Main diagnostic ROI
For the Y-shaped target, prioritize:
- the bifurcation / fork region
- branch tips
- any clearly mismatched radial region

## Output requirement
Produce at least one paper-candidate figure for Figure Family B.

Suggested filenames:
- `familyB_mechanism_y_rhoz.png`
- `familyB_mechanism_random_ext_rhoz.png`
- optionally:
  - `familyB_mechanism_combined.png`

---

# Figure Family C — Local zoom and error-map figure

## Purpose
This figure should make the compensation behavior obvious to reviewers.

It should answer:
- where exactly does ref3 fail?
- where exactly does U-Net recover?
- is the error visibly reduced?

## Required content
At minimum, do this for the **Y-shaped target**.

Optionally also do it for the random extended target if useful.

## Required panel types
For the selected target, provide:

### Row 1
local zoom reconstruction panels around the most informative ROI:
- ref3
- ref9
- BP
- U-Net
- optionally GT

### Row 2
corresponding error maps relative to GT:
- `|ref3 - GT|`
- `|ref9 - GT|`
- `|BP - GT|`
- `|U-Net - GT|`

### Optional Row 3
a compensation map such as:
- `|U-Net - ref3|`
or
- residual correction visualization

## Mandatory requirements
- the ROI must be chosen deliberately, not arbitrarily
- the ROI must be scientifically justified in the report
- normalization across methods must be fair and documented
- if contours help, overlay GT contour on the zoomed reconstructions

## Output requirement
Produce at least one paper-candidate figure for Figure Family C.

Suggested filenames:
- `familyC_zoom_error_y.png`
- `familyC_zoom_error_random_ext.png`

---

## Optional supplementary figure

### Supplementary point-target diagnostic figure
This is optional, not mandatory.

If implemented, use the two-point target only for:
- radial profile comparison
- peak location comparison
- radial shift / blur diagnosis

Do not present the point target as the main qualitative “image-like” figure.

Suggested outputs:
- `supp_point_profile.png`
- `supp_point_peak_shift.png`

---

## Data / target-generation guidance

### Reuse policy
You may reuse the draw001 target definitions if they remain suitable.

### Adjustments allowed
You may refine the target generation if needed, especially for readability:
- thicken the Y branches slightly if they are too visually weak
- make the random extended target more connected and more shape-like
- avoid targets that become visually unrecognizable after projection or rendering

### Important constraints
- do not make the targets too easy
- do not make the Y target so thick that structural differences disappear
- do not make the random extended target so dense that all methods look similar
- maintain scientific continuity with draw001

If target modifications are made, document them clearly.

---

## Rendering / visualization requirements

### General requirements
- all figures must be visually interpretable by a reader unfamiliar with the internal diagnostic pipeline
- panel titles and labels must be clear
- axis labels must be included where appropriate
- legends / colorbar labels must be included where needed
- use consistent normalization rules and document them

### For shape-readable figures
- prioritize shape recognizability over strict adherence to draw001 display format
- if using thresholding / isosurfaces, explain threshold selection
- if using MIP views, ensure the target remains interpretable

### For mechanism figures
- preserve the radial mismatch axis when useful
- clearly mark reference surfaces
- use overlays and annotations

### For error maps
- use a consistent error color scale within a figure
- clearly state whether the error is absolute amplitude error or another metric

---

## Output directory

Save all outputs under a new experiment directory, e.g.:

- `exp/task_real_draw002_qualitative/<timestamp>/`

Recommended structure:

- `task_real_draw002_report.md`
- `draw002_manifest.json`
- `metrics_draw002.json` (if metrics are produced)
- `viz/paper_candidates/familyA/...`
- `viz/paper_candidates/familyB/...`
- `viz/paper_candidates/familyC/...`
- `viz/progress/...`
- `dataset/...` if new target definitions are created
- any scripts created specifically for this task

---

## Required implementation behavior

Use and extend the repository codebase cleanly.

Prefer to reuse:
- draw001 reconstruction logic
- target generation utilities
- plotting helpers
- existing reconstruction and U-Net inference pipeline

Create minimal additional scripts as needed.

Suggested script name:
- `workspace/eval/task_real_draw002_qualitative.py`

Avoid large refactors unless necessary.

---

## Required report content

Create:

- `exp/task_real_draw002_qualitative/<timestamp>/task_real_draw002_report.md`

The report must contain the following sections.

### 1. Task objective
Explain that draw002 is a second-round redesign focused on reader-readable figures.

### 2. Summary of draw001 limitation
Explicitly state why draw001 was not sufficiently reader-friendly.

### 3. Figure families implemented
List:
- Figure Family A
- Figure Family B
- Figure Family C
- optional supplementary point-target figure if produced

### 4. Target definitions
Describe:
- Y-shaped target
- random connected extended target
- any modifications relative to draw001

### 5. Visualization choices
Document:
- rendering mode
- projection mode
- normalization
- threshold / contour settings
- ROI selection for zooms
- error-map definition

### 6. Reader-interpretability assessment
For each figure family, evaluate:
- can a reader recognize the target shape?
- can a reader understand method differences?
- can a reviewer identify the mismatch and compensation region?
- is the figure close to paper-ready?

### 7. Scientific interpretation
Discuss:
- how ref3 degrades the target
- whether ref9 is closer to BP
- whether U-Net visibly recovers structure
- whether the compensation is easy to interpret visually
- which figure family is strongest for the manuscript

### 8. Recommendation for manuscript use
Recommend:
- which figure should be the primary qualitative figure
- which should be a supplementary or mechanism figure
- whether another follow-up draw003 task is needed

---

## Acceptance criteria

This task is successful if and only if:

1. it explicitly addresses the reader-readability limitation of draw001
2. it keeps method scope fixed to:
   - ref3
   - ref9
   - BP
   - ordinary U-Net baseline
3. it uses Y-shaped and random extended target as primary qualitative targets
4. it produces **Figure Family A** (shape-readable figure)
5. it produces **Figure Family B** (mechanism-oriented diagnostic figure)
6. it produces **Figure Family C** (local zoom + error-map figure)
7. it writes a report explaining which figure family is strongest
8. outputs are stored under a traceable `exp/` directory
9. the resulting figures are substantially more interpretable than draw001

---

## Important caveats

- Do not silently substitute U-Net with ReMiC-Net or RSB-FiLM.
- Do not rely only on rho-z projection for the main figure.
- Do not keep point-target qualitative panels as the main reader-facing figure.
- Do not generate visually pretty but scientifically vague figures.
- Do not omit GT context where it is necessary for interpretation.
- Do not use per-panel normalization in a misleading way.
- Do not remove diagnostic power in the name of aesthetics.
- Do not create arbitrary zoom regions; they must be scientifically motivated.

---

## Final expected deliverables

The final expected deliverables are:

1. a reproducible experiment folder under `exp/task_real_draw002_qualitative/<timestamp>/`
2. at least one paper-candidate figure for **Figure Family A**
3. at least one paper-candidate figure for **Figure Family B**
4. at least one paper-candidate figure for **Figure Family C**
5. a report evaluating which figure family is strongest for the manuscript
6. optional supplementary point-target diagnostic figure(s), if useful

---

## Preferred end state

After this task, the project should be able to answer:

- “Which qualitative figure should go into the main paper?”
- “Which figure best shows structure-preserving compensation?”
- “Which figure best helps readers understand the target shape?”
- “Which figure best helps reviewers understand structured mismatch correction?”
