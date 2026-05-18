# task_real_struc_003a_report

status = COMPLETE

## 1. Executive Summary

Table 1 collection completed for BP, ref3, ref5, ref7, ref9, ref31, ref3+residual U-Net, and ref3+ReMiC-Net R04 on the frozen 100-sample main test split.
Best quality by NMSE: `ref3 + ReMiC-Net R04`. Fastest method: `ref3`.

## 2. Purpose: Table 1 Data Collection Only

This task only collects main-method and main-baseline results. No OOD, generic FiLM ablation, metadata ablation, RMA/PFA, or loss/architecture search is included.

## 3. Frozen Dataset and Test Split

Source: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006d_800_formal/20260419_112717`. Test samples: 100.

## 4. Methods Included in Table 1

T01 BP, T02 ref3, T03 ref5, T04 ref7, T05 ref9, T06 ref31, T07 ref3 + residual U-Net, T08 ref3 + ReMiC-Net R04.

## 5. Methods Excluded From This Task

Generic FiLM, metadata concat, R00, F02, F04, RMA, PFA, support-mask variants, hard-region losses, and OOD splits are excluded.

## 6. Metric Definitions

NMSE, PSNR, SSIM, and MAE are computed on normalized magnitude 24^3 volumes using the frozen project metric implementations. Exact true BP is independently peak-normalized after fitting to 24^3 because direct k-domain summation has an arbitrary amplitude scale; no GT structure is used for this normalization.

## 7. Runtime and Speedup Definition

Physical runtime is reconstruction wall time per sample. BP runtime is measured from the direct voxel-wise BP implementation. Learned-method Table 1 runtime is end-to-end ref3 runtime plus network inference runtime. Speedup is true-BP runtime divided by method runtime.

## 8. BP Baseline

BP uses exact k-domain voxel-wise backprojection in `workspace.eval.task_real_struc_003a_table1.true_bp_exact_k_domain`, not the reference-surface cache and not the range-profile accelerated helper. BP runtime mean is 28.113246 s/sample and speedup is fixed to 1.0.

## 9. Physical Reference-Surface Baselines: ref3 / ref5 / ref7 / ref9 / ref31

ref31 is reported as the dense-reference physical baseline using the 31-radius full reference-surface set. It is sourced from the historical `method='BP'` reference-surface cache and is intentionally separated from true BP. See `ref31_implementation_note.md`.

## 10. Learned Compensation Baselines: ref3+U-Net / ref3+ReMiC-Net R04

U-Net source: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_struc_001b_full_structure_diagnosis/20260515_001000_fullrunner`. R04 source: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_struc_002b_film_variant_search/20260516_104031`.

## 11. Table 1 Main Results

See `table1_main_results.csv`, `table1_main_results_mean_std.csv`, and `table1_ready_latex.tex`.

## 12. Interpretation for Paper Table 1

1. ReMiC-Net R04 improves over ref3: True.
2. ReMiC-Net R04 improves over ref3 + residual U-Net: True.
3. ReMiC-Net R04 compared with ref5/ref7/ref9: NMSE 1.001102 vs 3.510261/3.115017/2.803776.
4. ReMiC-Net R04 compared with ref31: NMSE 1.001102 vs 2.593919.
5. Runtime cost relative to ref3: 1.0058x.
6. Speedup relative to BP: 83.6804x.
7. Table 1 is ready for paper drafting. BP and ref31 are distinct: BP is exact k-domain voxel-wise backprojection; ref31 is the dense reference-surface baseline.

## 13. Limitations and Items Deferred to 003b / 003c

Component ablations, generic FiLM contribution, metadata contribution, and OOD generalization are deferred.

## 14. Final Recommendation

Use this Table 1 as the main baseline table and run task_real_struc_003b for component-ablation table preparation.

current_branch = task_struc_series
pushed_to_remote = yes
remote_branch = origin/task_struc_series
