## P00_rsbfilm_scalar_Pcyc

RSB-FiLM with geometry [Mshell, delta_rho, Pcyc]; 001b S08 equivalent.
kind=rsb_film, geom_mode=scalar

## P01_rsbfilm_no_Pcyc

RSB-FiLM with geometry [Mshell, delta_rho] and scalar Pcyc only for fixed envelope.
kind=rsb_film, geom_mode=none

## P02_rsbfilm_sincos_Pcyc

RSB-FiLM with geometry [Mshell, delta_rho, sin(pi*Pcyc), cos(pi*Pcyc)].
kind=rsb_film, geom_mode=sincos

## P03_rsbfilm_scalar_plus_sincos_Pcyc

RSB-FiLM with geometry [Mshell, delta_rho, Pcyc, sin(pi*Pcyc), cos(pi*Pcyc)].
kind=rsb_film, geom_mode=scalar_sincos

## P04_generic_film_scalar_Pcyc

Generic FiLM with geometry [Mshell, delta_rho, Pcyc]; 001b S07 equivalent.
kind=generic_film, geom_mode=scalar

## P05_generic_film_sincos_Pcyc

Generic FiLM with geometry [Mshell, delta_rho, sin(pi*Pcyc), cos(pi*Pcyc)].
kind=generic_film, geom_mode=sincos

## P06_concat_scalar_plus_sincos_Pcyc

Residual 3D U-Net with concatenated [X_ref3, Mshell, delta_rho, Pcyc, sin(pi*Pcyc), cos(pi*Pcyc)].
kind=concat_unet, geom_mode=scalar_sincos
