# Manisali-Inspired Synthetic Target Protocol for Cylindrical-Aperture 3-D Imaging

## 1. Purpose

This document defines a **Manisali-inspired synthetic target protocol** for the ReMiC-Net cylindrical-aperture 3-D imaging project.

The protocol is intended to support two different types of paper figures:

1. **Overall 3-D imaging figures**  
   These figures should provide a visually intuitive demonstration that the proposed cylindrical-aperture imaging pipeline can recover volumetric extended targets.

2. **Reference-surface mismatch compensation figures**  
   These figures should expose the structured mismatch caused by reduced-reference cylindrical imaging operators such as `ref3`, and should show whether the ordinary U-Net baseline or the final proposed method compensates this mismatch.

The key decision is:

> We borrow the *idea* of Manisali-style synthetic extended targets and 3-D visualization, but we do **not** directly copy Manisali's target generator, geometry, figures, or data distribution.

The target protocol must be adapted to the present problem:

- near-field cylindrical aperture;
- reference-surface approximation;
- `ref3/ref5/ref7/ref9/BP` comparison;
- magnitude reflectivity reconstruction;
- structured mismatch induced by radial deviation from reference surfaces.

---

## 2. Relation to Manisali et al.

The paper:

> I. Manisali, O. Oral, and F. S. Oktem, "Efficient physics-based learned reconstruction methods for real-time 3D near-field MIMO radar imaging," *Digital Signal Processing*, vol. 144, 104274, 2024.

uses synthetically generated extended targets and presents 3-D reconstruction results in a visually clear form.

However, the present project differs from Manisali et al. in several essential ways.

| Item | Manisali et al. | Present ReMiC-Net project |
|---|---|---|
| Imaging geometry | planar near-field MIMO | cylindrical-aperture near-field imaging |
| Grid | Cartesian 3-D voxel grid | cylindrical or cylindrical-derived 3-D imaging grid |
| Main physical issue | efficient learned reconstruction from MIMO observations | structured mismatch from reduced-reference cylindrical operators |
| Intermediate reconstruction | adjoint / physics-based backprojection-like image | `ref3` or other reduced-reference reconstruction |
| Learning objective | recover target magnitude from physics-based input | compensate reference-surface approximation mismatch |
| Target style | synthetic complex-valued extended targets with random phase | synthetic reflectivity volumes designed for cylindrical mismatch analysis |
| Primary figure role | demonstrate 3-D learned reconstruction quality | demonstrate both 3-D recovery and reference-surface compensation |

Therefore, this protocol should be described as:

> **Manisali-inspired**, not Manisali-reproduced.

---

## 3. Figure-use taxonomy

The same synthetic target family should not be forced to serve all scientific purposes. The manuscript should use at least two figure categories.

### 3.1 Category A — Overall 3-D imaging figure

Purpose:

- show visually appealing 3-D recovery;
- demonstrate that the method works on volumetric extended targets;
- provide a figure comparable in spirit to existing learned near-field imaging papers.

Recommended target style:

- connected or semi-connected 3-D volumetric target;
- irregular but visually interpretable;
- moderate radial span;
- not too sparse;
- not too dense.

Recommended methods to show:

1. GT
2. `ref3`
3. `ref9`
4. `BP`
5. ordinary U-Net baseline
6. final proposed method, if available

If the first-round experiment only compares four methods, use:

1. `ref3`
2. `ref9`
3. `BP`
4. ordinary U-Net baseline

### 3.2 Category B — Reference-surface mismatch compensation figure

Purpose:

- expose why reduced-reference cylindrical imaging fails;
- show that mismatch varies with radial deviation from the nearest reference surface;
- show how learning-based compensation improves the `ref3` result.

Recommended target style:

- two isolated points, one near a reference surface and one far from a reference surface;
- Y-shaped extended target crossing different radial mismatch regions;
- random extended target constrained to span reference-surface-friendly and reference-surface-unfriendly radial regions;
- optional local zoom-in, radial profile, or error map.

This category is the core evidence for the paper's main scientific claim.

---

## 4. Core design principles

### 4.1 Extended target means volumetric support, not a few sparse points

In this protocol, an extended target must not be constructed as only a small number of isolated point scatterers.

A valid extended target should satisfy at least one of the following:

- connected 3-D support;
- semi-connected 3-D support with nearby components;
- a thickened curve, surface, or letter-like shape;
- an irregular volumetric blob;
- a multi-blob object with physically plausible spatial continuity.

A target made of only 2-10 isolated points is a **point-target diagnostic sample**, not an extended target.

### 4.2 Use synthetic reflectivity volume terminology

The generated object should be called:

- `synthetic reflectivity volume`;
- `voxelized reflectivity target`;
- `synthetic volumetric extended target`.

Avoid implying that the synthetic target is a precise physical material geometry. The support region represents the effective reflectivity support used for imaging evaluation.

### 4.3 Preserve the cylindrical-aperture problem

Targets should be generated in the coordinate convention used by the project. If the internal reconstruction grid is cylindrical, target construction should respect:

- radial coordinate;
- azimuth coordinate;
- height coordinate;
- reference-surface placement;
- nearest-reference deviation.

For visualization, the target may be converted to Cartesian coordinates, unfolded cylindrical views, maximum projections, or volume rendering.

### 4.4 Separate beauty from diagnosis

A visually attractive 3-D figure is not necessarily the best figure for proving mismatch compensation.

Therefore:

- use Category A figures for overall quality;
- use Category B figures for compensation evidence;
- do not force one figure to do everything.

---

## 5. Target families

The protocol defines four target families.

---

### 5.1 Family P — Point-target diagnostic samples

Purpose:

- diagnose PSF, defocus, localization, and reference-surface mismatch;
- not intended as the main extended-target figure.

Recommended construction:

- one or two point scatterers;
- at least one point near a reference surface;
- at least one point far from the nearest reference surface;
- points separated in azimuth and/or height to avoid visual merging.

Required metadata:

- point coordinates;
- nearest reference surface index;
- radial deviation from nearest reference surface;
- whether each point is reference-surface-friendly or reference-surface-unfriendly.

Use in paper:

- compensation diagnosis;
- PSF-style figure;
- local profile curve.

Do not use this family as the main 3-D extended-target demonstration.

---

### 5.2 Family S — Structured shape targets

Purpose:

- provide visually interpretable extended targets;
- show shape preservation and deformation.

Recommended examples:

- Y-shaped target;
- T-shaped target;
- arc-shaped target;
- ring segment;
- curved strip;
- crossed branches.

Recommended construction:

1. define a skeleton curve or graph in cylindrical or Cartesian coordinates;
2. thicken the skeleton into a 3-D tube;
3. assign magnitude reflectivity to the tube voxels;
4. optionally apply mild amplitude variation;
5. optionally apply boundary smoothing.

For the Y-shaped target:

- the bifurcation should be visible;
- branches should be thin enough to reveal blur and distortion;
- at least one branch should extend across radial mismatch regions;
- avoid making the entire target lie exactly on a reference surface.

Use in paper:

- qualitative comparison;
- local zoom-in around bifurcation;
- profile across a branch;
- mismatch compensation figure.

---

### 5.3 Family R — Random volumetric extended targets

Purpose:

- provide Manisali-inspired overall 3-D target appearance;
- demonstrate recovery of irregular volumetric objects.

Recommended construction strategies:

#### Strategy R1 — Random ellipsoid union

1. sample `K` ellipsoid centers within the valid imaging region;
2. give each ellipsoid random semi-axis lengths;
3. combine them by union;
4. enforce connectedness or near-connectedness;
5. optionally smooth the boundary;
6. normalize reflectivity magnitude.

Typical configuration:

- `K = 3-8`;
- each ellipsoid occupies a moderate local volume;
- ellipsoids should overlap or nearly touch;
- avoid producing a set of completely disconnected dots.

#### Strategy R2 — Random-walk tube

1. sample a 3-D random path;
2. constrain it inside the imaging region;
3. thicken the path into a tube;
4. optionally branch the path;
5. optionally add local blobs around the path.

This produces an irregular but connected extended object.

#### Strategy R3 — Thresholded smooth random field

1. generate a smooth random 3-D field;
2. threshold it to create a support mask;
3. keep the largest connected component;
4. optionally apply dilation/erosion;
5. normalize reflectivity magnitude.

This can produce organic-looking random volumetric targets.

Recommended first choice:

> Use Strategy R1 for the first Manisali-inspired overall 3-D figure because it is simple, controllable, and easy to reproduce.

Use in paper:

- overall 3-D imaging figure;
- visual comparison across methods;
- maximum-projection figure.

---

### 5.4 Family C — Compensation-aware random extended targets

Purpose:

- bridge the gap between visually attractive random volumetric targets and mismatch-sensitive diagnostic targets.

Construction:

- start from Family R;
- require the support to span both reference-surface-friendly and reference-surface-unfriendly radial regions;
- enforce nontrivial radial thickness;
- ensure part of the object is near a reference surface and part is far from the nearest reference surface.

Required checks:

- support voxels should cover at least two radial mismatch bins;
- support should include voxels with small nearest-reference deviation;
- support should include voxels with large nearest-reference deviation;
- if available, support should cover different `P_cyc` bins.

Use in paper:

- qualitative figure that looks like an extended target but still exposes reference-surface mismatch;
- optional error map and profile analysis.

Recommended for ReMiC-Net:

> Family C should be the main random extended-target family for the paper, because it is closer to the paper's scientific problem than a purely generic random blob.

---

## 6. Reflectivity magnitude and phase protocol

### 6.1 Magnitude field

The basic target is a magnitude reflectivity volume:

\[
\rho(\mathbf{r}) \ge 0.
\]

For most figures, use normalized magnitude:

\[
0 \le \rho(\mathbf{r}) \le 1.
\]

Recommended magnitude modes:

| Mode | Description | Recommended use |
|---|---|---|
| M0 | binary magnitude: 0 outside support, 1 inside support | diagnostics and clean figures |
| M1 | soft boundary magnitude | overall 3-D figures |
| M2 | random amplitude variation inside support | realism-oriented extended targets |
| M3 | material-region amplitude variation | future advanced experiments |

For first-round paper figures:

- use M0 for point and Y-shaped diagnostics;
- use M1 or M2 for Manisali-inspired overall targets.

### 6.2 Phase field

A complex reflectivity can be written as:

\[
x(\mathbf{r}) = \rho(\mathbf{r}) \exp(j\phi(\mathbf{r})).
\]

Recommended phase modes:

| Mode | Description | Recommended use |
|---|---|---|
| P0 | zero phase or real nonnegative reflectivity | clean baseline, easiest to interpret |
| P1 | i.i.d. random phase, \(\phi \sim U(0, 2\pi)\) | Manisali-inspired realism |
| P2 | spatially correlated random phase | future realism study |
| P3 | material/region-dependent phase | not recommended for current paper |

Recommended first-round decision:

- Use P0 for mismatch diagnosis figures.
- Use both P0 and P1 only if the codebase supports complex-valued forward simulation robustly.
- If the learning target is magnitude-only, report evaluation against \(|x|\), not complex \(x\).

Important:

> Do not introduce random phase into the main figure if it makes the compensation mechanism harder to interpret.

---

## 7. Reference-surface-aware constraints

Because the present paper is about reduced-reference cylindrical imaging, random targets should not be sampled blindly.

For each generated target, compute or record:

- nearest reference surface index;
- radial deviation from nearest reference surface;
- normalized radial mismatch bin;
- optional phase-cycle deviation `P_cyc`;
- fraction of support voxels in each mismatch bin.

### 7.1 Mismatch-bin coverage

Define three informal bins:

| Bin | Meaning |
|---|---|
| B0 | near reference surface; expected low mismatch |
| B1 | medium radial deviation |
| B2 | far from reference surface; expected high mismatch |

A compensation-aware target should satisfy:

- support fraction in B0 > 0;
- support fraction in B2 > 0;
- B2 fraction should not be negligible.

Recommended threshold for first experiments:

- B0 support fraction ≥ 10%;
- B2 support fraction ≥ 10%.

The exact thresholds can be adjusted according to the reference-surface layout.

### 7.2 Avoid trivial target placement

Avoid targets that:

- lie entirely on one reference surface;
- lie entirely in a very easy imaging region;
- are too small to reveal structured mismatch;
- are too dense and large, making all methods visually similar;
- contain too many disconnected tiny components.

---

## 8. Visualization protocol

### 8.1 Overall 3-D rendering

For Manisali-inspired overall figures, use one or both of:

1. 3-D volume rendering;
2. 3-D isosurface / voxel rendering.

Recommended settings:

- show physical coordinate axes;
- use the same spatial bounds for all methods;
- use the same intensity normalization for a given target;
- show GT if possible;
- show ref3, ref9, BP, and U-Net under identical rendering settings.

Suggested method order:

1. GT
2. ref3
3. ref9
4. BP
5. U-Net

If the final proposed method differs from U-Net baseline, use:

1. GT
2. ref3
3. ref9
4. BP
5. U-Net baseline
6. proposed method

### 8.2 Maximum projection

Use maximum projection as a compact 2-D summary of a 3-D volume:

\[
I_{\max}(u,v) = \max_w I(u,v,w).
\]

Recommended projection views:

- top / azimuth-range view;
- range-height view;
- azimuth-height view;
- or the closest equivalents in the cylindrical coordinate system.

Important:

- maximum projection can hide depth-dependent errors;
- use it for overview, not as the only proof of compensation.

### 8.3 Slice views

Use slice views for compensation diagnosis:

- radial slice;
- azimuthal slice;
- height slice;
- slice through the target center;
- slice crossing a high-mismatch region.

Slice views are often more useful than volume rendering for showing reference-surface compensation.

### 8.4 Local zoom-in

Use local zoom-in for:

- two-point diagnostics;
- Y-shaped bifurcation;
- thin branches;
- far-from-reference regions;
- high-error regions.

### 8.5 Normalization

For fair comparison:

- use the same display range across methods for the same target;
- do not let each panel auto-scale independently unless clearly labeled;
- save both linear and dB/log versions if necessary;
- use the same threshold for 3-D rendering across methods.

Recommended:

- linear display for support shape;
- dB/log display for sidelobes and weak artifacts;
- same-scale version as the primary figure.

---

## 9. Recommended figure plan for the manuscript

### Figure Group 1 — Overall 3-D reconstruction

Target:

- Family R or Family C random volumetric extended target.

Methods:

- GT;
- ref3;
- ref9;
- BP;
- U-Net baseline;
- final method if available.

Views:

- 3-D volume rendering;
- optional maximum projection.

Scientific message:

> The learned compensation framework can reconstruct visually coherent 3-D volumetric targets in cylindrical-aperture imaging.

### Figure Group 2 — Reference-surface mismatch diagnosis

Target:

- Family P two-point target.

Methods:

- ref3;
- ref9;
- BP;
- U-Net baseline;
- final method if available.

Views:

- local slice;
- radial profile;
- optional PSF-like plot.

Scientific message:

> Reduced-reference reconstruction error depends strongly on radial deviation from the nearest reference surface.

### Figure Group 3 — Structured extended-target compensation

Target:

- Family S Y-shaped target;
- or Family C compensation-aware random target.

Views:

- slice or maximum projection;
- local zoom-in;
- error map.

Scientific message:

> The learned method compensates structured mismatch not only for isolated points but also for extended structures.

---

## 10. Implementation requirements

Each generated synthetic target should save a metadata file.

Recommended file:

```text
sample_spec.json
```

Required fields:

```json
{
  "target_id": "example_id",
  "target_family": "R",
  "target_subtype": "ellipsoid_union",
  "grid_shape": [],
  "coordinate_system": "cylindrical_or_cartesian",
  "support_voxel_count": 0,
  "support_fraction": 0.0,
  "magnitude_mode": "M1",
  "phase_mode": "P0",
  "random_seed": 0,
  "reference_surface_config": {},
  "mismatch_bin_fractions": {
    "B0_near_reference": 0.0,
    "B1_medium": 0.0,
    "B2_far_reference": 0.0
  },
  "notes": ""
}
```

For random targets, also save:

- random seed;
- number of components;
- component centers;
- component sizes;
- post-processing steps;
- connected-component statistics.

---

## 11. Acceptance criteria for a valid Manisali-inspired target

A target is valid for the overall 3-D figure if:

1. it is a 3-D volumetric reflectivity target;
2. it is not a sparse point set;
3. it has reproducible generation metadata;
4. it fits within the valid imaging field of view;
5. it can be reconstructed by ref3/ref9/BP/U-Net without special-case code;
6. it can be visualized using consistent 3-D rendering settings.

A target is valid for compensation analysis if, in addition:

1. it spans different radial mismatch regions;
2. it includes both near-reference and far-from-reference voxels;
3. it produces visible differences between ref3 and higher-quality references;
4. it does not hide errors due to excessive thickness or excessive projection overlap.

---

## 12. Recommended first Codex implementation

For the first implementation round, do not attempt to reproduce Manisali's full data generator. Instead implement:

### Target A — Manisali-inspired overall target

- Family R1: random ellipsoid union;
- magnitude mode M1 or M2;
- phase mode P0 initially;
- optional P1 if complex forward simulation is stable;
- output GT + reconstructions;
- render using volume rendering and max projection.

### Target B — Compensation-aware random target

- Family C derived from R1;
- enforced radial mismatch-bin coverage;
- magnitude mode M1;
- phase mode P0;
- output same methods;
- render using slice + max projection + optional zoom-in.

### Target C — Y-shaped target

- Family S;
- branch crosses radial mismatch regions;
- magnitude mode M0 or M1;
- phase mode P0;
- output same methods;
- render using slice + zoom-in.

---

## 13. Recommended terminology for the paper

Use:

- "Manisali-inspired volumetric synthetic targets";
- "voxelized synthetic reflectivity volumes";
- "random volumetric extended targets";
- "reference-surface-aware extended targets";
- "compensation-aware target design."

Avoid:

- "we use Manisali's target generator" unless the exact generator is actually used;
- "extended target generated by several points";
- "real object geometry" when only synthetic reflectivity support is defined;
- "random blob" in formal paper text.

Suggested sentence:

> Inspired by the volumetric synthetic targets used in learning-based near-field radar imaging, we construct voxelized reflectivity volumes with connected or semi-connected support regions. Unlike generic random targets, a subset of the generated targets is constrained to span different radial deviations from the nearest reference surface, thereby exposing the structured mismatch induced by reduced-reference cylindrical reconstruction.

---

## 14. Known risks and mitigations

### Risk 1 — The overall 3-D figure looks good but does not prove compensation

Mitigation:

- put compensation evidence in separate figures;
- include mismatch-aware targets and local profiles.

### Risk 2 — Random phase makes the figure harder to interpret

Mitigation:

- start with P0;
- add P1 only as an ablation or supplementary experiment.

### Risk 3 — Maximum projection hides radial errors

Mitigation:

- include slice views;
- include zoom-in or profile plots.

### Risk 4 — Target is too easy

Mitigation:

- enforce radial mismatch coverage;
- include far-from-reference support.

### Risk 5 — Target is too hard or visually chaotic

Mitigation:

- control component count;
- use connected-component filtering;
- tune thickness and amplitude variation.

---

## 15. Summary decision

The project is ready to produce **Manisali-inspired 3-D overall effect figures**, provided that the target generator is adapted to cylindrical-aperture imaging rather than copied directly.

The recommended path is:

1. do not directly reuse Manisali's generator;
2. build a cylindrical-reference-aware volumetric target protocol;
3. use Manisali-like visualization for overall 3-D quality;
4. use mismatch-sensitive targets for compensation evidence;
5. clearly separate these two figure roles in the manuscript.
