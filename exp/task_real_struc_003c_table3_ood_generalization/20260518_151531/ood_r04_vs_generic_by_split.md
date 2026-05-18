# ood_r04_vs_generic_by_split

## Leave-One-Family-Out OOD

delta_NMSE = 0.002376; delta_PSNR = 0.009995; delta_SSIM = 0.002461.
R04 better seed counts: NMSE 2/3, PSNR 2/3, SSIM 2/3.
Paired sample ratios: NMSE 0.650, SSIM 0.697.
Bootstrap paired delta_NMSE 95% CI: [0.001615, 0.003198].
Conclusion: tied within tolerance.

## Random-ET OOD

delta_NMSE = -0.000186; delta_PSNR = 0.010953; delta_SSIM = 0.010007.
R04 better seed counts: NMSE 1/3, PSNR 1/3, SSIM 1/3.
Paired sample ratios: NMSE 0.553, SSIM 0.607.
Bootstrap paired delta_NMSE 95% CI: [-0.017169, 0.017012].
Conclusion: mixed.

## Unseen-Parameter OOD

delta_NMSE = -0.000296; delta_PSNR = -0.001282; delta_SSIM = -0.000549.
R04 better seed counts: NMSE 2/3, PSNR 2/3, SSIM 1/3.
Paired sample ratios: NMSE 0.527, SSIM 0.393.
Bootstrap paired delta_NMSE 95% CI: [-0.001287, 0.000830].
Conclusion: tied within tolerance.

