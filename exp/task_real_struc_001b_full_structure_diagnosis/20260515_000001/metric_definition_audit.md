# metric_definition_audit

## Overall NMSE

Overall NMSE is computed over the full 24^3 normalized volume: sum((pred-GT)^2)/sum(GT^2).

## Hard-Region NMSE

Hard-region NMSE should use the same squared-error numerator but restrict voxels to a deterministic mask, with denominator sum(GT^2 over the same mask). 001a used support-derived quantile masks for delta_rho and Pcyc diagnostics.

## Support and Background

Overall metrics can be dominated by low-valued background voxels for MAE-like metrics and by high-energy foreground for NMSE. 001b therefore requires support_masked_NMSE, foreground_MAE, background_MAE, high_delta_rho_support_NMSE, and high_Pcyc_support_NMSE in the full run.

## Current Status

Metric definitions are documented, but unified diagnostic metrics were not computed for full 001b because full model predictions were not generated.
