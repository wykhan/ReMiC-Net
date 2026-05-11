# simulation_protocol.md

## 文件角色

本文件用于冻结真正 3D 柱面物理仿真的几何、采样、信号模型与当前 ReMiC-Net 输入设计所需的派生物理常数。

本版本新增并冻结：

\[
f_c,\lambda_c,k_c^{(2w)}
\]

以及用于生成：

\[
P_{\mathrm{cyc}}
\]

的计算规则。

---

# 1. 生成依据

本协议基于：

1. 谭维贤等《高精度毫米波柱面孔径全息成像算法研究》；
2. `points_4_202406.txt` 中的 MATLAB 实现参数；
3. 当前 ReMiC-Net Geometry branch 输入冻结：
   \[
   [M_{\mathrm{shell}},\delta\rho,P_{\mathrm{cyc}}].
   \]

基本原则：

> 理论模型遵循谭维贤论文；protocol v1 数值参数以 `points_4_202406.txt` 为准；`Pcyc` 由当前频段中心频率和最近参考面径向偏差派生。

---

# 2. 坐标系与几何定义

## 2.1 坐标系

目标点使用笛卡尔坐标与柱坐标：

\[
P(x,y,z)
\]

\[
P(\rho,\theta,z).
\]

天线阵元位置：

\[
T(\rho',\theta',z').
\]

## 2.2 当前 protocol v1 几何主参数

```text
C        = 3e8 m/s
R        = 0.600 m
X0       = 0.300 m
H        = 2.000 m
theta_u  = 30.0 deg
theta_h  = 30.0 deg
```

含义：

- `R`：柱面扫描轨道半径；
- `X0`：主要照射场景半径；
- `H`：高度向成像范围；
- `theta_u`：方位向有效观测角；
- `theta_h`：高度向有效观测角。

---

# 3. 信号模型

## 3.1 单目标回波模型

采用柱面孔径近场球面波模型：

\[
s(K_\omega,\theta',z')
=
I(\rho,\theta,z)\exp(-j2K_\omega R).
\]

其中：

- \(I(\rho,\theta,z)\)：目标散射系数；
- \(K_\omega=2\pi f/c\)：单程波数；
- \(R\)：天线阵元到目标点的距离。

## 3.2 距离表达式

\[
R
=
\sqrt{
\rho'^2+\rho^2-2\rho'\rho\cos(\theta-\theta')
+
(z-z')^2
}.
\]

## 3.3 扩展目标回波模型

\[
S(K_\omega,\theta',z')
=
\iiint I(\rho,\theta,z)\exp(-j2K_\omega R)\,dv.
\]

## 3.4 当前代码实现口径

在 `points_4_202406.txt` 中：

```text
Kw = 4*pi*f/C
s3 += exp(-1j * Kw * Rn)
```

也就是说，代码中的 `Kw` 已经吸收了双程相位因子：

\[
K_w = \frac{4\pi f}{c}.
\]

因此：

\[
\exp(-j K_w R)
=
\exp(-j2K_\omega R).
\]

---

# 4. 场景边界与传播时延范围

```text
rmin = R - X0 = 0.300000 m
rmax = (R + X0) / cos(theta_h/2) = 0.931749 m
tmin = 2*rmin/C = 2.000000 ns
tmax = 2*rmax/C = 6.211657 ns
```

说明：

- `rmin` 对应最近目标点；
- `rmax` 考虑了有效观测锥限制下的最远目标点；
- point target 与 ET target 均不得超出该物理成像包络，除非 protocol 升级。

---

# 5. 距离向 / 频率向参数冻结

## 5.1 频段

```text
fmin = 30 GHz
fmax = 39 GHz
Br   = 9 GHz
```

## 5.2 双程波数定义

\[
k_{\min}^{(2w)}=\frac{4\pi f_{\min}}{c}=1256.637061\;\mathrm{rad/m},
\]

\[
k_{\max}^{(2w)}=\frac{4\pi f_{\max}}{c}=1633.628180\;\mathrm{rad/m}.
\]

## 5.3 距离向采样

```text
Nr = 181
Kw = linspace(kmin, kmax, Nr)
dk = 2.094395102393197 rad/m
```

## 5.4 距离向理论分辨率

代码中：

```text
delta_x = 0.886 * C / (2 * Br)
```

对应：

```text
delta_x ≈ 14.766667 mm
```

建议在论文和新代码中重命名为：

```text
range_resolution_theory
```

---

# 6. 中心频率与 Pcyc 派生常数

## 6.1 中心频率

当前 protocol v1 冻结：

\[
f_c=\frac{f_{\min}+f_{\max}}{2}.
\]

因此：

\[
f_c=34.5\;\mathrm{GHz}.
\]

## 6.2 中心波长

\[
\lambda_c=\frac{c}{f_c}.
\]

数值为：

\[
\lambda_c=0.008695652\;\mathrm{m}=8.695652\;\mathrm{mm}.
\]

## 6.3 中心双程波数

\[
k_c^{(2w)}=\frac{4\pi f_c}{c}
=
\frac{4\pi}{\lambda_c}.
\]

数值为：

\[
k_c^{(2w)}=1445.132621\;\mathrm{rad/m}.
\]

## 6.4 用途

该常数仅用于生成 ReMiC-Net 的 Geometry branch 输入：

\[
P_{\mathrm{cyc}}.
\]

它不是替代全频带成像模型，也不是把 broadband echo 简化为单频模型。它只是将最近参考面径向偏差转换成一个稳定的、归一化的中心频率双程相位状态。

---

# 7. Pcyc 生成规则

## 7.1 最近参考面径向偏差

对每个体素 \(v\)：

\[
\rho(v)=\sqrt{x(v)^2+y(v)^2}.
\]

由 `reference_surface_strategy.md` 得到最近参考面：

\[
\rho_{\mathrm{ref}}^{\ast}(v).
\]

计算：

\[
\delta\rho(v)=\rho(v)-\rho_{\mathrm{ref}}^{\ast}(v).
\]

## 7.2 周期包裹相位偏差

\[
\phi_{\mathrm{cyc}}(v)
=
\operatorname{wrap}_{(-\pi,\pi]}
\left(
k_c^{(2w)}\delta\rho(v)
\right).
\]

## 7.3 归一化 Pcyc

\[
\boxed{
P_{\mathrm{cyc}}(v)
=
\frac{\phi_{\mathrm{cyc}}(v)}{\pi}
}
\]

因此：

\[
P_{\mathrm{cyc}}(v)\in(-1,1].
\]

## 7.4 与 \(\pi/4\) 条件的关系

\[
|\phi_{\mathrm{cyc}}|\leq\frac{\pi}{4}
\Longleftrightarrow
|P_{\mathrm{cyc}}|\leq0.25.
\]

该关系可用于相位偏差分区分析。

---

# 8. 高度向参数冻结

```text
dh = 0.004000 m
h  = -H/2 : dh : H/2
```

因此：

```text
z ∈ [-1.0, 1.0] m
```

高度向采样点数由代码生成。

---

# 9. 方位向参数冻结

```text
Na = 1101
u  = linspace(-pi, pi, Na)
du = 2*pi/(Na-1)
```

对应：

```text
du ≈ 0.005711987 rad
du ≈ 0.327273 deg
```

---

# 10. 参考柱面库

完整参考柱面库：

\[
\rho_{\mathrm{ref,full}}=\{0.00,0.01,\ldots,0.30\}\;\mathrm{m}.
\]

工程实现：

```text
Interval_rho = 0.01
rho_ref = 0 : Interval_rho : X0
```

reduced-reference 版本：

- `ref3`
- `ref5`
- `ref7`
- `ref9`

由 `reference_surface_strategy.md` 冻结。

---

# 11. 当前神经网络输入相关的 protocol 输出

`simulation_protocol.md` 为 ReMiC-Net 输入生成提供以下常数：

```text
C      = 3e8
fmin   = 30e9
fmax   = 39e9
fc     = 34.5e9
lambda_c = 8.695652e-3
k2w_c  = 1445.132621
```

`reference_surface_strategy.md` 负责：

```text
Mshell
delta_rho
Pcyc
```

`model_structure.md` 负责：

```text
X_ref3 + [Mshell, delta_rho, Pcyc] -> ReMiC-Net
```

---

# 12. 采样准则冻结

新项目所有真正柱面 3D 仿真必须满足谭维贤论文中的采样准则思想。

## 12.1 方位向采样

当前实现：

```text
du ≈ 0.327273 deg
```

## 12.2 高度向采样

当前实现：

```text
dh = 4 mm
```

## 12.3 频率采样

当前实现：

```text
fmin = 30 GHz
fmax = 39 GHz
Nr   = 181
```

---

# 13. 当前 protocol v1 适用范围

适用于：

1. 点目标物理仿真；
2. 稀疏随机点目标集；
3. 真正柱面 shape-family ET 数据集；
4. Manisali-style 随机 ET 数据集；
5. `ref3/ref5/ref7/ref9/BP` 传统基线；
6. `X_ref3 + [Mshell, δρ, Pcyc] -> ReMiC-Net`；
7. 后续 complex-valued extension 的前置对照。

---

# 14. 当前 protocol v1 不冻结的事项

以下事项仍需在 companion 文档中冻结：

1. point target 振幅分布；
2. ET target 体素幅度分布；
3. 是否加入随机散射相位；
4. support label 生成规则；
5. 训练 / 验证 / 测试划分；
6. BP 作为高精度基线时的具体网格设置。

---

# 15. 一句话冻结结论

> 当前 `simulation_protocol.md` 正式冻结了柱面几何、30–39 GHz 频段、中心频率 \(f_c=34.5\) GHz、中心波长 \(\lambda_c=8.695652\) mm、中心双程波数 \(k_c^{(2w)}=1445.132621\) rad/m；该双程波数用于从最近参考面径向偏差 \(\delta\rho\) 生成 ReMiC-Net 的周期包裹归一化相位偏差 \(P_{\mathrm{cyc}}\)。

---

# 12. RSB-FiLM 相关派生量

本版本补充 ReMiC-Net with RSB-FiLM 需要的相位失配包络生成规则。

## 12.1 输入来源

RSB-FiLM 使用已经由本 protocol 生成的：

\[
P_{\mathrm{cyc}}(v)
=
\frac{1}{\pi}\operatorname{wrap}_{(-\pi,\pi]}
\left(k_c^{(2w)}\delta\rho(v)\right).
\]

不需要额外物理常数。

## 12.2 RSB-FiLM phase-mismatch envelope

定义：

\[
\boxed{
 m(v)=\epsilon_m+(1-\epsilon_m)|P_{\mathrm{cyc}}(v)|
}
\]

默认：

```text
epsilon_m = 0.05
```

因此：

\[
 m(v)\in[0.05,1].
\]

## 12.3 数据格式

`Pcyc` 数据格式：

```text
Pcyc.shape = [Nz, Ny, Nx]
Pcyc.dtype = float32
Pcyc.range ≈ (-1, 1]
```

`m_rsb` 数据格式：

```text
m_rsb.shape = [Nz, Ny, Nx]
m_rsb.dtype = float32
m_rsb.range = [epsilon_m, 1]
```

送入 PyTorch 时：

```text
Pcyc  -> [B, 1, Nz, Ny, Nx]
m_rsb -> [B, 1, Nz, Ny, Nx]
```

注意：

- `Pcyc` 是 Geometry branch 输入通道；
- `m_rsb` 不是输入通道，而是 RSB-FiLM 内部使用的 deterministic envelope；
- 如果工程实现方便，也可在 dataset 中预先缓存 `m_rsb`，但论文中不应把它描述为第四个 metadata 输入。

## 12.4 多尺度下采样

对 RSB-FiLM 使用层级 \(l\)：

\[
 m_l=\operatorname{Downsample}_l(m_{\mathrm{rsb}}).
\]

推荐实现：

```text
average pooling or trilinear interpolation
```

要求：

```text
m_l.shape = [B, 1, Dz_l, Dy_l, Dx_l]
```

并在 RSB-FiLM 中广播到通道维。

## 12.5 默认 RSB-FiLM 超参数

```text
epsilon_m   = 0.05
alpha_gamma = 0.5
alpha_beta  = 0.1
```

论文公式中仍保留符号：

\[
\epsilon_m,
\quad
\alpha_\gamma,
\quad
\alpha_\beta.
\]

消融范围：

```text
alpha_gamma ∈ {0.25, 0.5, 1.0}
alpha_beta  ∈ {0.0, 0.1, 0.25}
```

---

# 13. 当前 protocol 与 RSB-FiLM 的边界

本 protocol 负责生成：

- \(M_{\mathrm{shell}}\)
- \(\delta\rho\)
- \(P_{\mathrm{cyc}}\)
- \(m_{\mathrm{rsb}}\) if cached

本 protocol 不负责定义：

- neural network layer numbers；
- RSB-FiLM insertion locations；
- loss weights；
- training schedule。

这些内容由 `model_structure.md` 和 `experiment_matrix.md` 冻结。

