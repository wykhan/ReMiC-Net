# task_real_struc_002a_report

status = COMPLETE

## 1. Executive Summary

002a ran P00-P06 on the frozen 800/100/100 split for 50 epochs and seeds [0, 1, 2].
Best overall model by NMSE mean: `P05_generic_film_sincos_Pcyc`.
Best SSIM model: `P04_generic_film_scalar_Pcyc`.
Decision: adopt sin-cos Pcyc for RSB-FiLM.

## 2. Purpose of 002a

This task isolates the Pcyc encoding choice for ReMiC-Net: no learnable Pcyc, scalar Pcyc, sin-cos Pcyc, and scalar+sin-cos Pcyc.

## 3. Relation to 001b

P00 is the 002a rerun of 001b S08. P04 is the 002a rerun of 001b S07. The prior 001b directory is `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_struc_001b_full_structure_diagnosis/20260515_001000_fullrunner`; this run retrained all required seeds with the 002a pipeline.

## 4. Frozen Setup and Scope Control

Frozen data source, split, ref3 backbone, reference radii, residual learning form, AdamW optimizer, L1 residual loss, RSB envelope, FiLM placement, and alpha/epsilon parameters were kept fixed. The intended variable is only the Pcyc encoding in learnable input channels.

## 5. Pcyc Encoding Audit

See `Pcyc_encoding_audit.md` and `Pcyc_encoding_stats.csv`.

## 6. Model Variants

P00-P06 are listed in `model_variants.json` and `model_config_diffs.md`.

## 7. Training Protocol

AdamW, lr=0.001, weight_decay=0.0001, batch_size=8, epochs=50, min_epochs=50, L1 residual/image loss. Best checkpoints are saved locally under `checkpoints/` and ignored by git.

## 8. Main Test Results

See `metrics_overall_by_seed.csv` and `metrics_overall_summary.csv`.

## 9. Multi-Seed Stability

P00 NMSE_mean=1.0100239095297747, NMSE_std=0.02182570904570788; P02 NMSE_mean=1.0051151071654791, NMSE_std=0.0118313876428905; P03 NMSE_mean=2.663782073085143, NMSE_std=2.357172289912139.

## 10. Runtime and Complexity

See `runtime_table.csv` and `parameter_count_table.csv`.

## 11. OOD Results

OOD datasets were evaluated when available. See `metrics_ood.csv` and `per_sample_ood_metrics.csv`.

## 12. Diagnostics by |delta_rho| and |Pcyc|

See `metrics_by_delta_rho.csv` and `metrics_by_Pcyc.csv`. These diagnostics are interpretive, not primary decision criteria.

## 13. Shell-Boundary and Family-Wise Diagnostics

See `metrics_by_shell_boundary.csv`, `metrics_support_masked.csv`, and `metrics_by_family.csv`.

## 14. Visual Comparison

See `recon_compare/` panels.

## 15. Interpretation: Which Pcyc Encoding Is Best?

Scalar baseline P00 remains the model to beat. P02 adoption rule pass: True. P03 adoption rule pass: False. P05 generic-FiLM sin-cos rule pass: True. P01 comparable-to-P00 rule pass: False.

## 16. Decision: Should Default ReMiC-Net Change Pcyc Encoding?

adopt sin-cos Pcyc for RSB-FiLM

## 17. Recommendation for task_real_struc_002b

If none of the Pcyc encodings clearly beats P00 after OOD review, move to RSB envelope optimization in 002b while keeping scalar Pcyc as the default learnable geometry input.

current_branch = task_struc_series
pushed_to_remote = yes
remote_branch = origin/task_struc_series
