# task_real_draw004 — Manisali-Inspired 3D Overall Imaging Figure with a Complete Y-Shaped Target

## Task Title
Draw a Manisali-inspired 3D overall qualitative imaging figure for cylindrical-aperture 3-D imaging using a visually complete Y-shaped volumetric target.

---

## 1. Task objective

This task aims to generate a **Manisali-inspired 3D overall imaging figure** for the ReMiC-Net manuscript.

The figure should emphasize:

1. the overall 3-D reconstruction capability of the cylindrical-aperture imaging pipeline;
2. the visual completeness and interpretability of the reconstructed volumetric target;
3. a presentation style comparable in spirit to Manisali-style learned 3-D imaging figures.

This task is **not** primarily a mismatch-compensation diagnosis task.  
Its primary purpose is to create a strong **overall 3-D qualitative figure**.

---

## 2. Required context files

Before implementation, read and follow:

1. `CONTEXT/manisali_inspired_target_protocol.md`
2. `remic_net_effect_figure_design_recommendations.md`
3. any relevant project protocol documents related to current cylindrical imaging and reconstruction workflow
4. current scripts / code for:
   - `ref3`
   - `ref9`
   - `BP`
   - ordinary U-Net baseline

If any of the above files are missing or inconsistent, stop and report clearly.

---

## 3. Main design goal

Create a **single visually strong Y-shaped volumetric extended target** and reconstruct it using multiple methods, then present the results in a **Manisali-inspired 3D visualization style**.

The resulting figure should answer:

- Can the cylindrical-aperture pipeline reconstruct a complete 3-D Y-shaped target?
- How do `ref3`, `ref9`, `BP`, and ordinary U-Net compare in overall visual quality?
- Can the learned baseline recover a more complete and visually coherent 3-D target than `ref3`?

---

## 4. Target specification

### 4.1 Required target type
Use a **Y-shaped volumetric extended target**.

This Y-shaped target must be:

- visually complete;
- aesthetically clean and interpretable;
- clearly recognizable as the letter **Y**;
- volumetric, not just a few sparse points;
- suitable for 3-D volume rendering;
- suitable for 2-D maximum-projection visualization.

### 4.2 Geometric requirements
The Y-shaped target should satisfy:

1. it has a clear trunk and two upper branches;
2. the bifurcation region is visually clean;
3. each branch has nonzero thickness;
4. the target is not too thin to disappear in rendering;
5. the target is not too thick to become a blob;
6. the whole target should lie fully inside the valid imaging region;
7. the target should occupy a moderate portion of the scene, not too small and not too close to the boundaries.

### 4.3 Visual preference
The Y-shaped target should look:

- complete;
- balanced;
- smooth;
- elegant;
- suitable for use as a manuscript figure.

This is an **overall 3-D figure**, so visual quality matters.

### 4.4 Recommended construction
Use the target-family guidance from `manisali_inspired_target_protocol.md`, especially the structured-shape target family.

Recommended construction procedure:

1. define a Y-shaped centerline / skeleton;
2. thicken the skeleton into a 3-D tubular support;
3. optionally smooth the boundary;
4. assign reflectivity magnitude values;
5. optionally use mild amplitude variation inside the support;
6. save target-generation metadata.

### 4.5 Recommended magnitude / phase mode
For this task, use a simple and robust choice unless there is a strong reason otherwise:

- magnitude mode: `M1` or `M0`
- phase mode: `P0`

That is:

- use a clean magnitude reflectivity volume;
- avoid random phase in the first round unless already well supported and stable.

The purpose of this figure is visual clarity, not phase realism.

---

## 5. Methods to compare

At minimum, reconstruct the same Y-shaped target using:

1. `ref3`
2. `ref9`
3. `BP`
4. ordinary `U-Net` baseline

Important:
- here, `U-Net` means the **current main learning method’s ordinary U-Net baseline version**
- do **not** substitute it with ReMiC-Net, FiLM, RSB-FiLM, or any stronger variant unless explicitly added as an extra panel

Optional:
- if the current project has a finalized proposed method ready and it is easy to include, you may generate an additional comparison version
- however, the minimum required deliverable remains the four methods above

---

## 6. Visualization requirements

### 6.1 Main figure style
The figure should be **Manisali-inspired** in presentation style.

This means:

- emphasize overall 3-D shape recovery;
- use visually clear 3-D rendering;
- optionally include maximum-projection views;
- produce a figure suitable for manuscript use.

Do **not** copy Manisali’s exact figure layout or artwork.  
Instead, create a new figure in a similar spirit.

### 6.2 Required visual outputs
Produce the following outputs.

#### A. 3-D rendering for each method
For the Y-shaped target, produce one 3-D rendering for each of:

- GT (strongly recommended)
- ref3
- ref9
- BP
- U-Net

If GT is not shown in the main composite figure, it should still be saved separately.

#### B. 2-D maximum-projection views
Produce maximum-projection views for the same target and methods.

Recommended projections:
- one top-like view;
- one side-like view;

Use the most suitable projections for the cylindrical reconstruction representation.

#### C. Composite figure
Produce at least one main composite figure suitable for paper drafting.

Recommended primary layout:

- columns: `GT | ref3 | ref9 | BP | U-Net`
- rows:
  - row 1: 3-D rendering
  - row 2: max-projection view 1
  - row 3: max-projection view 2

This gives a recommended **3 × 5** figure.

If layout constraints make this impractical, a reduced but still manuscript-usable layout is acceptable, such as:
- one row of 3-D renderings
- one row of projections

But the preferred output is a richer comparison figure.

### 6.3 Rendering consistency
For fair comparison:

- use the same viewpoint for all 3-D renderings;
- use the same spatial bounds;
- use the same normalization or thresholding strategy across methods for the same target;
- do not auto-scale each panel independently in a misleading way;
- use a consistent rendering threshold for the reconstructed volume, unless a justified correction is necessary.

### 6.4 Figure quality
The final composite figure should be:

- clean;
- readable;
- balanced;
- suitable for direct manuscript insertion after minor polishing.

Avoid clutter and overly technical debug-style layouts.

---

## 7. Scope of this task

This task is **not** intended to fully analyze mismatch compensation.

Therefore:

- the target does **not** need to be deliberately optimized to maximize ref3 failure;
- the main goal is not local error diagnosis;
- local zoom-in and error maps are optional, not required.

This task is specifically for the **overall 3-D qualitative figure family**.

---

## 8. Recommended scientific message

The figure should support a statement like:

> A Manisali-inspired volumetric Y-shaped target is reconstructed using the reduced-reference cylindrical operators and the learning-based baseline. The comparison visually demonstrates the overall 3-D reconstruction capability of the cylindrical-aperture pipeline, and shows that the learned baseline produces a more coherent volumetric recovery than the low-complexity `ref3` backbone.

Do not overclaim.

---

## 9. Implementation requirements

### 9.1 Experiment folder
Create a new experiment directory:

```text
exp/task_real_draw004_<timestamp>/
