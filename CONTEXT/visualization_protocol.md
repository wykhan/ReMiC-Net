# visualization_protocol.md

## 文件角色

本文件用于**冻结项目中的可视化输出规范**，服务于两个目标：

1. **实验进展可视化**：让研究者能够快速判断当前实验是否有改进、问题出在哪里、哪类样本在拖后腿。
2. **论文候选图可视化**：让实验输出能够直接筛选为论文正文或补充材料的候选图，减少后期返工。

本协议适用于以下任务阶段：

* true cylindrical point-target validation
* shape-family ET baseline evaluation
* two-stage learning evaluation
* 后续 physics-consistency / echo-consistency 扩展

本协议应与以下文件配套使用：

* `real_cylindrical_master_document_with_physics_consistency.md`
* `simulation_protocol.md`
* `reference_surface_strategy.md`
* `et_dataset_protocol.md`
* 各 task 的 `task_real_xxx_report.md`

---

# 1. 总原则

## 1.1 双层输出原则

每个核心任务必须同时生成两类图：

### A. Progress Figures

用于**日常研究判断**，帮助快速发现问题和判断趋势。

特点：

* 信息量大
* 允许带内部任务名、样本 ID、实验代号
* 可包含更多子图
* 主要用于内部调试、周报、主控窗口分析

### B. Paper-Candidate Figures

用于**论文候选图筛选**。

特点：

* 版式统一
* 标题简洁
* 不使用内部实验代号
* 色标、尺度、切片规则严格一致
* 可以直接进入论文正文或补充材料

**禁止只输出其中一类。**

---

## 1.2 可比性优先

所有方法比较图必须满足：

* **同一 colormap**
* **同一 normalization rule**
* **同一 slice rule**
* **同一坐标范围**
* **同一裁剪边界**

如果不满足以上条件，不得将其标记为 paper candidate。

---

## 1.3 论文结果图服务于问题定义，而非仅服务于“好看”

所有论文候选图必须至少支持回答下列问题之一：

1. 方法是否推动了速度–质量边界？
2. hardest families 是否获得改进？
3. 关键 failure modes 是否得到缓解？
4. learning / consistency 是否真正改善了结构，而不是只改善均值？

凡不能回答上述问题的图，优先放入 supplementary，而不是正文。

---

# 2. 输出目录规范

每个任务的 `viz/` 目录固定为：

```text
viz/
├── progress/
│   ├── curves/
│   ├── recon_compare/
│   ├── slices/
│   └── scene_3d/
├── paper_candidates/
│   ├── curves/
│   ├── qualitative/
│   ├── tables_as_figs/
│   └── supplementary/
└── manifest/
```

说明：

* `progress/`：内部进展图
* `paper_candidates/`：论文候选图
* `manifest/`：图清单与元信息

---

# 3. 图文件命名规范

## 3.1 曲线图

命名格式：

```text
<task>_<figure_topic>_<split>_<version>.png
```

示例：

* `006b_runtime_quality_frontier_test_v1.png`
* `006b_family_metrics_test_v1.png`
* `006b_failure_mode_mainline_vs_baselines_test_v1.png`

---

## 3.2 单样本 qualitative 图

命名格式：

```text
<task>_<sample_role>_<family>_<sample_id>_<figure_type>.png
```

示例：

* `006b_hard_improved_point_cluster_0007_compare.png`
* `006b_hard_failure_line_0020_compare.png`
* `006b_ordinary_success_double_line_0005_compare.png`

---

## 3.3 论文候选图命名

论文候选图不得继续使用内部实验代号作为图名主标识。

推荐命名：

* `fig_main_frontier.png`
* `fig_family_metrics.png`
* `fig_failure_modes.png`
* `fig_hardcase_improved.png`
* `fig_hardcase_failure.png`

---

## 3.4 禁止项

论文候选图文件名禁止出现：

* `M1`
* `M2`
* `M3`
* `debug`
* `tmp`
* `final_final`

论文候选图统一使用：

* `ours`
* `frozen_mainline`
* `baseline_ref3`
* `baseline_ref9`
* `bp`

---

# 4. 统一视觉规范

## 4.1 Colormap 规范

### 幅度图

所有 GT / baseline / learned / consistency 输出图必须使用同一 colormap。

推荐：

* `viridis`
* 或 `magma`

### 误差图

所有 error map 必须使用另一套固定 colormap。

推荐：

* `inferno`
* 或灰度反转系

禁止：

* 同一比较组中不同方法使用不同 colormap
* 论文候选图中混用多种色图而不说明

---

## 4.2 Normalization 规范

同一组方法对比图必须共享同一 normalization 规则。

允许的规则只有两种：

### Rule A：GT-based normalization

以 GT 的最大值或固定全局范围作为归一化基准。

### Rule B：global group normalization

同一组比较中的所有方法，共享一个全局最大值或固定可视范围。

必须在图注或 manifest 中写明使用了哪条规则。

禁止：

* 每张图单独自适应拉伸
* baseline 与 ours 使用不同动态范围

---

## 4.3 Slice Rule 规范

所有切片图必须显式声明切片规则。

只允许以下三种：

1. `central slice`
2. `maximum-energy slice`
3. `orthogonal triple slices through maximum voxel`

推荐默认规则：

* Progress figures：可使用 `central slice` 或 `maximum-energy slice`
* Paper candidates：默认使用 `orthogonal triple slices through maximum voxel`

禁止不说明切片位置。

---

## 4.4 坐标与裁剪规范

所有方法图必须：

* 使用相同物理坐标范围
* 使用相同图像裁剪边界
* 使用相同比例尺
* 使用统一轴方向约定

如因展示需要进行局部放大，必须另出 zoom-in panel，并保留 full view。

---

## 4.5 文字规范

### Progress figures

可使用：

* sample id
* task id
* family 名称
* split 名称
* 内部方法代号

### Paper-candidate figures

必须避免：

* 内部 task 编号喧宾夺主
* `M1/M2/M3` 作为方法主名称
* 冗长标题

推荐方法名：

* `Ref3`
* `Ref5`
* `Ref7`
* `Ref9`
* `BP`
* `Ours`

---

# 5. 每个任务必须产出的标准图集

以下 8 类图为核心任务的最低要求。

---

## 图 1：速度–质量前沿图

### 作用

回答主问题：

> 方法是否推动了传统速度–质量边界。

### 推荐文件名

* progress: `runtime_quality_frontier_with_learning.png`
* paper candidate: `fig_main_frontier.png`

### 内容要求

* x 轴：runtime（s）
* y 轴：NMSE mean
* 方法点：`ref3/ref5/ref7/ref9/BP/Ours`
* `Ours` 使用明显不同 marker
* 尽量标注 speedup vs BP

### 论文优先级

**最高，正文必备候选。**

---

## 图 2：family-level 指标图

### 作用

回答：

> hardest families 是哪些，方法在 family 维度上是否稳定。

### 推荐文件名

* progress: `family_metrics_mainline_vs_baselines.png`
* paper candidate: `fig_family_metrics.png`

### 内容要求

* x 轴：family
* y 轴：至少包含 NMSE mean
* 方法：建议至少 `ref3/ref9/BP/Ours`
* 若需要可拆成多图：NMSE / PSNR / SSIM 分开

### 论文优先级

**高，正文候选。**

---

## 图 3：failure-mode 统计图

### 作用

回答：

> 方法修掉了哪些结构性失败，而不是只提升平均值。

### 推荐文件名

* progress: `failure_mode_mainline_vs_baselines.png`
* paper candidate: `fig_failure_modes.png`

### 重点 failure modes

* `F2`: edge break / contour fracture
* `F3`: thin-structure disappearance
* `F4`: support fragmentation

### 论文优先级

**高，正文候选。**

---

## 图 4：family-level 分布图

### 作用

用于防止“均值被少数样本拉动”的质疑。

### 推荐文件名

* progress: `nmse_distribution_by_family_and_method.png`
* paper candidate: `fig_family_distributions.png`

### 形式

* boxplot
* violin plot

### family 优先级

优先 hardest families：

* `point_cluster`
* `line`
* `L-shape`

### 论文优先级

**中高，优先补充材料；若版面允许可进正文。**

---

## 图 5：hard improved case

### 作用

展示 hardest family 中，方法成功修复结构的典型样本。

### 推荐文件名

* progress: `hard_improved_<family>_<id>_compare.png`
* paper candidate: `fig_hardcase_improved.png`

### 推荐 family

优先：

* `point_cluster`
* 或 `line`

### 版式要求

至少包含：

* GT
* Ref3
* Ref9
* BP
* Ours
* `|Ref3 - GT|`
* `|Ours - GT|`

### 论文优先级

**高，正文候选。**

---

## 图 6：hard failure case

### 作用

展示方法当前边界，提升可信度。

### 推荐文件名

* progress: `hard_failure_<family>_<id>_compare.png`
* paper candidate: `fig_hardcase_failure.png`

### 推荐 family

优先：

* `line`
* 或结构最细、最脆弱的 family

### 论文优先级

**高，正文候选。**

---

## 图 7：dataset / GT gallery

### 作用

用于数据集说明与实验设置说明。

### 推荐文件名

* progress: `dataset_scene_gallery.png`
* paper candidate: `fig_dataset_gallery.png`

### 内容要求

每个 family 至少一个样本，展示：

* GT 3D 视图
* top / front / side projection

### 论文优先级

**中，适合数据集说明或 supplementary。**

---

## 图 8：训练曲线图

### 作用

展示训练是否正常、是否存在明显过拟合或发散。

### 推荐文件名

* progress: `train_val_loss_mainline.png`
* paper candidate: `fig_training_curves.png`

### 内容要求

* train loss
* val loss
* best checkpoint 标记
* 如有学习率调度，标注主要阶段

### 论文优先级

**中，通常放 supplementary。**

---

# 6. qualitative 图统一版式

## 6.1 模板 A：主对比图

适合正文。

### 排列建议

第一行：

* GT
* Ref3
* Ref9
* BP
* Ours

第二行：

* `|Ref3 - GT|`
* `|Ref9 - GT|`
* `|BP - GT|`
* `|Ours - GT|`
* 指标文本框

### 规则

* 同一 colormap
* 同一 normalization
* 同一切片规则
* 每列顶部写方法名
* 图底部写对应指标

---

## 6.2 模板 B：三正交切片图

适合补充材料或困难案例剖析。

### 排列建议

每个方法一列，三行分别是：

* axial
* coronal
* sagittal

### 规则

* 所有方法使用相同切片位置
* 每列写方法名
* 每列底部写指标

---

# 7. 进展图与论文候选图的关系

## 7.1 Progress Figures

用途：

* 追踪实验趋势
* 定位问题
* 帮助主控窗口判断下一步

特点：

* 可保留 sample id
* 可带内部任务代号
* 图数量可以更多

## 7.2 Paper-Candidate Figures

用途：

* 直接服务论文写作

特点：

* 统一命名
* 统一尺度
* 不带内部 debug 信息
* 可直接进入 LaTeX

**同一核心结果必须至少同时有一张 progress 图和一张 paper-candidate 图。**

---

# 8. 元信息与图清单

每个任务的 `viz/manifest/figure_manifest.json` 中，每张图必须记录：

* `figure_name`
* `figure_path`
* `task`
* `figure_type`
* `dataset`
* `split`
* `sample_id`（如适用）
* `family`
* `methods_shown`
* `slice_rule`
* `normalization_rule`
* `main_message`
* `recommended_for_paper`
* `recommended_section`

其中 `recommended_section` 只允许以下值：

* `main_results`
* `family_analysis`
* `failure_analysis`
* `dataset_description`
* `supplementary`

---

# 9. 每个任务必须输出的“正文候选五图”

每个核心任务结束后，Codex 必须自动给出一套“正文候选五图”，固定包括：

1. `fig_main_frontier.png`
2. `fig_family_metrics.png`
3. `fig_failure_modes.png`
4. `fig_hardcase_improved.png`
5. `fig_hardcase_failure.png`

并在 `task_real_xxx_report.md` 中单独列出：

* 这五张图各自支持什么结论
* 推荐放在论文哪一节
* 是否需要进一步重绘

---

# 10. 需要额外补强的可视化

为了提升论文说服力，Codex 在后续任务中应优先补以下图：

## 10.1 family-level distribution

不是只给均值柱状图，还要给：

* boxplot / violin plot

## 10.2 Ours vs BP hardest-case error map

如果 `Ours` 在当前实验中超过 BP，必须专门补：

* `|BP - GT|`
* `|Ours - GT|`

## 10.3 failure-by-family

不仅统计整体 failure counts，还要按 family 分开展示 F2/F3/F4。

## 10.4 train / val / test consistency

如任务涉及训练，建议补：

* train/val loss
* per-family test metrics
* 若可能，再补 OOD 或 unseen-parameter 验证图

---

# 11. Codex 执行硬规则

以后所有需要绘图的任务，Codex 必须遵守以下规则：

1. 同时生成 `progress/` 与 `paper_candidates/` 两层图。
2. 所有方法比较图使用同一 colormap、同一 normalization、同一切片规则。
3. 论文候选图中禁止使用内部代号 `M1/M2/M3`。
4. 每个核心任务至少输出本协议规定的 8 类标准图。
5. 每张论文候选图必须在 `figure_manifest.json` 中完整登记。
6. 每个任务结束时，必须在报告中自动给出“正文候选五图”。
7. 若某图不满足统一尺度 / 切片 / 归一化要求，禁止标记为 paper candidate。


