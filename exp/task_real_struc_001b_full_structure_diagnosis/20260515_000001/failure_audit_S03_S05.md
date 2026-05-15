# failure_audit_S03_S05

001a observed collapse for S03 and S05 under 48/12/24 samples and 2 epochs.

- S03 001a NMSE/SSIM: 31.70182440053975 / 0.001341314375087611
- S05 001a NMSE/SSIM: 28.853263289964044 / 0.0014788602410576984

## Current 001b Status

Full corrective retraining was not completed, so the task cannot answer whether S03/S05 still fail after full training.

## Preliminary Causes To Test

- Metadata scale: delta_rho is in meters while Mshell and Pcyc are dimensionless; scale imbalance must be tested during full training.
- Pcyc wrap discontinuity: S09-S11 are required to test sin/cos periodic encoding.
- Channel normalization: concat variants mix sparse one-hot maps with continuous image and phase channels.
- Undertraining: 001a used only 2 epochs; this remains a plausible cause until 50-epoch curves are available.
