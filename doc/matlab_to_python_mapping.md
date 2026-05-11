# matlab_to_python_mapping

## Mapping Summary

| MATLAB step | MATLAB location | Python location |
| --- | --- | --- |
| Echo tensor layout `s3(azimuth, frequency, height)` | `points_4_202406.m` | `workspace.recon.cyl_fast_reference_engine._make_local_dense_echo` |
| Height FFT `fty` | `points_4_202406.m`, `fty.m` | `workspace.recon.cyl_fast_reference_engine._fft_height_then_azimuth` |
| Azimuth FFT `ftx` | `points_4_202406.m`, `ftx.m` | `workspace.recon.cyl_fast_reference_engine._fft_height_then_azimuth` |
| `Kwz` construction | `points_4_202406.m` | `workspace.recon.cyl_fast_reference_engine._reference_surface_stack` |
| Reference kernel `exp(1i * rn_ref * Kwz) * Kw / 2` | `points_4_202406.m` | `workspace.recon.cyl_fast_reference_engine._reference_surface_stack` |
| Azimuth inverse FFT `iftx` after frequency summation | `points_4_202406.m`, `iftx.m` | `workspace.recon.cyl_fast_reference_engine._reference_surface_stack` |
| Height inverse FFT `ifty` | `points_4_202406.m`, `ifty.m` | `workspace.recon.cyl_fast_reference_engine._reference_surface_stack` |
| Cartesian geometry correction | `points_4_202406.m` | `workspace.recon.cyl_fast_reference_engine._geometry_correct_to_cartesian` |

## Step Preservation Status

- Must preserve exactly:
  - FFT order
  - reference-surface matching kernel form
  - one common engine shared by all reduced-reference variants
  - height inverse FFT after reference-surface imaging
- Can be engineering-refactored without changing the algorithm class:
  - local sparse-echo window extraction
  - vectorized kernel application with SciPy FFT
  - Cartesian interpolation implementation details

## Current Protocol-v1 Method Mapping

- `ref3`: use reference set `[0.00, 0.15, 0.30] m`
- `ref5`: use reference set `[0.00, 0.08, 0.15, 0.22, 0.30] m`
- `ref7`: use reference set `[0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30] m`
- `ref9`: use reference set `[0.00, 0.04, 0.08, 0.11, 0.15, 0.19, 0.22, 0.26, 0.30] m`
- `BP`: use the full library `0.00:0.01:0.30`

## Answer To The Required Audit Question

The Python implementation now strictly reproduces these MATLAB fast-algorithm stages:

1. Echo tensor preparation on cylindrical sampling axes.
2. Height FFT.
3. Azimuth FFT.
4. Reference-surface matching in the transformed domain using `Kwz`.
5. Frequency summation plus azimuth inverse FFT to form cylindrical images on each reference surface.
6. Height inverse FFT.
7. Geometry correction into a Cartesian amplitude volume.
