

````markdown
# task_real_struc_001b: Full ReMiC-Net Structure Diagnosis With Metadata Audit and Failure Correction

## 0. Task Identity

Task name:

```text
task_real_struc_001b
````

Experiment title:

```text
Full ReMiC-Net Structure Diagnosis With Metadata Audit and Failure Correction
```

Target branch for all code, reports, and lightweight results:

```text
task_struc_series
```

This task is a corrective full experiment following `task_real_struc_001`.

The previous `task_real_struc_001` run is now reclassified as:

```text
task_real_struc_001a_smoke_test
```

It was useful only as a code-path smoke test because it used:

```text
train_limit = 48
val_limit   = 12
test_limit  = 24
epochs      = 2
seed        = 0
```

Those settings are not sufficient for scientific interpretation.

This task must complete a **full, reference-worthy structure diagnosis experiment**. If the hard requirements below cannot be satisfied, Codex must not write a success report. Instead, write an `incomplete_report.md`.

---

## 1. Core Purpose

This task must answer:

> After fixing the shortcomings found in `task_real_struc_001a`, do ReMiC-Net's two intended structural advantages—reference-surface-aware metadata and geometry-conditioned FiLM / RSB-FiLM modulation—provide a real and reliable benefit over plain residual 3D U-Net?

The task must explicitly correct and investigate the following issues discovered in `task_real_struc_001a`:

1. `S03_concat_Mshell` collapsed.
2. `S05_concat_Mshell_delta_Pcyc` collapsed.
3. `S07_generic_film_middeep` and `S08_rsbfilm_middeep_default` had better overall NMSE but poor SSIM.
4. Hard-region metrics did not support RSB-FiLM superiority.
5. Overall metrics and hard-region metrics appeared inconsistent.
6. Metadata correctness, scaling, alignment, and Pcyc wrap behavior were not audited.
7. Training was too short to determine convergence.
8. OOD evaluation was not run.

This task is not allowed to merely rerun the 001a smoke test.

---

## 2. Branch and Git Requirements

Before doing any work:

```bash
git fetch origin
git checkout task_struc_series
git pull origin task_struc_series
```

All new files must be committed and pushed to:

```text
origin/task_struc_series
```

Do not push directly to `master`.

At the end of the task, run:

```bash
git status
git branch --show-current
git log --oneline -5
```

The final report must state:

```text
current_branch = task_struc_series
pushed_to_remote = yes/no
remote_branch = origin/task_struc_series
```

If pushing fails, record the reason in `incomplete_report.md`.

---

## 3. Repository and Source Documents

Use the repository:

```text
https://github.com/wykhan/ReMiC-Net/
```

Use the following context documents as frozen authority:

```text
CONTEXT/real_cylindrical_master_document_with_physics_consistency.md
CONTEXT/simulation_protocol.md
CONTEXT/reference_surface_strategy.md
CONTEXT/repo_map.md
PROMPTS/task_real_struc_001.md
```

Also inspect the outputs from 001a:

```text
exp/task_real_struc_001_remicnet_core_structure_diagnosis/20260515_000001/
```

Especially:

```text
task_real_struc_001_report.md
config_summary.json
metrics_overall.csv
metrics_by_delta_rho.csv
metrics_by_Pcyc.csv
metrics_by_shell_boundary.csv
metrics_by_family.csv
metrics_ood.csv
model_config_diffs.md
```

The final report of this task must explicitly compare 001b against 001a and explain what changed.

---

## 4. Frozen Scientific Setup

### 4.1 Physical backbone

Use:

```text
ref3
```

as the reduced-reference physical backbone.

The ref3 reference cylindrical surfaces are:

```text
[0.00, 0.15, 0.30] m
```

Do not change the reference-surface strategy.

### 4.2 Main input

The main image input is:

```text
X_ref3
```

### 4.3 Geometry metadata

The metadata fields are:

```text
Mshell
delta_rho
Pcyc
```

Definitions:

```text
Mshell    : 3-channel nearest reference-surface allocation map for ref3
delta_rho : signed radial deviation from nearest reference surface
Pcyc      : wrapped two-way phase mismatch divided by pi
```

### 4.4 Output

All learning models must use residual learning:

```text
Delta_x_hat = f_theta(...)
x_hat = X_ref3 + Delta_x_hat
```

Do not change the task into direct full-image regression.

### 4.5 Label

Use ground-truth reflectivity magnitude volume as the supervised label.

Do not use BP as training label.

### 4.6 Prohibited additions

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

---

## 5. Hard Completion Requirements

This task is complete only if all hard requirements are satisfied.

### 5.1 Full dataset requirement

Use the frozen full main split:

```text
train = 800
val   = 100
test  = 100
```

The source dataset is expected to be:

```text
/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006d_800_formal/20260419_112717/
```

If the full split is unavailable, do not silently downsample.

Instead:

1. record the missing file or failure reason;
2. create `incomplete_report.md`;
3. do not claim task completion.

### 5.2 Training length requirement

For all trainable variants, run at least:

```text
epochs >= 50
```

Use early stopping only if:

```text
patience >= 10
min_delta is clearly defined
best validation checkpoint is saved
training curve shows convergence or plateau
```

A 2-epoch or smoke-test run is prohibited.

### 5.3 Seed requirement

At minimum, run all S01-S08 variants with:

```text
seed = 0
```

Then run the following key variants with 3 seeds:

```text
S02_plain_residual_unet
S04_concat_Mshell_delta
S05_concat_Mshell_delta_Pcyc
S06_geometry_branch_bottleneck_concat
S07_generic_film_middeep
S08_rsbfilm_middeep_default
```

Required seeds:

```text
0, 1, 2
```

If compute is insufficient for all 3-seed variants, do not call the task fully complete. Write `incomplete_report.md` and clearly state which variants remain.

### 5.4 OOD requirement

Run OOD evaluation if OOD data/interfaces exist.

Required OOD splits:

```text
Leave-One-Family-Out OOD
Random-ET OOD
Unseen-Parameter OOD
```

If OOD data or scripts are unavailable, Codex must verify this, not assume it.

The report must include one of:

```text
OOD evaluated successfully
```

or:

```text
OOD unavailable because: <specific reason>
```

Do not leave OOD as a generic “not evaluated” without investigation.

### 5.5 Metadata audit requirement

Before training, run and save a full metadata audit.

Required audit file:

```text
metadata_audit_report.md
metadata_stats.csv
metadata_histograms/
```

The audit must include:

```text
X_ref3 min/max/mean/std
GT min/max/mean/std
Mshell channel sums and one-hot validity check
delta_rho min/max/mean/std
delta_rho unique shell-wise statistics
Pcyc min/max/mean/std
Pcyc histogram
abs(Pcyc)<=0.25 ratio
abs(Pcyc)>0.25 ratio
spatial alignment check between metadata and X_ref3
shell boundary voxel counts
NaN / Inf check for all fields
```

### 5.6 Failure investigation requirement

The previous run showed collapse in:

```text
S03_concat_Mshell
S05_concat_Mshell_delta_Pcyc
```

This task must investigate these failures.

Required outputs:

```text
failure_audit_S03_S05.md
input_channel_scale_table.csv
training_loss_curves_S03_S05.png
gradient_norms_S03_S05.csv if available
prediction_value_stats_S03_S05.csv
```

At minimum, answer:

```text
Did S03/S05 fail because of metadata scale?
Did they fail because of Pcyc wrap discontinuity?
Did they fail because of channel normalization?
Did they fail because 001a trained only 2 epochs?
Did they still fail after full training?
```

### 5.7 Metric consistency requirement

The previous run showed conflict between overall metrics and hard-region metrics.

This task must audit metric definitions.

Required output:

```text
metric_definition_audit.md
```

It must explain:

```text
how overall NMSE is computed
how hard-region NMSE is computed
whether normalization denominators are consistent
whether hard-region metrics are computed over support only or full volume
whether background voxels dominate overall metrics
```

Also provide a unified alternative diagnostic metric:

```text
support_masked_NMSE
foreground_MAE
background_MAE
high_delta_rho_support_NMSE
high_Pcyc_support_NMSE
```

This does not add a support head or Dice loss. It is only an evaluation mask derived from GT support for diagnostics.

---

## 6. Required Model Variants

Run the following variants.

### S01_ref3

No learning.

Evaluate ref3 directly.

### S02_plain_residual_unet

Input:

```text
X_ref3
```

Model:

```text
plain residual 3D U-Net
```

### S03_concat_Mshell

Input:

```text
[X_ref3, Mshell]
```

Purpose:

```text
retest whether S03 collapse was due to 001a undertraining or metadata scaling
```

### S04_concat_Mshell_delta

Input:

```text
[X_ref3, Mshell, delta_rho]
```

Purpose:

```text
strong simple metadata baseline
```

### S05_concat_Mshell_delta_Pcyc

Input:

```text
[X_ref3, Mshell, delta_rho, Pcyc]
```

Purpose:

```text
retest whether scalar Pcyc still collapses under full training and proper metadata audit
```

### S06_geometry_branch_bottleneck_concat

Inputs:

```text
image branch: X_ref3
geometry branch: [Mshell, delta_rho, Pcyc]
fusion: bottleneck concat
```

Purpose:

```text
strong geometry branch baseline
```

### S07_generic_film_middeep

Inputs:

```text
image branch: X_ref3
geometry branch: [Mshell, delta_rho, Pcyc]
fusion: generic FiLM
placement: E2, E3, B, D3, D2
```

Purpose:

```text
test whether generic FiLM remains structurally useful after full training
```

### S08_rsbfilm_middeep_default

Inputs:

```text
image branch: X_ref3
geometry branch: [Mshell, delta_rho, Pcyc]
fusion: RSB-FiLM
placement: E2, E3, B, D3, D2
```

Default RSB-FiLM parameters:

```text
epsilon_m   = 0.05
alpha_gamma = 0.5
alpha_beta  = 0.1
m(v) = epsilon_m + (1 - epsilon_m) * abs(Pcyc(v))
```

Purpose:

```text
test whether default RSB-FiLM is supported after full training
```

---

## 7. Mandatory Corrective Variants

In addition to S01-S08, run the following corrective variants because 001a exposed a Pcyc failure.

### S09_concat_Mshell_delta_Pcyc_sincos

Input:

```text
[X_ref3, Mshell, delta_rho, sin(pi*Pcyc), cos(pi*Pcyc)]
```

Purpose:

```text
test whether scalar Pcyc collapse is caused by wrap discontinuity
```

### S10_geometry_branch_bottleneck_concat_Pcyc_sincos

Inputs:

```text
image branch: X_ref3
geometry branch: [Mshell, delta_rho, sin(pi*Pcyc), cos(pi*Pcyc)]
fusion: bottleneck concat
```

Purpose:

```text
test whether S06 improves when Pcyc is encoded periodically
```

### S11_rsbfilm_Pcyc_sincos

Inputs:

```text
image branch: X_ref3
geometry branch: [Mshell, delta_rho, sin(pi*Pcyc), cos(pi*Pcyc)]
fusion: RSB-FiLM
placement: E2, E3, B, D3, D2
```

Envelope options:

Use the default envelope based on scalar Pcyc magnitude:

```text
m(v) = epsilon_m + (1 - epsilon_m) * abs(Pcyc(v))
```

but feed sin/cos Pcyc to the geometry branch.

Purpose:

```text
test whether RSB-FiLM failure is due to scalar Pcyc representation
```

---

## 8. Training Protocol

Use a unified training protocol.

Recommended default unless existing stable project config overrides it:

```text
optimizer: AdamW
learning_rate: 1e-3
weight_decay: 1e-4
batch_size: largest stable batch size
epochs: >= 50
early_stopping_patience: >= 10
loss: residual/image L1
optional loss: SSIM only if already implemented consistently
mixed_precision: allowed if stable
gradient_clipping: allowed if needed
```

Important restrictions:

```text
Do not tune each model separately.
Do not give ReMiC-Net more epochs than U-Net.
Do not change split across variants.
Do not silently change architecture depth or base_channels across variants unless explicitly controlled and reported.
Do not use 2-epoch smoke-test settings.
```

### 8.1 Convergence requirement

For every trainable variant, save:

```text
train_loss_curve.csv
val_loss_curve.csv
best_epoch.txt
checkpoint_best.pt
```

The report must state whether each model converged, plateaued, or failed.

### 8.2 Failure rule

If a model collapses, do not delete it.

Record:

```text
final train loss
final val loss
prediction min/max/mean/std
whether NaN/Inf occurred
whether gradient explosion occurred if measurable
example failed visualization
```

---

## 9. Evaluation Metrics

For every model and seed, report:

```text
NMSE
PSNR
SSIM
MAE
runtime_per_sample
speedup_vs_BP if BP runtime is available
parameter count
peak GPU memory if available
best epoch
```

For multi-seed variants, report:

```text
mean
std
best
worst
```

### 9.1 Hard-region metrics

Report metrics by:

```text
|delta_rho| small / medium / large
|Pcyc| small / medium / large
abs(Pcyc)<=0.25
abs(Pcyc)>0.25
shell boundary band
```

### 9.2 Unified diagnostic metrics

Also report:

```text
foreground_NMSE
background_MAE
support_masked_NMSE
high_delta_rho_support_NMSE
high_Pcyc_support_NMSE
family_wise_NMSE
family_wise_PSNR
family_wise_SSIM
```

### 9.3 OOD metrics

If available, report:

```text
OOD_NMSE
OOD_PSNR
OOD_SSIM
OOD_family_wise_metrics
```

---

## 10. Visualization Requirements

Save visual comparisons for:

```text
best case
median case
failure case
hard high-|Pcyc| case
hard large-|delta_rho| case
shell-boundary hard case
```

Each panel must include:

```text
GT
ref3
S02
S04
S05
S06
S08
S09
S10
S11
error maps
```

If too many columns make the figure unreadable, split into two panels:

```text
core_models_panel
corrective_models_panel
```

Views:

```text
central slices
maximum intensity projection
cylindrical unwrap view if available
foreground zoom
high-error zoom
```

Do not cherry-pick only successful cases.

---

## 11. Output Directory

Create a new timestamped experiment root:

```text
exp/task_real_struc_001b_full_structure_diagnosis/<timestamp>/
```

Required files:

```text
task_real_struc_001b_report.md
incomplete_report.md                         # only if incomplete
config_summary.json
model_variants.json
metadata_audit_report.md
metadata_stats.csv
metadata_histograms/
failure_audit_S03_S05.md
metric_definition_audit.md
metrics_overall_by_seed.csv
metrics_overall_summary.csv
metrics_by_delta_rho.csv
metrics_by_Pcyc.csv
metrics_by_shell_boundary.csv
metrics_by_family.csv
metrics_support_masked.csv
metrics_ood.csv
runtime_table.csv
parameter_count_table.csv
training_curves/
checkpoints/
recon_compare/
diagnostic_plots/
model_config_diffs.md
environment.txt
git_status.txt
```

Do not commit large checkpoints if repository policy or `.gitignore` excludes them. If checkpoints are not committed, record their local paths in the report.

Lightweight CSV, JSON, Markdown reports, and representative images should be committed.

---

## 12. Required Report Structure

The final report must use this structure:

```text
# task_real_struc_001b_report

## 1. Executive Summary

## 2. Why 001b Was Needed

## 3. What Was Wrong or Insufficient in 001a

## 4. Dataset and Full-Split Verification

## 5. Metadata Audit

## 6. Metric Definition Audit

## 7. Model Variants and Corrective Variants

## 8. Training Protocol and Convergence

## 9. Overall Results

## 10. Multi-Seed Results

## 11. Diagnostics by |delta_rho|

## 12. Diagnostics by |Pcyc|

## 13. Shell-Boundary Diagnostics

## 14. Support-Masked and Foreground/Background Diagnostics

## 15. Family-Wise Results

## 16. OOD Results

## 17. S03/S05 Failure Investigation

## 18. FiLM and RSB-FiLM Analysis

## 19. Visual Comparison

## 20. Runtime and Complexity

## 21. Final Scientific Interpretation

## 22. Decision: Which Model Is Actually Supported?

## 23. Recommendation for task_real_struc_002
```

---

## 13. Decision Rules

Use these rules strictly.

### Rule 1: Plain U-Net baseline

If S02 is worse than ref3 after full training, conclude:

```text
plain residual U-Net is not yet a reliable learning baseline under this setting
```

and investigate convergence.

### Rule 2: Metadata usefulness

If S04 beats S02 and ref3, conclude:

```text
Mshell + delta_rho metadata is useful
```

If S04 fails, investigate metadata scaling and alignment.

### Rule 3: Scalar Pcyc usefulness

If S05 fails but S09 succeeds, conclude:

```text
scalar Pcyc encoding is problematic; periodic sin-cos encoding is preferred
```

If both S05 and S09 fail, conclude:

```text
Pcyc may be harmful or incorrectly generated; audit required before reuse
```

### Rule 4: Geometry branch usefulness

If S06 beats S04 with comparable or better SSIM, conclude:

```text
separate geometry branch is useful beyond input concatenation
```

If S06 only improves NMSE but hurts SSIM, do not freeze it as final.

### Rule 5: FiLM usefulness

If S07 beats S06 on overall and hard-region metrics without SSIM collapse, conclude:

```text
generic FiLM is useful
```

Otherwise:

```text
generic FiLM is not yet justified
```

### Rule 6: RSB-FiLM usefulness

If S08 or S11 beats S07 and S06 in high-|delta_rho|, high-|Pcyc|, shell-boundary, and OOD settings without SSIM collapse, conclude:

```text
RSB-FiLM is structurally justified
```

If it only improves overall NMSE but hurts SSIM or hard-region metrics, conclude:

```text
RSB-FiLM remains unproven
```

### Rule 7: Final model support

A model can be recommended for freezing only if it satisfies:

```text
better than S02 in overall NMSE
not worse than S02 in SSIM
better than S02 or ref3 in hard-region metrics
stable across seeds or at least not seed-fragile
reasonable runtime
no unresolved metadata failure
```

---

## 14. Completion Policy

If all hard requirements are satisfied, create:

```text
task_real_struc_001b_report.md
```

and state:

```text
status = COMPLETE
```

If any hard requirement is not satisfied, create:

```text
incomplete_report.md
```

and state:

```text
status = INCOMPLETE
```

Do not write a success-style executive summary for incomplete work.

Incomplete report must include:

```text
completed items
missing items
failure reasons
commands already run
recommended next command
whether any partial results are scientifically interpretable
```

---

## 15. Prohibited Behavior

Do not:

```text
run only a tiny subset and call it complete
train for 2 epochs and call it complete
skip metadata audit
skip S03/S05 failure investigation
skip metric consistency audit
skip OOD investigation
claim RSB-FiLM is supported based only on overall NMSE
ignore SSIM collapse
change dataset split between variants
tune each model separately
silently change geometry or reference surfaces
use BP as training label
commit large checkpoints or caches unnecessarily
push to master
```

---

## 16. Final Console Output

At the end, print:

```text
task_real_struc_001b status: COMPLETE or INCOMPLETE
experiment_root:
current_branch:
remote_push_status:
best_overall_model:
best_SSIM_model:
best_hard_region_model:
S03_failure_status:
S05_failure_status:
Pcyc_scalar_status:
Pcyc_sincos_status:
RSBFiLM_status:
recommendation_for_task_real_struc_002:
```

Then commit and push lightweight deliverables:

```bash
git add PROMPTS/task_real_struc_001b.md
git add scripts workspace CONTEXT doc
git add exp/task_real_struc_001b_full_structure_diagnosis/<timestamp>/*.md
git add exp/task_real_struc_001b_full_structure_diagnosis/<timestamp>/*.csv
git add exp/task_real_struc_001b_full_structure_diagnosis/<timestamp>/*.json
git add exp/task_real_struc_001b_full_structure_diagnosis/<timestamp>/diagnostic_plots
git add exp/task_real_struc_001b_full_structure_diagnosis/<timestamp>/recon_compare
git commit -m "Add full struc 001b ReMiC-Net diagnosis"
git push origin task_struc_series
```

Do not commit large checkpoint files if they are ignored by repository policy. Record their local paths instead.

```

这版 `001b` 的核心变化是：**把完整数据、足够训练轮数、metadata 审计、S03/S05 失败追查、指标口径审计、OOD 调查、分支提交都写成硬性要求**。Codex 如果做不到，就只能提交 `incomplete_report.md`，不能再把 smoke test 包装成完整实验。
```

