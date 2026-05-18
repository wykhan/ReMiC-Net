# task_real_struc_003c_report

## 1. Executive Summary

status = COMPLETE. All four Table 3 methods were evaluated on all three available OOD splits. The best method by average OOD NMSE is O03_ref3_metadata_RSB_FiLM_R04. R04-vs-generic-FiLM conclusion: R04 and generic FiLM show comparable OOD performance.

current_branch = task_struc_series
pushed_to_remote = yes
remote_branch = origin/task_struc_series

## 2. Purpose: Table 3 OOD Generalization

This task prepares the compact OOD generalization table and tests whether R04 shows stronger OOD robustness than generic FiLM. It is not a Table 1 physical-baseline comparison and not a Table 2 component ablation.

## 3. Relation to Table 1 and Table 2

Table 1 is reused only for the ref3 runtime convention. Table 2 established a small main-test R04 advantage over generic FiLM; this task evaluates whether that advantage is clearer on OOD.

## 4. Frozen Dataset, OOD Splits, and Checkpoint Sources

Dataset source: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006d_800_formal/20260419_112717`. Frozen trained split: train=800, val=100, test=100.

- Leave-One-Family-Out OOD: available at `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006d_800_formal/20260419_112717/datasets/leave_one_family_out_ood/dataset/index.json`
- Random-ET OOD: available at `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006d_800_formal/20260419_112717/datasets/random_et_ood/dataset/index.json`
- Unseen-Parameter OOD: available at `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006d_800_formal/20260419_112717/datasets/unseen_param_ood/dataset/index.json`

Checkpoint/result sources: O00/O01 from `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_struc_001b_full_structure_diagnosis/20260515_001000_fullrunner`; O02/O03 from `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_struc_002b_film_variant_search/20260516_104031`.

## 5. Methods Included in Table 3

Included exactly: O00_ref3, O01_ref3_residual_UNet, O02_ref3_metadata_generic_FiLM, O03_ref3_metadata_RSB_FiLM_R04.

## 6. Methods Excluded From This Task

Excluded from the main table: BP, ref5/ref7/ref9/ref31, metadata concat, R00/R01/R02/R03/R05, F02/F04, scalar Pcyc variants, support-mask variants, hard-region loss variants, RMA, and PFA.

## 7. OOD Evaluation Protocol

Cached OOD predictions/metrics from compatible prior runs were reused. For learned models, network runtime is reused from Table 2 to avoid mixing timing baselines from different historical OOD runs; the table end-to-end runtime is latest main ref3 runtime plus that network runtime. Main ref3 runtime from Table 1: 0.334021s/sample.

## 8. Table 3 OOD Results

See `metrics_ood_summary.csv`, `metrics_ood_by_seed.csv`, and `table3_ood_ready_latex.tex`. R04 NMSE by split: Leave-One-Family-Out 1.003535, Random-ET 1.156704, Unseen-Parameter 0.993286.

## 9. R04 vs Generic FiLM on OOD

- Leave-One-Family-Out OOD: delta_NMSE=0.002376, delta_PSNR=0.009995, delta_SSIM=0.002461, CI=[0.001615, 0.003198], tied within tolerance
- Random-ET OOD: delta_NMSE=-0.000186, delta_PSNR=0.010953, delta_SSIM=0.010007, CI=[-0.017169, 0.017012], mixed
- Unseen-Parameter OOD: delta_NMSE=-0.000296, delta_PSNR=-0.001282, delta_SSIM=-0.000549, CI=[-0.001287, 0.000830], tied within tolerance

Overall: R04 and generic FiLM show comparable OOD performance.

## 10. Seed Stability and Paired Sample Analysis

Seed-wise and paired sample-wise results are in `ood_significance_r04_vs_generic.csv` and `ood_r04_vs_generic_by_split.md`. Bootstrap uses 1000 paired resamples over seed/sample pairs. The evidence should be read at the modest-effect scale unless the confidence interval excludes zero for a split.

## 11. Runtime Notes

OOD measured ref3 runtimes: {"Leave-One-Family-Out OOD": 0.3842128359901835, "Random-ET OOD": 1.6779991902002802, "Unseen-Parameter OOD": 0.5474259072697533}. The main table uses end-to-end runtime, not network-only runtime. R04 overhead over generic FiLM is negligible relative to ref3 reconstruction.

## 12. Interpretation for Paper Table 3

1. R04 improves over ref3 on OOD: yes, NMSE gains by split are [5.701423, 5.895697, 1.902819].
2. R04 improves over residual U-Net on OOD: yes on average; NMSE gains by split are [0.406362, 0.412687, 0.134328].
3. R04 improves over generic FiLM on OOD: not clearly; R04 and generic FiLM show comparable OOD performance.
4. The R04-vs-generic-FiLM OOD advantage is best described as: R04 and generic FiLM show comparable OOD performance.
5. Hardest OOD split by R04 NMSE: Random-ET OOD.
6. OOD behavior supports using R04 as the final model, but the paper wording should match the measured advantage rather than overclaim.
7. Table 3 is ready for paper drafting.

## 13. Limitations

This report does not compare physical baseline quality-speed tradeoffs, Pcyc encoding alternatives, F02/F04 as main methods, support-aware objectives, or RMA/PFA baselines.

## 14. Final Recommendation

Use R04 as the final ReMiC-Net OOD row and include generic FiLM as the key internal baseline. State the OOD conclusion exactly as supported by the significance table.
