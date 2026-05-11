# model_structure.md

## Document Role

This document freezes the current ReMiC-Net model structure for the paper/project:

**Physics-Guided Learned Compensation of Structured Mismatch in Reduced-Reference Cylindrical Aperture 3-D Imaging**

This version incorporates two latest decisions:

1. The Geometry branch input is frozen as
   \[
   G(v)=\left[M_{\mathrm{shell}}(v),\;\delta\rho(v),\;P_{\mathrm{cyc}}(v)\right].
   \]
2. The feature fusion module is upgraded from generic FiLM-style modulation to
   **RSB-FiLM: Reference-Surface-Bounded FiLM**.

This version also removes the support segmentation auxiliary head, BCE/Dice loss, and Dice metric from the main method. The current paper is positioned as **residual mismatch compensation**, not support segmentation.

The current method remains **physics-guided** rather than **complex-echo-consistent**, because the network reconstructs magnitude-domain reflectivity and does not estimate complex reflectivity phase. Complex echo-domain consistency is reserved for future complex-valued extensions.

This document should be used together with:

- `real_cylindrical_master_document.md`
- `simulation_protocol.md`
- `reference_surface_strategy.md`

---

# 0. Version Update Note

## 0.1 Main update

The previous Pcyc version used:

\[
G(v)=
[
M_{\mathrm{shell}}(v),
\delta\rho(v),
P_{\mathrm{cyc}}(v)
]
\]

with generic FiLM-style modulation:

\[
\widetilde{F}_l=(1+\gamma_l)\odot F_l+\beta_l.
\]

The current version freezes the fusion module as:

> **RSB-FiLM: Reference-Surface-Bounded FiLM**.

The RSB-FiLM block uses bounded affine modulation controlled by a deterministic reference-surface phase-mismatch envelope. This prevents learned modulation parameters from overriding the known reference-surface mismatch prior.

## 0.2 Removed from the current main method

The following items are removed from the main architecture and main loss:

- support mask auxiliary head;
- BCE support loss;
- Dice support loss;
- support Dice metric as a main evaluation metric;
- support prior as an input channel;
- valid FOV mask as an input channel.

They can be revisited only as separate future variants or supplementary ablations.

## 0.3 Current method identity

The adopted model is:

> **ReMiC-Net with RSB-FiLM: a Reference-Surface-Aware Residual Mismatch Compensation Network for Reduced-Reference Cylindrical Aperture 3-D Imaging.**

A more descriptive phrase is:

> **a physics-guided residual compensation network with reference-surface-aware cyclic phase conditioning and bounded FiLM feature modulation.**

---

# 1. Model Positioning

The adopted model is not a generic image-enhancement network. It is a:

> **reference-surface-aware, physics-guided residual mismatch compensation network**

for:

> **structured mismatch induced by reduced-reference cylindrical aperture imaging.**

The design principles are:

1. **Physical backbone first**  
   The reduced-reference cylindrical imaging operator `ref3` is retained as the first-stage physical backbone.

2. **Residual learning rather than full image regression**  
   The network learns the mismatch residual between the coarse reconstruction and the high-quality target.

3. **Reference-surface-aware geometry conditioning**  
   The network explicitly uses:
   \[
   [M_{\mathrm{shell}},\delta\rho,P_{\mathrm{cyc}}].
   \]

4. **Bounded modulation rather than unconstrained FiLM**  
   RSB-FiLM bounds the learned feature modulation using fixed scaling limits and a deterministic phase-mismatch envelope.

5. **No support segmentation side task in the main method**  
   The paper focuses on magnitude reflectivity reconstruction and structured mismatch compensation.

---

# 2. Overall Pipeline

## Stage 1: Reduced-reference cylindrical physical backbone

Input raw cylindrical echo data:

\[
y
\]

Use the reduced-reference cylindrical operator:

\[
x_{\mathrm{ref3}}=\mathcal{R}_{\mathrm{ref3}}(y).
\]

where:

- \(y\) is the measured or simulated cylindrical echo data;
- \(\mathcal{R}_{\mathrm{ref3}}\) is the reduced-reference cylindrical imaging operator using 3 reference surfaces;
- \(x_{\mathrm{ref3}}\) is the coarse reconstruction volume.

## Stage 2: ReMiC-Net residual mismatch compensation

The second-stage network takes:

- main image input:
  \[
  X_{\mathrm{ref3}}
  \]
- Geometry branch input:
  \[
  G=[M_{\mathrm{shell}},\delta\rho,P_{\mathrm{cyc}}]
  \]

and predicts:

\[
\widehat{\Delta x}=f_\theta(X_{\mathrm{ref3}},G).
\]

The final reconstruction is:

\[
\boxed{
\hat{x}=X_{\mathrm{ref3}}+\widehat{\Delta x}
}
\]

Important freeze:

> The final residual output is **not** multiplied by a physical gate. The residual output remains clean and direct.

---

# 3. Frozen Input Definition

## 3.1 Main input: `X_ref3`

\[
X_{\mathrm{ref3}}:=x_{\mathrm{ref3}}.
\]

Meaning:

- Coarse reconstruction produced by the `ref3` reduced-reference cylindrical physical backbone.
- Primary image-domain warm start.
- Carries the approximation artifacts to be corrected.

## 3.2 Geometry branch input

\[
\boxed{
G(v)=
[
M_{\mathrm{shell}}(v),
\delta\rho(v),
P_{\mathrm{cyc}}(v)
]
}
\]

where \(v\) denotes a voxel.

---

### (1) `Mshell`: shell/reference allocation map

Meaning:

- Indicates which reference shell / assigned reference surface is responsible for voxel \(v\).
- For `ref3`, it corresponds to the nearest reference surface among:
  \[
  [0.00,0.15,0.30]\;\mathrm{m}.
  \]

Recommended implementation:

- v1 recommended choice: **one-hot shell id**.
- For `ref3`, this gives 3 channels.
- A single assigned-reference-radius map is acceptable as an engineering simplification, but the paper description should use \(M_{\mathrm{shell}}\).

Role:

- Tells the network which approximate physical kernel is effectively responsible for the voxel.
- Helps distinguish different error regimes across radial shells.
- Prevents the network from treating all radial locations as sharing the same mismatch pattern.

---

### (2) `δρ`: signed nearest-reference radial deviation

Definition:

\[
\delta\rho(v)=\rho(v)-\rho_{\mathrm{ref}}^{\ast}(v),
\]

where:

- \(\rho(v)\) is the voxel radial coordinate;
- \(\rho_{\mathrm{ref}}^{\ast}(v)\) is the assigned nearest reference-surface radius.

Recommended implementation:

1. Compute the physical deviation in meters:
   \[
   \delta\rho_{\mathrm{raw}}(v)=\rho(v)-\rho_{\mathrm{ref}}^{\ast}(v).
   \]

2. Use \(\delta\rho_{\mathrm{raw}}\) to compute \(P_{\mathrm{cyc}}\).

3. For network input, use a normalized signed deviation:
   \[
   \widetilde{\delta\rho}(v)=
   \operatorname{clip}
   \left(
   \frac{\delta\rho_{\mathrm{raw}}(v)}{\Delta\rho_{\mathrm{shell}}/2},
   -1,1
   \right).
   \]

Writing convention:

- In paper equations, \(\delta\rho\) denotes the signed nearest-reference deviation.
- In code, record whether the raw or normalized version is used.

Role:

- Encodes how far the voxel is from its assigned reference surface.
- Encodes the sign of the mismatch.
- Provides direct geometric mismatch information.

---

### (3) `Pcyc`: cyclic phase-deviation encoding

Formal name:

> **cyclic phase-deviation encoding**

Chinese writing:

> **周期包裹的归一化相位偏差**

Definition:

\[
\boxed{
P_{\mathrm{cyc}}(v)
=
\frac{1}{\pi}
\operatorname{wrap}_{(-\pi,\pi]}
\left(
 k_{c}^{(2w)}\delta\rho_{\mathrm{raw}}(v)
\right)
}
\]

where:

\[
k_{c}^{(2w)}=\frac{4\pi f_c}{c}=\frac{4\pi}{\lambda_c}.
\]

Current protocol v1:

\[
f_c=34.5\;\mathrm{GHz},
\]

\[
\lambda_c=8.695652\;\mathrm{mm},
\]

\[
k_c^{(2w)}=1445.132621\;\mathrm{rad/m}.
\]

Range:

\[
P_{\mathrm{cyc}}(v)\in(-1,1].
\]

Interpretation:

- \(P_{\mathrm{cyc}}\) does not remove phase periodicity.
- It folds the two-way phase deviation into the principal interval.
- It tells the network the cyclic phase state associated with radial deviation from the reference surface.

Relation to the \(\pi/4\) phase-error intuition:

\[
|\phi_{\mathrm{wrap}}|\leq\frac{\pi}{4}
\quad\Longleftrightarrow\quad
|P_{\mathrm{cyc}}|\leq0.25.
\]

Role:

- Complements \(\delta\rho\).
- \(\delta\rho\) tells the network the signed geometric deviation.
- \(P_{\mathrm{cyc}}\) tells the network the cyclic two-way phase state.
- The two are related but not redundant.

---

# 4. RSB-FiLM: Reference-Surface-Bounded FiLM

## 4.1 Motivation

Generic FiLM uses learned affine modulation:

\[
\widetilde{F}_l=(1+\gamma_l)\odot F_l+\beta_l.
\]

In ReMiC-Net, unconstrained \(\gamma_l\) and \(\beta_l\) could become too large and override the reference-surface prior. RSB-FiLM avoids this by bounding the learned modulation with:

1. a deterministic reference-surface phase-mismatch envelope;
2. fixed scaling limits \(\alpha_\gamma\) and \(\alpha_\beta\);
3. tanh-bounded raw modulation tensors.

## 4.2 Deterministic phase-mismatch envelope

Define:

\[
\boxed{
 m(v)=\epsilon_m+(1-\epsilon_m)|P_{\mathrm{cyc}}(v)|
}
\]

where:

- \(P_{\mathrm{cyc}}(v)\in(-1,1]\);
- \(m(v)\in[\epsilon_m,1]\);
- default \(\epsilon_m=0.05\).

Interpretation:

- small wrapped phase deviation \(\Rightarrow\) weak allowed modulation;
- large wrapped phase deviation \(\Rightarrow\) strong allowed modulation;
- \(\epsilon_m\) prevents the modulation from becoming exactly zero in near-reference areas.

For the \(l\)-th U-Net scale:

\[
 m_l=\operatorname{Downsample}_l(m),
\]

where `Downsample` uses average pooling or trilinear interpolation to match the spatial size of \(F_l\). The map \(m_l\) is broadcast along the channel dimension.

## 4.3 Bounded modulation parameters

The geometry branch predicts raw tensors:

\[
\Gamma_l,
\quad
B_l.
\]

They are converted into bounded FiLM parameters by:

\[
\boxed{
\gamma_l=m_l\alpha_\gamma\tanh(\Gamma_l)
}
\]

\[
\boxed{
\beta_l=m_l\alpha_\beta\tanh(B_l)
}
\]

Therefore:

\[
|\gamma_l|\leq m_l\alpha_\gamma,
\]

\[
|\beta_l|\leq m_l\alpha_\beta.
\]

## 4.4 RSB-FiLM feature modulation

The modulated feature is:

\[
\boxed{
\widetilde{F}_l
=
\left[1+m_l\alpha_\gamma\tanh(\Gamma_l)\right]\odot F_l
+
 m_l\alpha_\beta\tanh(B_l)
}
\]

Equivalent form:

\[
\widetilde{F}_l=(1+\gamma_l)\odot F_l+\beta_l.
\]

Key interpretation:

- \(\Gamma_l,B_l\) learn **how** to modulate features.
- \(m_l\) determines **how strongly modulation is physically allowed**.
- \(\alpha_\gamma,\alpha_\beta\) set conservative global upper bounds.

## 4.5 Default scaling limits

Default values:

\[
\boxed{
\alpha_\gamma=0.5,
\qquad
\alpha_\beta=0.1
}
\]

These values are implementation defaults, but the paper equations should keep symbolic \(\alpha_\gamma,\alpha_\beta\).

Sensitivity ablation:

\[
\alpha_\gamma\in\{0.25,0.5,1.0\},
\]

\[
\alpha_\beta\in\{0,0.1,0.25\}.
\]

## 4.6 Initialization

Recommended implementation:

- zero-initialize the last convolution / projection layer producing \(\Gamma_l\) and \(B_l\);
- at initialization:
  \[
  \Gamma_l\approx0,
  \quad
  B_l\approx0,
  \]
  hence:
  \[
  \widetilde{F}_l\approx F_l.
  \]

This makes the model start close to a plain residual 3D U-Net and avoids early training instability.

## 4.7 Normalization position

Recommended placement within a selected block:

> Conv / Conv3D -> GroupNorm or InstanceNorm -> RSB-FiLM -> activation.

For small 3D batches, GroupNorm or InstanceNorm is preferred over BatchNorm.

---

# 5. 3D U-Net Placement Strategy

Assume a four-level 3D U-Net with:

\[
E_0,E_1,E_2,E_3,B,D_3,D_2,D_1,D_0.
\]

Here:

- \(E_0,E_1\): shallow encoder layers;
- \(E_2,E_3\): middle/deep encoder layers;
- \(B\): bottleneck;
- \(D_3,D_2\): deep decoder layers;
- \(D_1,D_0\): shallow decoder layers.

## 5.1 Frozen default RSB-FiLM locations

\[
\boxed{
\mathcal{L}_{\mathrm{RSB}}
=
\{E_2,E_3,B,D_3,D_2\}
}
\]

## 5.2 Explicitly not modulated

Do not apply RSB-FiLM to:

\[
\boxed{
E_0,E_1,D_1,D_0
}
\]

Do not apply RSB-FiLM directly to skip-connection tensors.

## 5.3 Reason

ReMiC-Net is a residual compensation network, not an image generation network. The decoder must retain direct access to unmodified shallow features from \(X_{\mathrm{ref3}}\). Therefore:

- shallow features and skip paths remain clean observation paths;
- middle and deep features are geometry-conditioned compensation paths.

## 5.4 Generalization to other U-Net depths

If a different U-Net depth is used, apply RSB-FiLM only to:

- the last two encoder scales;
- the bottleneck;
- the first two decoder scales after the bottleneck.

Avoid the first two shallow scales and the final output-near scale.

---

# 6. Frozen Output Head

The current main model keeps only:

> **Residual Head**

Output:

\[
\widehat{\Delta x}.
\]

Final reconstruction:

\[
\boxed{
\hat{x}=X_{\mathrm{ref3}}+\widehat{\Delta x}
}
\]

Target residual:

\[
\Delta x^{\star}=x^{\star}-X_{\mathrm{ref3}}.
\]

No support mask head is used in the current main method.

---

# 7. Frozen Loss Design

## 7.1 Main residual/image loss

Default loss:

\[
\boxed{
\mathcal{L}
=
\lambda_{\mathrm{res}}
\left\|\widehat{\Delta x}-\Delta x^{\star}\right\|_1
+
\lambda_{\mathrm{ssim}}
\left(1-\operatorname{SSIM}(\hat{x},x^{\star})\right)
}
\]

A simpler version is acceptable for initial experiments:

\[
\mathcal{L}=\left\|\widehat{\Delta x}-\Delta x^{\star}\right\|_1.
\]

Equivalent image-domain L1 form:

\[
\left\|\hat{x}-x^{\star}\right\|_1.
\]

## 7.2 Explicitly excluded losses

The current main method does not include:

- support BCE loss;
- support Dice loss;
- complex echo-domain consistency loss;
- sampled complex forward echo loss;
- echo-domain NMSE as a training objective;
- \(\gamma,\beta\) regularization loss as a required term.

Reason:

- support segmentation would make the paper less focused;
- complex echo consistency is not appropriate for magnitude-only reconstruction;
- RSB-FiLM already constrains \(\gamma,\beta\) structurally through bounded parameterization.

---

# 8. Recommended Ablation Order

## 8.1 Main architecture ablation

Recommended order:

1. `ref3` physical backbone only.
2. `ref3 + plain 3D U-Net`.
3. `ref3 + residual-only 3D U-Net`.
4. residual + \(M_{\mathrm{shell}}\).
5. residual + \(M_{\mathrm{shell}}+\delta\rho\).
6. residual + \(M_{\mathrm{shell}}+\delta\rho+P_{\mathrm{cyc}}\).
7. residual + Geometry branch + generic FiLM.
8. residual + Geometry branch + **RSB-FiLM**.

Critical comparisons:

\[
[M_{\mathrm{shell}},\delta\rho]
\quad\text{vs.}\quad
[M_{\mathrm{shell}},\delta\rho,P_{\mathrm{cyc}}]
\]

and:

\[
\text{generic FiLM}
\quad\text{vs.}\quad
\text{RSB-FiLM}.
\]

## 8.2 RSB-FiLM placement ablation

Recommended placement ablation:

| Setting | RSB-FiLM locations | Purpose |
|---|---|---|
| No FiLM | none | residual baseline |
| Bottleneck only | \(B\) | test global geometry conditioning |
| Encoder deep | \(E_2,E_3,B\) | test middle/deep encoding modulation |
| Encoder + decoder deep | \(E_2,E_3,B,D_3,D_2\) | default main method |
| All levels | \(E_0,E_1,E_2,E_3,B,D_3,D_2,D_1,D_0\) | verify shallow all-level modulation is not necessary |

## 8.3 Scaling limit ablation

\[
\alpha_\gamma\in\{0.25,0.5,1.0\}
\]

\[
\alpha_\beta\in\{0,0.1,0.25\}
\]

Default:

\[
\alpha_\gamma=0.5,
\quad
\alpha_\beta=0.1.
\]

## 8.4 Not recommended as main ablation

Do not center the main ablation table around:

- reintroduced `valid FOV mask`;
- reintroduced `support prior`;
- support mask head;
- Dice metric;
- complex echo-domain consistency.

These would dilute the current method story.

---

# 9. Main Evaluation Metrics

Main metrics:

- runtime;
- speedup vs BP;
- magnitude NMSE;
- PSNR;
- SSIM.

Diagnostic metrics/plots:

1. NMSE / SSIM grouped by \(|\delta\rho|\);
2. NMSE / SSIM grouped by \(|P_{\mathrm{cyc}}|\);
3. error comparison between \(|P_{\mathrm{cyc}}|\le0.25\) and \(|P_{\mathrm{cyc}}|>0.25\);
4. performance drop after removing \(P_{\mathrm{cyc}}\);
5. performance drop after replacing RSB-FiLM with generic FiLM.

Not main metrics:

- support Dice;
- complex echo-domain NMSE.

---

# 10. Final Frozen Model Summary

## Inputs

\[
\boxed{
\mathbf{u}
=
[
X_{\mathrm{ref3}},
M_{\mathrm{shell}},
\delta\rho,
P_{\mathrm{cyc}}
]
}
\]

## Core architecture

- Image branch: 3D U-Net encoder-decoder over \(X_{\mathrm{ref3}}\).
- Geometry branch: encodes \([M_{\mathrm{shell}},\delta\rho,P_{\mathrm{cyc}}]\).
- Fusion: RSB-FiLM.
- Output: residual head only.

## RSB-FiLM formula

\[
\boxed{
\widetilde{F}_l
=
\left[1+m_l\alpha_\gamma\tanh(\Gamma_l)\right]\odot F_l
+
 m_l\alpha_\beta\tanh(B_l)
}
\]

with:

\[
\boxed{
m(v)=\epsilon_m+(1-\epsilon_m)|P_{\mathrm{cyc}}(v)|
}
\]

and default:

\[
\epsilon_m=0.05,
\quad
\alpha_\gamma=0.5,
\quad
\alpha_\beta=0.1.
\]

## RSB-FiLM locations

\[
\boxed{
\mathcal{L}_{\mathrm{RSB}}=\{E_2,E_3,B,D_3,D_2\}
}
\]

## Output

\[
\boxed{
\hat{x}=X_{\mathrm{ref3}}+\widehat{\Delta x}
}
\]

No final residual physical gate is used.

## Loss

\[
\boxed{
\mathcal{L}
=
\lambda_{\mathrm{res}}
\|\widehat{\Delta x}-\Delta x^{\star}\|_1
+
\lambda_{\mathrm{ssim}}(1-\operatorname{SSIM}(\hat{x},x^{\star}))
}
\]

---

# 11. Final Statement

This document freezes the current project model as:

> **ReMiC-Net with RSB-FiLM: a Reference-Surface-Aware Physics-Guided Residual Mismatch Compensation Network using cyclic phase-deviation metadata and bounded FiLM modulation.**

Any future modification to:

- input channel definition;
- \(P_{\mathrm{cyc}}\) formula;
- RSB-FiLM envelope;
- RSB-FiLM placement;
- output head design;
- loss composition;
- support segmentation extension;
- complex-valued echo consistency extension

must create a new versioned update rather than silently modifying this file.
