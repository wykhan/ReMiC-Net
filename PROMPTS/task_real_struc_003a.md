
````markdown
# task_real_struc_003a: Table 1 Main Baseline Data Collection

## 0. Task Identity

Task name:

```text
task_real_struc_003a
````

Experiment title:

```text
Main Method and Baseline Data Collection for Table 1
```

Target branch:

```text
task_struc_series
```

This task belongs to the `task_real_struc` experiment line.

This is **not** a structure search task.

This is **not** an ablation task.

This is **not** an OOD task.

The only goal of this task is to collect reliable data for the planned paper Table 1:

> Main Method and Main Baseline Comparison.

---

## 1. Scope of This Task

This task only collects Table 1 results.

Table 2 component ablation and Table 3 OOD generalization will be handled by later tasks.

Do not implement or evaluate:

```text
metadata ablation
generic FiLM component ablation
RSB-FiLM component ablation
OOD evaluation
RMA / PFA baseline
new network structures
new loss functions
hard-region loss
support/Dice/BCE loss
complex echo-domain consistency
```

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

## 3. Frozen Project Setup

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

This task must evaluate on the frozen main test set:

```text
test = 100 samples
```

All methods must be evaluated on the same test samples.

---

## 4. Target Table 1 Methods

Collect results for the following methods only.

Use exact method names.

---

### T01_BP

Category:

```text
Exact / high-quality physical baseline
```

Method:

```text
BP
```

Purpose:

```text
traditional high-quality reference baseline
```

Requirements:

```text
evaluate magnitude NMSE / PSNR / SSIM on the frozen main test set
measure runtime_per_sample
speedup_vs_BP = 1.0
```

If full BP on all 100 test samples is too expensive but existing BP reconstructions are already available in the frozen dataset, reuse them.

If BP reconstructions are unavailable, run BP on the 100 test samples if feasible.

If BP cannot be run or found, do not fabricate values. Create `incomplete_report.md` and clearly state what is missing.

---

### T02_ref3

Category:

```text
Fast physical backbone
```

Method:

```text
ref3
```

Purpose:

```text
fast reduced-reference physical reconstruction and input to learned models
```

Requirements:

```text
evaluate magnitude NMSE / PSNR / SSIM
measure runtime_per_sample
compute speedup_vs_BP
```

---

### T03_ref9

Category:

```text
Intermediate-reference physical baseline
```

Method:

```text
ref9
```

Purpose:

```text
representative stronger physical baseline with more reference surfaces
```

Requirements:

```text
evaluate magnitude NMSE / PSNR / SSIM
measure runtime_per_sample
compute speedup_vs_BP
```

Do not additionally include ref5 or ref7 in Table 1.

---

### T04_ref31

Category:

```text
Dense-reference physical baseline
```

Method:

```text
ref31
```

Purpose:

```text
high-reference-count physical baseline inside the reference-surface method family
```

Requirements:

```text
evaluate magnitude NMSE / PSNR / SSIM
measure runtime_per_sample
compute speedup_vs_BP
```

Important:

```text
ref31 is not BP.
ref31 must be described as dense-reference physical baseline, not as ground truth.
```

If ref31 is not already implemented, implement it using the existing reference-surface engine by generating 31 reference surfaces over the same imaging radial range/protocol.

Do not change the ref3/ref9 protocol when adding ref31.

---

### T05_ref3_plus_residual_UNet

Category:

```text
Learned compensation baseline
```

Method:

```text
ref3 + residual U-Net
```

Purpose:

```text
plain learning baseline using X_ref3 without ReMiC-Net metadata or RSB-FiLM
```

Requirements:

```text
input: X_ref3
output: Delta_x_hat
final: x_hat = X_ref3 + Delta_x_hat
evaluate magnitude NMSE / PSNR / SSIM
measure runtime_per_sample
compute speedup_vs_BP
```

Use the trained S02 / plain residual U-Net checkpoints from prior full experiments if compatible.

Preferred sources:

```text
exp/task_real_struc_001b_full_structure_diagnosis/20260515_001000_fullrunner/
```

If compatible checkpoints are not available, rerun the model under the same training protocol used in 001b:

```text
train = 800
val = 100
epochs = 50
seeds = 0,1,2
optimizer = AdamW
lr = 1e-3
weight_decay = 1e-4
loss = residual/image L1
```

Report mean ± std over available seeds.

---

### T06_ref3_plus_ReMiCNet_R04

Category:

```text
Proposed method
```

Method:

```text
ref3 + ReMiC-Net R04
```

Frozen model:

```text
R04_rsbfilm_env_productPcycDelta
```

Use the frozen R04 design:

```text
main input:
X_ref3

geometry input:
Mshell
delta_rho
sin(pi * Pcyc)
cos(pi * Pcyc)

conditioning:
RSB-FiLM at E2, E3, B, D3, D2

RSB envelope:
m(v) = epsilon_m + (1 - epsilon_m) * sqrt(abs(Pcyc(v)) * abs(delta_rho_norm(v)))

delta_rho_norm:
clip(abs(delta_rho) / 0.075, 0, 1)

default parameters:
epsilon_m   = 0.05
alpha_gamma = 0.5
alpha_beta  = 0.1

output:
Delta_x_hat

final reconstruction:
x_hat = X_ref3 + Delta_x_hat
```

Purpose:

```text
proposed ReMiC-Net method with finalized input and finalized RSB-FiLM variant
```

Requirements:

```text
evaluate magnitude NMSE / PSNR / SSIM
measure runtime_per_sample
compute speedup_vs_BP
```

Use the trained R04 checkpoints from 002b if compatible.

Preferred source:

```text
exp/task_real_struc_002b_film_variant_search/20260516_104031/
```

If compatible checkpoints are not available, rerun R04 under the same training protocol used in 002b:

```text
train = 800
val = 100
epochs = 50
seeds = 0,1,2
optimizer = AdamW
lr = 1e-3
weight_decay = 1e-4
loss = residual/image L1
```

Report mean ± std over available seeds.

---

## 5. Methods Explicitly Excluded From Table 1

Do not include the following in Table 1:

```text
ref5
ref7
generic FiLM
metadata concat
R00
F02
F04
RMA
PFA
support-mask variants
hard-region loss variants
```

Rationale:

```text
generic FiLM and metadata concat belong to Table 2 component ablation.
OOD belongs to Table 3.
RMA/PFA feasibility is not part of this task.
```

---

## 6. Primary Metrics

Use the frozen primary metrics:

```text
runtime
speedup vs BP
magnitude NMSE
PSNR
SSIM
```

For every method, report:

```text
NMSE
PSNR
SSIM
MAE
runtime_per_sample
speedup_vs_BP
num_test_samples
```

For learned methods with multiple seeds, report:

```text
mean
std
best
worst
num_seeds
```

For deterministic physical methods, report:

```text
mean over test samples
std over test samples if available
num_test_samples
```

---

## 7. Runtime Measurement Rules

Runtime must be measured consistently.

For physical methods:

```text
runtime_per_sample = reconstruction time per test sample
```

For learned compensation methods:

Report both:

```text
network_runtime_per_sample
end_to_end_runtime_per_sample = ref3_runtime_per_sample + network_runtime_per_sample
```

For Table 1, use:

```text
end_to_end_runtime_per_sample
```

for `ref3 + U-Net` and `ref3 + ReMiC-Net R04`.

The speedup must be:

```text
speedup_vs_BP = BP_runtime_per_sample / method_runtime_per_sample
```

If BP runtime is unavailable, leave `speedup_vs_BP` blank and explain why in the report.

Do not compare network-only runtime against BP runtime in the main table.

---

## 8. Output Directory

Create a new timestamped experiment root:

```text
exp/task_real_struc_003a_table1_main_baselines/<timestamp>/
```

Required files:

```text
task_real_struc_003a_report.md
incomplete_report.md                         # only if incomplete
config_summary.json
table1_main_results.csv
table1_main_results_mean_std.csv
per_sample_metrics.csv
runtime_table.csv
speedup_table.csv
method_sources.json
model_checkpoint_sources.json
ref31_implementation_note.md
environment.txt
git_status.txt
```

Optional but recommended:

```text
table1_ready.md
table1_ready_latex.tex
representative_visuals/
```

---

## 9. Required CSV Format

### table1_main_results_mean_std.csv

Use columns:

```text
category
method
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
runtime_per_sample_mean
runtime_per_sample_std
network_runtime_per_sample_mean
end_to_end_runtime_per_sample_mean
speedup_vs_BP_mean
source
notes
```

For physical methods:

```text
num_seeds = 1
network_runtime_per_sample_mean = blank
end_to_end_runtime_per_sample_mean = runtime_per_sample_mean
```

For learned methods:

```text
runtime_per_sample_mean = end_to_end_runtime_per_sample_mean
network_runtime_per_sample_mean = model inference only
end_to_end_runtime_per_sample_mean = ref3 runtime + network runtime
```

---

## 10. Required Report Structure

The final report must use:

```text
# task_real_struc_003a_report

## 1. Executive Summary

## 2. Purpose: Table 1 Data Collection Only

## 3. Frozen Dataset and Test Split

## 4. Methods Included in Table 1

## 5. Methods Excluded From This Task

## 6. Metric Definitions

## 7. Runtime and Speedup Definition

## 8. BP Baseline

## 9. Physical Reference-Surface Baselines: ref3 / ref9 / ref31

## 10. Learned Compensation Baselines: ref3+U-Net / ref3+ReMiC-Net R04

## 11. Table 1 Main Results

## 12. Interpretation for Paper Table 1

## 13. Limitations and Items Deferred to 003b / 003c

## 14. Final Recommendation
```

---

## 11. Interpretation Requirements

The report must explicitly answer:

```text
1. Does ReMiC-Net R04 improve over ref3?
2. Does ReMiC-Net R04 improve over ref3 + residual U-Net?
3. How does ReMiC-Net R04 compare with ref9?
4. How does ReMiC-Net R04 compare with ref31?
5. What is the runtime cost of ReMiC-Net R04 relative to ref3?
6. What is the speedup of ReMiC-Net R04 relative to BP?
7. Is the Table 1 result ready for the paper?
```

Do not draw conclusions about:

```text
component ablation
metadata contribution
generic FiLM contribution
OOD generalization
```

Those belong to later tasks.

---

## 12. Completion Policy

If all six target methods are evaluated successfully:

```text
T01_BP
T02_ref3
T03_ref9
T04_ref31
T05_ref3_plus_residual_UNet
T06_ref3_plus_ReMiCNet_R04
```

create:

```text
task_real_struc_003a_report.md
status = COMPLETE
```

If any required method cannot be evaluated, create:

```text
incomplete_report.md
status = INCOMPLETE
```

The incomplete report must state:

```text
which method is missing
why it is missing
whether existing cached results were searched
what command or implementation step is needed next
whether partial Table 1 results are usable
```

Do not report incomplete work as complete.

---

## 13. Prohibited Behavior

Do not:

```text
add RMA/PFA baseline
evaluate OOD splits
run metadata/generic FiLM/component ablation
change the frozen R04 model
change Pcyc encoding
change RSB envelope
change dataset split
use BP as training label
compare network-only runtime against BP in Table 1
push to master
```

---

## 14. Final Console Output

At the end, print:

```text
task_real_struc_003a status: COMPLETE or INCOMPLETE
experiment_root:
current_branch:
remote_push_status:
BP_available:
ref3_available:
ref9_available:
ref31_available:
U-Net_available:
ReMiCNet_R04_available:
best_quality_method_by_NMSE:
fastest_method:
best_speed_quality_tradeoff:
table1_ready: yes/no
recommendation_for_task_real_struc_003b:
```

Then commit and push lightweight deliverables:

```bash
git add PROMPTS/task_real_struc_003a.md
git add scripts workspace doc
git add exp/task_real_struc_003a_table1_main_baselines/<timestamp>/*.md
git add exp/task_real_struc_003a_table1_main_baselines/<timestamp>/*.csv
git add exp/task_real_struc_003a_table1_main_baselines/<timestamp>/*.json
git add exp/task_real_struc_003a_table1_main_baselines/<timestamp>/*.tex
git commit -m "Add struc 003a table1 main baseline results"
git push origin task_struc_series
```

Do not commit large checkpoints or caches if ignored by repository policy. Record their local paths instead.

````

这版 `003a` 的关键点是：

```text
只做表 1；
只比较 BP / ref3 / ref9 / ref31 / ref3+U-Net / ref3+ReMiC-Net R04；
不做 generic FiLM；
不做 OOD；
不做 RMA/PFA；
runtime 统一使用 end-to-end runtime。
````

