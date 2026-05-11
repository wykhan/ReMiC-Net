# task_real_draw003 — 3D Rotated Thick-Y Reader-Readable Figure Experiment

## Task Title
Third-round qualitative figure experiment for a reader-readable, 3D-recognizable, thick-Y target and mechanism-oriented mismatch-compensation visualization

---

## Background

The previous tasks established the following:

### draw001
`task_real_draw001` verified that a qualitative comparison figure family is scientifically useful, but its `rho-z max-over-theta` projections were not reader-friendly.

### draw002
`task_real_draw002` improved readability by splitting the figure design into:

- **Family A**: shape-readable views
- **Family B**: mechanism-oriented diagnostic views
- **Family C**: local zoom + error / correction views

This was a meaningful step forward. However, the remaining limitation is now clear:

> The current Y-shaped target is still too close to a thin point-built skeleton rather than a clearly recognizable 3D object with thickness.

As a result:
- readers may still not perceive the target as a true object
- qualitative figures still do not fully match the intuition of a “3D imaging paper”
- the current target is not strong enough as a visually compelling main manuscript figure

Therefore, the next step is to **upgrade the target itself**, not merely the rendering.

---

## Core redesign idea

The central idea of draw003 is:

> Replace the thin Y-skeleton target with a **standard, recognizable, thick Y-shaped 3D object**, optionally rotated in 3D space, and use that object to generate reader-readable manuscript figures.

This should make the manuscript figure stronger because:
1. the target becomes immediately recognizable to readers
2. the target behaves as a true extended object rather than a sparse point skeleton
3. thickness helps reveal structural preservation or distortion
4. 3D rotation creates a more realistic and visually informative imaging scenario
5. 3D perspective views become meaningful and attractive
6. mechanism figures become easier to interpret because readers already understand the underlying object

---

## Frozen method definition

The compared methods must remain:

1. `ref3`
2. `ref9`
3. `BP`
4. `ref3 + U-Net`

Important:

- `U-Net` here still means the **ordinary residual 3D U-Net baseline**
- it is **not** ReMiC-Net / RSB-FiLM
- it is **not** a stronger learned variant
- in all qualitative figures, the final learning-based reconstruction must be shown as the **final compensated result**, not the residual alone

Use a reader-facing label such as:

- `ref3 + U-Net`
or
- `Learned compensation (ref3 + U-Net)`

Do **not** label the final panel simply as `U-Net` if that would obscure that it is a residual compensation result.

---

## Main goal

Create a new figure family centered on a **thick, rotated, recognizable 3D Y-shaped target**, such that:

- readers can immediately understand the object shape
- readers can visually compare reconstruction quality across methods
- reviewers can identify mismatch distortion and compensation
- the resulting figure family becomes significantly closer to a manuscript-ready qualitative figure

This task is primarily about:
- **target redesign**
- **object-recognizable rendering**
- **reader-readable manuscript figures**
- **mechanism-linked follow-up views**

---

## Required target design

## Primary target
The primary target in draw003 must be a:

### **thick 3D Y-shaped object**

This target should satisfy the following design requirements.

### Geometric requirements
- clearly recognizable as the letter **Y**
- have **finite thickness**, not only a one-voxel or one-line skeleton
- behave like a compact extended target / reflectivity body
- include:
  - a trunk
  - two branches
- have branch width and/or volume thickness sufficient to make the target visually readable in 3D and in projections

### Thickness requirements
The target must not be too thin.
It should be thick enough that:
- the object appears as an actual body
- local blur / smearing / shape distortion can be visually judged
- the target remains recognizable in MIP and perspective views

At the same time:
- do not make it excessively thick, or the fine structural differences between methods may disappear

### Rotation requirements
The target should be rotated in 3D space to make the geometry more realistic and visually informative.

Recommended approach:
- apply rotation around multiple axes, e.g. x / y / z
- example style:
  - small-to-moderate rotation about x
  - moderate rotation about y
  - moderate rotation about z

Exact angles need not match this example, but the target should:
- not be perfectly axis-aligned
- not lie trivially in a single principal plane
- not become so tilted that it becomes visually confusing

### Recommended object placement
Place the rotated thick-Y target so that:
- part of the structure lies near a ref3 reference radius
- part of the structure lies between reference radii
- the object spans a meaningful range in:
  - radial direction
  - azimuth-related direction
  - height direction

This is important because the figure should still be able to reveal structured mismatch behavior.

---

## Optional secondary target

If time and implementation complexity allow, an optional secondary target may also be created:

- a **thick rotated irregular extended target**

However, this is **optional**.
The main mandatory focus of draw003 is the **thick rotated Y target**.

If only one target is completed well, that is acceptable.

Quality is more important than number of targets.

---

## Figure families to produce

draw003 should produce **three figure families**, similar in spirit to draw002, but now centered on the improved target.

---

# Figure Family A — Primary reader-facing object-recognizable figure

## Purpose
This is the main candidate for the manuscript’s qualitative reconstruction figure.

It must let a reader immediately see:
- what the target object is
- what its 3D orientation is
- how different methods reconstruct it
- whether the learned compensation improves the visible structure

## Required content
For the thick rotated Y target, show:

- GT
- ref3
- ref9
- BP
- ref3 + U-Net

## Preferred visualization style
Use one or more of the following, prioritizing reader readability:

### Preferred
- **3D perspective rendering**
- **3D isosurface view**
- **3D volume rendering**

### Strongly recommended addition
Also include **multi-view projections** or **MIPs**, such as:
- xy
- xz
- yz

The ideal outcome is either:
- one compact figure that includes both perspective and multi-view support
or
- one main perspective figure and one auxiliary multi-view figure

## Important requirement
The target orientation should be understandable.
If necessary, also include a small “GT object only” inset to show the intended target pose.

## Output requirement
Produce at least one paper-candidate figure, e.g.:

- `familyA_primary_thickY_perspective.png`
- `familyA_primary_thickY_multiview.png`
- optionally a combined figure:
  - `familyA_primary_thickY_combined.png`

---

# Figure Family B — Mechanism-oriented mismatch-compensation figure

## Purpose
This figure explains the structured mismatch mechanism and the compensation behavior.

It should connect the reader-readable object view to the radial mismatch interpretation.

## Required content
For the thick rotated Y target, produce a diagnostic figure using:
- `rho-z max-over-theta` projection
or another similarly appropriate diagnostic projection

Show:
- GT
- ref3
- ref9
- BP
- ref3 + U-Net

## Mandatory readability aids
This mechanism figure must include:
1. GT contour or skeleton overlay
2. ref3 reference-surface markers
3. ROI box around the key distortion/compensation region
4. labels or annotations if useful

## Key diagnostic region
Prioritize the most informative region, such as:
- Y bifurcation / fork
- branch tips
- branch region crossing inter-reference radii
- a region where ref3 visibly smears or shifts structure

## Output requirement
Produce at least one paper-candidate figure, e.g.:

- `familyB_mechanism_thickY_rhoz.png`

---

# Figure Family C — Local zoom + error + correction figure

## Purpose
This is the reviewer-facing evidence figure.

It should explicitly show:
- where ref3 fails
- where BP/ref9 are better
- where `ref3 + U-Net` changes the image
- whether the final compensated result becomes closer to GT

## Required content
For the thick rotated Y target, choose a scientifically meaningful ROI and show:

### Row 1
zoomed reconstruction:
- GT
- ref3
- ref9
- BP
- ref3 + U-Net

### Row 2
absolute error to GT:
- GT cell may be blank or marked as reference
- `|ref3-GT|`
- `|ref9-GT|`
- `|BP-GT|`
- `|ref3+U-Net-GT|`

### Row 3
correction / change relative to ref3:
- GT cell may be blank
- ref3 cell may be marked baseline
- `|ref9-ref3|`
- `|BP-ref3|`
- `|(ref3+U-Net)-ref3|`

## Mandatory requirements
- the ROI must be justified and documented
- the ROI should ideally center on the fork / branch continuity / radial distortion region
- normalization must be fair and documented
- GT contour overlay is recommended on the reconstruction row

## Output requirement
Produce at least one paper-candidate figure, e.g.:

- `familyC_zoom_error_thickY.png`

---

## Optional supplementary point-target diagnostic figure

This remains optional.

If implemented, it should only serve as a supplementary mechanism check, not a main qualitative figure.

Allowed supplementary uses:
- radial profile
- peak shift
- blur width
- side-lobe comparison

Do not make it the main figure.

---

## Required implementation detail: final learning result

This must be enforced consistently in both code and figure labeling:

### Correct learning-based figure content
The learning-based reconstruction panel must represent:

\[
\hat{x}_{\text{final}} = x_{\text{ref3}} + \Delta x_{\text{U-Net}}
\]

That is:
- the final compensated reconstruction
- not the residual alone

### Reader-facing naming
Use labels such as:
- `ref3 + U-Net`
- `Learned compensation`
- `Compensated result`

Avoid labels that could make readers think the network directly reconstructs from scratch.

---

## Target-generation guidance

## Recommended construction strategy
Construct the thick Y target as a compact 3D object rather than a single-line skeleton.

Possible ways include:
- building a voxelized Y-shaped solid
- dilating a clean Y skeleton into a volumetric object
- creating cylindrical/rectangular branch primitives and merging them
- generating a binary mask then assigning reflectivity amplitude within the occupied region

Any of these are acceptable as long as the final target:
- is clearly recognizable
- has controllable thickness
- behaves as an extended object

## Reflectivity assignment
You may use:
- uniform reflectivity
or
- mildly varying reflectivity

But keep the object visually interpretable.
Avoid making the target too texturally complex.

## Rotation implementation
Apply controlled 3D rotation to the thick-Y object before embedding it into the scene.

Document:
- how the object is defined
- how thickness is defined
- what rotation angles are used
- how the object is positioned relative to the cylindrical coordinate scene

---

## Rendering requirements

## General principles
The figures must prioritize:
1. reader readability
2. scientific interpretability
3. fair method comparison

## For Family A
- object recognizability is the top priority
- perspective view should be visually clear
- if one perspective view is insufficient, add multi-view MIPs
- keep method layout consistent

## For Family B
- preserve diagnostic value
- clearly indicate reference surfaces
- clearly indicate GT support / contour
- clearly show the ROI of interest

## For Family C
- choose a compact but informative crop
- use clearly readable error maps
- use consistent scales within each row of comparison

---

## Output directory

Save all outputs under:

- `exp/task_real_draw003_qualitative/<timestamp>/`

Recommended contents:

- `task_real_draw003_report.md`
- `draw003_manifest.json`
- `metrics_draw003.json`
- `dataset/...` if a new target definition is generated
- `viz/paper_candidates/familyA/...`
- `viz/paper_candidates/familyB/...`
- `viz/paper_candidates/familyC/...`
- `viz/progress/...`
- helper scripts if needed

Suggested implementation script:
- `workspace/eval/task_real_draw003_qualitative.py`

---

## Required report content

Create:

- `exp/task_real_draw003_qualitative/<timestamp>/task_real_draw003_report.md`

The report must contain the following sections.

### 1. Task objective
Explain that draw003 upgrades the target itself to a thick rotated 3D Y object.

### 2. Why draw002 was not yet sufficient
State that draw002 improved rendering and annotation, but the underlying Y target was still too skeleton-like.

### 3. Thick-Y target design
Describe:
- how the thick Y object was built
- how thickness was chosen
- how rotation was applied
- how the object was positioned in the imaging scene

### 4. Figure families implemented
List:
- Family A
- Family B
- Family C
- optional supplementary figures if any

### 5. Visualization choices
Document:
- rendering style
- MIP or perspective choices
- ROI selection
- normalization
- contour / annotation settings
- how `ref3 + U-Net` was displayed

### 6. Reader-interpretability assessment
Evaluate:
- whether the object is immediately recognizable
- whether the 3D orientation is understandable
- whether the difference between methods is visually clear
- whether the learned compensation is easier to understand than in draw002

### 7. Scientific interpretation
Discuss:
- how ref3 distorts the thick rotated Y
- whether ref9 is closer to BP
- whether `ref3 + U-Net` improves visible structure
- whether the object thickness helps expose structural distortion or recovery
- which figure family is strongest

### 8. Recommendation for manuscript use
Recommend:
- which figure should be the main paper qualitative figure
- which should be the mechanism figure
- whether a draw004 is needed
- whether the next step should replace `ref3 + U-Net` with the true ReMiC-Net / RSB-FiLM method

---

## Acceptance criteria

This task is successful if and only if:

1. a clearly recognizable **thick rotated Y-shaped 3D target** is created
2. the learning-based result is displayed as **ref3 + U-Net**, not residual alone
3. a reader-facing **Family A** figure is produced
4. a mechanism-oriented **Family B** figure is produced
5. a reviewer-facing **Family C** figure is produced
6. the resulting figure family is more object-readable than draw002
7. outputs are reproducibly stored under `exp/task_real_draw003_qualitative/...`
8. the report explains whether the thick-Y redesign meaningfully improved the manuscript figure quality

---

## Important caveats

- Do not silently change the learning method to ReMiC-Net or RSB-FiLM.
- Do not display residual-only U-Net output as if it were the final reconstruction.
- Do not make the thick Y target so thick that all methods look similar.
- Do not make the target so thin that it becomes a skeleton again.
- Do not choose a trivial axis-aligned pose.
- Do not overcomplicate the target with unnecessary texture.
- Do not omit diagnostic support (Family B / Family C) in favor of only pretty 3D views.
- Do not sacrifice fair comparison for aesthetics.

---

## Final expected deliverables

The final expected deliverables are:

1. a reproducible experiment folder under `exp/task_real_draw003_qualitative/<timestamp>/`
2. a new thick rotated Y target definition
3. at least one paper-candidate **Family A** figure
4. at least one paper-candidate **Family B** figure
5. at least one paper-candidate **Family C** figure
6. a report evaluating whether the thick-Y redesign improved readability and manuscript suitability

---

## Preferred end state

After this task, the project should be able to answer:

- “Is a thick rotated Y object better than the skeleton Y for the manuscript?”
- “Can readers now immediately understand what object is being imaged?”
- “Can reviewers now see where mismatch distortion happens and where compensation acts?”
- “Is this figure family strong enough to become the main qualitative figure in the paper?”
- “Should the next step switch the learning-based panel from ordinary U-Net to the true ReMiC-Net / RSB-FiLM result?”
