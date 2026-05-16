
````markdown
# task_real_struc_002a: Pcyc Encoding Ablation for ReMiC-Net

## 0. Task Identity

Task name:

```text
task_real_struc_002a
````

Experiment title:

```text
Pcyc Encoding Ablation for ReMiC-Net
```

Target branch:

```text
task_struc_series
```

This task is a focused follow-up to:

```text
task_real_struc_001b
```

Previous full-run result directory:

```text
exp/task_real_struc_001b_full_structure_diagnosis/20260515_001000_fullrunner/
```

This task must focus only on:

```text
Pcyc encoding
```

Do not introduce new envelope strategies, new loss functions, hard-region sampling, support-mask losses, or large FiLM hyperparameter grids in this task.

---

## 1. Background and Motivation

`task_real_struc_001b` established that:

1. `S08_rsbfilm_middeep_default` is a stable ReMiC-Net candidate.
2. `S08` outperforms `S02_plain_residual_unet` on the frozen main metrics:

   * magnitude NMSE
   * PSNR
   * SSIM
   * seed stability
3. `S05_concat_Mshell_delta_Pcyc` using scalar Pcyc is seed-fragile.
4. `S09_concat_Mshell_delta_Pcyc_sincos` achieved strong single-seed NMSE, but was not tested with 3 seeds.
5. `S11_rsbfilm_Pcyc_sincos` was also only tested with one seed.
6. Therefore, the next question is not whether ReMiC-Net beats U-Net, but which Pcyc encoding is best for ReMiC-Net.

The scientific question of this task is:

> Should ReMiC-Net use scalar Pcyc, sin-cos Pcyc, scalar+sin-cos Pcyc, or no Pcyc?

---

## 2. Branch and Git Requirements

Before doing any work:

```bash
git fetch origin
git checkout task_struc_series
git pull origin task_struc_series
```

All new code, prompts, reports, and lightweight results must be committed and pushed to:

```text
origin/task_struc_series
```

Do not push to `master`.

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

---

## 3. Frozen Project Setup

Use the frozen project context:

```text
CONTEXT/real_cylindrical_master_document_with_physics_consistency.md
CONTEXT/simulation_protocol.md
CONTEXT/reference_surface_strategy.md
CONTEXT/repo_map.md
```

Use the frozen data source from 001b:

```text
/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006d_800_formal/20260419_112717/
```

Use the full main split:

```text
train = 800
val   = 100
test  = 100
```

Physical backbone:

```text
ref3
```

Reference surfaces:

```text
[0.00, 0.15, 0.30] m
```

Main input:

```text
X_ref3
```

Geometry metadata base fields:

```text
Mshell
delta_rho
Pcyc
```

Learning form:

```text
Delta_x_hat = f_theta(...)
x_hat = X_ref3 + Delta_x_hat
```

Training label:

```text
ground-truth reflectivity magnitude volume
```

Do not use BP as training label.

---

## 4. Scope Control

This task must not change:

```text
network backbone depth
base channel count
training loss
optimizer
reference-surface protocol
dataset split
RSB-FiLM placement
RSB-FiLM envelope formula
alpha_gamma / alpha_beta / epsilon_m
```

The only intended experimental variable is:

```text
Pcyc encoding used by the geometry branch or input channels
```

Keep the RSB-FiLM default envelope unchanged:

```text
m(v) = epsilon_m + (1 - epsilon_m) * abs(Pcyc(v))
```

Default RSB-FiLM parameters remain:

```text
epsilon_m   = 0.05
alpha_gamma = 0.5
alpha_beta  = 0.1
```

Default RSB-FiLM placement remains:

```text
E2, E3, B, D3, D2
```

---

## 5. Required Model Variants

Run the following variants.

Use exact names.

---

### P00_rsbfilm_scalar_Pcyc

Equivalent to the 001b `S08_rsbfilm_middeep_default`.

Inputs:

```text
image branch: X_ref3
geometry branch: [Mshell, delta_rho, Pcyc]
RSB envelope: abs(Pcyc)
```

Purpose:

```text
baseline default ReMiC-Net from 001b
```

If the 001b checkpoints and metrics for S08 are fully available and compatible, they may be reused as baseline references. However, if any implementation changed after 001b, rerun P00 with the same 002a pipeline.

---

### P01_rsbfilm_no_Pcyc

Inputs:

```text
image branch: X_ref3
geometry branch: [Mshell, delta_rho]
RSB envelope: abs(Pcyc)
```

Important:

```text
Pcyc is not fed into the geometry branch, but scalar Pcyc may still be used internally to compute the fixed RSB envelope.
```

Purpose:

```text
test whether Pcyc is necessary as a learnable conditioning input
```

---

### P02_rsbfilm_sincos_Pcyc

Inputs:

```text
image branch: X_ref3
geometry branch: [Mshell, delta_rho, sin(pi * Pcyc), cos(pi * Pcyc)]
RSB envelope: abs(Pcyc)
```

Purpose:

```text
test whether periodic sin-cos encoding avoids scalar Pcyc wrap discontinuity
```

---

### P03_rsbfilm_scalar_plus_sincos_Pcyc

Inputs:

```text
image branch: X_ref3
geometry branch: [Mshell, delta_rho, Pcyc, sin(pi * Pcyc), cos(pi * Pcyc)]
RSB envelope: abs(Pcyc)
```

Purpose:

```text
test whether combining signed scalar phase state and periodic encoding is better than either alone
```

---

### P04_generic_film_scalar_Pcyc

Equivalent to 001b `S07_generic_film_middeep`.

Inputs:

```text
image branch: X_ref3
geometry branch: [Mshell, delta_rho, Pcyc]
generic FiLM
```

Purpose:

```text
generic FiLM baseline under scalar Pcyc
```

May reuse 001b S07 if compatible.

---

### P05_generic_film_sincos_Pcyc

Inputs:

```text
image branch: X_ref3
geometry branch: [Mshell, delta_rho, sin(pi * Pcyc), cos(pi * Pcyc)]
generic FiLM
```

Purpose:

```text
test whether Pcyc encoding benefit is specific to RSB-FiLM or also appears in generic FiLM
```

---

### P06_concat_scalar_plus_sincos_Pcyc

Inputs:

```text
[X_ref3, Mshell, delta_rho, Pcyc, sin(pi * Pcyc), cos(pi * Pcyc)]
```

Model:

```text
plain residual 3D U-Net with input-channel concatenation
```

Purpose:

```text
input-concat reference to determine whether Pcyc encoding helps only with FiLM or also with direct channel concatenation
```

---

## 6. Required Seeds

Run all P00-P06 variants with:

```text
seed = 0, 1, 2
```

If a baseline is reused from 001b, copy its metrics into the 002a summary table and clearly mark:

```text
source = reused_from_001b
```

If any required seed cannot be completed, do not mark the task complete. Write `incomplete_report.md`.

---

## 7. Training Protocol

Use the same protocol as 001b unless there is a documented bug fix.

Required:

```text
optimizer: AdamW
learning_rate: 1e-3
weight_decay: 1e-4
batch_size: 8 unless GPU memory requires change
epochs: 50
min_epochs: 50
early_stopping_patience: 10 if implemented, but do not stop before 50 epochs
loss: residual/image L1
```

Do not add:

```text
SSIM loss unless it was already part of the exact 001b training protocol
hard-region weighted loss
foreground/support weighted loss
Dice/BCE
complex echo consistency
```

For every trainable run, save:

```text
train_loss_curve.csv
val_loss_curve.csv
best_epoch.txt
checkpoint_best.pt
prediction_value_stats.csv
```

Large checkpoints may remain uncommitted if ignored by `.gitignore`, but their local paths must be recorded.

---

## 8. Metadata and Encoding Audit

Before training, verify and save:

```text
Pcyc_encoding_audit.md
Pcyc_encoding_stats.csv
```

The audit must include:

```text
Pcyc min/max/mean/std
sin(pi*Pcyc) min/max/mean/std
cos(pi*Pcyc) min/max/mean/std
correlation between Pcyc and sin/cos channels if useful
ratio abs(Pcyc)<=0.25
ratio abs(Pcyc)>0.25
NaN/Inf check for all encoded channels
shape and alignment check for each encoded channel
```

Also verify that:

```text
sin(pi*Pcyc)^2 + cos(pi*Pcyc)^2 ≈ 1
```

within numerical tolerance.

---

## 9. Main Metrics

Use the frozen primary metrics:

```text
runtime
speedup vs BP
magnitude NMSE
PSNR
SSIM
```

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

For every model, report:

```text
mean
std
best
worst
```

Main decision must be based on:

```text
NMSE_mean
PSNR_mean
SSIM_mean
runtime_per_sample
seed stability
```

Do not use support-masked or high-mismatch diagnostics as the primary decision rule.

---

## 10. Diagnostic Metrics

Also report diagnostic metrics, but clearly label them as diagnostics rather than primary metrics.

Required diagnostic files:

```text
metrics_by_delta_rho.csv
metrics_by_Pcyc.csv
metrics_by_shell_boundary.csv
metrics_support_masked.csv
metrics_by_family.csv
metrics_ood.csv
```

Diagnostics should include:

```text
|delta_rho| small / medium / large
|Pcyc| small / medium / large
abs(Pcyc)<=0.25
abs(Pcyc)>0.25
shell-boundary band
family-wise metrics
support-masked metrics
```

These are used to interpret mechanism, not to override the frozen primary metrics.

---

## 11. OOD Evaluation

Evaluate all P00-P06 variants on available OOD splits:

```text
Leave-One-Family-Out OOD
Random-ET OOD
Unseen-Parameter OOD
```

If OOD data are unavailable, give a specific reason.

Required:

```text
metrics_ood.csv
per_sample_ood_metrics.csv
```

For OOD, report:

```text
NMSE_mean
PSNR_mean
SSIM_mean
MAE_mean
runtime_with_ref3_per_sample_mean
num_samples
status
```

---

## 12. Output Directory

Create:

```text
exp/task_real_struc_002a_pcyc_encoding_ablation/<timestamp>/
```

Required files:

```text
task_real_struc_002a_report.md
incomplete_report.md                         # only if incomplete
config_summary.json
model_variants.json
Pcyc_encoding_audit.md
Pcyc_encoding_stats.csv
metrics_overall_by_seed.csv
metrics_overall_summary.csv
metrics_by_delta_rho.csv
metrics_by_Pcyc.csv
metrics_by_shell_boundary.csv
metrics_support_masked.csv
metrics_by_family.csv
metrics_ood.csv
per_sample_ood_metrics.csv
runtime_table.csv
parameter_count_table.csv
training_curves/
prediction_value_stats/
recon_compare/
diagnostic_plots/
model_config_diffs.md
environment.txt
git_status.txt
```

---

## 13. Required Report Structure

The final report must use:

```text
# task_real_struc_002a_report

## 1. Executive Summary

## 2. Purpose of 002a

## 3. Relation to 001b

## 4. Frozen Setup and Scope Control

## 5. Pcyc Encoding Audit

## 6. Model Variants

## 7. Training Protocol

## 8. Main Test Results

## 9. Multi-Seed Stability

## 10. Runtime and Complexity

## 11. OOD Results

## 12. Diagnostics by |delta_rho| and |Pcyc|

## 13. Shell-Boundary and Family-Wise Diagnostics

## 14. Visual Comparison

## 15. Interpretation: Which Pcyc Encoding Is Best?

## 16. Decision: Should Default ReMiC-Net Change Pcyc Encoding?

## 17. Recommendation for task_real_struc_002b
```

---

## 14. Decision Rules

Use these rules strictly.

### Rule 1: Default baseline

The default model to beat is:

```text
P00_rsbfilm_scalar_Pcyc
```

which corresponds to 001b S08.

### Rule 2: sin-cos adoption

Adopt sin-cos Pcyc only if P02 or P05 satisfies:

```text
NMSE_mean <= P00 NMSE_mean
PSNR_mean >= P00 PSNR_mean
SSIM_mean >= P00 SSIM_mean - small_tolerance
NMSE_std not larger than P00 by more than 20%
runtime increase <= 20%
OOD not worse than P00
```

Suggested small tolerance:

```text
SSIM tolerance = 0.005
```

### Rule 3: scalar+sin-cos adoption

Adopt scalar+sin-cos Pcyc only if P03 satisfies:

```text
better or equal NMSE_mean than P00
better or equal PSNR_mean than P00
SSIM_mean not worse than P00
seed stability comparable to P00
OOD comparable or better
```

### Rule 4: remove Pcyc

If P01 is comparable to P00, conclude:

```text
Pcyc may not be necessary as a learnable geometry input under the current RSB-FiLM design.
```

But do not remove Pcyc from the RSB envelope in this task.

### Rule 5: concat reference

If P06 performs well but FiLM variants do not, conclude:

```text
Pcyc encoding helps, but current FiLM injection may be suboptimal.
```

If P06 performs poorly while P02/P03 perform well, conclude:

```text
Pcyc is more effective as modulation context than as raw input channel.
```

### Rule 6: no change

If none of P01-P06 clearly beats P00, conclude:

```text
Keep default scalar Pcyc RSB-FiLM from 001b for now.
```

Then recommend moving to envelope optimization in `task_real_struc_002b`.

---

## 15. Completion Policy

If all required variants and seeds complete, create:

```text
task_real_struc_002a_report.md
status = COMPLETE
```

If not, create:

```text
incomplete_report.md
status = INCOMPLETE
```

Do not report incomplete work as success.

---

## 16. Prohibited Behavior

Do not:

```text
change reference surfaces
change dataset split
change loss function
add support/Dice/BCE loss
add hard-region loss
change envelope formula except where explicitly fixed as default abs(Pcyc)
change alpha_gamma / alpha_beta / epsilon_m
train only one seed and call it complete
skip OOD evaluation
skip runtime reporting
push to master
```

---

## 17. Final Console Output

At the end, print:

```text
task_real_struc_002a status: COMPLETE or INCOMPLETE
experiment_root:
current_branch:
remote_push_status:
best_main_metric_model:
best_SSIM_model:
best_OOD_model:
Pcyc_scalar_status:
Pcyc_sincos_status:
Pcyc_scalar_plus_sincos_status:
Pcyc_no_input_status:
recommendation_for_task_real_struc_002b:
```

Then commit and push lightweight results:

```bash
git add PROMPTS/task_real_struc_002a.md
git add scripts workspace doc
git add exp/task_real_struc_002a_pcyc_encoding_ablation/<timestamp>/*.md
git add exp/task_real_struc_002a_pcyc_encoding_ablation/<timestamp>/*.csv
git add exp/task_real_struc_002a_pcyc_encoding_ablation/<timestamp>/*.json
git add exp/task_real_struc_002a_pcyc_encoding_ablation/<timestamp>/diagnostic_plots
git add exp/task_real_struc_002a_pcyc_encoding_ablation/<timestamp>/recon_compare
git commit -m "Add struc 002a Pcyc encoding ablation"
git push origin task_struc_series
```

Do not commit large checkpoints if ignored by repository policy. Record their local paths in the report.

```

这个 002a 的关键是：**只回答 Pcyc 编码问题**。  
如果 002a 发现 `P03_rsbfilm_scalar_plus_sincos_Pcyc` 或 `P02_rsbfilm_sincos_Pcyc` 稳定超过 P00，就可以把下一版 ReMiC-Net 的 Pcyc 输入冻结下来；如果没有超过，就保留 001b 的 S08 默认 scalar Pcyc，进入 002b 做 envelope 优化。
```

