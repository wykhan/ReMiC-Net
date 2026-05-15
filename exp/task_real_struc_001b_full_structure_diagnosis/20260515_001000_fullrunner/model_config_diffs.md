## S01_ref3

No learning: ref3 physical reconstruction directly.
kind=ref3, geom_mode=scalar

## S02_plain_residual_unet

Residual 3D U-Net with X_ref3 only.
kind=concat_unet, geom_mode=scalar

## S03_concat_Mshell

Residual 3D U-Net with [X_ref3, Mshell].
kind=concat_unet, geom_mode=scalar

## S04_concat_Mshell_delta

Residual 3D U-Net with [X_ref3, Mshell, delta_rho].
kind=concat_unet, geom_mode=scalar

## S05_concat_Mshell_delta_Pcyc

Residual 3D U-Net with [X_ref3, Mshell, delta_rho, Pcyc].
kind=concat_unet, geom_mode=scalar

## S06_geometry_branch_bottleneck_concat

Image branch plus geometry branch with bottleneck concat.
kind=bottleneck_concat, geom_mode=scalar

## S07_generic_film_middeep

Geometry branch plus generic FiLM.
kind=generic_film, geom_mode=scalar

## S08_rsbfilm_middeep_default

Geometry branch plus RSB-FiLM default envelope.
kind=rsb_film, geom_mode=scalar

## S09_concat_Mshell_delta_Pcyc_sincos

Concat with periodic Pcyc sin/cos.
kind=concat_unet, geom_mode=sincos

## S10_geometry_branch_bottleneck_concat_Pcyc_sincos

Geometry branch bottleneck concat with periodic Pcyc.
kind=bottleneck_concat, geom_mode=sincos

## S11_rsbfilm_Pcyc_sincos

RSB-FiLM with periodic Pcyc geometry input and scalar envelope.
kind=rsb_film, geom_mode=sincos
