# engine_modes

## Tensor Modes

- `active`
  - Build a contiguous local azimuth window and local contiguous height window from the active sparse echo support.
  - Use this as the default fast mode.
  - Report `active_coverage_ratio` against the local tensor size.

- `dense_global`
  - Build a full protocol tensor with shape `1101 x 181 x 501`.
  - Keep zeros outside the active sparse support.
  - Use this as strict MATLAB / audit mode for hardening comparisons.
  - Not part of the default front-end after `task_real_004b`.

## Geometry Modes

- `linear`
  - Direct bilinear interpolation on the available azimuth axis and current reference-set axis.
  - Cheapest option.
  - Retained only for comparison / legacy compatibility.

- `sinc`
  - Expand the cylindrical image stack to the full protocol reference library.
  - Apply MATLAB-inspired local sinc stencil in azimuth and radial directions during Cartesian correction.
  - Intended to reduce wrap-boundary artifacts and improve MATLAB consistency.
  - Default geometry mode from `task_real_004c` onward.

## Default Front-End Freeze

- Default accelerated front-end:
  - `tensor_mode = active`
  - `geom_mode = sinc`
- Frozen name:
  - `Variant B = active windows + full-library sinc geometry correction`
- `dense_global` remains available only for audit / debug work.
