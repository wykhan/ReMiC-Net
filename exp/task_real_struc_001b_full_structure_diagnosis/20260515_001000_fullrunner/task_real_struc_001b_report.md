# task_real_struc_001b_report

status = COMPLETE

## 1. Executive Summary

Full 001b ran S01-S11 on the frozen 800/100/100 split for 50 epochs with required multi-seed variants.
Best overall model by NMSE mean: `S09_concat_Mshell_delta_Pcyc_sincos`.
Best SSIM model: `S08_rsbfilm_middeep_default`.

## 2. Why 001b Was Needed

001a was only a smoke test; it used 48/12/24 samples and 2 epochs. 001b corrects that with full split training, metadata audit, S09-S11 corrective variants, and OOD availability investigation.

## 3. What Was Wrong or Insufficient in 001a

001a was undertrained and used a metadata cache with invalid one-hot padding. The old metadata implementation left display-padding voxels without valid shell allocation.

## 4. Dataset and Full-Split Verification

Verified 800 train / 100 val / 100 test from the frozen 006d handoff manifest.

## 5. Metadata Audit

See `metadata_audit_report.md` and `metadata_stats.csv`. Corrected metadata uses x-y-z axis alignment, valid one-hot shell fill in padding, and scalar Pcyc plus sin/cos corrective channels.

## 6. Metric Definition Audit

See `metric_definition_audit.md`.

## 7. Model Variants and Corrective Variants

See `model_variants.json` and `model_config_diffs.md`.

## 8. Training Protocol and Convergence

AdamW, lr=0.001, weight_decay=0.0001, batch_size=8, epochs=50, min_epochs=50, patience=10. Best checkpoints saved locally under `checkpoints/` and are ignored by git.

## 9. Overall Results

See `metrics_overall_by_seed.csv` and `metrics_overall_summary.csv`.

## 10. Multi-Seed Results

S02/S04/S05/S06/S07/S08 were run with seeds 0,1,2. Other trainable variants were run with seed 0.

## 11. Diagnostics by |delta_rho|

See `metrics_by_delta_rho.csv`.

## 12. Diagnostics by |Pcyc|

See `metrics_by_Pcyc.csv`.

## 13. Shell-Boundary Diagnostics

See `metrics_by_shell_boundary.csv`.

## 14. Support-Masked and Foreground/Background Diagnostics

See `metrics_support_masked.csv`.

## 15. Family-Wise Results

See `metrics_by_family.csv`.

## 16. OOD Results

OOD datasets were found and evaluated with the trained checkpoints. See `metrics_ood.csv` and `per_sample_ood_metrics.csv`.

## 17. S03/S05 Failure Investigation

S03 summary: NMSE_mean=0.996159649730595, SSIM_mean=0.48518480910675693. S05 summary: NMSE_mean=2.6625633589310245, SSIM_mean=0.38562109240724984. See `failure_audit_S03_S05.md`.

## 18. FiLM and RSB-FiLM Analysis

S08 RSB summary: NMSE_mean=1.0014634334527768, SSIM_mean=0.48618716461835604. S11 periodic RSB summary: NMSE_mean=1.018916823494882, SSIM_mean=0.4843729226333772.

## 19. Visual Comparison

See `recon_compare/` panels.

## 20. Runtime and Complexity

See `runtime_table.csv` and `parameter_count_table.csv`.

## 21. Final Scientific Interpretation

Use the summary tables to decide whether metadata and modulation are stable across seeds; do not rely on a single overall NMSE.

## 22. Decision: Which Model Is Actually Supported?

Supported candidate by current full run: `S09_concat_Mshell_delta_Pcyc_sincos` by NMSE, `S08_rsbfilm_middeep_default` by SSIM. Apply hard-region and seed-stability filters before freezing.

## 23. Recommendation for task_real_struc_002

Run OOD inference for the best stable candidates and decide whether to tune periodic Pcyc or RSB envelope strength.
