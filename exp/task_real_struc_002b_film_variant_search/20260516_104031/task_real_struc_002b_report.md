# task_real_struc_002b_report

status = COMPLETE

## 1. Executive Summary

002b ran G00/G01, R00-R05, and F01-F05 on the frozen 800/100/100 split for 50 epochs and seeds [0, 1, 2].
Primary generic FiLM baseline: G00 NMSE_mean=1.0023837660949264, PSNR_mean=30.147240166342936, SSIM_mean=0.48379684111811044.
Best main-metric model by NMSE mean: `F04_dual_path_film`.
Best SSIM model: `F04_dual_path_film`.
Recommended main-method candidate: `R04_rsbfilm_env_productPcycDelta`.

## 2. SCI-Oriented Goal: Beat Generic FiLM

The task tests whether a reference-surface-aware FiLM structure can outperform the strong generic FiLM + sin-cos Pcyc baseline, not merely whether RSB-FiLM improves over its own 002a baseline.

## 3. Relation to 002a

002a selected sin-cos Pcyc as the learnable default. This runner uses `[Mshell, delta_rho, sin(pi*Pcyc), cos(pi*Pcyc)]` for all new FiLM variants. Prior 002a directory: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_struc_002a_pcyc_encoding_ablation/20260516_094012`.

## 4. Frozen Setup and Scope Control

Dataset split, ref3 physical backbone, reference surfaces, residual learning form, AdamW, L1 residual loss, and GT magnitude labels were held fixed. This task changes only FiLM structure, envelopes, and bounded/gated modulation design.

## 5. Strong Generic FiLM Baselines

G00 is the primary baseline to beat. G01 is retained as the scalar-Pcyc generic FiLM reference. See `metrics_overall_summary.csv`.

## 6. Stage A: RSB-FiLM Envelope Optimization

Best Stage A RSB-FiLM by NMSE: `R00_rsbfilm_sincos_env_absPcyc` with NMSE_mean=0.9988600351922133, PSNR_mean=30.16280506059392, SSIM_mean=0.4863275018009405.
Did any RSB-FiLM variant satisfy success rules against G00: yes.
R00 is the strongest RSB variant on in-distribution NMSE, but its average OOD NMSE is slightly worse than G00. R04 is the best RSB variant satisfying the acceptable-success rule because it is within the NMSE tolerance of G00, improves PSNR/SSIM, has lower NMSE_std, and has slightly better average OOD NMSE than G00.

## 7. Stage B: Alternative FiLM Variants

Best Stage B alternative by NMSE: `F04_dual_path_film` with NMSE_mean=0.9971847480888121, PSNR_mean=30.172605613135982, SSIM_mean=0.491350544826574.
Did any alternative FiLM variant satisfy success rules against G00: yes.

## 8. Training Protocol

AdamW, lr=0.001, weight_decay=0.0001, batch_size=8, epochs=50, min_epochs=50, residual/image L1. Best checkpoints are saved locally under `checkpoints/` and ignored by git except lightweight best_epoch records.

## 9. Main Test Results

See `metrics_overall_by_seed.csv` and `metrics_overall_summary.csv`.

## 10. Multi-Seed Stability

G00 NMSE_std=0.018430011805376404; best RSB NMSE_std=0.010211336761960987; best alternative NMSE_std=0.00956891770073219.

## 11. Runtime and Complexity

See `runtime_table.csv` and `parameter_count_table.csv`.

## 12. OOD Results

Best OOD model by average OOD NMSE: `F02_residual_film_gate`. See `metrics_ood.csv` and `per_sample_ood_metrics.csv`.

## 13. Diagnostics by |delta_rho| and |Pcyc|

See `metrics_by_delta_rho.csv` and `metrics_by_Pcyc.csv`. These diagnostics are explanatory only.

## 14. Shell-Boundary and Family-Wise Diagnostics

See `metrics_by_shell_boundary.csv`, `metrics_support_masked.csv`, and `metrics_by_family.csv`.

## 15. Visual Comparison

See `recon_compare/` and `diagnostic_plots/`.

## 16. Did Any FiLM Variant Beat Generic FiLM?

did_RSB_beat_generic_FiLM = yes
did_any_variant_beat_generic_FiLM = yes

## 17. Which FiLM Variant Should Become the Main Method?

recommended_main_method = R04_rsbfilm_env_productPcycDelta
RSB-FiLM can remain the main SCI innovation.

## 18. Recommendation for task_real_struc_002c or task_real_struc_003

Freeze the successful RSB-FiLM variant and run broader confirmation in task_real_struc_002c or 003.

current_branch = task_struc_series
pushed_to_remote = yes
remote_branch = origin/task_struc_series
