# et_dataset_protocol

## Role

This document freezes the shape-family extended-target dataset protocol for `task_real_005`.
It is the ET counterpart to `CONTEXT/dataset_protocol.md`, which remains the frozen point-target protocol.

## Scope

- This version freezes the Phase ET-1 shape-family dataset only
- The physical front-end remains the frozen true cylindrical simulation plus Variant B reconstruction chain
- This document does not authorize physics consistency, real-data integration, or random Manisali-style ET generation

## Frozen Family Set

The Phase ET-1 dataset must include the following six families:

- `line`
- `cross`
- `L-shape`
- `double-line`
- `small_rect_edge`
- `point_cluster`

These six families are mandatory and cannot be removed or substituted.
Additional families may be appended later, but not at the expense of this frozen core set.

## Parameter Diversity Requirements

Each family must explicitly vary:

- size / support extent
- in-plane orientation
- placement in radius, azimuth, and height
- boundary proximity, including near-edge cases
- thickness or width
- gap, break, or spacing structure where applicable
- amplitude variation across the support
- multi-instance or multi-segment composition where the family definition permits it

The dataset builder must not generate simple template copies with only seed changes.

## Split Design

### Recommended Long-Term Formal Scale

Per family:

- `train = 1000`
- `val = 200`
- `test = 200`

### Frozen ET-1 Executed Scale For task_real_005

Per family:

- `train = 16`
- `val = 4`
- `test = 4`

Reason for reduced ET-1 scale:

- `task_real_005` is the first full true-cylindrical ET baseline pass
- each sample requires true sparse echo synthesis plus `ref3/ref5/ref7/ref9/BP` reconstruction
- the current priority is to freeze dataset structure, surface family-specific failures, and produce a trainable handoff manifest rather than to saturate final training scale

This reduced executed scale is frozen for `task_real_005` only.
If later tasks expand the ET dataset, they must do so by explicit protocol revision or addendum.

## Ground Truth Definition

- Ground truth is the voxel truth amplitude volume generated from the scene scatterer support
- GT must never be replaced by a BP image
- BP is retained only as the highest-quality traditional baseline in the current project

## Geometry And Simulation Constraints

The ET dataset must remain consistent with `CONTEXT/simulation_protocol.md`:

- cylindrical scan radius `R = 0.6 m`
- scene radius `X0 = 0.3 m`
- scene height `H = 2.0 m`
- Cartesian voxel spacing `5 mm` in `x/y`
- height spacing `4 mm` in `z`
- frequency and aperture sampling inherited from protocol v1

Family generation defines the target support only.
It must not alter the physical protocol, scan geometry, or forward model.

## Forward Model And Reconstruction Boundary

- Forward data origin must be true 3D cylindrical sparse echoes
- Forward simulator entry is `workspace.sim.forward_cylindrical_point`
- Traditional ET reconstruction must use the frozen accelerated front-end:
  - `Variant B = active windows + full-library sinc geometry correction`
- Baseline methods are:
  - `ref3`
  - `ref5`
  - `ref7`
  - `ref9`
  - `BP`

No 2D proxy family renderer, pseudo-reference image generator, or planar/MIMO adjoint front-end may replace this chain.

## Shape Construction Rules

The ET builder must construct each family from protocol-consistent scatterer sets on the frozen 3D voxel grid.
The current ET-1 family semantics are:

- `line`: one elongated thin support with variable length, orientation, width, and optional local break
- `cross`: two intersecting line supports with variable arm lengths and width
- `L-shape`: two orthogonal arms sharing one corner, with variable aspect ratio and width
- `double-line`: two roughly parallel thin supports with controlled separation and possible amplitude imbalance
- `small_rect_edge`: a small rectangle perimeter or partial perimeter placed preferentially near the outer radial envelope
- `point_cluster`: one or two compact point groups with varied density and amplitude spread

## Metadata Requirements

Every ET sample must record at least:

- sample id
- family
- split
- seed
- shape parameter dictionary
- placement parameters
- orientation parameter
- size parameters
- amplitude rule summary
- point count
- GT volume path
- sparse echo path after simulation

## Learning Handoff Intent

The dataset must support a future second-stage learning interface of the form:

- `RED_ref3 -> 3D U-Net -> GT amplitude`

Therefore the ET artifacts must preserve stable paths for:

- `ref3` coarse reconstruction volumes
- GT amplitude volumes
- split membership
- family labels for balancing or curriculum decisions

## Current Task Boundary

This ET protocol is frozen for `task_real_005` dataset generation and traditional baseline evaluation only.
It does not by itself approve network training, physics consistency constraints, or paper-scale final data volume.
