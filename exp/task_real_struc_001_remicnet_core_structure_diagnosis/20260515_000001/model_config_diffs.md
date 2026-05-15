# model_config_diffs

## S01_ref3

No learning: ref3 physical reconstruction directly.

## S02_plain_residual_unet

Residual 3D U-Net with X_ref3 only.

## S03_concat_Mshell

Residual 3D U-Net with [X_ref3, Mshell].

## S04_concat_Mshell_delta

Residual 3D U-Net with [X_ref3, Mshell, delta_rho].

## S05_concat_Mshell_delta_Pcyc

Residual 3D U-Net with [X_ref3, Mshell, delta_rho, Pcyc].

## S06_geometry_branch_bottleneck_concat

Image branch plus geometry branch with bottleneck concat.

## S07_generic_film_middeep

Geometry branch plus generic FiLM at available mid/deep stages.

## S08_rsbfilm_middeep_default

Geometry branch plus RSB-FiLM envelope and bounded gamma/beta.
