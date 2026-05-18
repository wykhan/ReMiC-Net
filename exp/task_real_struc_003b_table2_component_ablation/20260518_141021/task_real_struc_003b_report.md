# task_real_struc_003b_report

## 1. Executive Summary

status = COMPLETE. All four Table 2 variants were evaluated on the frozen 800/100/100 main split with seeds 0, 1, and 2. The best NMSE variant is ref3 + metadata + RSB-FiLM R04 (1.001102); the best SSIM variant is ref3 + metadata + RSB-FiLM R04 (0.484811).

current_branch = task_struc_series
pushed_to_remote = yes
remote_branch = origin/task_struc_series

## 2. Purpose: Table 2 Component Ablation Only

This run only prepares the ReMiC-Net component ablation table: residual U-Net, metadata concat, generic FiLM, and RSB-FiLM R04. It does not evaluate BP, ref5/ref7/ref9/ref31, OOD splits, Pcyc encoding alternatives, RMA/PFA, support losses, or gate/dual-path variants.

## 3. Relation to Table 1 and Prior Tasks

A00 reuses the compatible residual U-Net checkpoints from 001b. A02 and A03 reuse the compatible 002b sin-cos metadata FiLM and R04 checkpoints. The ref3 runtime is taken from 003a and added to network runtime for the end-to-end runtime reported here.

## 4. Frozen Dataset and Test Split

Dataset source: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006d_800_formal/20260419_112717`. The frozen main split is train=800, val=100, test=100. Every row in Table 2 reports the same 100-sample main test set.

## 5. Finalized Metadata Definition

All metadata-based variants use exactly `Mshell`, `delta_rho`, `sin(pi * Pcyc)`, and `cos(pi * Pcyc)`. Scalar Pcyc, valid FOV masks, support priors, and scalar+sin-cos mixtures are excluded from Table 2.

## 6. Variants Included in Table 2

- A00_ref3_residual_UNet: 1.430389 NMSE, 0.449707 SSIM.
- A01_ref3_metadata_concat_sincos: 1.020151 NMSE, 0.482541 SSIM.
- A02_ref3_metadata_generic_FiLM_sincos: 1.002384 NMSE, 0.483797 SSIM.
- A03_ref3_metadata_RSB_FiLM_R04: 1.001102 NMSE, 0.484811 SSIM.

## 7. Variants Excluded From This Task

Excluded: BP, ref3 alone, ref5/ref7/ref9/ref31, R00-R05 except R04 as the final row, F02/F04, scalar Pcyc variants, scalar+sin-cos variants, support-mask variants, hard-region loss variants, and all OOD results.

## 8. Training / Reuse Protocol

Optimizer and rerun protocol: AdamW, learning_rate=1e-3, weight_decay=1e-4, batch_size=8, epochs=50, min_epochs=50, residual/image L1. A01 seed 1 and seed 2 were rerun in this 003b root because no compatible cached sin-cos metadata-concat checkpoints existed for those seeds.

## 9. Table 2 Main Results

See `table2_component_ablation_by_seed.csv` and `table2_component_ablation_mean_std.csv`. Main means: A00 NMSE 1.430389, A01 1.020151, A02 1.002384, A03 1.001102.

## 10. Incremental Component Gains

Metadata concat vs residual U-Net: NMSE gain 0.410238, PSNR gain 0.842193, SSIM gain 0.032834.

Generic FiLM vs metadata concat: NMSE gain 0.017767, PSNR gain 0.067196, SSIM gain 0.001256.

RSB-FiLM R04 vs generic FiLM: NMSE gain 0.001281, PSNR gain 0.005154, SSIM gain 0.001014.

Final R04 vs residual U-Net: NMSE gain 0.429287, PSNR gain 0.914543, SSIM gain 0.035104.

## 11. Runtime and Complexity Notes

Runtime is end-to-end: ref3 runtime plus network inference. A00 runtime mean is 0.334980s; A01 is 0.335060s; A02 is 0.335869s; A03 is 0.335960s. R04 adds 0.000980s over residual U-Net.

## 12. Interpretation for Paper Table 2

1. Metadata concat improves over residual U-Net on mean NMSE and SSIM.
2. Metadata + generic FiLM improves over metadata concat on mean NMSE and PSNR, but SSIM is nearly flat.
3. RSB-FiLM R04 improves over generic FiLM on mean NMSE, PSNR, and SSIM.
4. Final ReMiC-Net R04 improves over residual U-Net by 30.01% relative NMSE.
5. The runtime overhead of adding metadata and FiLM is small relative to the ref3 backbone; the A03 end-to-end overhead over A00 is 0.000980s/sample.
6. Table 2 is ready for paper drafting.

## 13. Limitations and Items Deferred to 003c

This table does not test OOD generalization, physical-baseline comparison, Pcyc encoding alternatives, support-aware objectives, or new architecture families. Those are deferred and should not be inferred from Table 2.

## 14. Final Recommendation

Use A03_ref3_metadata_RSB_FiLM_R04 as the Table 2 final ReMiC-Net row. Report the compact four-row progression and state that all metadata variants use finalized sin-cos Pcyc encoding.
