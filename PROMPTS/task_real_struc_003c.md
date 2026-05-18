
````markdown
# task_real_struc_003c: Table 3 OOD Generalization and R04-vs-Generic-FiLM Analysis

## 0. Task Identity

Task name:

```text
task_real_struc_003c
````

Experiment title:

```text
OOD Generalization Table and R04-vs-Generic-FiLM Analysis
```

Target branch:

```text
task_struc_series
```

This task belongs to the `task_real_struc` experiment line.

This is **not** a structure search task.

This is **not** a Table 1 physical-baseline task.

This is **not** a Table 2 component-ablation task.

The only goals of this task are:

```text
1. Prepare the planned paper Table 3: OOD Generalization Results.
2. Evaluate whether ReMiC-Net R04 clearly outperforms generic FiLM under OOD conditions.
```

---

## 1. Background and Motivation

Table 1 has already been prepared in:

```text
exp/task_real_struc_003a_table1_main_baselines/20260518_103251/
```

Table 2 has already been prepared in:

```text
exp/task_real_struc_003b_table2_component_ablation/20260518_141021/
```

Table 2 showed that:

```text
ref3 + metadata + RSB-FiLM R04
```

slightly outperforms:

```text
ref3 + metadata + generic FiLM
```

on the main test set, but the advantage is small.

Therefore, this task must specifically answer:

> Does ReMiC-Net R04 show a clearer advantage over generic FiLM on OOD generalization?

This is important because the SCI paper should not claim that RSB-FiLM is strongly superior to generic FiLM based only on a very small main-test improvement. If R04 has stronger OOD robustness, that becomes a much stronger argument for the reference-surface-aware RSB-FiLM design.

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

The trained models must correspond to the frozen main split:

```text
train = 800
val   = 100
test  = 100
```

Physical backbone:

```text
ref3
```

Main input:

```text
X_ref3
```

Training label:

```text
ground-truth reflectivity magnitude volume
```

Do not use BP as training label.

No retraining is expected unless a required checkpoint is missing.

---

## 4. OOD Splits to Evaluate

Evaluate on all available OOD splits:

```text
Leave-One-Family-Out OOD
Random-ET OOD
Unseen-Parameter OOD
```

If any OOD split is unavailable, do not silently skip it. The report must state:

```text
split name
expected path
whether files exist
why evaluation could not be performed
whether Table 3 remains usable
```

Required OOD output files:

```text
metrics_ood_by_seed.csv
metrics_ood_summary.csv
per_sample_ood_metrics.csv
ood_significance_r04_vs_generic.csv
table3_ood_ready_latex.tex
table3_ood_ready.md
```

---

## 5. Target Table 3 Methods

Evaluate exactly the following methods for Table 3.

Use exact variant names.

---

### O00_ref3

Table label:

```text
ref3
```

Role:

```text
fast physical backbone baseline
```

Input / output:

```text
X_ref3 physical reconstruction only
```

Purpose:

```text
shows OOD performance of the reduced-reference physical backbone before learning compensation
```

No seeds.

Use the same ref3 OOD reconstructions if available, otherwise compute them.

---

### O01_ref3_residual_UNet

Table label:

```text
ref3 + residual U-Net
```

Role:

```text
plain learned compensation baseline without metadata or FiLM
```

Input:

```text
X_ref3
```

Expected checkpoint source:

```text
exp/task_real_struc_001b_full_structure_diagnosis/20260515_001000_fullrunner/
```

Equivalent previous variant:

```text
S02_plain_residual_unet
```

Evaluate seeds:

```text
0, 1, 2
```

---

### O02_ref3_metadata_generic_FiLM

Table label:

```text
ref3 + metadata + generic FiLM
```

Role:

```text
strong internal ablation baseline using ReMiC-Net metadata but no RSB envelope
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

Expected checkpoint source:

```text
exp/task_real_struc_002b_film_variant_search/20260516_104031/
```

Equivalent previous variant:

```text
G00_generic_film_sincos_Pcyc
```

Evaluate seeds:

```text
0, 1, 2
```

This is the key comparison baseline for R04.

---

### O03_ref3_metadata_RSB_FiLM_R04

Table label:

```text
ref3 + metadata + RSB-FiLM R04
```

Role:

```text
proposed final ReMiC-Net method
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

Expected checkpoint source:

```text
exp/task_real_struc_002b_film_variant_search/20260516_104031/
```

Equivalent previous variant:

```text
R04_rsbfilm_env_productPcycDelta
```

Evaluate seeds:

```text
0, 1, 2
```

---

## 6. Methods Explicitly Excluded From Table 3

Do not include the following in the main Table 3:

```text
BP
ref5
ref7
ref9
ref31
metadata concat
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
RMA
PFA
```

Rationale:

```text
Table 3 is the compact OOD generalization table.
F02/F04 are off-mainline gate/dual-path variants.
R00-R05 were structure-search variants.
Pcyc encoding was already settled in 002a.
Physical baseline quality-speed comparison belongs to Table 1.
Component ablation belongs to Table 2.
```

Exception:

If F02/F04 OOD results are already cached and trivial to summarize, they may be included in an optional appendix file:

```text
optional_ood_variant_reference.csv
```

But they must not appear in the main Table 3 unless explicitly noted as supplementary.

---

## 7. Finalized Metadata Definition

All metadata-based variants must use:

```text
Mshell
delta_rho
sin(pi * Pcyc)
cos(pi * Pcyc)
```

Do not use:

```text
scalar Pcyc
scalar + sin-cos Pcyc mixture
valid FOV mask
support prior
support mask
```

All metadata-based variants use the finalized sin-cos Pcyc encoding from task_real_struc_002a.

---

## 8. Main OOD Metrics

For each method, OOD split, and seed, report:

```text
NMSE
PSNR
SSIM
MAE
num_samples
network_runtime_per_sample
end_to_end_runtime_per_sample
```

For learned methods:

```text
end_to_end_runtime_per_sample = ref3_runtime_per_sample + network_runtime_per_sample
```

For physical ref3:

```text
end_to_end_runtime_per_sample = ref3 reconstruction runtime
```

The main Table 3 should report:

```text
NMSE mean ± std
PSNR mean ± std
SSIM mean ± std
```

for each OOD split.

Runtime may be reported in a separate OOD runtime table if Table 3 becomes too wide.

---

## 9. R04-vs-Generic-FiLM OOD Significance Analysis

This task must explicitly analyze whether R04 is meaningfully better than generic FiLM on OOD.

Compare:

```text
O03_ref3_metadata_RSB_FiLM_R04
```

against:

```text
O02_ref3_metadata_generic_FiLM
```

For each OOD split, compute:

```text
delta_NMSE = NMSE_generic_FiLM - NMSE_R04
delta_PSNR = PSNR_R04 - PSNR_generic_FiLM
delta_SSIM = SSIM_R04 - SSIM_generic_FiLM
relative_NMSE_improvement_pct = delta_NMSE / NMSE_generic_FiLM * 100
```

Also compute seed-level and per-sample paired comparisons if possible.

Required significance / robustness outputs:

```text
ood_significance_r04_vs_generic.csv
ood_r04_vs_generic_by_split.md
```

The CSV should include:

```text
ood_split
num_samples
num_seeds
generic_NMSE_mean
r04_NMSE_mean
delta_NMSE
relative_NMSE_improvement_pct
generic_PSNR_mean
r04_PSNR_mean
delta_PSNR
generic_SSIM_mean
r04_SSIM_mean
delta_SSIM
r04_better_seed_count_NMSE
r04_better_seed_count_PSNR
r04_better_seed_count_SSIM
r04_better_sample_ratio_NMSE
r04_better_sample_ratio_SSIM
bootstrap_delta_NMSE_ci95_low
bootstrap_delta_NMSE_ci95_high
conclusion
```

If bootstrap is implemented, use paired bootstrap over samples with at least:

```text
num_bootstrap = 1000
```

If bootstrap is not feasible, at least compute:

```text
seed-wise comparison
paired sample-wise better ratio
mean ± std by seed
```

Do not claim statistical significance unless supported by the computed evidence.

---

## 10. Decision Rules

Use the following decision rules in the report.

### Rule 1: R04 clearly outperforms generic FiLM on OOD

Conclude clear OOD advantage only if R04 satisfies most of:

```text
R04 has lower NMSE_mean than generic FiLM on at least 2 of 3 OOD splits
R04 has higher SSIM_mean than generic FiLM on at least 2 of 3 OOD splits
R04 has equal or better PSNR_mean on at least 2 of 3 OOD splits
R04 has smaller seed std on at least 2 of 3 OOD splits
R04 has positive paired delta_NMSE with CI not crossing zero if bootstrap is available
runtime overhead is negligible
```

### Rule 2: R04 has modest but consistent OOD advantage

Use this conclusion if:

```text
R04 improves most mean metrics, but the gains are small or CI crosses zero.
```

Recommended wording:

```text
R04 provides a consistent but modest OOD improvement over generic FiLM.
```

### Rule 3: R04 and generic FiLM are essentially tied on OOD

Use this conclusion if:

```text
R04 and generic FiLM are within tolerance on most OOD metrics.
```

Tolerances:

```text
NMSE tolerance = 0.005
PSNR tolerance = 0.03 dB
SSIM tolerance = 0.005
```

Recommended wording:

```text
R04 and generic FiLM show comparable OOD performance; the value of R04 should be mainly interpreted as physical interpretability with negligible overhead rather than strong OOD superiority.
```

### Rule 4: generic FiLM outperforms R04 on OOD

Use this conclusion if:

```text
generic FiLM is better on most OOD metrics and splits.
```

Recommended wording:

```text
The current R04 design does not show OOD superiority over generic FiLM. R04 may still be used as the final method if main-test performance and physical interpretability are prioritized, but the paper should avoid claiming OOD superiority.
```

---

## 11. Runtime Rules

Use the latest ref3 runtime from:

```text
exp/task_real_struc_003a_table1_main_baselines/20260518_103251/
```

For learned models:

```text
end_to_end_runtime = ref3_runtime + network_runtime
```

Do not compare network-only runtime as the main runtime.

Report runtime in:

```text
ood_runtime_table.csv
```

If OOD split-specific physical reconstruction runtime differs from main-test ref3 runtime, report both:

```text
main_ref3_runtime_used_for_table
ood_measured_ref3_runtime
```

and explain which one is used.

---

## 12. Required Output Directory

Create a new timestamped experiment root:

```text
exp/task_real_struc_003c_table3_ood_generalization/<timestamp>/
```

Required files:

```text
task_real_struc_003c_report.md
incomplete_report.md                         # only if incomplete
config_summary.json
model_variants.json
metrics_ood_by_seed.csv
metrics_ood_summary.csv
per_sample_ood_metrics.csv
ood_significance_r04_vs_generic.csv
ood_r04_vs_generic_by_split.md
ood_runtime_table.csv
table3_ood_ready.md
table3_ood_ready_latex.tex
method_sources.json
model_checkpoint_sources.json
environment.txt
git_status.txt
```

Optional but useful:

```text
ood_bar_plots/
ood_visual_examples/
optional_ood_variant_reference.csv
```

---

## 13. Required CSV Format

### metrics_ood_summary.csv

Use columns:

```text
method_id
table_label
ood_split
num_seeds
num_samples
NMSE_mean
NMSE_std
PSNR_mean
PSNR_std
SSIM_mean
SSIM_std
MAE_mean
MAE_std
network_runtime_per_sample_mean
end_to_end_runtime_per_sample_mean
source
notes
```

### metrics_ood_by_seed.csv

Use columns:

```text
method_id
table_label
ood_split
seed
num_samples
NMSE_mean
PSNR_mean
SSIM_mean
MAE_mean
network_runtime_per_sample
end_to_end_runtime_per_sample
source
notes
```

### per_sample_ood_metrics.csv

Use columns:

```text
method_id
table_label
ood_split
seed
sample_id
NMSE
PSNR
SSIM
MAE
```

---

## 14. Paper-Ready Table 3 Format

The LaTeX table should be compact.

Recommended format:

```latex
\begin{tabular}{lccc}
\toprule
Method & Leave-One-Family-Out & Random-ET & Unseen-Parameter \\
\midrule
ref3 & NMSE / PSNR / SSIM & ... & ... \\
ref3 + residual U-Net & ... & ... & ... \\
ref3 + metadata + generic FiLM & ... & ... & ... \\
ref3 + metadata + RSB-FiLM R04 & ... & ... & ... \\
\bottomrule
\end{tabular}
```

If this is too wide, create three subtables or report only NMSE in the main table and place PSNR/SSIM in an auxiliary table.

Preferred compact cell format:

```text
NMSE / PSNR / SSIM
```

Example:

```text
1.023 / 30.05 / 0.481
```

For final paper, mean ± std may be used if it remains readable.

Add note:

```text
All learned methods use ref3 as the physical backbone. Metadata-based variants use the finalized sin-cos Pcyc encoding.
```

---

## 15. Required Report Structure

The final report must use:

```text
# task_real_struc_003c_report

## 1. Executive Summary

## 2. Purpose: Table 3 OOD Generalization

## 3. Relation to Table 1 and Table 2

## 4. Frozen Dataset, OOD Splits, and Checkpoint Sources

## 5. Methods Included in Table 3

## 6. Methods Excluded From This Task

## 7. OOD Evaluation Protocol

## 8. Table 3 OOD Results

## 9. R04 vs Generic FiLM on OOD

## 10. Seed Stability and Paired Sample Analysis

## 11. Runtime Notes

## 12. Interpretation for Paper Table 3

## 13. Limitations

## 14. Final Recommendation
```

---

## 16. Interpretation Requirements

The report must explicitly answer:

```text
1. Does ReMiC-Net R04 improve over ref3 on OOD?
2. Does ReMiC-Net R04 improve over residual U-Net on OOD?
3. Does ReMiC-Net R04 improve over generic FiLM on OOD?
4. Is the R04-vs-generic-FiLM OOD advantage clear, modest, tied, or negative?
5. Which OOD split is hardest?
6. Does OOD behavior support using R04 as the final ReMiC-Net model?
7. Is Table 3 ready for paper drafting?
```

The report must not draw conclusions about:

```text
Table 1 physical baseline speed-quality comparison
Pcyc encoding alternatives
F02/F04 as main methods
support-aware objectives
RMA/PFA baselines
```

---

## 17. Completion Policy

If all four target methods are evaluated on all available OOD splits:

```text
O00_ref3
O01_ref3_residual_UNet
O02_ref3_metadata_generic_FiLM
O03_ref3_metadata_RSB_FiLM_R04
```

and the R04-vs-generic-FiLM OOD comparison is completed, create:

```text
task_real_struc_003c_report.md
status = COMPLETE
```

If a required method, seed, or OOD split cannot be evaluated, create:

```text
incomplete_report.md
status = INCOMPLETE
```

The incomplete report must state:

```text
which method / seed / split is missing
whether compatible cached checkpoints were searched
whether rerun or re-evaluation was attempted
what command or implementation step is needed next
whether partial Table 3 results are usable
```

Do not report incomplete work as complete.

---

## 18. Prohibited Behavior

Do not:

```text
train new architectures
change the frozen R04 model
change metadata definition
change Pcyc encoding
add support/Dice/BCE loss
add hard-region loss
add echo-domain consistency loss
add RMA/PFA
add BP/ref5/ref7/ref9/ref31 into Table 3
use network-only runtime as main runtime
claim R04 OOD superiority without evidence
push to master
```

---

## 19. Final Console Output

At the end, print:

```text
task_real_struc_003c status: COMPLETE or INCOMPLETE
experiment_root:
current_branch:
remote_push_status:
OOD_splits_evaluated:
O00_ref3_available:
O01_residual_UNet_available:
O02_generic_FiLM_available:
O03_R04_available:
best_OOD_method_by_average_NMSE:
hardest_OOD_split:
R04_vs_generic_FiLM_OOD_conclusion:
table3_ready: yes/no
recommendation_for_next_task:
```

Then commit and push lightweight deliverables:

```bash
git add PROMPTS/task_real_struc_003c.md
git add scripts workspace doc
git add exp/task_real_struc_003c_table3_ood_generalization/<timestamp>/*.md
git add exp/task_real_struc_003c_table3_ood_generalization/<timestamp>/*.csv
git add exp/task_real_struc_003c_table3_ood_generalization/<timestamp>/*.json
git add exp/task_real_struc_003c_table3_ood_generalization/<timestamp>/*.tex
git add exp/task_real_struc_003c_table3_ood_generalization/<timestamp>/ood_bar_plots
git add exp/task_real_struc_003c_table3_ood_generalization/<timestamp>/ood_visual_examples
git commit -m "Add struc 003c table3 OOD generalization results"
git push origin task_struc_series
```

Do not commit large checkpoints or caches if ignored by repository policy. Record their local paths instead.

````

这版 `003c` 的核心是：

```text
表 3 不再只放 ref3 / U-Net / R04；
必须加入 generic FiLM；
重点判断 R04 在 OOD 上是否比 generic FiLM 更有优势。
````

