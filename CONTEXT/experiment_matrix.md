# experiment_matrix

## Phase 0: Bootstrap / Project Startup

- Goal: freeze repository structure, governance, minimal scripts, and reporting conventions
- Input / Output: input is frozen context docs and repository root; output is a reproducible project skeleton with bootstrap reports
- In current task: yes
- Status: this task prepares and validates the phase

## Phase 1: Point-Target Physical Chain Validation

- Goal: verify forward simulation, reconstruction baselines, and reduced-reference behavior on point targets
- Input / Output: input is protocol-compliant point-target scene definitions and scripts; output is validated point-target datasets, reconstructions, and diagnostic metrics
- In current task: no
- Status: not started, only prepared by bootstrap

## Phase 2: Traditional Baselines `ref3/ref5/ref7/ref9/BP`

- Goal: establish quality-runtime trade-offs for traditional cylindrical baselines
- Input / Output: input is validated simulation and reconstruction pipeline; output is baseline images, metrics, and runtime comparisons
- In current task: no
- Status: not started, only prepared by bootstrap

## Phase 3: Minimal Two-Stage Learned Imaging Mainline

- Goal: run the minimal `RED_ref3 -> 3D U-Net -> GT amplitude` learning pipeline
- Input / Output: input is validated physical backbone data pairs; output is trained second-stage model, evaluation metrics, and error-compensation analysis
- In current task: no
- Status: not started, only prepared by bootstrap

## Phase 4: Extended-Target Main Experiments

- Goal: evaluate the method on the paper’s primary extended-target scenarios
- Input / Output: input is frozen ET datasets and trained pipeline; output is primary result tables, visualizations, and ablations on structured targets
- In current task: no
- Status: not started, only prepared by bootstrap

## Phase 5: Physics Consistency Extension

- Goal: add explicit physics-consistency or forward-echo-consistency extensions to the mainline method
- Input / Output: input is the trained two-stage imaging baseline and protocol-compliant echo modeling; output is extended losses or modules with comparison reports
- In current task: no
- Status: not started, only prepared by bootstrap
