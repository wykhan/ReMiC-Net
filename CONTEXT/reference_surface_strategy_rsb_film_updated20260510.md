# reference_surface_strategy.md

## 文件角色

本文件用于正式冻结新项目中参考柱面（reference cylindrical surfaces）的选择策略，并补充当前 ReMiC-Net 输入设计所需的几何 metadata 生成规则。

本版本新增并冻结：

\[
[M_{\mathrm{shell}},\delta\rho,P_{\mathrm{cyc}}]
\]

作为 Geometry branch 的 reference-surface-aware metadata。

---

# 1. 理论依据与项目立场

谭维贤等的柱面孔径全息成像方法将成像区域划分为不同半径的成像柱面，并依据成像精度和相位误差控制范围设置参考柱面，以简化重复计算匹配滤波函数的过程。

本项目沿用这一物理机制，但将其用于 learning-based mismatch compensation：

- 少参考面物理骨干提供快速粗重建；
- 参考面分配与径向偏差提供误差上下文；
- 周期相位偏差 \(P_{\mathrm{cyc}}\) 将径向失配进一步映射为双程传播相位状态；
- ReMiC-Net 学习补偿 structured mismatch。

---

# 2. 完整参考柱面库

完整参考柱面库定义为：

\[
\rho_{\mathrm{ref,full}}=\{0.00,0.01,0.02,\ldots,0.30\}\;\mathrm{m}.
\]

其中：

- 最小参考半径：`0.00 m`
- 最大参考半径：`0.30 m`
- 间隔：`0.01 m`
- 总数：`31`

工程实现对应：

```text
rho_ref = 0 : 0.01 : X0
X0 = 0.3
```

---

# 3. reduced-reference 抽样原则

## 3.1 总原则

`ref3/ref5/ref7/ref9` 均从同一个 full reference-surface library 中抽样。

必须满足：

1. 含两端点；
2. 径向尽量均匀；
3. deterministic；
4. 可复现；
5. 不允许不同实验使用不同参考面集合。

## 3.2 统一抽样算法

给定：

- 完整参考柱面库长度 \(L=31\)
- 目标参考面数量 \(N\in\{3,5,7,9\}\)

定义：

```text
idx(N) = round(linspace(0, L-1, N))
```

即：

```text
idx(N) = round(linspace(0, 30, N))
```

---

# 4. ref3 / ref5 / ref7 / ref9 正式冻结结果

## 4.1 ref3

0-based 索引：

```text
[0, 15, 30]
```

参考柱面半径：

```text
[0.00, 0.15, 0.30] m
```

角色：

- 当前默认 reduced-reference physical backbone；
- ReMiC-Net 的主输入 \(X_{\mathrm{ref3}}\) 由该物理骨干生成。

## 4.2 ref5

0-based 索引：

```text
[0, 8, 15, 22, 30]
```

参考柱面半径：

```text
[0.00, 0.08, 0.15, 0.22, 0.30] m
```

## 4.3 ref7

0-based 索引：

```text
[0, 5, 10, 15, 20, 25, 30]
```

参考柱面半径：

```text
[0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30] m
```

## 4.4 ref9

0-based 索引：

```text
[0, 4, 8, 11, 15, 19, 22, 26, 30]
```

参考柱面半径：

```text
[0.00, 0.04, 0.08, 0.11, 0.15, 0.19, 0.22, 0.26, 0.30] m
```

---

# 5. 最近参考柱面分配规则

对任一体素 \(v\)，其柱面半径为：

\[
\rho(v)=\sqrt{x(v)^2+y(v)^2}.
\]

给定 selected reference set：

\[
\mathcal{S}_{N}=\{\rho_{\mathrm{ref},1},\ldots,\rho_{\mathrm{ref},N}\}.
\]

最近参考柱面定义为：

\[
\rho_{\mathrm{ref}}^{\ast}(v)
=
\arg\min_{\rho_r\in\mathcal{S}_{N}}
|\rho(v)-\rho_r|.
\]

对应 shell id 为：

\[
s(v)
=
\arg\min_{i}
|\rho(v)-\rho_{\mathrm{ref},i}|.
\]

---

# 6. Geometry branch metadata 生成规则

当前 ReMiC-Net Geometry branch 输入冻结为：

\[
G(v)=
[
M_{\mathrm{shell}}(v),\delta\rho(v),P_{\mathrm{cyc}}(v)
].
\]

---

## 6.1 `Mshell`: shell/reference allocation map

### 定义

\[
M_{\mathrm{shell}}(v)=\operatorname{onehot}(s(v)).
\]

对 `ref3`：

\[
\mathcal{S}_{3}=[0.00,0.15,0.30]\;\mathrm{m}.
\]

因此：

\[
M_{\mathrm{shell}}(v)\in\{0,1\}^{3}.
\]

### ref3 shell 边界

对 `ref3`，最近参考面的分界点为相邻参考面的中点：

\[
b_1=\frac{0.00+0.15}{2}=0.075\;\mathrm{m},
\]

\[
b_2=\frac{0.15+0.30}{2}=0.225\;\mathrm{m}.
\]

因此：

- \(0.00\le\rho<0.075\)：shell 0，对应参考面 \(0.00\) m；
- \(0.075\le\rho<0.225\)：shell 1，对应参考面 \(0.15\) m；
- \(0.225\le\rho\le0.30\)：shell 2，对应参考面 \(0.30\) m。

### 角色

`Mshell` 告诉网络当前体素由哪个参考面近似负责。

---

## 6.2 `δρ`: nearest-reference radial deviation

### 定义

\[
\delta\rho(v)
=
\rho(v)-\rho_{\mathrm{ref}}^{\ast}(v).
\]

### 单位

- 原始定义单位为 meter。
- 推荐保留 raw physical value 用于计算 \(P_{\mathrm{cyc}}\)。

### 网络输入规范

工程实现可选择以下两种方式之一：

#### 方式 A：直接输入 raw deviation

\[
\delta\rho_{\mathrm{in}}(v)=\delta\rho(v).
\]

#### 方式 B：输入归一化 signed deviation

\[
\widetilde{\delta\rho}(v)
=
\frac{\delta\rho(v)}
{\Delta\rho_{\mathrm{local}}/2}.
\]

其中 \(\Delta\rho_{\mathrm{local}}\) 为相邻参考面间隔或局部 shell 宽度。

冻结建议：

- 论文公式中使用 \(\delta\rho\)；
- 代码若归一化，必须在 config 中显式记录。

### 角色

`δρ` 告诉网络体素离参考面有多远、偏向哪一侧。

---

## 6.3 `Pcyc`: cyclic phase-deviation encoding

### 正式英文名称

```text
cyclic phase-deviation encoding
```

### 推荐中文名称

```text
周期包裹的归一化相位偏差
```

### 定义

\[
\boxed{
P_{\mathrm{cyc}}(v)
=
\frac{1}{\pi}
\operatorname{wrap}_{(-\pi,\pi]}
\left(
k_c^{(2w)}\delta\rho(v)
\right)
}
\]

其中：

\[
k_c^{(2w)}=\frac{4\pi f_c}{c}
=
\frac{4\pi}{\lambda_c}.
\]

### 当前 protocol v1 常数

当前 `simulation_protocol.md` 冻结：

\[
f_{\min}=30\;\mathrm{GHz},
\quad
f_{\max}=39\;\mathrm{GHz}.
\]

因此：

\[
f_c=34.5\;\mathrm{GHz},
\]

\[
\lambda_c=\frac{c}{f_c}=8.695652\;\mathrm{mm},
\]

\[
k_c^{(2w)}=1445.132621\;\mathrm{rad/m}.
\]

### wrap 函数

推荐实现：

```python
phi = k2w_c * delta_rho_raw
phi_wrap = (phi + pi) % (2*pi) - pi
Pcyc = phi_wrap / pi
```

若希望区间为 \((-\pi,\pi]\)，可对边界点做工程修正。一般深度学习输入中边界点不影响结果。

### 角色

`Pcyc` 告诉网络：

- 几何偏差在双程传播相位上处于哪个周期位置；
- 哪些体素处于主值相位误差较小区域；
- 哪些体素处于主值相位误差较大区域。

### 与 \(\pi/4\) 相位误差条件的关系

\[
|\phi_{\mathrm{wrap}}|\leq\frac{\pi}{4}
\Longleftrightarrow
|P_{\mathrm{cyc}}|\leq0.25.
\]

这可用于诊断和可视化。

---

# 7. `δρ` 与 `Pcyc` 的关系

二者不重复。

## 7.1 `δρ`

表示：

- 几何距离偏差；
- 物理单位为 meter；
- 有正负方向；
- 不考虑相位周期。

## 7.2 `Pcyc`

表示：

- 双程传播相位偏差；
- 经过 \(2\pi\) 周期包裹；
- 归一化到 \((-1,1]\)；
- 反映相位状态，而不是距离本身。

因此：

\[
\delta\rho \neq P_{\mathrm{cyc}}.
\]

一个告诉网络“离参考面多远”，另一个告诉网络“这个距离偏差对应什么相位状态”。

---

# 8. 当前不作为 Geometry branch 输入的内容

以下内容不属于当前冻结 Geometry branch 输入：

## 8.1 valid FOV mask

状态：

- 不作为当前主方法输入；
- 可作为有效区域筛选、评测 mask 或可视化诊断；
- 若未来重新加入，必须作为新的 input ablation。

## 8.2 support prior

状态：

- 不作为当前主方法输入；
- support 信息通过 support head 和 support loss 提供监督；
- 若未来重新加入，必须明确区分 input prior 与 output supervision。

---

# 9. 点目标与 extended target 中的使用方式

## 9.1 点目标

点目标实验中必须记录：

- \(\rho_{\mathrm{target}}\)
- \(\rho_{\mathrm{ref}}^{\ast}\)
- shell id
- \(\delta\rho\)
- \(P_{\mathrm{cyc}}\)

并分析：

- 不同 \(|\delta\rho|\) 下的失焦程度；
- 不同 \(|P_{\mathrm{cyc}}|\) 下的误差变化；
- \(P_{\mathrm{cyc}}\) 是否有助于解释 ref3 的 structured mismatch。

## 9.2 extended target

extended target 中每个体素均应生成：

\[
M_{\mathrm{shell}}(v),\delta\rho(v),P_{\mathrm{cyc}}(v).
\]

这些 metadata 与 \(X_{\mathrm{ref3}}\) 一起输入 ReMiC-Net。

---

# 10. 代码实现伪代码

```python
import numpy as np

def wrap_to_pi(phi):
    return (phi + np.pi) % (2 * np.pi) - np.pi

def build_ref_metadata(rho_grid, selected_refs, fc=34.5e9, c=3e8):
    selected_refs = np.asarray(selected_refs, dtype=np.float32)

    # nearest reference index
    dist = np.abs(rho_grid[..., None] - selected_refs[None, None, None, :])
    shell_idx = np.argmin(dist, axis=-1)

    # one-hot shell map
    M_shell = np.eye(len(selected_refs), dtype=np.float32)[shell_idx]

    # raw signed radial deviation
    rho_ref_star = selected_refs[shell_idx]
    delta_rho = rho_grid - rho_ref_star

    # cyclic phase-deviation encoding
    k2w_c = 4 * np.pi * fc / c
    phi_wrap = wrap_to_pi(k2w_c * delta_rho)
    P_cyc = phi_wrap / np.pi

    return M_shell, delta_rho, P_cyc
```

---

# 11. 推荐消融

必须优先比较：

1. \(M_{\mathrm{shell}}\)
2. \(M_{\mathrm{shell}}+\delta\rho\)
3. \(M_{\mathrm{shell}}+\delta\rho+P_{\mathrm{cyc}}\)

核心判断：

> 若加入 \(P_{\mathrm{cyc}}\) 后，在远离参考面或相位主值偏差较大的区域明显改善，则可以证明该输入不是冗余工程特征，而是 reference-surface approximation error 的物理编码。

---

# 12. 一句话冻结结论

> `reference_surface_strategy.md` 当前冻结：参考柱面库仍为 `0.00:0.01:0.30 m`，`ref3/ref5/ref7/ref9` 仍采用含两端点的径向均匀抽样；在此基础上，ReMiC-Net 的 reference-surface-aware metadata 正式冻结为 `[Mshell, δρ, Pcyc]`，其中 `Pcyc` 为由最近参考面径向偏差计算得到的周期包裹归一化双程相位偏差。

---

# 10. RSB-FiLM 使用的相位失配包络

本版本补充 ReMiC-Net with RSB-FiLM 所需的 deterministic phase-mismatch envelope。

注意：该包络不是新的 Geometry branch 输入通道，而是 RSB-FiLM 内部用于限制 FiLM 调制强度的结构性物理先验。

## 10.1 定义

已知：

\[
P_{\mathrm{cyc}}(v)\in(-1,1].
\]

定义：

\[
\boxed{
 m(v)=\epsilon_m+(1-\epsilon_m)|P_{\mathrm{cyc}}(v)|
}
\]

默认：

\[
\epsilon_m=0.05.
\]

因此：

\[
 m(v)\in[\epsilon_m,1].
\]

## 10.2 物理含义

- 当 \(|P_{\mathrm{cyc}}|\) 较小时，体素相对于参考面的主值相位偏差较小，RSB-FiLM 只允许弱调制。
- 当 \(|P_{\mathrm{cyc}}|\) 较大时，体素相对于参考面的主值相位偏差较大，RSB-FiLM 允许更强调制。
- \(\epsilon_m\) 保证参考面附近仍保留微弱可学习补偿能力，避免完全关闭调制。

## 10.3 与 \(\pi/4\) 相位误差条件的关系

由：

\[
|\phi_{\mathrm{wrap}}|\leq\frac{\pi}{4}
\Longleftrightarrow
|P_{\mathrm{cyc}}|\leq0.25
\]

可知：

- \(|P_{\mathrm{cyc}}|\leq0.25\)：主值相位偏差处于较小区间；
- \(|P_{\mathrm{cyc}}|>0.25\)：主值相位偏差超出较小误差区间。

该分界可用于 diagnostic analysis，但 RSB-FiLM 主结构采用连续包络 \(m(v)\)，不使用硬阈值。

## 10.4 用于不同尺度

对 U-Net 第 \(l\) 个使用 RSB-FiLM 的尺度，使用：

\[
 m_l=\operatorname{Downsample}_l(m).
\]

其中 `Downsample` 可采用：

- average pooling；或
- trilinear interpolation。

要求：

- \(m_l\) 的空间尺寸必须与 \(F_l\) 一致；
- \(m_l\) 沿通道维广播；
- 不作为额外可学习参数。

## 10.5 与 Geometry branch 输入的关系

当前 Geometry branch 输入仍为：

\[
G(v)=
[
M_{\mathrm{shell}}(v),\delta\rho(v),P_{\mathrm{cyc}}(v)
].
\]

RSB-FiLM 包络：

\[
m(v)=\epsilon_m+(1-\epsilon_m)|P_{\mathrm{cyc}}(v)|
\]

不改变输入通道数量。

解释方式：

- \(P_{\mathrm{cyc}}\) 作为输入，提供周期相位状态；
- \(m\) 作为 deterministic envelope，限制 FiLM 调制强度；
- 二者角色不同，前者提供条件信息，后者提供结构约束。

