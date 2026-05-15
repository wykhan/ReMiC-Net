# task_real_struc_001_report

## 1. Executive Summary

This is a first-pass, one-seed structure diagnosis on a deterministic subset of the frozen 800/100/100 dataset. All S01-S08 variants were executed under the same residual-learning protocol. The run is diagnostic, not final model tuning.

- S02 vs S05: S05 does not improve over S02
- S05 vs S07: S07 improves over S05
- S07 vs S08: S08 improves over S07
- Best current candidate by NMSE: `S06_geometry_branch_bottleneck_concat`

## 2. Repository and Code Inspection

Inspected `CONTEXT/`, `PROMPTS/`, `scripts/`, `exp/`, `doc/`, and `workspace/`. Reused the frozen `ref3` protocol, `workspace/common/remic_metadata.py`, existing 3D residual U-Net patterns, existing ReMiC-Net/RSB-FiLM concepts, and frozen 006d learning handoff data. The previous task_real_008 implementation compared only baseline U-Net and one ReMiC-Net; this task adds S01-S08 structural ablations.

## 3. Dataset and Split Description

Source manifest: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006d_800_formal/20260419_112717/learning_handoff_manifest_main_800_100_100.json`. Full split is 800 train / 100 val / 100 test; this run used `48` train, `12` val, `24` test samples selected deterministically and stratified by family. OOD interfaces exist in prior scripts, but S01-S08 OOD evaluation was not run in this bounded first-pass diagnosis.

## 4. Model Variants

| key | kind | description |
| --- | --- | --- |
| S01_ref3 | ref3 | No learning: ref3 physical reconstruction directly. |
| S02_plain_residual_unet | concat_unet | Residual 3D U-Net with X_ref3 only. |
| S03_concat_Mshell | concat_unet | Residual 3D U-Net with [X_ref3, Mshell]. |
| S04_concat_Mshell_delta | concat_unet | Residual 3D U-Net with [X_ref3, Mshell, delta_rho]. |
| S05_concat_Mshell_delta_Pcyc | concat_unet | Residual 3D U-Net with [X_ref3, Mshell, delta_rho, Pcyc]. |
| S06_geometry_branch_bottleneck_concat | bottleneck_concat | Image branch plus geometry branch with bottleneck concat. |
| S07_generic_film_middeep | generic_film | Geometry branch plus generic FiLM at available mid/deep stages. |
| S08_rsbfilm_middeep_default | rsb_film | Geometry branch plus RSB-FiLM envelope and bounded gamma/beta. |

## 5. Training Protocol

Seed `0`, AdamW, learning rate `0.001`, weight decay `0.0001`, batch size `4`, epochs `2`, residual L1 loss. The supervised label is GT reflectivity magnitude; BP is not used as label. No support head, BCE/Dice, support prior, FOV mask, or complex echo loss was added.

## 6. Overall Results

| variant | NMSE | PSNR | SSIM | runtime_per_sample | speedup_vs_BP | peak_GPU_memory | num_test_samples |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S01_ref3 | 5.71065 | 23.65197 | 0.19062 | 0.00000 | not_applicable | 139.63 MB | 24 |
| S02_plain_residual_unet | 6.38834 | 23.10868 | 0.09006 | 0.00171 | 1151.73726 | 139.63 MB | 24 |
| S03_concat_Mshell | 31.70182 | 15.82132 | 0.00134 | 0.00095 | 2078.30937 | 139.63 MB | 24 |
| S04_concat_Mshell_delta | 5.43161 | 23.86043 | 0.20012 | 0.00103 | 1913.17363 | 139.63 MB | 24 |
| S05_concat_Mshell_delta_Pcyc | 28.85326 | 16.19125 | 0.00148 | 0.00104 | 1905.38928 | 139.63 MB | 24 |
| S06_geometry_branch_bottleneck_concat | 4.61620 | 24.37595 | 0.20330 | 0.00149 | 1321.59201 | 139.63 MB | 24 |
| S07_generic_film_middeep | 4.71487 | 23.96137 | 0.07843 | 0.00215 | 919.03006 | 139.63 MB | 24 |
| S08_rsbfilm_middeep_default | 4.62180 | 24.03621 | 0.08076 | 0.00189 | 1042.85916 | 139.63 MB | 24 |

## 7. Diagnostics by |delta_rho|

See `metrics_by_delta_rho.csv`. Bins are per-sample support quantiles: small, medium, large.

## 8. Diagnostics by |Pcyc|

See `metrics_by_Pcyc.csv`. Includes quantile bins and the physical split `abs(Pcyc)<=0.25` versus `abs(Pcyc)>0.25`.

## 9. Shell-Boundary Diagnostics

See `metrics_by_shell_boundary.csv`. Shell-boundary band is +/- `0.01` m around rho=0.075 m and rho=0.225 m.

## 10. Family-Wise Results

See `metrics_by_family.csv`. Family labels are inherited from the frozen handoff manifest.

## 11. OOD Results

See `metrics_ood.csv`. OOD S01-S08 execution is recorded as not evaluated in this first-pass run; no OOD conclusions are claimed.

## 12. Runtime and Complexity

See `runtime_table.csv` and `parameter_count_table.csv`.

## 13. Visual Comparison

Representative panels are saved under `recon_compare/` for best, median, failure, hard high-|Pcyc|, and hard large-|delta_rho| cases. Panels include GT, ref3, S02, S05, S07, S08, plus error MIPs.

## 14. Key Findings

S05 does not improve over S02. S07 improves over S05. S08 improves over S07. The first-pass result should be interpreted as a structure signal under limited compute rather than a final ranking.

## 15. Failure Analysis

If structured variants underperform S02, likely bottlenecks are metadata scaling/encoding, FiLM placement in the shallow two-downsample trunk, and training dominated by easy regions. The run does not prove ReMiC-Net ineffective.

## 16. Decision: Is ReMiC-Net structurally justified?

Current decision: `yes, provisionally`. Metadata/FiLM justification requires longer/full-split confirmation and OOD hard-region evaluation.

## 17. Recommendation for task_real_struc_002

Continue with the best structured variant and validate on OOD in task_real_struc_002.
