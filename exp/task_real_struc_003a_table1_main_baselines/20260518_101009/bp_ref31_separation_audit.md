# bp_ref31_separation_audit

The earlier 003a output incorrectly mapped the historical frozen cache key `BP` to both Table 1 `BP` and `ref31`. Code inspection shows that historical cache was produced by `reconstruct_cylindrical_reference(method='BP')`, where `PROTOCOL_V1.reference_sets['BP']` is the 31-radius reference-surface grid. The corrected output recomputes `BP` with `true_backproject_sparse_echo` and reserves the historical cache for `ref31` only.

Generated files carrying corrected BP data:

- `true_bp_audit.csv`: direct-BP runtime and reconstruction-grid audit per sample.
- `per_sample_metrics.csv`: corrected per-sample Table 1 metrics; rows with `method=BP` are true BP.
- `table1_main_results_mean_std.csv`: corrected aggregate Table 1 values.
