## G00_generic_film_sincos_Pcyc

Generic FiLM with geometry [Mshell, delta_rho, sin(pi*Pcyc), cos(pi*Pcyc)]; primary baseline.
kind=generic_film, geom_mode=sincos, envelope_mode=none

## G01_generic_film_scalar_Pcyc

Generic FiLM with geometry [Mshell, delta_rho, Pcyc]; secondary SSIM-strong baseline.
kind=generic_film, geom_mode=scalar, envelope_mode=none

## R00_rsbfilm_sincos_env_absPcyc

RSB-FiLM with sin-cos Pcyc geometry and abs(Pcyc) envelope.
kind=rsb_film, geom_mode=sincos, envelope_mode=abs_pcyc

## R01_rsbfilm_env_absDelta

RSB-FiLM with abs(delta_rho)/0.075 envelope.
kind=rsb_film, geom_mode=sincos, envelope_mode=abs_delta

## R02_rsbfilm_env_maxPcycDelta

RSB-FiLM with max(abs(Pcyc), abs(delta_rho)/0.075) envelope.
kind=rsb_film, geom_mode=sincos, envelope_mode=max_pcyc_delta

## R03_rsbfilm_env_avgPcycDelta

RSB-FiLM with average abs(Pcyc) and normalized abs(delta_rho) envelope.
kind=rsb_film, geom_mode=sincos, envelope_mode=avg_pcyc_delta

## R04_rsbfilm_env_productPcycDelta

RSB-FiLM with sqrt(abs(Pcyc)*normalized abs(delta_rho)) envelope.
kind=rsb_film, geom_mode=sincos, envelope_mode=product_pcyc_delta

## R05_rsbfilm_env_softPcyc

RSB-FiLM with sigmoid soft high-Pcyc envelope.
kind=rsb_film, geom_mode=sincos, envelope_mode=soft_pcyc

## F01_bounded_generic_film

Generic FiLM with bounded gamma and beta and no physical envelope.
kind=bounded_generic_film, geom_mode=sincos, envelope_mode=none

## F02_residual_film_gate

Bounded generic FiLM blended with original features by a learned gate.
kind=residual_film_gate, geom_mode=sincos, envelope_mode=none

## F03_reference_surface_gated_film

Bounded FiLM with physical abs(Pcyc) envelope and learned gate.
kind=reference_surface_gated_film, geom_mode=sincos, envelope_mode=abs_pcyc

## F04_dual_path_film

Dual generic/RSB FiLM paths blended by a learned gate.
kind=dual_path_film, geom_mode=sincos, envelope_mode=abs_pcyc

## F05_delta_conditioned_film

Bounded FiLM controlled by normalized abs(delta_rho) envelope.
kind=delta_conditioned_film, geom_mode=sincos, envelope_mode=abs_delta
