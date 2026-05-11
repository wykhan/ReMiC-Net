# et_dataset_protocol_800

## Goal

Freeze the task_real_006d family-aware formal dataset at the literature-scale budget:

- main train = 800
- main val = 100
- main test = 100
- unseen-parameter OOD = 100
- leave-one-family-out focused OOD = 100
- random-ET OOD = 100

All data remain true 3D cylindrical simulation data under the existing protocol-v1 forward model and the frozen Variant B / ref3 reconstruction route.

## Family set

- `line`
- `cross`
- `L-shape`
- `double-line`
- `small_rect_edge`
- `point_cluster`

## Main split allocation

### Train 800

- `point_cluster = 180`
- `line = 160`
- `L-shape = 160`
- `cross = 110`
- `double-line = 100`
- `small_rect_edge = 90`

### Val 100

- `point_cluster = 20`
- `line = 20`
- `L-shape = 20`
- `cross = 15`
- `double-line = 15`
- `small_rect_edge = 10`

### Test 100

- `point_cluster = 20`
- `line = 20`
- `L-shape = 20`
- `cross = 15`
- `double-line = 15`
- `small_rect_edge = 10`

## Stratified coverage rules

The main set is generated with parameter-stratified sampling rather than naive uniform random draws. Each family is cycled through explicit bucket targets for:

- radial position: `center / off_center / boundary`
- azimuth sector: `low / mid / high / near_seam`
- height: `lower / mid / upper`
- size regime: `small / medium / large`
- intensity regime: `weak / medium / strong`
- boundary proximity: `interior / edge_biased`

Family-specific parameter buckets are additionally tracked:

- `line`: length, width, orientation, near-seam orientation
- `point_cluster`: point count, cluster count, density, multi-cluster structure
- `L-shape`: arm lengths, arm ratio, width
- `double-line`: spacing, length, width, amplitude imbalance
- `cross`: arm lengths, width, symmetry imbalance
- `small_rect_edge`: width, height, open-edge pattern, edge bias

## OOD sets

### unseen-parameter OOD

Focused on the `line` family using a held-out parameter regime:

- longer line lengths
- thicker strokes
- seam-adjacent azimuth and edge-biased placement

Those combinations are excluded from the main train split.

### leave-one-family-out focused OOD

Focused on `point_cluster` as the hardest family-style stress set, with denser multi-cluster structures and larger inter-cluster spread than the main train distribution.

### random-ET OOD

Generated with clustered random extended targets inspired by literature-scale synthetic ET design, but still executed through the true cylindrical forward simulator.

## Frozen mainline definition

- front-end: `Variant B`
- physics backbone: `ref3`
- second stage: `3D U-Net`
- training target: GT amplitude volume
- input: ref3 coarse amplitude volume

## Non-goals

- no physics-consistency loss
- no complex supervision
- no front-end replacement
- no recipe re-search
- no real measured echoes
