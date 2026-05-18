# bp_ref31_separation_audit

The earlier 003a output had two runtime problems: it mapped the historical frozen cache key `BP` to both Table 1 `BP` and `ref31`, and then mixed newly measured BP wall time with historical reference-surface cache wall times. The corrected output recomputes all physical runtimes in one run. `BP` is exact k-domain voxel-wise backprojection with an explicit sum over active sparse measurements and all frequencies. `ref31` is the 31-reference reference-surface approximation produced by `reconstruct_cylindrical_reference(method='BP')` and labeled as `ref31`.

Generated files carrying corrected BP data:

- `true_bp_audit.csv`: exact-BP runtime and reconstruction-grid audit per sample.
- `per_sample_metrics.csv`: corrected per-sample Table 1 metrics; rows with `method=BP` are exact true BP.
- `table1_main_results_mean_std.csv`: corrected aggregate Table 1 values.
