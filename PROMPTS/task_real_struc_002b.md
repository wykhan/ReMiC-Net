

````markdown id="rrvhai"
# task_real_struc_002b: Search for a FiLM Variant That Outperforms Generic FiLM

## 0. Task Identity

Task name:

```text
task_real_struc_002b
````

Experiment title:

```text
Search for a Reference-Surface-Aware FiLM Variant That Outperforms Generic FiLM
```

Target branch:

```text
task_struc_series
```

This task follows:

```text
task_real_struc_001b
task_real_struc_002a
```

Previous 002a result directory:

```text
exp/task_real_struc_002a_pcyc_encoding_ablation/20260516_094012/
```

---

## 1. Core Scientific Goal

This task is not merely an RSB-FiLM envelope ablation.

The SCI-paper-oriented goal is:

> Find a FiLM-variant structure that outperforms the strong generic FiLM baseline.

RSB-FiLM is the first candidate. If optimized RSB-FiLM can outperform generic FiLM, it should remain the main structural innovation.

If optimized RSB-FiLM cannot outperform generic FiLM, this task should further explore other reference-surface-aware FiLM variants to determine whether another physically motivated FiLM structure can become the main method.

The task must answer:

```text
Can a reference-surface-aware FiLM variant outperform generic FiLM in magnitude NMSE, PSNR, SSIM, runtime, and OOD stability?
```

---

## 2. Background From 002a

002a established that learnable Pcyc input should use sin-cos encoding.

Therefore, all new ReMiC-Net / FiLM variants in this task must use:

```text
geometry input = [Mshell, delta_rho, sin(pi * Pcyc), cos(pi * Pcyc)]
```

Do not return to scalar Pcyc as the default learnable geometry input.

In 002a:

```text
P02_rsbfilm_sincos_Pcyc
```

is the current RSB-FiLM sin-cos baseline.

The strongest generic FiLM baselines are:

```text
P04_generic_film_scalar_Pcyc
P05_generic_film_sincos_Pcyc
```

Among them, `P05_generic_film_sincos_Pcyc` is the most important direct baseline because it uses the same sin-cos Pcyc encoding as the new ReMiC-Net variants.

The main target of 002b is to beat:

```text
P05_generic_film_sincos_Pcyc
```

not merely to beat P02.

---

## 3. Branch and Git Requirements

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

## 4. Frozen Project Setup

Use the frozen project context:

```text
CONTEXT/real_cylindrical_master_document_with_physics_consistency.md
CONTEXT/simulation_protocol.md
CONTEXT/reference_surface_strategy.md
CONTEXT/repo_map.md
```

Use the frozen data source:

```text
/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006d_800_formal/20260419_112717/
```

Use the full split:

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

## 5. Frozen Main Metrics

The primary model-selection metrics are:

```text
runtime
speedup vs BP
magnitude NMSE
PSNR
SSIM
```

Also report seed stability and OOD stability.

Do not use support-masked metrics, high-mismatch metrics, or shell-boundary metrics as primary selection criteria. They are diagnostic only.

---

## 6. Scope Control

This task may change:

```text
FiLM variant structure
RSB-FiLM envelope formula
how geometry features generate gamma/beta/gates
bounded modulation design
```

This task must not change:

```text
dataset split
ref3 physical backbone
training label
residual learning form
loss function
optimizer family
Pcyc learnable input encoding default
reference surfaces
```

Default learnable geometry input remains:

```text
[Mshell, delta_rho, sin(pi*Pcyc), cos(pi*Pcyc)]
```

Do not add:

```text
support mask auxiliary head
Dice loss
BCE loss
hard-region loss
foreground/support weighted loss
complex echo-domain consistency loss
```

This task focuses on FiLM structure, not loss design.

---

## 7. Required Baselines

Use exact names.

### G00_generic_film_sincos_Pcyc

Equivalent to 002a `P05_generic_film_sincos_Pcyc`.

Inputs:

```text
image branch: X_ref3
geometry branch: [Mshell, delta_rho, sin(pi*Pcyc), cos(pi*Pcyc)]
fusion: generic FiLM
```

Purpose:

```text
strong direct generic FiLM baseline to beat
```

If 002a checkpoints and metrics are compatible, reuse them and mark:

```text
source = reused_from_002a
```

Otherwise rerun with the 002b pipeline.

### G01_generic_film_scalar_Pcyc

Equivalent to 002a `P04_generic_film_scalar_Pcyc`.

Purpose:

```text
SSIM-strong generic FiLM reference
```

May be reused from 002a if compatible.

### R00_rsbfilm_sincos_env_absPcyc

Equivalent to 002a `P02_rsbfilm_sincos_Pcyc`.

Inputs:

```text
image branch: X_ref3
geometry branch: [Mshell, delta_rho, sin(pi*Pcyc), cos(pi*Pcyc)]
fusion: RSB-FiLM
envelope: abs(Pcyc)
```

Purpose:

```text
current RSB-FiLM baseline
```

---

## 8. Stage A: Optimize RSB-FiLM Envelope

First test whether improved RSB-FiLM can beat generic FiLM.

All Stage A variants use:

```text
geometry input = [Mshell, delta_rho, sin(pi*Pcyc), cos(pi*Pcyc)]
RSB-FiLM placement = E2, E3, B, D3, D2
epsilon_m   = 0.05
alpha_gamma = 0.5
alpha_beta  = 0.1
```

Define:

```text
delta_rho_norm = clip(abs(delta_rho) / 0.075, 0, 1)
p = abs(Pcyc)
d = delta_rho_norm
```

### R01_rsbfilm_env_absDelta

Envelope:

```text
m = epsilon_m + (1 - epsilon_m) * d
```

Purpose:

```text
test whether geometric radial deviation is a better modulation strength indicator than wrapped phase state
```

### R02_rsbfilm_env_maxPcycDelta

Envelope:

```text
m = epsilon_m + (1 - epsilon_m) * max(p, d)
```

Purpose:

```text
avoid underestimating mismatch when Pcyc is small because of phase wrapping but geometric deviation is large
```

### R03_rsbfilm_env_avgPcycDelta

Envelope:

```text
m = epsilon_m + (1 - epsilon_m) * (0.5 * p + 0.5 * d)
```

Purpose:

```text
smoothly combine cyclic phase mismatch and geometric radial deviation
```

### R04_rsbfilm_env_productPcycDelta

Envelope:

```text
m = epsilon_m + (1 - epsilon_m) * sqrt(clamp(p * d, 0, 1))
```

Purpose:

```text
emphasize regions where both phase mismatch and geometric deviation are high
```

### R05_rsbfilm_env_softPcyc

Envelope:

```text
m = epsilon_m + (1 - epsilon_m) * sigmoid(k * (p - 0.25))
```

Use:

```text
k = 8
```

Purpose:

```text
softly emphasize high cyclic phase mismatch regions while preserving differentiability
```

---

## 9. Stage B: Explore Alternative FiLM Variants if RSB-FiLM Is Not Enough

Stage B must be executed if no Stage A RSB-FiLM variant clearly outperforms `G00_generic_film_sincos_Pcyc` on the main criteria.

The goal of Stage B is to find a different FiLM variant that can serve as the SCI innovation point.

All Stage B variants still use:

```text
geometry input = [Mshell, delta_rho, sin(pi*Pcyc), cos(pi*Pcyc)]
```

### F01_bounded_generic_film

Use generic FiLM, but bound gamma and beta:

```text
gamma_bounded = alpha_gamma * tanh(gamma_raw)
beta_bounded  = alpha_beta  * tanh(beta_raw)
F_tilde = (1 + gamma_bounded) * F + beta_bounded
```

No physical envelope.

Purpose:

```text
test whether bounded modulation alone improves stability over generic FiLM
```

### F02_residual_film_gate

Use a learnable gate that blends original features and modulated features:

```text
F_film = (1 + gamma_bounded) * F + beta_bounded
g = sigmoid(g_raw)
F_tilde = (1 - g) * F + g * F_film
```

Purpose:

```text
prevent over-modulation and allow the network to decide where FiLM should act
```

### F03_reference_surface_gated_film

Use physical envelope and learnable gate jointly:

```text
m_phys = epsilon_m + (1 - epsilon_m) * p
g_learn = sigmoid(g_raw)
g = clamp(m_phys * g_learn, 0, 1)
F_film = (1 + gamma_bounded) * F + beta_bounded
F_tilde = (1 - g) * F + g * F_film
```

Purpose:

```text
combine physical RSB prior with learnable adaptive gating
```

### F04_dual_path_film

Use two modulation paths:

```text
generic path: gamma_g, beta_g
RSB path:     gamma_r, beta_r controlled by physical envelope
```

Then blend:

```text
w = sigmoid(w_raw)
F_generic = (1 + gamma_g) * F + beta_g
F_rsb     = (1 + m * gamma_r_bounded) * F + m * beta_r_bounded
F_tilde   = (1 - w) * F_generic + w * F_rsb
```

Purpose:

```text
let the model interpolate between free generic FiLM and physically constrained RSB-FiLM
```

### F05_delta_conditioned_film

Use delta-rho-conditioned bounded FiLM:

```text
m_delta = epsilon_m + (1 - epsilon_m) * d
F_tilde = (1 + m_delta * gamma_bounded) * F + m_delta * beta_bounded
```

Purpose:

```text
test whether radial deviation is a better physical conditioner than phase mismatch for FiLM control
```

---

## 10. Recommended Execution Strategy

To control compute, use a two-pass strategy.

### Pass 1: Full Stage A

Run these with seeds:

```text
0, 1, 2
```

Variants:

```text
G00_generic_film_sincos_Pcyc
G01_generic_film_scalar_Pcyc
R00_rsbfilm_sincos_env_absPcyc
R01_rsbfilm_env_absDelta
R02_rsbfilm_env_maxPcycDelta
R03_rsbfilm_env_avgPcycDelta
R04_rsbfilm_env_productPcycDelta
R05_rsbfilm_env_softPcyc
```

### Pass 2: Conditional Stage B

If none of R01-R05 beats G00, run Stage B.

Run first with:

```text
seed = 0
```

Variants:

```text
F01_bounded_generic_film
F02_residual_film_gate
F03_reference_surface_gated_film
F04_dual_path_film
F05_delta_conditioned_film
```

Then select the top 2 Stage B variants by main validation/test metrics and rerun them with:

```text
seed = 1, 2
```

If compute is sufficient, run all F01-F05 with seeds 0,1,2.

---

## 11. Training Protocol

Use the same training protocol as 002a unless there is a documented bug fix.

Required:

```text
optimizer: AdamW
learning_rate: 1e-3
weight_decay: 1e-4
batch_size: 8 unless GPU memory requires change
epochs: 50
min_epochs: 50
loss: residual/image L1
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

## 12. Main Metrics

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

Primary decision must be based on:

```text
NMSE_mean
PSNR_mean
SSIM_mean
runtime_per_sample
seed stability
OOD NMSE / PSNR / SSIM
```

---

## 13. Diagnostic Metrics

Also report diagnostic metrics, but clearly label them as diagnostics:

```text
metrics_by_delta_rho.csv
metrics_by_Pcyc.csv
metrics_by_shell_boundary.csv
metrics_support_masked.csv
metrics_by_family.csv
```

Diagnostics are used to explain mechanism, not to override the frozen primary metrics.

---

## 14. OOD Evaluation

Evaluate all completed variants on:

```text
Leave-One-Family-Out OOD
Random-ET OOD
Unseen-Parameter OOD
```

Required files:

```text
metrics_ood.csv
per_sample_ood_metrics.csv
```

---

## 15. Output Directory

Create:

```text
exp/task_real_struc_002b_film_variant_search/<timestamp>/
```

Required files:

```text
task_real_struc_002b_report.md
incomplete_report.md                         # only if incomplete
config_summary.json
model_variants.json
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
final_conclusion.json
```

---

## 16. Required Report Structure

The final report must use:

```text
# task_real_struc_002b_report

## 1. Executive Summary

## 2. SCI-Oriented Goal: Beat Generic FiLM

## 3. Relation to 002a

## 4. Frozen Setup and Scope Control

## 5. Strong Generic FiLM Baselines

## 6. Stage A: RSB-FiLM Envelope Optimization

## 7. Stage B: Alternative FiLM Variants

## 8. Training Protocol

## 9. Main Test Results

## 10. Multi-Seed Stability

## 11. Runtime and Complexity

## 12. OOD Results

## 13. Diagnostics by |delta_rho| and |Pcyc|

## 14. Shell-Boundary and Family-Wise Diagnostics

## 15. Visual Comparison

## 16. Did Any FiLM Variant Beat Generic FiLM?

## 17. Which FiLM Variant Should Become the Main Method?

## 18. Recommendation for task_real_struc_002c or task_real_struc_003
```

---

## 17. Decision Rules

### Rule 1: Generic FiLM strong baseline

The primary baseline to beat is:

```text
G00_generic_film_sincos_Pcyc
```

A secondary generic baseline is:

```text
G01_generic_film_scalar_Pcyc
```

### Rule 2: Strong success

A FiLM variant is considered a strong success if it satisfies:

```text
NMSE_mean < G00 NMSE_mean
PSNR_mean > G00 PSNR_mean
SSIM_mean >= G00 SSIM_mean
NMSE_std <= G00 NMSE_std
OOD average not worse than G00
runtime increase <= 20%
```

### Rule 3: Acceptable success

A FiLM variant is considered acceptable if it satisfies:

```text
NMSE_mean approximately equal to G00
PSNR_mean approximately equal to G00
SSIM_mean approximately equal to G00
seed stability better than G00
OOD stability better than G00
runtime comparable to G00
```

Use tolerances:

```text
NMSE tolerance: 0.005
PSNR tolerance: 0.03 dB
SSIM tolerance: 0.005
```

### Rule 4: RSB-FiLM retained as main method

RSB-FiLM can remain the main SCI innovation only if one of R01-R05 satisfies strong or acceptable success.

### Rule 5: Alternative FiLM variant becomes main method

If no RSB-FiLM variant succeeds, but one of F01-F05 satisfies strong or acceptable success, recommend that variant as the new main method.

### Rule 6: Generic FiLM remains strongest

If no FiLM variant beats or matches G00 under the rules above, conclude:

```text
No proposed FiLM variant currently justifies replacing generic FiLM.
```

Then recommend either:

```text
1. make generic FiLM + sin-cos Pcyc the main model, or
2. continue to task_real_struc_002c for modulation strength / placement search.
```

Do not falsely claim RSB-FiLM is superior if it is not.

---

## 18. Final Conclusion Requirements

The final conclusion must explicitly answer:

```text
1. Did any RSB-FiLM envelope variant beat generic FiLM?
2. If yes, which one and why?
3. If no, did any alternative FiLM variant beat generic FiLM?
4. Which model should be the next main-method candidate?
5. Should RSB-FiLM remain the main innovation, become an ablation, or be replaced?
6. What should be done in 002c or 003?
```

---

## 19. Completion Policy

If all required Stage A variants complete and Stage B is either not needed or completed according to the conditional rule, create:

```text
task_real_struc_002b_report.md
status = COMPLETE
```

If a required run fails or Stage B is required but not executed, create:

```text
incomplete_report.md
status = INCOMPLETE
```

Do not report incomplete work as success.

---

## 20. Prohibited Behavior

Do not:

```text
change dataset split
change physical backbone
change reference surfaces
change training label
add hard-region loss
add support/Dice/BCE loss
use BP as training label
return to scalar Pcyc as default input
skip generic FiLM baseline comparison
claim RSB-FiLM is superior without beating or matching G00
push to master
```

---

## 21. Final Console Output

At the end, print:

```text
task_real_struc_002b status: COMPLETE or INCOMPLETE
experiment_root:
current_branch:
remote_push_status:
best_main_metric_model:
best_SSIM_model:
best_OOD_model:
best_RSB_FiLM_variant:
best_alternative_FiLM_variant:
did_RSB_beat_generic_FiLM: yes/no
did_any_variant_beat_generic_FiLM: yes/no
recommended_main_method:
recommendation_for_next_task:
```

Then commit and push lightweight results:

```bash
git add PROMPTS/task_real_struc_002b.md
git add scripts workspace doc
git add exp/task_real_struc_002b_film_variant_search/<timestamp>/*.md
git add exp/task_real_struc_002b_film_variant_search/<timestamp>/*.csv
git add exp/task_real_struc_002b_film_variant_search/<timestamp>/*.json
git add exp/task_real_struc_002b_film_variant_search/<timestamp>/diagnostic_plots
git add exp/task_real_struc_002b_film_variant_search/<timestamp>/recon_compare
git commit -m "Add struc 002b FiLM variant search"
git push origin task_struc_series
```

Do not commit large checkpoints if ignored by repository policy. Record their local paths in the report.

```

这版 002b 的定位是：**以 generic FiLM 为必须超越的强基线，优先优化 RSB-FiLM；若 RSB-FiLM 不够强，则继续探索其他 FiLM 变种，最终找到一个能支撑 SCI 创新点的 FiLM 结构。**
```

