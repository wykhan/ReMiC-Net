# ReMiC-Net 论文效果图绘制建议

**主题：用于展示 reduced-reference reference-surface approximation error 及其学习补偿效果的图像体系**

本文档汇总当前 ReMiC-Net / RSB-FiLM 论文中值得绘制的效果图，并按照对论文主线的支撑价值进行降序排列。排序依据不是“图是否好看”，而是图是否能够清楚证明：

> 少参考面柱面快速成像引入的结构化参考面近似误差，能够被 ReMiC-Net 有针对性地补偿。

当前论文主线是：

\[
x_{\mathrm{ref3}}=\mathcal{R}_{\mathrm{ref3}}(y)
\]

\[
\widehat{\Delta x}=f_\theta(X_{\mathrm{ref3}},G),
\qquad
\hat{x}=X_{\mathrm{ref3}}+\widehat{\Delta x}
\]

其中几何分支输入冻结为：

\[
G(v)=\left[M_{\mathrm{shell}}(v),\delta\rho(v),P_{\mathrm{cyc}}(v)\right].
\]

因此，主效果图必须尽量体现三件事：

1. 参考面附近与参考面之间的误差差异；
2. ref3 的结构化失配在径向 \(\rho\) 维上的表现；
3. ReMiC-Net 的补偿是否集中发生在 reference-surface mismatch 最严重的区域。

---

## 一、总原则

### 1. 主图必须保留 \(\rho\) 维

你的算法不是一般的图像增强，而是针对参考面近似算法的补偿。参考面近似误差主要沿半径 / 壳层方向表现出来。因此，主图不能轻易把 \(\rho\) 维压掉。

不适合作为主证据图的显示方式包括：

\[
I_{\mathrm{unwrap}}(\theta,z)=\max_\rho |\hat{x}(\rho,\theta,z)|
\]

以及：

\[
I_{\mathrm{front}}(x,z)=\max_y |\hat{x}(x,y,z)|.
\]

这两类图可以作为概览图或读者友好图，但它们会抹掉参考面之间的误差信息，不能作为证明补偿机制的主图。

### 2. 主图要显式标出参考面位置

对 ref3，参考面为：

\[
\rho_{\mathrm{ref}}=[0.00,0.15,0.30]\;\mathrm{m}.
\]

对 ref5/ref7/ref9，也应在需要时标出对应参考面。凡是横轴包含 \(\rho\) 的图，都建议用竖虚线标出参考面位置。

### 3. 不要随机选切片

切片应围绕参考面机制设计，优先选择：

1. 参考面壳层；
2. 两个参考面之间的中点壳层；
3. 离最近参考面最远的壳层；
4. 目标主体穿过的 \(\theta\) 或 \(z\) 切片。

---

# 二、效果图推荐列表（按价值降序）

---

## 1. Reference-Surface-Aware Multi-Shell Comparison

### 图名建议

**Reference-Surface-Aware Shell-wise Qualitative Comparison**

或：

**Qualitative Comparison on Reference and Inter-Reference Shells**

### 希望表达什么

这张图要直接回答：

> ref3 在参考面附近本来就较好，但在参考面之间退化明显；ReMiC-Net 的主要收益正发生在这些非参考壳层上。

这是最能体现论文核心机制的图。

### 如何绘制

固定若干半径层，画每个半径壳层上的柱面展开图：

\[
I_{\mathrm{shell}}(\theta,z;\rho_i)=|\hat{x}(\rho_i,\theta,z)|.
\]

行方向选择不同壳层，例如：

1. \(\rho=\rho_{\mathrm{ref},1}\)：参考面壳层；
2. \(\rho=(\rho_{\mathrm{ref},1}+\rho_{\mathrm{ref},2})/2\)：参考面中点壳层；
3. \(\rho=\rho_{\mathrm{ref},2}\)：另一个参考面壳层；
4. \(\rho=(\rho_{\mathrm{ref},2}+\rho_{\mathrm{ref},3})/2\)：另一个中点壳层。

列方向建议：

\[
\text{GT/BP},\quad \text{ref3},\quad \text{ref7/ref9},\quad \text{Ours},\quad \text{Error/Improvement}.
\]

如果版面紧张，可以减少为：

\[
\text{GT/BP},\quad \text{ref3},\quad \text{Ours},\quad \text{Error/Improvement}.
\]

### 为何有价值

这张图可以直接展示：

- 参考面上 ref3 可能已经不差；
- 参考面之间 ref3 明显退化；
- ReMiC-Net 的提升集中在非参考壳层；
- 补偿效果与 \(M_{\mathrm{shell}},\delta\rho,P_{\mathrm{cyc}}\) 的设计逻辑一致。

它能防止审稿人把方法理解为 generic image enhancement CNN。

### 推荐位置

主文实验部分的第一张 qualitative figure。

---

## 2. Shell-wise Error Curve vs Radius

### 图名建议

**Shell-wise Reconstruction Error as a Function of Radius**

或：

**Radial Distribution of Reference-Surface Approximation Error**

### 希望表达什么

将第一张图的视觉结论定量化：

> ref3 的误差随 \(\rho\) 呈现结构化起伏，在参考面附近较低，在参考面之间较高；ReMiC-Net 显著压低并平滑这种误差起伏。

### 如何绘制

对每一个半径壳层计算 shell-wise NMSE：

\[
\mathrm{NMSE}_{\mathrm{shell}}(\rho_i)=
\frac{
\|\hat{x}(\rho_i,\cdot,\cdot)-x^\star(\rho_i,\cdot,\cdot)\|_2^2
}{
\|x^\star(\rho_i,\cdot,\cdot)\|_2^2
}.
\]

横轴：

\[
\rho
\]

纵轴：

\[
\mathrm{NMSE}_{\mathrm{shell}}(\rho)
\]

曲线建议包含：

- ref3；
- ref5/ref7/ref9；
- BP；
- Ours。

并在图上用竖虚线标出 ref3 参考面：

\[
\rho=0.00,\;0.15,\;0.30\;\mathrm{m}.
\]

### 为何有价值

整体 NMSE 只能说明 Ours 更好，但不能说明好在哪里。这张图可以证明：

> Ours 不是无差别增强，而是在 reference-surface approximation error 最严重的径向区域发挥作用。

这是非常适合 TGRS/JSTAR 论文的机制型定量图。

### 推荐位置

主文实验部分，紧跟 Multi-Shell Comparison。

---

## 3. Error Improvement Map in \(\rho-z\) or \(\rho-\theta\) Plane

### 图名建议

**Spatial Map of Compensation Gain**

或：

**Improvement Map of Learned Mismatch Compensation**

### 希望表达什么

直接展示：

> ReMiC-Net 的补偿到底发生在哪里。

### 如何绘制

定义 improvement：

\[
\Delta(\rho,\theta,z)=
|x_{\mathrm{ref3}}-x^\star|-|x_{\mathrm{ours}}-x^\star|.
\]

若：

\[
\Delta>0,
\]

说明 Ours 比 ref3 更接近真值。

可画两类切片。

#### 方式 A：固定 \(\theta=\theta_0\)，画 \(\rho-z\) 平面

\[
\Delta(\rho,z;\theta_0).
\]

#### 方式 B：固定 \(z=z_0\)，画 \(\rho-\theta\) 平面

\[
\Delta(\rho,\theta;z_0).
\]

建议叠加参考面位置。

### 为何有价值

它将“补偿”从视觉感受变成空间分布证据。它可以证明：

- 改善主要集中在参考面之间；
- 改善集中在目标支撑区域；
- 网络没有简单地全局锐化或全局增亮；
- residual compensation 具有物理针对性。

### 推荐位置

主文或补充材料。若版面允许，建议放主文。

---

## 4. \(\rho-z\) Slice Comparison through Target Main Structure

### 图名建议

**Radial–Vertical Slice Comparison**

或：

**\(\rho-z\) Slice Visualization of Radial Defocus Compensation**

### 希望表达什么

展示 reference-surface mismatch 最典型的视觉后果：

- 径向失焦；
- 径向拉伸；
- 目标厚度变胖；
- 结构断裂；
- 边界模糊；
- 非参考层能量错位。

### 如何绘制

选一个穿过目标主体的方位角：

\[
\theta=\theta_0.
\]

画：

\[
I_{\rho z}(\rho,z;\theta_0)=|\hat{x}(\rho,\theta_0,z)|.
\]

列方向：

\[
\text{GT/BP},\quad \text{ref3},\quad \text{ref7/ref9},\quad \text{Ours},\quad \text{Error}.
\]

横轴为 \(\rho\)，纵轴为 \(z\)。

### 为何有价值

你的主要误差与径向参考面有关，\(\rho-z\) 切片比 front-view 更适合展示补偿效果。front-view 会把径向信息压掉，而 \(\rho-z\) 切片能让审稿人直接看到径向方向是否被修复。

### 推荐位置

主文定性图，尤其适合展示 extended target 的结构恢复。

---

## 5. Performance vs Nearest-Reference Distance

### 图名建议

**Reconstruction Quality versus Distance to Nearest Reference Surface**

### 希望表达什么

回答：

> 离参考面越远，ref3 是否越差？Ours 是否在远离参考面的区域收益更大？

这张图直接对应 \(\delta\rho\) 和 \(P_{\mathrm{cyc}}\) 的方法设计。

### 如何绘制

定义体素到最近参考面的距离：

\[
d_{\mathrm{nr}}(v)=\min_m|\rho(v)-\rho_{\mathrm{ref},m}|.
\]

按 \(d_{\mathrm{nr}}\) 分桶，例如：

- 0–2.5 mm；
- 2.5–5 mm；
- 5–7.5 mm；
- 7.5–10 mm；
- 10 mm 以上。

每个桶内计算：

\[
\mathrm{NMSE},\quad \mathrm{MAE},\quad \mathrm{SSIM},\quad \text{or}\quad \Delta\mathrm{NMSE}.
\]

横轴：

\[
d_{\mathrm{nr}}\ \text{bin}
\]

纵轴：

\[
\text{NMSE or NMSE reduction}.
\]

方法：

\[
\text{ref3},\quad \text{ref7/ref9},\quad \text{Ours}.
\]

### 为何有价值

如果 Ours 在大 \(d_{\mathrm{nr}}\) 区域收益最大，就可以强力支撑：

> 网络确实利用 reference-surface-aware metadata 补偿了近似误差。

这张图是机制验证图，不是普通效果图。

### 推荐位置

主文定量分析部分。

---

## 6. \(\rho-\theta\) Slice Comparison at Representative Height

### 图名建议

**Radial–Azimuthal Slice Comparison at a Representative Height**

### 希望表达什么

展示同一高度层上，目标在径向和方位向的形状是否被恢复。

尤其适合安检场景，例如：

- 胸部高度；
- 腰部高度；
- 腿部高度；
- 贴体目标所在高度。

### 如何绘制

固定：

\[
z=z_0.
\]

画：

\[
I_{\rho\theta}(\rho,\theta;z_0)=|\hat{x}(\rho,\theta,z_0)|.
\]

列方向：

\[
\text{GT/BP},\quad \text{ref3},\quad \text{ref7/ref9},\quad \text{Ours},\quad \text{Error}.
\]

### 为何有价值

它保留了 \(\rho\) 维，能够展示：

- 目标是否沿径向变厚；
- 多目标是否被粘连；
- ref3 是否在参考面之间出现伪影；
- Ours 是否恢复目标的径向边界。

它也适合展示 extended target 的结构完整性。

### 推荐位置

主文或补充材料。若 extended target 是主战场，建议至少放一张。

---

## 7. Residual Prediction Map

### 图名建议

**Learned Residual Distribution**

或：

**Predicted Mismatch Residual of ReMiC-Net**

### 希望表达什么

展示网络实际学到的残差：

\[
\widehat{\Delta x}=f_\theta(X_{\mathrm{ref3}},G).
\]

最终输出为：

\[
\hat{x}=X_{\mathrm{ref3}}+\widehat{\Delta x}.
\]

这张图的目标是证明网络不是从零生成图像，而是在 ref3 的基础上做 residual correction。

### 如何绘制

在与主图相同的壳层或切片上，画：

\[
\widehat{\Delta x}(\rho,\theta,z).
\]

可选显示方式：

1. 残差绝对值；
2. 带符号 residual；
3. 归一化 residual：

\[
\frac{\widehat{\Delta x}}{\max |X_{\mathrm{ref3}}|}.
\]

### 为何有价值

它能说明 ReMiC-Net 的方法身份：

> physics-guided residual mismatch compensation。

如果残差主要集中在非参考壳层、目标边界和失焦区域，方法解释力会大幅增强。

### 推荐位置

方法解释图或补充材料。主文版面允许时可放。

---

## 8. Two-Scatterer Resolving Capability Test

### 图名建议

**Two-Scatterer Resolving Capability under Reduced-Reference Approximation**

### 希望表达什么

不要称为系统 PSF。它要表达：

> 在相同雷达参数下，ref3 是否因为参考面近似导致相邻散射体粘连；Ours 是否更接近 BP 的可分辨能力。

### 如何绘制

设计三组双点。

#### 径向双点

\[
(\rho_1,\theta,z),\quad(\rho_2,\theta,z).
\]

改变：

\[
\Delta\rho.
\]

#### 方位双点

\[
(\rho,\theta_1,z),\quad(\rho,\theta_2,z).
\]

改变弧长：

\[
\rho\Delta\theta.
\]

#### 高度双点

\[
(\rho,\theta,z_1),\quad(\rho,\theta,z_2).
\]

改变：

\[
\Delta z.
\]

每行一个间距，每列一个方法：

\[
\text{GT},\quad \text{ref3},\quad \text{BP},\quad \text{Ours}.
\]

同时给一维 profile，显示是否有两个峰。

### 为何有价值

它能说明：

- Ours 没有把两个点过度平滑成一个点；
- Ours 没有产生虚假超分辨；
- Ours 在 reduced-reference approximation 下更好地保持相邻散射体的可分辨性。

但它只是前置诊断，不能作为 extended target 学习成像的主结论。

### 推荐位置

实验前置验证部分或补充材料。

---

## 9. Cylindrical Unwrapped Overview

### 图名建议

**Unwrapped Cylindrical Projection for Global Visualization**

### 希望表达什么

展示整体目标在周向和高度方向的位置分布：

\[
I_{\mathrm{unwrap}}(\theta,z)=\max_\rho |\hat{x}(\rho,\theta,z)|.
\]

### 如何绘制

对所有方法统一做半径最大值投影：

\[
I_{\mathrm{unwrap}}(\theta,z)=
\max_{\rho\in[\rho_{\min},\rho_{\max}]}
|\hat{x}(\rho,\theta,z)|.
\]

列方向：

\[
\text{GT/BP},\quad \text{ref3},\quad \text{ref7/ref9},\quad \text{Ours}.
\]

### 为何有价值

它适合安检场景，因为类似“把人体表面展开”。但它会压掉 \(\rho\) 维，而你的主要误差恰恰发生在参考面之间的径向维。因此，它只能作为 overview，不能作为核心证据图。

### 推荐位置

应用展示或补充材料。

---

## 10. Cartesian Front-View Projection

### 图名建议

**Cartesian Front-View Projection for Intuitive Interpretation**

### 希望表达什么

让读者直观看到“像不像人体 / 目标”，尤其适合安检应用。

### 如何绘制

先将柱面体重采样到笛卡尔体：

\[
x=\rho\cos\theta,
\qquad
y=\rho\sin\theta.
\]

然后画前半空间投影：

\[
I_{\mathrm{front}}(x,z)=
\max_{y\ge 0}|\hat{x}(x,y,z)|.
\]

不要把前后全投影到一起，否则前后目标会混叠。

### 为何有价值

front-view 的价值是应用解释，而不是机制证明。它可以帮助非柱面成像领域的读者快速理解结果，但不能体现 reference-surface mismatch 的补偿位置。

### 推荐位置

主文后半部分、应用展示图或补充材料。

---

## 11. Ref3 / Ref5 / Ref7 / Ref9 / BP / Ours Speed–Quality Trade-off Plot

### 图名建议

**Speed–Quality Trade-off between Reference-Surface Count and Learned Compensation**

### 希望表达什么

展示核心工程价值：

> Ours 保持 ref3 级速度，但质量接近或超过更多参考面的高质量方法。

### 如何绘制

横轴：

\[
\text{Runtime}
\]

纵轴可以选：

\[
\text{NMSE},\quad \text{PSNR},\quad \text{SSIM}.
\]

每个点是：

\[
\text{ref3},\quad \text{ref5},\quad \text{ref7},\quad \text{ref9},\quad \text{BP},\quad \text{Ours}.
\]

可以用箭头表示：

\[
\text{ref3}\rightarrow\text{Ours}.
\]

### 为何有价值

你的论文不仅是质量更高，而是推动速度–质量边界。该图比表格更直观，适合作为总览图。

### 推荐位置

实验结果总览或消融总结部分。

---

## 12. Failure-Mode Case Study on Extended Targets

### 图名建议

**Failure-Mode Analysis of Reduced-Reference Imaging on Extended Targets**

### 希望表达什么

按 failure mode 展示 ref3 的典型问题及 Ours 的修复效果，例如：

- radial defocus；
- shell-wise discontinuity；
- support fragmentation；
- weak target suppression；
- false scattering artifacts；
- multi-object confusion。

### 如何绘制

每一行一个典型 failure case。每列：

\[
\text{GT/BP},\quad \text{ref3},\quad \text{Ours},\quad \text{Error}.
\]

显示方式优先选择：

- \(\rho-z\) 切片；
- \(\rho-\theta\) 切片；
- shell-wise \(\theta-z\) 图。

### 为何有价值

它借鉴了文献中“统一模板 + 不同目标难度 / 不同失败模式”的组织方式。不要随机堆图，而应让每个 case 服务一个明确论点。

### 推荐位置

主文少量展示，更多放补充材料。

---

## 13. Sphere / Cylinder / Simple Canonical Target Comparison

### 图名建议

**Canonical Simple Target Reconstruction**

### 希望表达什么

用小球、圆柱、板状体等标准目标连接点目标与复杂 extended target。

### 如何绘制

目标类型可以包括：

- small sphere；
- medium sphere；
- cylinder；
- plate；
- two separated objects。

每个目标用统一模板：

\[
\text{GT/BP},\quad \text{ref3},\quad \text{Ours},\quad \text{Error}.
\]

显示方式优先用：

- \(\rho-z\)；
- \(\rho-\theta\)；
- shell-wise \(\theta-z\)。

### 为何有价值

球体可以作为 quasi-point 或 simple extended target，但不建议完全替代点目标。它适合做过渡实验，不能成为论文主战场。

### 推荐位置

可选，适合补充材料或前置验证部分。

---

## 14. Pure 3D Volume Rendering / Point Cloud Rendering

### 图名建议

**3D Rendering of Reconstructed Reflectivity Volume**

### 希望表达什么

给读者一个三维整体印象。

### 如何绘制

对三维体做：

- isosurface；
- voxel rendering；
- top-k scatter cloud；
- transparent volume rendering。

列方向：

\[
\text{GT/BP},\quad \text{ref3},\quad \text{Ours}.
\]

### 为何价值有限

3D 渲染看起来直观，但难以严肃比较：

- 参考面之间的误差；
- 径向失焦；
- shell-wise compensation；
- 局部结构恢复。

它适合放在图形摘要、poster、补充材料，不适合作为核心证据图。

---

# 三、主文最小推荐图组

如果主文版面有限，建议优先保留以下 6 类图：

1. **Reference-Surface-Aware Multi-Shell Comparison**  
   主定性图，直接展示参考面与非参考壳层差异。

2. **Shell-wise Error Curve vs Radius**  
   主定量机制图，证明误差随半径结构化变化并被压低。

3. **Error Improvement Map**  
   直接显示补偿发生在哪里。

4. **\(\rho-z\) Slice Comparison**  
   展示径向失焦、结构断裂和补偿效果。

5. **Performance vs Nearest-Reference Distance**  
   证明方法收益与 \(\delta\rho/P_{\mathrm{cyc}}\) 机制一致。

6. **\(\rho-\theta\) Slice at Representative Height**  
   展示 extended target 在径向–方位平面的结构恢复。

---

# 四、可选补充图组

如果补充材料或 appendix 版面允许，可以继续加入：

7. **Residual Prediction Map**  
   展示 ReMiC-Net 学到的 residual distribution。

8. **Two-Scatterer Resolving Capability Test**  
   用作前置诊断，不称为全局 PSF。

9. **Cylindrical Unwrapped Overview**  
   用于安检场景整体展示，但不能作为主证据。

10. **Cartesian Front-View Projection**  
    用于读者直观理解人体/目标形状。

11. **Speed–Quality Trade-off Plot**  
    展示 ref3+learning 推动速度–质量边界。

12. **Failure-Mode Case Study**  
    按错误类型展示补偿效果。

13. **Canonical Sphere/Cylinder Target**  
    用作点目标与 extended target 之间的过渡实验。

14. **3D Volume Rendering**  
    仅用于整体展示或图形摘要。

---

# 五、建议的论文图表组织方式

## Figure 1：几何与参考面示意图

展示：

- 柱面孔径扫描几何；
- 成像半径范围；
- ref3/ref5/ref7/ref9 参考面；
- 参考面层与中间层的选择方式。

目的：让读者理解后续 shell-wise 图为什么这样选。

## Figure 2：主定性图：Multi-Shell Comparison

展示：

- GT/BP；
- ref3；
- ref7/ref9；
- Ours；
- Error/Improvement。

行方向为参考面层和参考面中间层。

## Figure 3：机制定量图：Shell-wise Error vs Radius

展示：

- ref3 误差随 \(\rho\) 起伏；
- Ours 压低非参考层误差；
- 参考面位置用竖线标出。

## Figure 4：局部切片图：\(\rho-z\) / \(\rho-\theta\)

展示：

- 径向失焦；
- 结构断裂；
- 目标变厚；
- Ours 的局部修复。

## Figure 5：Nearest-Reference Distance 分桶图

展示：

- 离参考面越远，ref3 越差；
- Ours 在远离参考面的区域收益最大。

## Figure 6：Speed–Quality Trade-off

展示：

- ref3 很快但质量差；
- BP 质量好但慢；
- Ours 接近高质量同时保持 ref3 级速度。

---

# 六、推荐图注写法模板

## 1. Multi-Shell Comparison 图注模板

**中文模板：**

图 X 展示了不同半径壳层上的重建结果对比。所选壳层包括 ref3 参考面壳层以及相邻参考面之间的中点壳层。可以看到，ref3 在参考面附近的退化相对有限，而在参考面之间出现明显的径向失焦和结构断裂。相比之下，ReMiC-Net 在非参考壳层上显著恢复目标结构，表明所提出的 reference-surface-aware residual compensation 能够针对少参考面近似引起的结构化失配进行补偿。

**英文模板：**

Fig. X compares the reconstructed reflectivity on selected cylindrical shells, including both reference shells and inter-reference shells of the ref3 operator. The ref3 reconstruction shows relatively mild degradation near the reference shells but suffers from radial defocus and structural discontinuities between adjacent reference surfaces. In contrast, ReMiC-Net substantially restores the target structure on the inter-reference shells, indicating that the proposed reference-surface-aware residual compensation effectively mitigates the structured mismatch induced by reduced-reference imaging.

## 2. Shell-wise Error Curve 图注模板

**中文模板：**

图 X 给出了不同方法随半径变化的 shell-wise NMSE。竖虚线表示 ref3 使用的参考柱面位置。ref3 的误差在参考面附近较低，而在参考面之间明显升高，说明少参考面近似误差具有径向结构化特征。ReMiC-Net 显著降低了非参考壳层上的误差，并使径向误差分布更加平滑。

**英文模板：**

Fig. X reports the shell-wise NMSE as a function of the radial coordinate. The vertical dashed lines indicate the reference surfaces used by the ref3 operator. The ref3 reconstruction exhibits lower errors around the reference surfaces and increased errors between adjacent reference shells, confirming the radial structure of the reduced-reference approximation error. ReMiC-Net significantly reduces the errors on inter-reference shells and leads to a smoother radial error distribution.

## 3. Nearest-Reference Distance 图注模板

**中文模板：**

图 X 按体素到最近参考面的距离对重建误差进行分桶统计。随着距离最近参考面的径向偏差增大，ref3 的误差逐渐升高。ReMiC-Net 在大偏差区域取得更明显的误差降低，说明 \(\delta\rho\) 和 \(P_{\mathrm{cyc}}\) 提供的 reference-surface-aware 几何信息有助于网络识别并补偿高失配区域。

**英文模板：**

Fig. X evaluates the reconstruction error by grouping voxels according to their distance to the nearest reference surface. The error of the ref3 reconstruction increases as the nearest-reference deviation becomes larger. ReMiC-Net achieves more pronounced error reduction in high-deviation regions, demonstrating that the reference-surface-aware geometric cues encoded by \(\delta\rho\) and \(P_{\mathrm{cyc}}\) help the network identify and compensate high-mismatch regions.

---

# 七、最终结论

你的效果图体系不应围绕“整体图像看起来更好”来设计，而应围绕：

> **在哪些非参考壳层上，少参考面近似造成的结构化误差被补偿了。**

因此，最关键的原则是：

1. 主图必须保留 \(\rho\) 维；
2. 主图必须标出参考面位置；
3. 主图必须包含参考面层与参考面中间层的对比；
4. 定量图必须展示误差随 \(\rho\) 或 \(d_{\mathrm{nr}}\) 的变化；
5. front-view 和 unwrapped view 只能作为应用直观展示，不应作为核心证据。

