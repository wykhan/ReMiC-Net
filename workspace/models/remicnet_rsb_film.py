from __future__ import annotations

import torch
import torch.nn.functional as F
from torch import nn


class ConvBlock3d(nn.Module):
    def __init__(self, in_channels: int, out_channels: int) -> None:
        super().__init__()
        self.conv1 = nn.Conv3d(in_channels, out_channels, kernel_size=3, padding=1)
        self.act1 = nn.ReLU(inplace=True)
        self.conv2 = nn.Conv3d(out_channels, out_channels, kernel_size=3, padding=1)
        self.act2 = nn.ReLU(inplace=True)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.act1(self.conv1(x))
        x = self.act2(self.conv2(x))
        return x


class GeometryEncoder(nn.Module):
    def __init__(self, in_channels: int = 5, base_channels: int = 8) -> None:
        super().__init__()
        self.enc1 = ConvBlock3d(in_channels, base_channels)
        self.pool1 = nn.AvgPool3d(2)
        self.enc2 = ConvBlock3d(base_channels, base_channels * 2)
        self.pool2 = nn.AvgPool3d(2)
        self.bottleneck = ConvBlock3d(base_channels * 2, base_channels * 4)

    def forward(self, geom: torch.Tensor) -> dict[str, torch.Tensor]:
        g1 = self.enc1(geom)
        g2 = self.enc2(self.pool1(g1))
        gb = self.bottleneck(self.pool2(g2))
        return {"enc1": g1, "enc2": g2, "bottleneck": gb}


class RSBFiLM(nn.Module):
    def __init__(self, feature_channels: int, geometry_channels: int, alpha_gamma: float = 0.5, alpha_beta: float = 0.1) -> None:
        super().__init__()
        self.alpha_gamma = alpha_gamma
        self.alpha_beta = alpha_beta
        self.gamma_proj = nn.Conv3d(geometry_channels, feature_channels, kernel_size=1)
        self.beta_proj = nn.Conv3d(geometry_channels, feature_channels, kernel_size=1)
        nn.init.zeros_(self.gamma_proj.weight)
        nn.init.zeros_(self.gamma_proj.bias)
        nn.init.zeros_(self.beta_proj.weight)
        nn.init.zeros_(self.beta_proj.bias)

    def forward(self, features: torch.Tensor, geometry_feat: torch.Tensor, m_rsb: torch.Tensor) -> torch.Tensor:
        if geometry_feat.shape[-3:] != features.shape[-3:]:
            geometry_feat = F.interpolate(geometry_feat, size=features.shape[-3:], mode="trilinear", align_corners=False)
        if m_rsb.shape[-3:] != features.shape[-3:]:
            m_rsb = F.interpolate(m_rsb, size=features.shape[-3:], mode="trilinear", align_corners=False)
        gamma = m_rsb * self.alpha_gamma * torch.tanh(self.gamma_proj(geometry_feat))
        beta = m_rsb * self.alpha_beta * torch.tanh(self.beta_proj(geometry_feat))
        return (1.0 + gamma) * features + beta


class ResidualUNet3DBaseline(nn.Module):
    def __init__(self, in_channels: int = 1, out_channels: int = 1, base_channels: int = 8) -> None:
        super().__init__()
        self.enc1 = ConvBlock3d(in_channels, base_channels)
        self.pool1 = nn.MaxPool3d(2)
        self.enc2 = ConvBlock3d(base_channels, base_channels * 2)
        self.pool2 = nn.MaxPool3d(2)
        self.bottleneck = ConvBlock3d(base_channels * 2, base_channels * 4)
        self.up2 = nn.ConvTranspose3d(base_channels * 4, base_channels * 2, kernel_size=2, stride=2)
        self.dec2 = ConvBlock3d(base_channels * 4, base_channels * 2)
        self.up1 = nn.ConvTranspose3d(base_channels * 2, base_channels, kernel_size=2, stride=2)
        self.dec1 = ConvBlock3d(base_channels * 2, base_channels)
        self.head = nn.Conv3d(base_channels, out_channels, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        enc1 = self.enc1(x)
        enc2 = self.enc2(self.pool1(enc1))
        bottleneck = self.bottleneck(self.pool2(enc2))
        dec2 = self.up2(bottleneck)
        dec2 = torch.cat([dec2, enc2], dim=1)
        dec2 = self.dec2(dec2)
        dec1 = self.up1(dec2)
        dec1 = torch.cat([dec1, enc1], dim=1)
        dec1 = self.dec1(dec1)
        return self.head(dec1)


class ReMiCNetRSBFiLM(nn.Module):
    def __init__(
        self,
        in_channels: int = 1,
        geometry_channels: int = 5,
        out_channels: int = 1,
        base_channels: int = 8,
        alpha_gamma: float = 0.5,
        alpha_beta: float = 0.1,
    ) -> None:
        super().__init__()
        self.image_enc1 = ConvBlock3d(in_channels, base_channels)
        self.pool1 = nn.MaxPool3d(2)
        self.image_enc2 = ConvBlock3d(base_channels, base_channels * 2)
        self.pool2 = nn.MaxPool3d(2)
        self.image_bottleneck = ConvBlock3d(base_channels * 2, base_channels * 4)
        self.up2 = nn.ConvTranspose3d(base_channels * 4, base_channels * 2, kernel_size=2, stride=2)
        self.dec2 = ConvBlock3d(base_channels * 4, base_channels * 2)
        self.up1 = nn.ConvTranspose3d(base_channels * 2, base_channels, kernel_size=2, stride=2)
        self.dec1 = ConvBlock3d(base_channels * 2, base_channels)
        self.head = nn.Conv3d(base_channels, out_channels, kernel_size=1)

        self.geometry_encoder = GeometryEncoder(in_channels=geometry_channels, base_channels=base_channels)
        self.film_enc1 = RSBFiLM(base_channels, base_channels, alpha_gamma=alpha_gamma, alpha_beta=alpha_beta)
        self.film_enc2 = RSBFiLM(base_channels * 2, base_channels * 2, alpha_gamma=alpha_gamma, alpha_beta=alpha_beta)
        self.film_bottleneck = RSBFiLM(base_channels * 4, base_channels * 4, alpha_gamma=alpha_gamma, alpha_beta=alpha_beta)
        self.film_dec2 = RSBFiLM(base_channels * 2, base_channels * 2, alpha_gamma=alpha_gamma, alpha_beta=alpha_beta)
        self.film_dec1 = RSBFiLM(base_channels, base_channels, alpha_gamma=alpha_gamma, alpha_beta=alpha_beta)

    def forward(self, x: torch.Tensor, geometry: torch.Tensor, m_rsb: torch.Tensor) -> torch.Tensor:
        gfeats = self.geometry_encoder(geometry)
        enc1 = self.image_enc1(x)
        enc1 = self.film_enc1(enc1, gfeats["enc1"], m_rsb)
        enc2 = self.image_enc2(self.pool1(enc1))
        enc2 = self.film_enc2(enc2, gfeats["enc2"], m_rsb)
        bottleneck = self.image_bottleneck(self.pool2(enc2))
        bottleneck = self.film_bottleneck(bottleneck, gfeats["bottleneck"], m_rsb)
        dec2 = self.up2(bottleneck)
        dec2 = torch.cat([dec2, enc2], dim=1)
        dec2 = self.dec2(dec2)
        dec2 = self.film_dec2(dec2, gfeats["enc2"], m_rsb)
        dec1 = self.up1(dec2)
        dec1 = torch.cat([dec1, enc1], dim=1)
        dec1 = self.dec1(dec1)
        dec1 = self.film_dec1(dec1, gfeats["enc1"], m_rsb)
        return self.head(dec1)
