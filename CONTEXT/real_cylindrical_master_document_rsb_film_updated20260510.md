# real_cylindrical_master_document.md

## 项目名称

**Real Cylindrical Physics-Guided Learned 3D Imaging**

## 文档角色

本文件是柱面孔径 3D 学习成像论文项目的上位主控文档。

本版本完成两项关键更新：

1. ReMiC-Net 的 Geometry branch 输入正式冻结为：
   \[
   [M_{\mathrm{shell}},\delta\rho,P_{\mathrm{cyc}}].
   \]
2. ReMiC-Net 的特征调制模块正式升级为：
   
   > **RSB-FiLM: Reference-Surface-Bounded FiLM**。

同时，本版本将以下内容从主方法中移除：

- mask / support segmentation auxiliary head；
- BCE + Dice support loss；
- support Dice 作为主指标；
- `valid FOV mask` 作为网络输入；
- `support prior` 作为网络输入。

当前主线聚焦于：

> **reference-surface-aware residual mismatch compensation**。

---

# 1. 论文目标与问题定义

## 1.1 论文核心问题

本论文关注的问题不是一般意义上的图像增强，也不是单纯地让深度网络拟合 BP 输出。

本文要回答的是：

> **在真正柱面孔径物理仿真下，physics-guided learning 是否能够在保持少参考面快速成像低复杂度优势的同时，显著补偿 reduced-reference reference-surface approximation 造成的结构化失配，从而推动传统快速算法的速度–质量边界。**

核心矛盾是：

- 参考面数量越少，速度越快，但近似误差越大；
- 参考面数量越多，成像质量越好，但计算复杂度上升；
- 学习模块能否在低参考面物理骨干上补偿这种误差，使结果逼近高参考面或 BP 质量，同时保留 ref3 级别速度优势。

## 1.2 论文立场

本文采用以下立场：

1. **物理骨干优先，而非纯黑盒重建**  
   不从 raw echo 直接端到端回归 3D 图像，而是采用物理前端 + 学习补偿的两阶段路线。

2. **真正柱面物理仿真优先**  
   从柱面几何、前向回波、`ref3/ref5/ref7/ref9/BP` 重建链路出发。

3. **extended target 是主战场，点目标是前置验证**  
   点目标用于验证物理链路与误差机制；论文主结论必须落在 extended target 上。

4. **幅度重建为主**  
   当前阶段学习目标为 magnitude-domain reflectivity，不进行复反射率相位估计。

5. **当前主方法是 physics-guided，不是 complex-echo-consistent**  
   complex echo-domain consistency loss 不进入当前主损失函数。

6. **当前主方法不是 segmentation-assisted reconstruction**  
   mask head、Dice loss、support Dice 不作为主方法内容。

---

# 2. 方法总框架

## 2.1 第一阶段：少参考面柱面物理骨干

使用低参考面数量的参考面近似成像算法作为物理骨干：

\[
x_{\mathrm{ref3}}=\mathcal{R}_{\mathrm{ref3}}(y).
\]

其中：

- \(y\)：原始或仿真的柱面回波；
- \(\mathcal{R}_{\mathrm{ref3}}\)：使用 3 个参考柱面的 reduced-reference cylindrical imaging operator；
- \(x_{\mathrm{ref3}}\)：粗重建幅度体。

该阶段负责：

- 将原始柱面回波映射到粗粒度 3D 重建体；
- 提供具有物理意义的 warm start；
- 保留快速算法的低复杂度优势；
- 产生后续学习模块需要补偿的结构化失配。

## 2.2 第二阶段：ReMiC-Net with RSB-FiLM

ReMiC-Net 以 \(X_{\mathrm{ref3}}\) 作为主输入，以 reference-surface-aware metadata 作为 Geometry branch 输入，进行幅度域残差补偿。

当前冻结输入为：

\[
\mathbf{u}
=
[
X_{\mathrm{ref3}},
M_{\mathrm{shell}},
\delta\rho,
P_{\mathrm{cyc}}
].
\]

其中：

- \(X_{\mathrm{ref3}}\)：`ref3` 粗重建幅度体；
- \(M_{\mathrm{shell}}\)：参考面 / shell 分配编码；
- \(\delta\rho\)：体素到最近参考面的有符号径向偏差；
- \(P_{\mathrm{cyc}}\)：周期包裹的归一化相位偏差。

网络输出为：

\[
\widehat{\Delta x}.
\]

最终重建为：

\[
\boxed{
\hat{x}=X_{\mathrm{ref3}}+\widehat{\Delta x}
}
\]

## 2.3 RSB-FiLM 的角色

RSB-FiLM 是当前 ReMiC-Net 的核心结构增强：

> 几何分支不是简单拼接到图像输入，也不是生成额外输出头，而是生成受参考面相位失配包络约束的 FiLM 调制参数，从中深层调制 3D U-Net 的补偿特征。

RSB-FiLM 解决的问题是：

- 普通 FiLM 的 \(\gamma,\beta\) 可无界增大，可能压倒物理门控先验；
- 参考面附近不应被网络强行大幅调制；
- 相位偏差较大的区域应允许更强补偿；
- 浅层原始细节与 skip connection 不应被污染。

---

# 3. 数据集总设计

## 3.1 数据集一：稀疏随机点目标数据集

角色：

- 前置物理验证数据集。

作用：

1. 验证柱面前向仿真链路是否正确；
2. 验证 `ref3/ref5/ref7/ref9/BP` 的质量–复杂度变化趋势；
3. 验证不同半径、方位、高度位置上的参考面失配规律；
4. 验证 \(M_{\mathrm{shell}},\delta\rho,P_{\mathrm{cyc}}\) 是否与误差分布具有可解释关联；
5. 验证 RSB-FiLM 是否在高相位偏差区域提供更强补偿能力。

必须覆盖：

- 不同半径位置；
- 不同高度位置；
- 不同方位位置；
- 单点、双点、少量多点；
- 不同散射强度；
- 不同相对参考面距离与相位状态。

## 3.2 数据集二：extended target shape-family 数据集

角色：

- 主训练集 / 主验证集 / 主战场。

至少覆盖：

- `line`
- `cross`
- `L-shape`
- `double-line`
- `small_rect_edge`
- `point_cluster`

作用：

1. 检验算法在可解释结构场景下的表现；
2. 检验 thin-support、edge-like、connected-support 等难点；
3. 构成论文主图主表基础；
4. 检验 \(P_{\mathrm{cyc}}\) 是否能够帮助补偿径向参考面失配导致的散焦与结构断裂；
5. 检验 RSB-FiLM 相比普通 FiLM 是否改善结构化失配补偿。

## 3.3 数据集三：Manisali-style 随机 extended target 数据集

角色：

- 补充性训练 / 泛化数据集。

作用：

1. 防止模型只记住 hand-crafted family；
2. 检查模型对随机 extended targets 的泛化能力；
3. 与 shape-family 数据形成互补。

---

# 4. 几何与物理仿真原则

所有样本均应来自：

1. 柱面场景定义；
2. 柱面前向回波生成；
3. 柱面参考面近似算法重建；
4. 柱面高精度 BP 或高质量物理基线；
5. 统一评测。

不得使用二维代理图样作为主证据来源。

数据设计中必须显式考虑：

- 目标半径 / 距离向位置变化；
- 不同高度位置；
- 不同方位位置；
- 目标与参考面相对位置；
- 最近参考面分配；
- 径向偏差 \(\delta\rho\)；
- 周期相位偏差 \(P_{\mathrm{cyc}}\)；
- RSB-FiLM 相位失配包络 \(m\)；
- 参考面数量对误差和速度的影响；
- 柱面几何导致的近似失配随空间位置变化。

---

# 5. 训练标签与输入定义

## 5.1 标签定义

训练监督固定为：

> **场景真值 reflectivity / voxel truth 的幅度体**。

BP 只作为高精度传统基线，不作为训练标签。

## 5.2 second-stage 输入定义

主版本正式定义为：

> **`X_ref3` 粗重建幅度体 + `[Mshell, δρ, Pcyc]` reference-surface-aware geometry maps -> ReMiC-Net with RSB-FiLM -> residual compensation**

### 主输入

- `X_ref3`：由 `ref3` reduced-reference physical backbone 得到的粗重建幅度体。

### Geometry branch 输入

\[
G=[M_{\mathrm{shell}},\delta\rho,P_{\mathrm{cyc}}].
\]

#### `Mshell`

参考面 / shell 分配编码。对 `ref3`，推荐使用 3 通道 one-hot 编码。

#### `δρ`

\[
\delta\rho(v)=\rho(v)-\rho_{\mathrm{ref}}^{\ast}(v).
\]

表示体素半径与最近参考面半径之间的有符号偏差。

#### `Pcyc`

\[
P_{\mathrm{cyc}}(v)
=
\frac{1}{\pi}
\operatorname{wrap}_{(-\pi,\pi]}
\left(
\frac{4\pi f_c}{c}\delta\rho(v)
\right).
\]

推荐英文写法：

> cyclic phase-deviation encoding

推荐中文写法：

> 周期包裹的归一化相位偏差

### 不再作为当前主输入的通道

- `valid FOV mask`
- `support prior`

说明：

- `valid FOV mask` 可保留为 evaluation mask 或数据有效性过滤条件。
- `support prior` 不再作为输入。

## 5.3 输出定义

输出：

\[
\widehat{\Delta x}.
\]

最终重建：

\[
\boxed{
\hat{x}=X_{\mathrm{ref3}}+\widehat{\Delta x}
}
\]

不使用：

- support head；
- final residual gate。

---

# 6. RSB-FiLM 冻结定义

## 6.1 相位失配包络

\[
\boxed{
 m(v)=\epsilon_m+(1-\epsilon_m)|P_{\mathrm{cyc}}(v)|
}
\]

默认：

\[
\epsilon_m=0.05.
\]

第 \(l\) 层使用：

\[
m_l=\operatorname{Downsample}_l(m).
\]

## 6.2 RSB-FiLM 公式

Geometry branch 预测 raw tensors：

\[
\Gamma_l,
\quad
B_l.
\]

RSB-FiLM 调制为：

\[
\boxed{
\widetilde{F}_l
=
\left[1+m_l\alpha_\gamma\tanh(\Gamma_l)\right]\odot F_l
+
 m_l\alpha_\beta\tanh(B_l)
}
\]

默认：

\[
\alpha_\gamma=0.5,
\qquad
\alpha_\beta=0.1.
\]

但论文公式中保留符号 \(\alpha_\gamma,\alpha_\beta\)，并在消融中分析敏感性。

## 6.3 放置层级

假设四级 3D U-Net：

\[
E_0,E_1,E_2,E_3,B,D_3,D_2,D_1,D_0.
\]

默认放置：

\[
\boxed{
\mathcal{L}_{\mathrm{RSB}}=\{E_2,E_3,B,D_3,D_2\}
}
\]

明确不放置：

\[
E_0,E_1,D_1,D_0.
\]

明确不调制：

- skip connection path。

理由：

- 浅层和 skip path 保留 \(X_{\mathrm{ref3}}\) 的原始细节；
- 中深层进行 reference-surface-aware compensation strategy modulation。

---

# 7. 对照方法设计

## 7.1 传统基线

论文主对照必须包含：

- `ref3`
- `ref5`
- `ref7`
- `ref9`
- 高精度 `BP`

这组基线构成传统速度–质量曲线。

## 7.2 学习方法主线

学习方法主线定义为：

1. `ref3 + plain 3D U-Net`
2. `ref3 + residual 3D U-Net`
3. `ref3 + residual + Mshell`
4. `ref3 + residual + Mshell + δρ`
5. `ref3 + residual + Mshell + δρ + Pcyc`
6. `ref3 + Geometry branch + generic FiLM`
7. `ref3 + Geometry branch + RSB-FiLM`

## 7.3 不建议作为主线的对照

不建议把以下内容放入主表主图中心：

- raw echo -> 3D U-Net 纯黑盒；
- reintroduced `valid FOV mask` input；
- reintroduced `support prior` input；
- support mask head；
- Dice loss / support Dice；
- complex echo-domain consistency loss。

这些内容容易使主线分散。

---

# 8. 评测指标体系

## 8.1 主指标

必须保留：

- runtime；
- speedup vs BP；
- magnitude NMSE；
- PSNR；
- SSIM。

## 8.2 当前阶段不作为主指标

以下内容不作为主指标：

- support Dice；
- complex echo-domain NMSE；
- sampled complex forward consistency error；
- echo-domain consistency loss；
- 依赖复相位可控性的 measurement-domain fidelity 指标。

## 8.3 与 Pcyc / RSB-FiLM 相关的诊断指标

建议增加以下诊断图或表：

1. 按 \(|\delta\rho|\) 分组的 NMSE / SSIM；
2. 按 \(|P_{\mathrm{cyc}}|\) 分组的误差统计；
3. \(|P_{\mathrm{cyc}}|\le 0.25\) 与 \(|P_{\mathrm{cyc}}|>0.25\) 区域的误差对比；
4. 移除 \(P_{\mathrm{cyc}}\) 后的消融性能下降；
5. generic FiLM 与 RSB-FiLM 的性能差异；
6. RSB-FiLM placement ablation；
7. \(\alpha_\gamma,\alpha_\beta\) sensitivity ablation。

---

# 9. 消融实验设计

## 9.1 输入与结构消融

推荐消融顺序：

1. `ref3`
2. `ref3 + plain 3D U-Net`
3. `ref3 + residual-only`
4. `ref3 + residual + Mshell`
5. `ref3 + residual + Mshell + δρ`
6. `ref3 + residual + Mshell + δρ + Pcyc`
7. `ref3 + full Geometry branch + generic FiLM`
8. `ref3 + full Geometry branch + RSB-FiLM`

关键对比：

\[
[M_{\mathrm{shell}},\delta\rho]
\quad \text{vs.} \quad
[M_{\mathrm{shell}},\delta\rho,P_{\mathrm{cyc}}].
\]

以及：

\[
\text{generic FiLM}
\quad \text{vs.} \quad
\text{RSB-FiLM}.
\]

## 9.2 RSB-FiLM 放置位置消融

| 设置 | RSB-FiLM 位置 | 目的 |
|---|---|---|
| No FiLM | 无 | 普通 residual baseline |
| Bottleneck only | \(B\) | 仅验证全局几何调制 |
| Encoder deep | \(E_2,E_3,B\) | 验证中深层编码调制 |
| Encoder + decoder deep | \(E_2,E_3,B,D_3,D_2\) | 当前主方法 |
| All levels | \(E_0,E_1,E_2,E_3,B,D_3,D_2,D_1,D_0\) | 证明浅层全调制未必更好 |

## 9.3 RSB-FiLM 缩放上限消融

\[
\alpha_\gamma\in\{0.25,0.5,1.0\}
\]

\[
\alpha_\beta\in\{0,0.1,0.25\}
\]

默认：

\[
\alpha_\gamma=0.5,
\quad
\alpha_\beta=0.1.
\]

---

# 10. 当前 physics-guided 的正式含义

本文中的 physics-guided 体现在四个层面。

## 层次一：reduced-reference cylindrical physical backbone

第一阶段保留：

\[
x_{\mathrm{ref3}}=\mathcal{R}_{\mathrm{ref3}}(y).
\]

网络不是从 raw echo 黑盒回归，而是在物理粗成像结果上做补偿。

## 层次二：reference-surface-aware geometric metadata

ReMiC-Net 显式使用：

\[
[M_{\mathrm{shell}},\delta\rho,P_{\mathrm{cyc}}].
\]

这三个输入直接对应 reference-surface approximation 的误差来源。

## 层次三：cyclic phase-deviation conditioning

\[
P_{\mathrm{cyc}}
=
\frac{1}{\pi}
\operatorname{wrap}_{(-\pi,\pi]}
\left(
\frac{4\pi f_c}{c}\delta\rho
\right).
\]

该项将几何偏差映射为双程传播意义下的周期相位状态。

## 层次四：RSB-FiLM bounded feature modulation

\[
\widetilde{F}_l
=
\left[1+m_l\alpha_\gamma\tanh(\Gamma_l)\right]\odot F_l
+
 m_l\alpha_\beta\tanh(B_l).
\]

该结构使网络的补偿特征调制受参考面相位失配先验约束。

---

# 11. 当前主损失函数

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

初期实验可先使用：

\[
\mathcal{L}=\|\widehat{\Delta x}-\Delta x^{\star}\|_1.
\]

不使用：

- support BCE；
- support Dice；
- complex echo-domain consistency loss；
- \(\gamma,\beta\) 正则项作为必选 loss。

---

# 12. 当前主方法一句话定义

> **ReMiC-Net with RSB-FiLM uses a ref3 reduced-reference cylindrical physical reconstruction as warm start, takes reference-surface-aware geometry maps \([M_{\mathrm{shell}},\delta\rho,P_{\mathrm{cyc}}]\) as conditioning metadata, and performs bounded FiLM modulation in the middle/deep layers of a residual 3D U-Net to compensate structured reference-surface approximation mismatch.**

中文：

> **ReMiC-Net with RSB-FiLM 以 ref3 少参考面柱面物理重建作为 warm start，以 \([M_{\mathrm{shell}},\delta\rho,P_{\mathrm{cyc}}]\) 作为参考面几何条件，在残差 3D U-Net 的中深层通过有界 FiLM 调制补偿参考面近似带来的结构化失配。**

---

# 13. Final Statement

当前主线冻结为：

\[
\boxed{
X_{\mathrm{ref3}}
+
[M_{\mathrm{shell}},\delta\rho,P_{\mathrm{cyc}}]
\rightarrow
\text{Residual 3D U-Net with RSB-FiLM}
\rightarrow
\widehat{\Delta x}
\rightarrow
\hat{x}
}
\]

其中：

\[
\hat{x}=X_{\mathrm{ref3}}+\widehat{\Delta x}.
\]

该版本不再以 support segmentation、Dice、FOV mask 或 complex echo consistency 作为主方法内容。
