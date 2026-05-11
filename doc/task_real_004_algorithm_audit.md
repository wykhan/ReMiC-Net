# task_real_004_algorithm_audit

## Scope

- Audited `reference_plane_matlab_Tan/points_4_202406.m`
- Ran MATLAB R2018b directly through `scripts/run_matlab_reference_plane_audit.sh`
- Verified MATLAB helper transforms `ftx`, `fty`, `iftx`, `ifty`

## MATLAB Main Flow

1. Build or load cylindrical echo tensor `s3(azimuth, frequency, height)`.
2. Apply height-direction FFT with `fty`.
3. Apply azimuth-direction FFT with `ftx`.
4. Build `Kwz = sqrt(Kw^2 - Kz^2)` for each height-frequency pair.
5. For every reference radius `rho_ref(j)`:
   - build `rn_ref = sqrt(R^2 + rho_ref^2 - 2 R rho_ref cos(u))`
   - form reference matching kernel `exp(1i * rn_ref * Kwz) * (Kw / 2)`
   - FFT the kernel along azimuth
   - multiply it with echo spectrum
   - sum over frequency
   - inverse FFT along azimuth to get `Three_Image(:, j, nh)`
6. Apply height-direction inverse FFT with `ifty`.
7. Perform geometry correction from cylindrical `(u, rho_ref, z)` grid to Cartesian `(x, y, z)` through local sinc interpolation.

## Inputs / Outputs Seen In MATLAB

- Input echo layout: `s3(Na, Nr, Nh)`
- FFT order: height FFT first, then azimuth FFT
- Reference library in the original script: `rho_ref = 0:0.01:0.30`
- Matching output before geometry correction: `Three_Image(Na, Num_rho_ref, Nh)`
- Final Cartesian output: `Image_2D_Card(x, y, z)`

## What Was Missing In Python Before task_real_004

- The old Python path did not build a reference-surface image stack indexed by `rho_ref`.
- It did not perform the MATLAB-style frequency-domain matching kernel multiplication.
- It did not run a cylindrical-to-Cartesian geometry correction stage.
- Its FFT preprocessing existed only as a lightweight prelude to local matched filtering, not as the main accelerated engine.

## What Was Preserved In The New Engine

- Height FFT -> azimuth FFT ordering
- Reference-surface kernel construction in `Kwz`
- One shared cylindrical engine for `ref3/ref5/ref7/ref9/BP`
- Height inverse FFT after reference-surface matching
- Final geometry correction into Cartesian output volume

## Engineering Deviations

- The Python port operates on the active local azimuth-height window extracted from the saved sparse true-echo tensor, instead of forcing a dense global `1101 x 501` cube for every controlled point sample.
- Cartesian sampling uses linear interpolation over the available reduced reference set, rather than the original full-library sinc stencil. This keeps the reduced-reference approximation explicit while preserving target localization.
- The MATLAB audit run uses a synthetic single-point echo generated from the same formulas and helper transforms, rather than running the full human-body script end to end.
