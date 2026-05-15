

````markdown
# task_real_struc_001: ReMiC-Net Multi-Input and RSB-FiLM Core Structure Diagnosis

## 0. Task Identity

This task belongs to the `task_real_struc` experiment line.

Task name:

```text
task_real_struc_001
````

Experiment title:

```text
ReMiC-Net Multi-Input and RSB-FiLM Core Structure Diagnosis
```

This is a **structure diagnosis task**, not a final model tuning task.

The purpose is to determine whether the two intended structural advantages of ReMiC-Net are real and measurable:

1. reference-surface-aware multi-input metadata;
2. FiLM / RSB-FiLM geometry-conditioned feature modulation.

The task must answer:

> If ReMiC-Net is currently close to plain 3D U-Net, is the reason that the ReMiC-Net idea is ineffective, or that the current implementation details of multi-input, FiLM placement, geometry encoding, or modulation constraints are suboptimal?

---

## 1. Repository and Execution Context

Repository:

```text
https://github.com/wykhan/ReMiC-Net/
```

Default branch:

```text
master
```

The repository and experiment data are assumed to be directly readable in the execution environment.

Before implementing anything, inspect the repository structure and identify:

```text
CONTEXT/
PROMPTS/
scripts/
exp/
doc/
workspace/
```

Also inspect existing files related to:

```text
dataset generation
data loading
ref3/ref5/ref7/ref9/BP reconstruction
3D U-Net
ReMiC-Net
FiLM
RSB-FiLM
training loop
evaluation metrics
visualization
experiment reports
```

If formal training code already exists, reuse it.

If formal training code does not exist or is incomplete, implement the minimal missing modules under `workspace/` and expose all experiment execution through reproducible scripts under `scripts/`.

Do not rely on manual notebook-only execution.

---

## 2. Frozen Project Principles

Follow the existing project context documents as the source of authority:

```text
CONTEXT/real_cylindrical_master_document_with_physics_consistency.md
CONTEXT/simulation_protocol.md
CONTEXT/reference_surface_strategy.md
CONTEXT/repo_map.md
```

The following principles are frozen for this task.

### 2.1 Physical backbone

Use:

```text
ref3
```

as the reduced-reference physical backbone.

The `ref3` reference cylindrical surfaces are:

```text
[0.00, 0.15, 0.30] m
```

Do not redefine the reference-surface protocol in this task.

### 2.2 Main input

The main image input is:

```text
X_ref3
```

meaning the coarse magnitude reconstruction from the `ref3` reduced-reference cylindrical physical backbone.

### 2.3 Geometry metadata

The ReMiC-Net geometry metadata is:

```text
[Mshell, delta_rho, Pcyc]
```

Definitions:

```text
Mshell     : one-hot or equivalent shell/reference-surface allocation map
delta_rho  : signed nearest-reference radial deviation
Pcyc       : cyclic phase mismatch state derived from nearest-reference radial deviation
```

Use existing project definitions wherever available.

Do not silently change the physical meaning of these fields.

### 2.4 Output form

The learning model predicts a residual:

```text
Delta_x_hat
```

The final reconstruction must be:

```text
x_hat = X_ref3 + Delta_x_hat
```

Do not replace residual learning with full-image direct regression unless explicitly implemented as an additional diagnostic baseline.

### 2.5 Training label

Use the ground-truth reflectivity magnitude volume as the supervised label.

Do not use BP as the training label.

BP is a traditional high-quality baseline only.

### 2.6 Exclusions in this task

Do not add:

```text
support mask auxiliary head
BCE loss
Dice loss
support Dice as main metric
support prior input
valid FOV mask input
complex echo-domain consistency loss
```

This task focuses only on ReMiC-Net structure diagnosis.

---

## 3. Scientific Question

This task must answer the following scientific questions.

### Q1. Does reference-surface-aware metadata help?

Compare:

```text
X_ref3 only
```

against:

```text
X_ref3 + Mshell
X_ref3 + Mshell + delta_rho
X_ref3 + Mshell + delta_rho + Pcyc
```

The goal is to determine whether multi-input metadata improves reconstruction quality beyond plain residual 3D U-Net.

### Q2. Does FiLM help beyond simple input concatenation?

Compare:

```text
input-channel concatenation
```

against:

```text
geometry branch + bottleneck feature concat
geometry branch + generic FiLM
geometry branch + RSB-FiLM
```

The goal is to determine whether geometry information is more effective as a feature modulation signal than as ordinary image channels.

### Q3. Does RSB-FiLM provide physically meaningful advantages over generic FiLM?

RSB-FiLM should be useful especially in:

```text
large |delta_rho| regions
large |Pcyc| regions
shell-boundary regions
hard extended-target families
OOD tests
```

Even if overall NMSE improves only slightly, improvement in these physically meaningful hard regions is important.

### Q4. Where is the current bottleneck?

The final report must identify whether the weakness is mainly from:

```text
metadata not useful
metadata encoding problem
FiLM implementation problem
RSB-FiLM constraint too strong or too weak
loss dominated by easy regions
training sampling dominated by easy cases
dataset or split issue
```

This task does not need to solve all bottlenecks. It must locate them.

---

## 4. Required Model Variants

Run the following model variants under the same dataset split, seed policy, training schedule, optimizer, loss setting, and metric pipeline.

Use consistent naming exactly as below.

---

### S01_ref3

No learning.

Evaluate the `ref3` physical reconstruction directly.

Purpose:

```text
physical lower baseline
```

---

### S02_plain_residual_unet

Input:

```text
X_ref3
```

Model:

```text
plain residual 3D U-Net
```

Output:

```text
Delta_x_hat
```

Final:

```text
x_hat = X_ref3 + Delta_x_hat
```

Purpose:

```text
base learning baseline
```

This is the baseline ReMiC-Net must beat.

---

### S03_concat_Mshell

Input:

```text
[X_ref3, Mshell]
```

Model:

```text
plain residual 3D U-Net with input-channel concatenation
```

Purpose:

```text
test whether shell/reference allocation is useful
```

---

### S04_concat_Mshell_delta

Input:

```text
[X_ref3, Mshell, delta_rho]
```

Model:

```text
plain residual 3D U-Net with input-channel concatenation
```

Purpose:

```text
test whether nearest-reference radial deviation is useful
```

---

### S05_concat_Mshell_delta_Pcyc

Input:

```text
[X_ref3, Mshell, delta_rho, Pcyc]
```

Model:

```text
plain residual 3D U-Net with input-channel concatenation
```

Purpose:

```text
test whether full reference-surface-aware metadata is useful
```

---

### S06_geometry_branch_bottleneck_concat

Inputs:

```text
image branch input: X_ref3
geometry branch input: [Mshell, delta_rho, Pcyc]
```

Fusion:

```text
bottleneck feature concatenation only
```

No FiLM.

Purpose:

```text
separate geometry-branch benefit from FiLM benefit
```

---

### S07_generic_film_middeep

Inputs:

```text
image branch input: X_ref3
geometry branch input: [Mshell, delta_rho, Pcyc]
```

Fusion:

```text
generic FiLM
```

FiLM placement:

```text
E2, E3, B, D3, D2
```

where:

```text
E2/E3 : mid/deep encoder levels
B     : bottleneck
D3/D2 : deep/mid decoder levels
```

Purpose:

```text
test whether FiLM modulation is better than input concat and bottleneck concat
```

---

### S08_rsbfilm_middeep_default

Inputs:

```text
image branch input: X_ref3
geometry branch input: [Mshell, delta_rho, Pcyc]
```

Fusion:

```text
RSB-FiLM
```

FiLM placement:

```text
E2, E3, B, D3, D2
```

Default RSB-FiLM parameters:

```text
epsilon_m   = 0.05
alpha_gamma = 0.5
alpha_beta  = 0.1
```

Default envelope:

```text
m(v) = epsilon_m + (1 - epsilon_m) * abs(Pcyc(v))
```

Feature modulation:

```text
F_tilde = (1 + gamma_bounded) * F + beta_bounded
```

Implementation requirements:

```text
gamma and beta must be bounded
the residual output itself must not be multiplied by the physical envelope
the physical envelope only controls feature modulation strength
```

Purpose:

```text
main ReMiC-Net candidate in this task
```

---

## 5. Dataset and Split Requirements

Use the existing dataset if available.

At minimum, the experiment should support:

```text
train
validation
main test
```

If OOD splits already exist, also evaluate:

```text
Leave-One-Family-Out OOD
Random-ET OOD
Unseen-Parameter OOD
```

If OOD splits do not exist, do not fabricate conclusions. Instead:

1. report that OOD splits are unavailable;
2. prepare the evaluation interface for future OOD splits;
3. include this limitation in the final report.

The dataset must include or allow generation of:

```text
X_ref3
x_gt
Mshell
delta_rho
Pcyc
family label if available
sample id
```

If any required field is missing, implement a deterministic preprocessing step to generate it from the frozen geometry and reference-surface protocol.

Record all generated fields and formulas in the report.

---

## 6. Training Protocol

Use the same training protocol for S02-S08 unless a variant explicitly requires otherwise.

Recommended defaults, unless existing project config says otherwise:

```text
optimizer: AdamW
initial learning rate: 1e-3
weight decay: 1e-4
batch size: use largest stable batch size
epochs: use existing default; if unavailable, use 100 epochs or early stopping
early stopping: validation NMSE or validation loss
loss: residual/image L1 + optional SSIM if already used by current codebase
mixed precision: allowed if stable
gradient clipping: allowed if needed
```

Important:

```text
Do not tune each model separately.
Use a unified training schedule.
Do not give ReMiC-Net more epochs or a better optimizer than U-Net.
Do not change dataset split between variants.
```

Use at least:

```text
seed = 0
```

If compute permits, run:

```text
seed = 0, 1, 2
```

If only one seed is run, state clearly that the result is a first-pass diagnostic result.

---

## 7. Evaluation Metrics

For every model variant, report the following overall metrics:

```text
NMSE
PSNR
SSIM
runtime_per_sample
speedup_vs_BP if BP runtime is available
number_of_parameters
peak_GPU_memory if available
```

Also report the following diagnostic metrics.

### 7.1 Metrics by |delta_rho|

Bin by absolute radial deviation:

```text
small |delta_rho|
medium |delta_rho|
large |delta_rho|
```

Use deterministic bin thresholds.

If natural thresholds already exist in the project, use them.

Otherwise use quantile bins:

```text
0-33%
33-66%
66-100%
```

Report:

```text
NMSE_by_delta_rho_bin
SSIM_by_delta_rho_bin
MAE_by_delta_rho_bin
```

### 7.2 Metrics by |Pcyc|

Bin by absolute cyclic phase mismatch:

```text
small |Pcyc|
medium |Pcyc|
large |Pcyc|
```

Also report the physically important split:

```text
abs(Pcyc) <= 0.25
abs(Pcyc) > 0.25
```

Report:

```text
NMSE_by_Pcyc_bin
SSIM_by_Pcyc_bin
MAE_by_Pcyc_bin
```

### 7.3 Shell-boundary metrics

Evaluate regions near shell boundaries.

For ref3, shell boundaries are located near:

```text
rho = 0.075 m
rho = 0.225 m
```

Define a small boundary band, for example:

```text
within one or two radial grid cells
```

Report:

```text
NMSE_shell_boundary
SSIM_shell_boundary
MAE_shell_boundary
```

### 7.4 Family-wise metrics

If family labels exist, report metrics by family:

```text
line
cross
L-shape
double-line
small_rect_edge
point_cluster
other available families
```

Report:

```text
NMSE_by_family
PSNR_by_family
SSIM_by_family
```

### 7.5 OOD metrics

If OOD splits exist, report:

```text
Leave-One-Family-Out OOD metrics
Random-ET OOD metrics
Unseen-Parameter OOD metrics
```

If not available, record as:

```text
not available in current dataset
```

---

## 8. Visualization Requirements

For representative test samples, save visual comparisons.

At minimum include:

```text
GT
ref3
S02_plain_residual_unet
S05_concat_Mshell_delta_Pcyc
S07_generic_film_middeep
S08_rsbfilm_middeep_default
error maps
```

Use the same visualization operator for all methods.

Suggested views:

```text
central slices
maximum-intensity projection
cylindrical unwrap view if implemented
high-|Pcyc| region zoom
high-|delta_rho| region zoom
```

Do not cherry-pick only successful examples.

Include:

```text
best case
median case
failure case
hard high-|Pcyc| case
hard large-|delta_rho| case
```

---

## 9. Output Directory

Create a timestamped experiment root:

```text
exp/task_real_struc_001_remicnet_core_structure_diagnosis/<timestamp>/
```

The directory must contain:

```text
task_real_struc_001_report.md
config_summary.json
model_variants.json
metrics_overall.csv
metrics_by_delta_rho.csv
metrics_by_Pcyc.csv
metrics_by_shell_boundary.csv
metrics_by_family.csv
metrics_ood.csv
runtime_table.csv
parameter_count_table.csv
training_curves/
recon_compare/
diagnostic_plots/
model_config_diffs.md
environment.txt
git_status.txt
```

If a file cannot be generated because the corresponding data are unavailable, create the file anyway with an explicit explanation.

---

## 10. Required Final Report Structure

The final report must use the following structure.

```text
# task_real_struc_001_report

## 1. Executive Summary

## 2. Repository and Code Inspection

## 3. Dataset and Split Description

## 4. Model Variants

## 5. Training Protocol

## 6. Overall Results

## 7. Diagnostics by |delta_rho|

## 8. Diagnostics by |Pcyc|

## 9. Shell-Boundary Diagnostics

## 10. Family-Wise Results

## 11. OOD Results

## 12. Runtime and Complexity

## 13. Visual Comparison

## 14. Key Findings

## 15. Failure Analysis

## 16. Decision: Is ReMiC-Net structurally justified?

## 17. Recommendation for task_real_struc_002
```

---

## 11. Decision Rules

Use the following decision rules.

### Rule 1: metadata usefulness

If:

```text
S05 > S02
```

on overall metrics or hard-region metrics, then metadata is useful.

If S05 is not better than S02, inspect whether individual metadata variants S03 or S04 help.

### Rule 2: Pcyc usefulness

If:

```text
S05 > S04
```

especially in high-|Pcyc| regions, then Pcyc is useful.

If S05 is worse than S04, suspect Pcyc scalar encoding, normalization, or wrap discontinuity.

### Rule 3: geometry branch usefulness

If:

```text
S06 > S05
```

then a separate geometry branch is useful beyond input-channel concatenation.

### Rule 4: FiLM usefulness

If:

```text
S07 > S06
```

then FiLM modulation is useful.

If S07 is not better than S06, suspect FiLM placement, initialization, or gamma/beta instability.

### Rule 5: RSB-FiLM usefulness

If:

```text
S08 > S07
```

especially in:

```text
large |delta_rho|
large |Pcyc|
shell-boundary
OOD
```

then RSB-FiLM is justified.

If S08 has similar overall metrics but better hard-region metrics, still consider it promising.

If S08 is worse everywhere, suspect the RSB envelope or modulation bounds are too restrictive.

### Rule 6: structural continuation

Continue to task_real_struc_002 only if at least one of the following is true:

```text
S05 improves over S02
S07 improves over S05/S06
S08 improves over S07 in hard regions
S08 improves OOD stability
diagnostics show ReMiC-Net has localized physical advantages
```

If none is true, do not blindly continue tuning RSB-FiLM. First audit metadata correctness and dataset generation.

---

## 12. Acceptance Criteria

This task is complete only if:

1. all S01-S08 variants are either executed or explicitly marked unavailable with reasons;
2. overall metrics are reported for all available variants;
3. hard-region diagnostics by `|delta_rho|` and `|Pcyc|` are reported;
4. shell-boundary diagnostics are reported;
5. at least one visual comparison panel is generated;
6. final report clearly answers whether ReMiC-Net has a structural advantage over plain U-Net;
7. final report recommends a concrete next step for `task_real_struc_002`.

---

## 13. Prohibited Behavior

Do not:

```text
change frozen geometry or reference-surface protocol silently
use BP as training label
add support mask head
add Dice/BCE loss
add complex echo consistency
change dataset split between variants
tune hyperparameters separately for each variant
delete failed results
report only favorable samples
hide failed experiments
overwrite previous experiment outputs
```

All failures must be recorded in:

```text
debug.md
task_real_struc_001_report.md
```

---

## 14. Final Deliverable

At the end of the task, print the experiment root path, for example:

```text
exp/task_real_struc_001_remicnet_core_structure_diagnosis/20260515_XXXXXX/
```

Also provide a concise final conclusion:

```text
S02 vs S05:
S05 vs S07:
S07 vs S08:
Best current candidate:
Main bottleneck:
Recommendation for task_real_struc_002:
```

```

这个版本的 `task_real_struc_001` 只做 **核心结构诊断**，不要把 `Pcyc sin-cos`、envelope 改造、FiLM 强度网格、hard-region loss 全塞进去。那些应放到 `task_real_struc_002~004`，否则第一轮任务会过重，结论也会混乱。
```

