# ReMiC-Net Structure Master

**Recommended Git path:** `CONTEXT/remicnet_structure_master_current.md`  
**Status:** CURRENT CANONICAL STRUCTURE MASTER  
**Project:** ReMiC-Net / Reduced-Reference Cylindrical Aperture 3-D Imaging  
**Last updated:** 2026-05-21  
**Purpose:** Freeze the final model structure and resolve all conflicts among earlier ReMiC-Net structure notes, prompts, reports, and drafts.

---

## 0. Canonical Authority Statement

This document is the **only authoritative model-structure master** for the current ReMiC-Net paper and project.

If any conflict exists between this document and older project attachments, older Git documents, earlier Codex prompts, earlier experiment reports, previous ChatGPT conversations, or previous manuscript drafts, **this document has priority**.

In particular, this document supersedes and overrides earlier descriptions that:

1. define **RSB-FiLM as the conceptual identity or sole main method** of ReMiC-Net;
2. use scalar `Pcyc` as the direct network input instead of sin-cos encoding;
3. include valid FOV mask, support prior, support head, BCE loss, Dice loss, or support Dice metric in the main method;
4. include complex echo-domain consistency loss in the current magnitude-domain main method;
5. describe ReMiC-Net as a segmentation-assisted reconstruction framework;
6. describe ReMiC-Net as a black-box image enhancement module;
7. treat BP or dense-reference output as the training target by default.

The current canonical definition is:

```math
ReMiC-Net
=
reduced-reference physical backbone
+
reference-surface metadata-conditioned residual compensation network.
```

The conceptual main method is:

```text
X_ref3 + metadata-conditioned FiLM residual compensation
```

RSB-FiLM is retained as a **stable / constrained FiLM variant** and may be used as the final implemented variant, but it is not the conceptual definition of ReMiC-Net itself.

---

## 1. One-Sentence Model Definition

ReMiC-Net is a two-stage physics-guided 3-D imaging framework that first reconstructs a coarse magnitude volume using a low-complexity reduced-reference cylindrical physical operator and then applies a reference-surface metadata-conditioned residual compensation network to correct the structured mismatch caused by aggressive reference-surface reduction.

---

## 2. Final Model Identity

### 2.1 What ReMiC-Net is

ReMiC-Net is:

- a **physics-guided** learned compensation framework;
- a **reduced-reference cylindrical aperture imaging** method;
- a **reference-surface-aware residual mismatch compensation** network;
- a **metadata-conditioned FiLM residual compensation** architecture;
- a feed-forward image-domain compensation method built on a physical warm start.

The model is designed for:

```text
structured mismatch induced by reduced-reference cylindrical aperture imaging.
```

### 2.2 What ReMiC-Net is not

ReMiC-Net is not:

- a pure black-box echo-to-image network;
- a generic 3-D denoising or image-enhancement network;
- a segmentation-assisted reconstruction model;
- a complex-valued echo-consistency model;
- a deep unfolding / iterative reconstruction framework;
- a compressed-sensing solver;
- a support-mask prediction model;
- a model whose main identity is RSB-FiLM alone.

---

## 3. Final Pipeline

The final ReMiC-Net pipeline consists of two stages.

### Stage 1: Reduced-Reference Cylindrical Physical Backbone

Given cylindrical echo data `y`, the reduced-reference physical operator reconstructs a coarse magnitude volume:

```math
X_{ref3} = R_{ref3}(y).
```

where:

- `y` is the simulated or measured cylindrical aperture echo;
- `R_ref3` is the reduced-reference cylindrical imaging operator using three reference cylindrical surfaces;
- `X_ref3` is the coarse image-domain reconstruction;
- `ref3` is the default low-complexity physical backbone for all learned compensation variants.

The ref3 reference surfaces are:

```math
S_3 = {0.00, 0.15, 0.30} m.
```

This stage provides:

1. a physically meaningful warm start;
2. low computational complexity;
3. the structured approximation mismatch to be compensated by the network.

### Stage 2: Metadata-Conditioned Residual Compensation

The second stage predicts an image-domain residual:

```math
Delta_x_hat = f_theta(X_ref3, G),
```

where:

- `X_ref3` is the main image input;
- `G` is the reference-surface-aware metadata;
- `f_theta` is the learned residual compensation network.

The final output is:

```math
x_hat = X_ref3 + Delta_x_hat.
```

The residual output is not multiplied by a final physical gate. The final residual connection is direct.

---

## 4. Final Input Definition

### 4.1 Main image input

```math
X_ref3
```

Meaning:

- magnitude-domain ref3 coarse reconstruction;
- produced by the reduced-reference physical backbone;
- carries structured mismatch artifacts caused by aggressive reference-surface reduction.

### 4.2 Reference-surface metadata input

The final metadata input is:

```math
G(v)=
[
M_shell(v),
delta_rho(v),
sin(pi P_cyc(v)),
cos(pi P_cyc(v))
].
```

where `v` denotes a voxel.

This final metadata definition replaces all earlier scalar-`Pcyc` input definitions.

---

## 5. Metadata Definitions

### 5.1 Shell assignment map `Mshell`

For a voxel `v`, let its radial coordinate be

```math
rho(v)=sqrt(x(v)^2+y(v)^2).
```

Given a selected reference-surface set

```math
S_N = {rho_ref,1, rho_ref,2, ..., rho_ref,N},
```

the assigned nearest reference surface is

```math
rho_ref*(v) = argmin_{rho_r in S_N} |rho(v)-rho_r|.
```

The shell index is

```math
s(v)=argmin_i |rho(v)-rho_ref,i|.
```

For ref3,

```math
S_3=[0.00,0.15,0.30] m.
```

The shell map is implemented as one-hot encoding:

```math
M_shell(v)=onehot(s(v)).
```

For ref3:

```math
M_shell(v) in {0,1}^3.
```

Role:

- identifies which approximate reference-surface kernel is responsible for each voxel;
- separates different radial mismatch regimes;
- prevents the network from treating all radial locations as sharing the same error pattern.

### 5.2 Nearest-reference radial deviation `delta_rho`

The signed nearest-reference radial deviation is

```math
delta_rho(v)=rho(v)-rho_ref*(v).
```

where:

- `rho(v)` is the voxel radial coordinate;
- `rho_ref*(v)` is the assigned nearest reference-surface radius.

Role:

- measures how far each voxel is from its assigned reference surface;
- encodes the local severity of reference-surface approximation;
- complements `Mshell`, which only provides discrete shell identity.

For RSB-FiLM variants, the normalized deviation may be used:

```math
delta_rho_norm(v)=clip(|delta_rho(v)|/0.075,0,1).
```

This normalization is tied to the ref3 maximum half-interval deviation `0.075 m`.

### 5.3 Cyclic phase-deviation variable `Pcyc`

The cyclic phase-deviation variable maps radial mismatch into a wrapped phase state. It is derived from the two-way phase deviation at the center frequency.

The current simulation protocol uses:

```text
fmin = 30 GHz
fmax = 39 GHz
fc   = 34.5 GHz
```

The center wavelength is

```math
lambda_c = c / f_c.
```

The two-way center wavenumber is

```math
k_c^(2w) = 4 pi f_c / c.
```

The unwrapped phase deviation can be represented as

```math
Delta_phi_c(v)=k_c^(2w) delta_rho(v).
```

The wrapped cyclic phase state is normalized to a periodic range, denoted as `Pcyc(v)`.

Important:

```text
Pcyc is a physical intermediate variable.
The final network input does not use scalar Pcyc directly.
```

The final input uses:

```math
sin(pi P_cyc), cos(pi P_cyc).
```

Role:

- represents the periodic nature of phase mismatch;
- avoids discontinuity at the wrap boundary;
- improves stability compared with scalar `Pcyc`.

---

## 6. Final Network Concept

### 6.1 Main architecture

The canonical network is a 3-D residual U-Net style compensation network with metadata-conditioned FiLM modulation.

The image branch processes:

```math
X_ref3.
```

The metadata branch processes:

```math
G = [Mshell, delta_rho, sin(pi Pcyc), cos(pi Pcyc)].
```

The network predicts:

```math
Delta_x_hat.
```

The final output is:

```math
x_hat = X_ref3 + Delta_x_hat.
```

### 6.2 Metadata-conditioned FiLM as the conceptual main mechanism

The conceptual main compensation mechanism is metadata-conditioned FiLM.

For feature map `F_l` at layer `l`, metadata features generate FiLM parameters:

```math
gamma_l, beta_l = h_l(G).
```

The generic FiLM form is:

```math
F_tilde_l = (1 + gamma_l) * F_l + beta_l.
```

Role:

- uses reference-surface metadata as a conditioning signal;
- allows compensation behavior to vary with local mismatch context;
- is more expressive than simple metadata concatenation;
- remains a feed-forward residual compensation mechanism.

---

## 7. RSB-FiLM Positioning

### 7.1 Canonical status

RSB-FiLM is **not** the conceptual definition of ReMiC-Net.

The conceptual definition is:

```text
ReMiC-Net
= reduced-reference physical backbone
+ metadata-conditioned residual compensation.
```

RSB-FiLM is:

```text
a stable / constrained FiLM variant.
```

It may be adopted as the final implemented variant because it provides physical interpretability and negligible runtime overhead, but it should be described as a constrained implementation detail or ablation variant rather than the sole identity of the method.

### 7.2 RSB-FiLM R04 implementation

The current frozen R04 variant uses bounded FiLM modulation with a phase-geometry product envelope:

```math
m(v)=epsilon_m+(1-epsilon_m)*sqrt(|P_cyc(v)|*|delta_rho_norm(v)|).
```

where:

```math
delta_rho_norm(v)=clip(|delta_rho(v)|/0.075,0,1).
```

Default parameters:

```text
epsilon_m   = 0.05
alpha_gamma = 0.5
alpha_beta  = 0.1
```

Bounded modulation form:

```math
gamma_b = alpha_gamma * tanh(gamma),
beta_b  = alpha_beta  * tanh(beta).
```

The constrained FiLM form is:

```math
F_tilde_l = (1 + m * gamma_b) * F_l + m * beta_b.
```

RSB-FiLM is applied only to mid/deep layers, e.g.,

```text
E2, E3, B, D3, D2.
```

Role:

- stabilizes FiLM modulation;
- prevents uncontrolled feature scaling;
- ties modulation strength to reference-surface mismatch indicators;
- improves physical interpretability;
- preserves near-ref3 runtime.

### 7.3 How to describe RSB-FiLM in the paper

Recommended wording:

> ReMiC-Net uses reference-surface metadata-conditioned FiLM modulation as the main residual compensation mechanism. We further introduce RSB-FiLM as a constrained FiLM variant that bounds the affine modulation and modulates its strength using a phase-geometry product envelope derived from the reduced-reference mismatch. The ablation study shows that RSB-FiLM provides comparable or slightly improved accuracy over generic FiLM while offering better physical interpretability and negligible runtime overhead.

Avoid wording such as:

> ReMiC-Net is RSB-FiLM.

or:

> The main contribution is only RSB-FiLM.

or:

> RSB-FiLM significantly outperforms generic FiLM in all settings.

The experimental evidence supports a more precise claim:

```text
RSB-FiLM gives consistent but modest gains on the main test set and comparable OOD behavior to generic FiLM.
```

---

## 8. Removed From the Current Main Method

The following components are **not part of the current main method**.

### 8.1 Not used as network input

- valid FOV mask;
- support prior;
- scalar `Pcyc` as direct input;
- scalar + sin-cos mixed `Pcyc` input;
- BP output as network input.

### 8.2 Not used as output head

- support mask auxiliary head;
- segmentation head;
- geometry support head.

### 8.3 Not used as main loss

- BCE support loss;
- Dice support loss;
- support Dice loss;
- SSIM loss as a default training loss;
- complex echo-domain consistency loss;
- hard-region weighted loss;
- foreground/support weighted loss.

### 8.4 Not used as main evaluation metric

- support Dice;
- segmentation IoU;
- high-mismatch-region-only metrics as main paper metrics.

These items may be explored in future work or supplementary experiments, but they are not part of the current canonical ReMiC-Net structure.

---

## 9. Training Target and Loss

### 9.1 Training target

The target is the ground-truth magnitude reflectivity volume:

```math
x* = x_gt.
```

The residual target is:

```math
Delta_x* = x* - X_ref3.
```

The network predicts:

```math
Delta_x_hat.
```

The final output is:

```math
x_hat = X_ref3 + Delta_x_hat.
```

### 9.2 Default training loss

The default main training loss is image-domain residual / reconstruction loss. The simplest canonical form is:

```math
L_img = ||x_hat - x*||_1.
```

Equivalently, because `x_hat = X_ref3 + Delta_x_hat`, this can be written as residual supervision:

```math
L_res = ||Delta_x_hat - Delta_x*||_1.
```

Unless a future task explicitly changes the training protocol, the current canonical experiments use:

- optimizer: AdamW;
- learning rate: `1e-3`;
- weight decay: `1e-4`;
- epochs: 50;
- seeds: 0, 1, 2;
- training split: 800;
- validation split: 100;
- test split: 100.

---

## 10. Primary Evaluation Metrics

The frozen primary metrics are:

```text
runtime
speedup vs BP
magnitude NMSE
PSNR
SSIM
```

Support Dice, segmentation IoU, and high-mismatch-region-only metrics are not primary metrics.

### 10.1 NMSE

For reconstructed magnitude volume `x_hat` and ground-truth reflectivity magnitude volume `x*`:

```math
NMSE = ||x_hat - x*||_2^2 / ||x*||_2^2.
```

### 10.2 PSNR

For normalized magnitude volumes:

```math
MSE = (1/N) sum_i (x_hat_i - x*_i)^2.
```

```math
PSNR = 10 log10(x_max^2 / MSE).
```

If volumes are normalized to `[0,1]`, then:

```math
x_max = 1.
```

### 10.3 SSIM

SSIM is computed on normalized magnitude volumes. For two local windows `x` and `x_hat`:

```math
SSIM(x,x_hat)
=
((2 mu_x mu_xhat + C1)(2 sigma_xxhat + C2))
/
((mu_x^2 + mu_xhat^2 + C1)(sigma_x^2 + sigma_xhat^2 + C2)).
```

where:

- `mu_x`, `mu_xhat` are local means;
- `sigma_x^2`, `sigma_xhat^2` are local variances;
- `sigma_xxhat` is local covariance;
- `C1`, `C2` are stabilizing constants.

### 10.4 Runtime and speedup

For physical methods:

```math
T_method = T_physical_reconstruction.
```

For learned methods:

```math
T_method = T_ref3 + T_network.
```

Speedup vs BP is:

```math
Speedup = T_BP / T_method.
```

Network-only runtime must not be used as the main runtime in paper tables.

---

## 11. Reference-Surface Baselines

The full reference-surface library is:

```math
S_31 = {0.00, 0.01, ..., 0.30} m.
```

The deterministic reduced-reference sets are:

```text
ref3  = [0.00, 0.15, 0.30] m
ref5  = [0.00, 0.08, 0.15, 0.22, 0.30] m
ref7  = [0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30] m
ref9  = [0.00, 0.04, 0.08, 0.11, 0.15, 0.19, 0.22, 0.26, 0.30] m
ref31 = [0.00, 0.01, ..., 0.30] m
```

Roles:

- ref3: fast physical backbone and ReMiC-Net warm start;
- ref5/ref7/ref9: intermediate physical baselines;
- ref31: dense-reference physical baseline;
- BP: exact high-quality physical baseline, not identical to ref31.

---

## 12. Paper Table Logic

### 12.1 Table 1: Main baseline comparison

Purpose:

```text
show speed-quality tradeoff and final method advantage.
```

Methods:

1. BP;
2. ref3;
3. ref5;
4. ref7;
5. ref9;
6. ref31;
7. ref3 + residual U-Net;
8. ref3 + ReMiC-Net R04.

Main conclusion:

- reference-surface baselines show quality-runtime tradeoff;
- ReMiC-Net R04 keeps near-ref3 runtime;
- ReMiC-Net R04 achieves best NMSE / PSNR / SSIM;
- ReMiC-Net R04 is much faster than exact BP.

### 12.2 Table 2: Component ablation

Purpose:

```text
show component contributions.
```

Methods:

1. ref3 + residual U-Net;
2. ref3 + metadata concat;
3. ref3 + metadata + generic FiLM;
4. ref3 + metadata + RSB-FiLM R04.

Main conclusion:

- metadata is the largest source of improvement;
- metadata-driven FiLM is better than simple metadata concatenation;
- RSB-FiLM R04 gives consistent but modest gain over generic FiLM;
- RSB-FiLM mainly strengthens interpretability and stability with negligible overhead.

Do not include scalar `Pcyc` variants in the main Table 2. Pcyc encoding has already been resolved as sin-cos.

### 12.3 Table 3: OOD generalization

Purpose:

```text
evaluate generalization and R04-vs-generic-FiLM behavior.
```

Methods:

1. ref3;
2. ref3 + residual U-Net;
3. ref3 + metadata + generic FiLM;
4. ref3 + metadata + RSB-FiLM R04.

OOD splits:

1. Leave-One-Family-Out OOD;
2. Random-ET OOD;
3. Unseen-Parameter OOD.

Main conclusion:

- R04 clearly improves over ref3;
- R04 clearly improves over residual U-Net;
- R04 and generic FiLM are broadly comparable on OOD;
- R04 has slight advantage on leave-one-family-out and better SSIM on Random-ET;
- do not claim strong OOD superiority over generic FiLM.

Recommended wording:

> RSB-FiLM R04 provides comparable OOD generalization to generic FiLM while offering a more physically interpretable reference-surface-aware modulation mechanism and negligible runtime overhead.

---

## 13. Current Experimental Evidence Summary

### 13.1 Main comparison

Final Table 1 evidence shows:

- exact BP runtime is much larger than reference-surface methods;
- ref31 is faster than BP, consistent with complexity analysis;
- ref3 is the fastest physical backbone;
- ReMiC-Net R04 preserves near-ref3 runtime;
- ReMiC-Net R04 achieves best NMSE / PSNR / SSIM.

Canonical interpretation:

```text
ReMiC-Net improves the speed-quality frontier by compensating ref3 mismatch instead of increasing N_ref.
```

### 13.2 Component ablation

Final Table 2 evidence shows:

- metadata concat gives the largest gain over residual U-Net;
- generic FiLM gives a further small gain over metadata concat;
- RSB-FiLM R04 gives a consistent but modest gain over generic FiLM;
- total overhead over residual U-Net is negligible.

Canonical interpretation:

```text
The main method contribution is reference-surface metadata-conditioned compensation.
```

RSB-FiLM should be interpreted as:

```text
a physically constrained FiLM implementation that improves interpretability and stability.
```

### 13.3 OOD generalization

Final Table 3 evidence shows:

- R04 improves substantially over ref3;
- R04 improves over residual U-Net;
- R04 and generic FiLM are broadly tied on OOD;
- R04 should not be claimed as significantly better than generic FiLM on all OOD settings.

Canonical interpretation:

```text
R04 preserves or slightly improves accuracy while providing stronger physical interpretability.
```

---

## 14. Complexity Positioning

Let cylindrical echo data be sampled on a three-dimensional grid of size:

```math
Q x W x P,
```

where:

- `Q`: frequency / wavenumber samples;
- `W`: azimuth-angle samples;
- `P`: vertical-aperture samples.

Direct BP has complexity:

```math
C_BP = O(Q^2 W^2 P^2).
```

Reference-surface imaging with `N_ref` reference surfaces has complexity:

```math
C_refN = O(N_ref Q W P log(QW) + Q W P).
```

ReMiC-Net uses ref3 plus fixed feed-forward network inference:

```math
C_ReMiC = O(3 Q W P log(QW) + Q W P) + C_NN.
```

For a fixed 3-D CNN:

```math
C_NN = O(Q W P).
```

Thus:

```math
C_ReMiC ≈ O(Q W P log(QW)).
```

Canonical complexity claim:

```text
ReMiC-Net retains the dominant complexity order of the fast reference-surface family while avoiding BP-level complexity.
```

---

## 15. Recommended Paper Wording

### 15.1 Method identity

Use:

> The proposed ReMiC-Net consists of a reduced-reference cylindrical physical backbone and a reference-surface metadata-conditioned residual compensation network.

Avoid:

> ReMiC-Net is an RSB-FiLM network.

### 15.2 Metadata contribution

Use:

> The reference-surface metadata provides explicit information about shell assignment, radial deviation from the assigned reference surface, and cyclic phase mismatch. This information is the primary source of improvement over a plain residual U-Net.

### 15.3 FiLM contribution

Use:

> Metadata-conditioned FiLM modulation further improves over direct metadata concatenation, indicating that reference-surface metadata is more effective when used to condition feature extraction than when simply appended to the input channels.

### 15.4 RSB-FiLM contribution

Use:

> RSB-FiLM provides a constrained FiLM variant that bounds feature modulation and relates modulation strength to the phase-geometry mismatch envelope. It yields a consistent but modest gain over generic FiLM on the main test set and comparable OOD generalization, while improving physical interpretability and maintaining negligible runtime overhead.

Avoid:

> RSB-FiLM significantly outperforms generic FiLM in all cases.

### 15.5 OOD conclusion

Use:

> On OOD splits, R04 substantially outperforms ref3 and the plain residual U-Net. Compared with generic FiLM, it provides comparable OOD performance with slight advantages in selected splits, suggesting that the constrained modulation improves interpretability without sacrificing robustness.

---

## 16. Deprecated Historical Descriptions

The following historical descriptions are deprecated for the current paper.

### 16.1 Deprecated: RSB-FiLM as the main identity

Deprecated:

```text
ReMiC-Net = RSB-FiLM.
```

Current:

```text
ReMiC-Net = reduced-reference physical backbone + metadata-conditioned residual compensation.
```

### 16.2 Deprecated: scalar Pcyc as direct input

Deprecated:

```text
G = [Mshell, delta_rho, Pcyc].
```

Current:

```text
G = [Mshell, delta_rho, sin(pi Pcyc), cos(pi Pcyc)].
```

### 16.3 Deprecated: support-assisted main method

Deprecated:

- support prior input;
- valid FOV mask input;
- support mask head;
- BCE/Dice support loss;
- support Dice as main metric.

Current:

- no support auxiliary head;
- no support loss;
- no support prior input;
- no support Dice main metric.

### 16.4 Deprecated: complex echo-domain consistency in current main method

Deprecated:

- complex echo-domain loss in the current magnitude-domain model.

Current:

- magnitude-domain residual compensation;
- complex echo-domain consistency reserved for future complex-valued extensions.

---

## 17. Guidance for Future Codex / ChatGPT Tasks

All future tasks must include the following instruction near the top:

```text
Use CONTEXT/remicnet_structure_master_current.md as the only canonical model-structure authority.
If any older master document, model-structure note, experiment report, prompt, or conversation conflicts with it, ignore the older source and follow remicnet_structure_master_current.md.
```

For Chinese prompts:

```text
模型结构以 CONTEXT/remicnet_structure_master_current.md 为唯一权威准则。
如果旧 master、旧 model_structure、历史 prompt、历史实验报告或历史对话与该文件存在冲突，一律以该文件为准。
```

When asking Codex to update code, paper, figures, or experiments, explicitly state:

```text
Do not reintroduce support head, BCE/Dice loss, valid FOV input, support prior, scalar Pcyc direct input, or complex echo-domain consistency into the main method.
```

---

## 18. Recommended File Management

### 18.1 Current canonical file

Place this file at:

```text
CONTEXT/remicnet_structure_master_current.md
```

This is the only canonical model-structure master.

### 18.2 Deprecated files

Older files may be retained for history, but should be marked deprecated:

```text
DEPRECATED FOR CURRENT MODEL STRUCTURE.
Use CONTEXT/remicnet_structure_master_current.md as the only canonical structure master.
```

Recommended deprecated/archive candidates:

- `real_cylindrical_master_document_rsb_film_updated20260510.md`
- `model_structure_rsb_film_updated20260510.md`
- earlier ReMiC-Net structure notes that define RSB-FiLM as the main method
- earlier notes that include support-head / Dice / BCE / FOV / support prior in the main method

### 18.3 Supporting protocol files

The following files may remain as supporting physical-protocol documents after light updates:

- `simulation_protocol_rsb_film_updated20260510.md`
- `reference_surface_strategy_rsb_film_updated20260510.md`

They should be treated as supporting protocol files, not model-structure master files.

---

## 19. Final Canonical Summary

The final ReMiC-Net structure is:

```math
X_ref3 = R_ref3(y).
```

```math
G(v) = [Mshell(v), delta_rho(v), sin(pi Pcyc(v)), cos(pi Pcyc(v))].
```

```math
Delta_x_hat = f_theta(X_ref3, G).
```

```math
x_hat = X_ref3 + Delta_x_hat.
```

Conceptual identity:

```text
ReMiC-Net = reduced-reference physical backbone + reference-surface metadata-conditioned residual compensation network.
```

Implementation note:

```text
RSB-FiLM is a constrained FiLM variant, not the conceptual definition of ReMiC-Net.
```

Main evidence:

```text
metadata is the largest contributor; FiLM improves metadata use; RSB-FiLM gives modest accuracy gain and stronger physical interpretability.
```

Primary metrics:

```text
runtime, speedup vs BP, NMSE, PSNR, SSIM
```

This document is the final authority for the current ReMiC-Net model structure.
