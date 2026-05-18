

````markdown
# task_real_struc_003b: Table 2 ReMiC-Net Component Ablation

## 0. Task Identity

Task name:

```text
task_real_struc_003b
````

Experiment title:

```text
ReMiC-Net Component Ablation for Table 2
```

Target branch:

```text
task_struc_series
```

This task belongs to the `task_real_struc` experiment line.

This is **not** a structure search task.

This is **not** an OOD task.

This is **not** a physical-baseline timing task.

The only goal of this task is to collect reliable data for the planned paper Table 2:

> ReMiC-Net Component Ablation.

---

## 1. Scope of This Task

This task only prepares Table 2.

Table 1 main baseline results have already been prepared in:

```text
exp/task_real_struc_003a_table1_main_baselines/20260518_103251/
```

Table 3 OOD generalization will be handled by a later task.

Do not evaluate:

```text
BP
ref5
ref7
ref9
ref31
OOD splits
RMA / PFA
hard-region loss
support/Dice/BCE loss
complex echo-domain consistency
new network families
additional gate / dual-path variants
```

---

## 2. Paper Logic of Table 2

Table 2 should answer one question:

> How much does each ReMiC-Net component contribute?

The components to isolate are:

```text
1. Residual U-Net baseline
2. Reference-surface-aware metadata
3. Metadata-driven FiLM modulation
4. Metadata-driven RSB-FiLM with phase–geometry product envelope
```

The table should show the progression:

```text
ref3 + residual U-Net
→ ref3 + metadata concat
→ ref3 + metadata + generic FiLM
→ ref3 + metadata + RSB-FiLM R04
```

Do not make Table 2 about Pcyc encoding.

Pcyc encoding has already been fixed by task_real_struc_002a. All metadata-based variants in this task must use finalized sin-cos Pcyc encoding:

```text
sin(pi * Pcyc), cos(pi * Pcyc)
```

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

At the end, run:

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

Use the frozen formal dataset source:

```text
/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006d_800_formal/20260419_112717/
```

Use the frozen main split:

```text
train = 800
val   = 100
test  = 100
```

Evaluate all Table 2 variants on the same frozen main test set:

```text
test = 100 samples
```

Physical backbone:

```text
ref3
```

Main input:

```text
X_ref3
```

Final reconstruction form:

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

## 5. Finalized Metadata Definition

All metadata-based variants must use the finalized metadata:

```text
Mshell
delta_rho
sin(pi * Pcyc)
cos(pi * Pcyc)
```

For ref3:

```text
Mshell: one-hot shell id with 3 channels
delta_rho: signed nearest-reference radial deviation
Pcyc: wrapped cyclic phase-deviation variable
```

Do not use scalar Pcyc as the default metadata channel.

Do not include:

```text
valid FOV mask
support prior
support mask
raw scalar Pcyc
scalar + sin-cos Pcyc mixture
```

unless explicitly required for auditing, not for training.

---

## 6. Target Table 2 Variants

Collect results for exactly the following four variants.

Use exact variant names.

---

### A00_ref3_residual_UNet

Table label:

```text
ref3 + residual U-Net
```

Role:

```text
baseline learned compensation without metadata and without FiLM
```

Input:

```text
X_ref3
```

Metadata:

```text
none
```

Modulation:

```text
none
```

Envelope:

```text
none
```

Expected source:

```text
exp/task_real_struc_001b_full_structure_diagnosis/20260515_001000_fullrunner/
```

Equivalent previous variant:

```text
S02_plain_residual_unet
```

If compatible checkpoints and metrics are available, reuse them.

If not compatible, rerun with the frozen training protocol.

---

### A01_ref3_metadata_concat_sincos

Table label:

```text
ref3 + metadata concat
```

Role:

```text
tests whether reference-surface-aware metadata helps when simply concatenated as extra input channels
```

Input channels:

```text
X_ref3
Mshell
delta_rho
sin(pi * Pcyc)
cos(pi * Pcyc)
```

Architecture:

```text
plain residual 3D U-Net
```

Metadata handling:

```text
direct input-channel concatenation
```

Modulation:

```text
none
```

Envelope:

```text
none
```

Important:

This variant is not generic FiLM and not RSB-FiLM. It tests metadata contribution without feature modulation.

If an existing compatible checkpoint exists, reuse it only if it uses exactly:

```text
[Mshell, delta_rho, sin(pi*Pcyc), cos(pi*Pcyc)]
```

Do not reuse a variant that uses:

```text
scalar Pcyc
scalar + sin-cos Pcyc
support prior
valid FOV mask
```

If no compatible checkpoint exists, train this variant.

---

### A02_ref3_metadata_generic_FiLM_sincos

Table label:

```text
ref3 + metadata + generic FiLM
```

Role:

```text
tests whether metadata-driven feature modulation helps beyond direct metadata concatenation
```

Main input:

```text
X_ref3
```

Geometry input:

```text
Mshell
delta_rho
sin(pi * Pcyc)
cos(pi * Pcyc)
```

Modulation:

```text
generic FiLM
```

Envelope:

```text
none
```

Expected source:

```text
exp/task_real_struc_002b_film_variant_search/20260516_104031/
```

Equivalent previous variant:

```text
G00_generic_film_sincos_Pcyc
```

If compatible checkpoints and metrics are available, reuse them.

If not compatible, rerun with the frozen training protocol.

---

### A03_ref3_metadata_RSB_FiLM_R04

Table label:

```text
ref3 + metadata + RSB-FiLM R04
```

Role:

```text
proposed final ReMiC-Net component setting
```

Main input:

```text
X_ref3
```

Geometry input:

```text
Mshell
delta_rho
sin(pi * Pcyc)
cos(pi * Pcyc)
```

Modulation:

```text
bounded RSB-FiLM
```

RSB-FiLM placement:

```text
E2, E3, B, D3, D2
```

Envelope:

```text
m(v) = epsilon_m + (1 - epsilon_m) * sqrt(abs(Pcyc(v)) * abs(delta_rho_norm(v)))
```

where:

```text
delta_rho_norm = clip(abs(delta_rho) / 0.075, 0, 1)
```

Default parameters:

```text
epsilon_m   = 0.05
alpha_gamma = 0.5
alpha_beta  = 0.1
```

Expected source:

```text
exp/task_real_struc_002b_film_variant_search/20260516_104031/
```

Equivalent previous variant:

```text
R04_rsbfilm_env_productPcycDelta
```

If compatible checkpoints and metrics are available, reuse them.

If not compatible, rerun with the frozen training protocol.

---

## 7. Methods Explicitly Excluded From Table 2

Do not include:

```text
BP
ref3 alone
ref5
ref7
ref9
ref31
R00
R01
R02
R03
R05
F02
F04
Pcyc scalar variants
Pcyc scalar + sin-cos variants
support-mask variants
hard-region loss variants
OOD results
```

Rationale:

```text
Table 2 is a compact component-ablation table.
R00-R05 were structure-search variants.
F02/F04 are off-mainline gate/dual-path variants.
Pcyc encoding was already settled in 002a.
Physical baselines belong to Table 1.
OOD belongs to Table 3.
```

---

## 8. Seeds

For all trainable or reused learned variants, report:

```text
seed = 0, 1, 2
```

If a reused source contains all three seeds, reuse and summarize them.

If a reused source is missing a seed, rerun the missing seed or mark the task incomplete.

Do not report one-seed results as complete.

---

## 9. Training Protocol for Any Rerun

Use the same protocol as 002b unless there is a documented bug fix.

Required:

```text
optimizer: AdamW
learning_rate: 1e-3
weight_decay: 1e-4
batch_size: 8 unless GPU memory requires change
epochs: 50
min_epochs: 50
loss: residual/image L1
train = 800
val = 100
test = 100
```

Do not add:

```text
SSIM loss
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

## 10. Main Metrics

Use the frozen primary metrics:

```text
magnitude NMSE
PSNR
SSIM
runtime
```

For every variant and seed, report:

```text
NMSE
PSNR
SSIM
MAE
network_runtime_per_sample
end_to_end_runtime_per_sample
parameter count
peak GPU memory if available
best epoch
```

For every variant, report:

```text
mean
std
best
worst
num_seeds
```

For learned methods:

```text
end_to_end_runtime_per_sample = ref3_runtime_per_sample + network_runtime_per_sample
```

Use the latest ref3 runtime from task_real_struc_003a if available:

```text
exp/task_real_struc_003a_table1_main_baselines/20260518_103251/
```

Do not compare network-only runtime as the main runtime.

---

## 11. Required Table 2 CSV Format

Create:

```text
table2_component_ablation_mean_std.csv
```

with columns:

```text
variant_id
table_label
metadata
modulation
rsb_envelope
num_seeds
num_test_samples
NMSE_mean
NMSE_std
PSNR_mean
PSNR_std
SSIM_mean
SSIM_std
MAE_mean
MAE_std
network_runtime_per_sample_mean
network_runtime_per_sample_std
end_to_end_runtime_per_sample_mean
end_to_end_runtime_per_sample_std
param_count_mean
source
notes
```

Use metadata values:

```text
none
sin-cos metadata concat
sin-cos metadata branch
```

Use modulation values:

```text
none
generic FiLM
RSB-FiLM
```

Use envelope values:

```text
none
product sqrt(|Pcyc|*|delta_rho_norm|)
```

---

## 12. Required Output Directory

Create a new timestamped experiment root:

```text
exp/task_real_struc_003b_table2_component_ablation/<timestamp>/
```

Required files:

```text
task_real_struc_003b_report.md
incomplete_report.md                         # only if incomplete
config_summary.json
model_variants.json
table2_component_ablation_by_seed.csv
table2_component_ablation_mean_std.csv
table2_ready.md
table2_ready_latex.tex
runtime_table.csv
parameter_count_table.csv
method_sources.json
model_checkpoint_sources.json
training_curves/
prediction_value_stats/
representative_visuals/
environment.txt
git_status.txt
```

Optional but useful:

```text
component_gain_summary.csv
```

This file should report incremental gains:

```text
A01 - A00
A02 - A01
A03 - A02
A03 - A00
```

for:

```text
NMSE improvement
PSNR improvement
SSIM improvement
runtime overhead
```

---

## 13. Required Report Structure

The final report must use:

```text
# task_real_struc_003b_report

## 1. Executive Summary

## 2. Purpose: Table 2 Component Ablation Only

## 3. Relation to Table 1 and Prior Tasks

## 4. Frozen Dataset and Test Split

## 5. Finalized Metadata Definition

## 6. Variants Included in Table 2

## 7. Variants Excluded From This Task

## 8. Training / Reuse Protocol

## 9. Table 2 Main Results

## 10. Incremental Component Gains

## 11. Runtime and Complexity Notes

## 12. Interpretation for Paper Table 2

## 13. Limitations and Items Deferred to 003c

## 14. Final Recommendation
```

---

## 14. Interpretation Requirements

The report must explicitly answer:

```text
1. Does metadata concat improve over residual U-Net?
2. Does metadata + generic FiLM improve over metadata concat?
3. Does RSB-FiLM R04 improve over generic FiLM?
4. Does the final ReMiC-Net R04 improve over residual U-Net?
5. What is the runtime overhead of adding metadata and FiLM?
6. Is the Table 2 result ready for paper drafting?
```

The report must not draw conclusions about:

```text
BP comparison
ref5/ref7/ref9/ref31 comparison
OOD generalization
Pcyc encoding alternatives
F02/F04 gate/dual-path variants
```

---

## 15. Paper-Ready Table Format

The LaTeX table should use the following structure:

```latex
\begin{tabular}{lccccccc}
\toprule
Variant & Metadata & Modulation & RSB envelope & NMSE $\downarrow$ & PSNR $\uparrow$ & SSIM $\uparrow$ & Runtime (s) $\downarrow$ \\
\midrule
ref3 + residual U-Net & -- & -- & -- & ... & ... & ... & ... \\
ref3 + metadata concat & \checkmark & -- & -- & ... & ... & ... & ... \\
ref3 + metadata + generic FiLM & \checkmark & generic & -- & ... & ... & ... & ... \\
ref3 + metadata + RSB-FiLM R04 & \checkmark & RSB-FiLM & product & ... & ... & ... & ... \\
\bottomrule
\end{tabular}
```

Use concise labels. Do not include Pcyc encoding as a column.

Add a table note:

```text
All metadata-based variants use the finalized sin-cos Pcyc encoding.
```

---

## 16. Completion Policy

If all four target variants are evaluated successfully with three seeds:

```text
A00_ref3_residual_UNet
A01_ref3_metadata_concat_sincos
A02_ref3_metadata_generic_FiLM_sincos
A03_ref3_metadata_RSB_FiLM_R04
```

create:

```text
task_real_struc_003b_report.md
status = COMPLETE
```

If any required variant or seed cannot be evaluated, create:

```text
incomplete_report.md
status = INCOMPLETE
```

The incomplete report must state:

```text
which variant is missing
which seed is missing
whether compatible cached checkpoints were searched
whether rerun was attempted
what command or implementation step is needed next
whether partial Table 2 results are usable
```

Do not report incomplete work as complete.

---

## 17. Prohibited Behavior

Do not:

```text
evaluate BP/ref5/ref7/ref9/ref31
evaluate OOD splits
add RMA/PFA baseline
add Pcyc encoding variants
change the frozen R04 model
change the dataset split
change the loss function
add hard-region loss
add support/Dice/BCE loss
add echo-domain consistency loss
compare network-only runtime as main runtime
push to master
```

---

## 18. Final Console Output

At the end, print:

```text
task_real_struc_003b status: COMPLETE or INCOMPLETE
experiment_root:
current_branch:
remote_push_status:
A00_available:
A01_available:
A02_available:
A03_available:
best_quality_variant_by_NMSE:
best_SSIM_variant:
incremental_gain_metadata_concat:
incremental_gain_generic_FiLM:
incremental_gain_RSB_FiLM:
table2_ready: yes/no
recommendation_for_task_real_struc_003c:
```

Then commit and push lightweight deliverables:

```bash
git add PROMPTS/task_real_struc_003b.md
git add scripts workspace doc
git add exp/task_real_struc_003b_table2_component_ablation/<timestamp>/*.md
git add exp/task_real_struc_003b_table2_component_ablation/<timestamp>/*.csv
git add exp/task_real_struc_003b_table2_component_ablation/<timestamp>/*.json
git add exp/task_real_struc_003b_table2_component_ablation/<timestamp>/*.tex
git add exp/task_real_struc_003b_table2_component_ablation/<timestamp>/representative_visuals
git commit -m "Add struc 003b table2 component ablation results"
git push origin task_struc_series
```

Do not commit large checkpoints or caches if ignored by repository policy. Record their local paths instead.

````

这版 `003b` 的核心是：

```text
只做表 2；
只回答 metadata、generic FiLM、RSB-FiLM 各自贡献；
不再讨论 Pcyc encoding；
不再加入 F02/F04；
不碰 BP/ref 系列物理基线；
不做 OOD。
````

