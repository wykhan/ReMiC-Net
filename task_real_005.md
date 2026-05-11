
````markdown
# task_real_005：shape-family ET 主实验启动（冻结 Variant B 前端）

你现在服务于项目：

- `PROJECT_ROOT = /home/superws/2026_Projects/Codex_reference_plane_real`
- `CONTEXT = /home/superws/2026_Projects/Codex_reference_plane_real/CONTEXT`
- `workspace = /home/superws/2026_Projects/Codex_reference_plane_real/workspace`

已完成：
- `task_real_001`：bootstrap / 治理冻结
- `task_real_002`：true 3D cylindrical point chain smoke
- `task_real_003`：faithful point validation + radial mismatch evidence
- `task_real_004`：accelerated cylindrical reference-surface engine
- `task_real_004b`：wrap hardening + A/B/C/D 对照
- `task_real_004c`：冻结 Variant B 并完成 broader controlled point 确认

当前已知状态（来自 `task_real_004c_report.md`）：
- 默认传统前端已冻结为  
  **Variant B = active windows + full-library sinc geometry correction**
- `ref3/ref5/ref7/ref9/BP` 的平均速度—质量排序成立
- `ref7/ref9` 仍有局部非单调残留，但不再阻碍进入 ET 主战场
- 当前已具备启动 shape-family ET 主实验的条件

本任务进入：

> **Phase ET-1：shape-family ET 数据集构建 + 传统基线主实验**

---

## 一、任务定位

本任务的唯一目标是：

> 在 true 3D cylindrical simulation 下，构建 shape-family extended-target 主数据集，  
> 并使用已冻结的 Variant B 传统前端运行  
> `ref3/ref5/ref7/ref9/BP`，  
> 形成 ET 场景下的第一版主表、主图、failure taxonomy 和代表样本库。

本任务不是学习训练任务，不做 physics consistency，不接入真实数据。

---

## 二、必须遵守的上位文档

开始前必须阅读并遵守：

1. `CONTEXT/real_cylindrical_master_document_with_physics_consistency.md`
2. `CONTEXT/simulation_protocol.md`
3. `CONTEXT/reference_surface_strategy.md`
4. `CONTEXT/dataset_protocol.md`
5. `CONTEXT/project_brief.md`
6. `CONTEXT/experiment_matrix.md`
7. `PROMPTS/system_rules.md`
8. `PROMPTS/review_checklist.md`
9. `exp/task_real_004c_variantB_confirmation/*/task_real_004c_report.md`

此外，**必须认真参考以下外部基线资料**：
10. `Efficient physics-based learned reconstruction methods for real-time 3D near-field MIMO radar imaging.pdf`
11. 已授权可访问的 git 项目：`Efficient-Learned-3D-Near-Field-MIMO-Imaging`

### 强制要求
- 必须从 Manisali 论文与 git 项目中吸收：
  - 3D extended-target synthesizer / dataset 组织思路
  - 两阶段物理骨干 + 3D U-Net 的工程分层
  - 3D U-Net 输入输出与训练数据组织方式
  - 代表性的可视化与数据落盘方式
- 但不得把其平面/近场 MIMO 前端直接照搬为当前项目主前端
- 当前项目的物理前端必须仍然是：
  - **true cylindrical forward simulation**
  - **Variant B accelerated reference-surface front-end**
  - **BP 作为高精度传统基线**

---

## 三、强制硬约束

### 硬约束 1：ET 数据必须是 true 3D cylindrical simulation data
本任务中任何 dataset / split / sample family，都必须输出：

- `dataset_manifest.json`
- `dataset_protocol_snapshot.md`
- `data_origin_statement.md`

其中 `data_origin_statement.md` 必须明确写出：
- 这是 **true 3D cylindrical simulation data**
- 使用的 forward simulator 入口
- 使用的协议版本
- 使用的重建入口（Variant B + BP）
- 明确声明：不是二维代理 family 图样，不是人工糊成的 ref 图像

若无法证明 ET 数据来自真实 3D 柱面仿真，本任务不得算通过。

---

### 硬约束 2：本任务必须先冻结 ET dataset protocol
在开始正式生成 ET 数据之前，必须新增并冻结：

- `CONTEXT/et_dataset_protocol.md`

该文件必须是项目协议文件，不是临时注释。

---

### 硬约束 3：必须充分借鉴 Manisali 论文与 git 项目
本任务中，Codex 必须显式完成以下动作，并写入报告：

1. 说明从 Manisali 论文借鉴了哪些内容
2. 说明从 git 项目代码借鉴了哪些模块或实现方式
3. 说明哪些地方不能直接照搬，为什么
4. 明确指出：
   - Manisali 的 physics-based first stage 在当前项目中由 **柱面 Variant B 前端** 替代
   - Manisali 的 second-stage / dataset engineering 思路被保留为主要借鉴对象

不得只在报告里笼统写“参考了 Manisali”。

---

### 硬约束 4：每次实验都必须生成可视化
必须输出并保存：

#### A. 原始仿真数据可视化
- GT 3D occupancy / amplitude 视图
- top / front / side 三视图
- family 代表样本的 slice montage

#### B. 成像结果可视化
每个代表样本至少比较：
- GT
- `ref3`
- `ref5`
- `ref7`
- `ref9`
- `BP`

并输出：
- recon compare 图
- 三正交切片
- absolute error map / difference map

#### C. 指标曲线
必须输出：
- `runtime_vs_method_et.png`
- `speedup_vs_bp_et.png`
- `quality_vs_method_et.png`
- `metrics_by_family.png`
- `failure_mode_count_by_method.png`
- 若适合，再输出：
  - `nmse_by_family.png`
  - `psnr_by_family.png`
  - `ssim_by_family.png`

不得只保留 csv/json。

---

### 硬约束 5：必须生成统一命名的任务报告
本任务结束时，必须在产物目录中生成：

- `task_real_005_report.md`

不得使用临时命名风格替代。

---

## 四、严格边界

### 本任务允许做
- 冻结 `et_dataset_protocol.md`
- 构建 shape-family ET 数据集
- 生成 true cylindrical echoes
- 用 Variant B 前端重建 `ref3/ref5/ref7/ref9`
- 用 BP 生成高精度传统基线
- 统一评测与可视化
- 建立 ET failure taxonomy
- 生成主报告
- 更新 `CHANGELOG_DEV.md` 与 `debug.md`

### 本任务禁止做
- 不做学习训练
- 不做 physics consistency
- 不做 Manisali-style random ET dataset
- 不接入真实回波
- 不重新探索前端路线
- 不回退到旧二维代理数据集
- 不修改已有上位协议原文内容

---

## 五、本任务要回答的问题

1. 在 ET 主战场上，Variant B 前端下的 `ref3/ref5/ref7/ref9/BP` 速度—质量关系是否仍成立？
2. 哪些 shape family 对低参考面（尤其 `ref3`）最困难？
3. 哪些 failure mode 是学习补偿最值得优先攻克的？
4. 当前 ET 数据和传统基线是否已经足以支撑后续 `task_real_006` 的两阶段学习训练？

---

## 六、任务拆解

---

### Part A：冻结 ET dataset protocol

#### 目标
新增并冻结：

- `CONTEXT/et_dataset_protocol.md`

#### 必须写清楚的内容

##### 1. family 集合
至少包含以下六类：
- `line`
- `cross`
- `L-shape`
- `double-line`
- `small_rect_edge`
- `point_cluster`

不得擅自删减。新增 family 只能作为附加，不可替代主文档要求的基础 family。

##### 2. 每类的参数多样性
每类必须显式覆盖：
- 尺寸
- 方向
- 位置
- 边界接近程度
- 厚度 / 宽度
- 间距 / 缺口 / 断裂
- 强度变化
- 多实例组合方式

不得只做模板复制。

##### 3. split 设计
本任务先构建 **ET Phase-1 trainable set**，不必一上来就到论文最终规模。

建议起步规模：
- 每类：
  - train = 1000
  - val = 200
  - test = 200

若计算资源不足，可略降，但必须在协议里写明原因与最终规模。

##### 4. GT 定义
- GT 为 voxel truth amplitude volume
- 不使用 BP 作为训练标签
- BP 仅作为高精度传统基线

##### 5. 几何与仿真约束
- 必须与 `simulation_protocol.md` 保持一致
- 不得脱离 true cylindrical forward model
- family 只是目标形状层的定义，不得改变物理协议

#### 验收点
后续所有 ET 样本生成，都必须引用该协议。

---

### Part B：实现 shape-family ET 数据生成器

#### 目标
在 `workspace/` 下新增 ET shape-family dataset builder。

#### 必做要求
1. 必须脚本驱动，不允许手工散跑
2. 生成：
   - family 元数据
   - GT amplitude volume
   - scene metadata
   - true cylindrical sparse echoes
3. 每个样本至少记录：
   - family 类型
   - shape 参数
   - split
   - seed
   - placement / orientation / size 参数
   - 强度参数
4. 输出必须落到标准目录

#### 特别要求：借鉴 Manisali
请显式借鉴 Manisali git 项目中的：
- dataset 文件组织方式
- sample metadata 写法
- 代表样本可视化风格
- 可能的 3D shape synthesizer 分层设计

但必须保留当前项目的 cylindrical protocol。

#### 建议文件
- `workspace/data/et_shape_family_builder.py`
- `workspace/data/et_dataset_builder.py`

---

### Part C：运行 ET 传统基线主实验

#### 目标
使用已冻结的 Variant B 前端，对 ET 数据运行：

- `ref3`
- `ref5`
- `ref7`
- `ref9`
- `BP`

#### 要求
1. 统一输入为 true cylindrical echoes
2. 统一输出为 amplitude volume
3. 统一统计：
   - runtime
   - speedup vs BP
   - magnitude NMSE
   - PSNR
   - SSIM
4. 结果至少要支持：
   - 全集平均
   - family 分组平均
   - per-sample 查询

#### 输出文件
- `baseline_metrics_et.json`
- `runtime_table_et.csv`
- `quality_table_et.csv`

---

### Part D：建立 ET failure taxonomy

#### 目标
不要只给均值表，要建立结构性失败模式分类。

#### 建议 failure taxonomy
你可以据结果微调，但至少考虑以下类型：

- `F1`: overall blur / global smearing
- `F2`: edge break / contour fracture
- `F3`: thin-structure disappearance
- `F4`: support fragmentation
- `F5`: local geometric shift
- `F6`: weak-return region suppression

#### 要求
1. 至少对代表样本做人审阅式分类
2. 统计各方法在不同 family 上的失败分布
3. 这份 taxonomy 将作为 `task_real_006` 的学习补偿设计依据

#### 输出文件
- `failure_taxonomy.md`
- `failure_case_index.json`

---

### Part E：统一可视化输出

#### 必须创建目录
```text
viz/
├── scene_3d/
├── recon_compare/
├── curves/
└── slices/
````

#### 必须输出的曲线

1. `runtime_vs_method_et.png`
2. `speedup_vs_bp_et.png`
3. `quality_vs_method_et.png`
4. `metrics_by_family.png`
5. `failure_mode_count_by_method.png`

#### 必须输出的代表样本图

至少覆盖三类代表样本：

1. 对 `ref3` 很容易的 family
2. 对 `ref3` 明显困难的 family
3. 典型边缘/细线困难样本

每类都输出：

* GT 3D 图
* GT / ref3 / ref5 / ref7 / ref9 / BP 对比图
* slice / error 图

---

### Part F：为 `task_real_006` 做训练接口准备

#### 目标

虽然本任务不训练，但必须为下一任务铺路。

#### 必做项

1. 产出适合 `RED_ref3 -> 3D U-Net -> GT amplitude` 的训练数据索引
2. 明确：

   * `ref3` 粗图路径
   * GT 路径
   * split 索引
3. 在报告中给出：

   * 哪些 family 最值得优先作为 learning 主战场
   * 是否需要对某些 family 做采样均衡

#### 输出文件

* `learning_handoff_manifest.json`

---

## 七、脚本层要求

请新增或补齐：

1. `scripts/generate_et_shape_family_dataset.sh`
2. `scripts/run_et_baselines_variantB.sh`
3. `scripts/render_et_viz.sh`
4. `scripts/build_learning_handoff.sh`

### 脚本要求

* 必须可执行
* 必须把日志落盘
* 必须统一写入本任务 exp 目录
* 不允许手工散跑代替脚本流程

---

## 八、exp 目录规范

请为本任务创建固定产物目录：

```text id="k2rq5x"
exp/task_real_005_shape_family_et/<timestamp>/
```

至少输出：

1. `task_real_005_report.md`
2. `dataset_manifest.json`
3. `dataset_protocol_snapshot.md`
4. `data_origin_statement.md`
5. `baseline_metrics_et.json`
6. `runtime_table_et.csv`
7. `quality_table_et.csv`
8. `failure_taxonomy.md`
9. `failure_case_index.json`
10. `learning_handoff_manifest.json`
11. `tree.txt`
12. `logs/`
13. `viz/`

---

## 九、`task_real_005_report.md` 的强制结构

报告必须至少包含以下部分：

1. `Task Goal`
2. `ET Dataset Protocol Freeze Statement`
3. `Protocol / Context Files Used`
4. `Boundary Statement`
5. `Manisali Borrowing Summary`
6. `Dataset Summary`
7. `Experiment Summary`
8. `Key Metrics`
9. `Failure Taxonomy`
10. `Visual Outputs`
11. `Readiness for Learning Stage`
12. `Suggested Next Task`

并且必须包含固定小节：

### Key file paths for ChatGPT controller

集中列出：

* report 路径
* metrics 路径
* curves 路径
* representative visuals 路径
* logs 路径
* learning handoff 路径

---

## 十、推荐执行顺序

请按以下顺序推进：

1. 阅读上位文档与 `task_real_004c_report.md`
2. 阅读并审视 Manisali 论文与 git 项目，形成 borrowing summary
3. 新增并冻结 `CONTEXT/et_dataset_protocol.md`
4. 实现 ET shape-family dataset builder
5. 生成 true cylindrical ET 数据与 echoes
6. 运行 Variant B 下的 `ref3/ref5/ref7/ref9/BP`
7. 统计 metrics 与 family 分组结果
8. 建立 failure taxonomy
9. 生成标准化可视化
10. 构建 learning handoff manifest
11. 生成 `task_real_005_report.md`
12. 更新 `CHANGELOG_DEV.md` 与 `debug.md`
13. 确保 git 工作区可提交

---

## 十一、验收标准

本任务只有在以下条件全部满足时才算完成：

1. `CONTEXT/et_dataset_protocol.md` 已创建并冻结
2. ET 数据已证明来自 true 3D cylindrical simulation
3. `ref3/ref5/ref7/ref9/BP` 全部在 ET 数据上跑通
4. ET 场景下的速度—质量排序已形成第一版主表
5. 已建立 family 分组结果
6. 已建立 ET failure taxonomy
7. 已输出标准化 3D 图、成像对比图、曲线图
8. 已生成 `learning_handoff_manifest.json`
9. 已生成 `task_real_005_report.md`
10. git 工作区保持可提交状态

---

## 十二、最终判断要求

在最终报告中，请明确回答：

1. shape-family ET 数据集是否已经足以支撑下一步学习训练？
2. 哪些 family 是 learning 主战场？
3. Variant B 作为 ET 传统前端是否表现稳定？
4. `Ready for learning stage?` 回答必须是：

   * `yes`
   * `no`
   * `conditional`

---

## 十三、最终终端汇报格式

任务完成后，请按如下格式做最终汇报：

1. `PROJECT_ROOT = ...`
2. `ET dataset protocol = pass / partial pass / fail`
3. `true 3D cylindrical ET data proof = pass / partial pass / fail`
4. `ET baseline Variant B chain = pass / partial pass / fail`
5. `failure taxonomy = pass / partial pass / fail`
6. `learning handoff = pass / partial pass / fail`
7. `visualization outputs = pass / partial pass / fail`
8. `Artifacts = ...`
9. `Ready for learning stage? = yes / no / conditional`
10. `Suggested next task = task_real_006 (...)`

---

## 十四、提醒

* 这次正式进入 ET 主战场
* 但仍停留在传统前端与数据层，不进入训练
* 必须充分借鉴 Manisali 的论文与代码工程方式
* 当前项目的 physics-based first stage 不是 adjoint，而是 **Variant B cylindrical accelerated front-end**
* 本任务结束后，应直接进入 `task_real_006`

```
```

