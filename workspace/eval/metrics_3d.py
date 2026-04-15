from __future__ import annotations

import numpy as np


def nmse(pred: np.ndarray, target: np.ndarray) -> float:
    denom = float(np.sum(target**2)) + 1e-12
    return float(np.sum((pred - target) ** 2) / denom)


def psnr(pred: np.ndarray, target: np.ndarray) -> float:
    mse = float(np.mean((pred - target) ** 2))
    if mse <= 1e-12:
        return 120.0
    peak = float(np.max(target)) if float(np.max(target)) > 0 else 1.0
    return float(20.0 * np.log10(peak) - 10.0 * np.log10(mse))


def ssim_global(pred: np.ndarray, target: np.ndarray) -> float:
    pred = pred.astype(np.float64)
    target = target.astype(np.float64)
    c1 = 0.01**2
    c2 = 0.03**2
    mu_x = float(np.mean(pred))
    mu_y = float(np.mean(target))
    sigma_x = float(np.var(pred))
    sigma_y = float(np.var(target))
    sigma_xy = float(np.mean((pred - mu_x) * (target - mu_y)))
    numerator = (2.0 * mu_x * mu_y + c1) * (2.0 * sigma_xy + c2)
    denominator = (mu_x**2 + mu_y**2 + c1) * (sigma_x + sigma_y + c2)
    return float(numerator / (denominator + 1e-12))
