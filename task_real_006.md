
````markdown 
# task_real_006：正式两阶段学习训练（对齐 master-document 量级）

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
- `task_real_004c`：冻结 Variant B 并确认 broader controlled point suite
- `task_real_005`：shape-family ET 数据集、传统主表、failure taxonomy、learning handoff

当前已知状态（来自 `task_real_005_report.md`）：
- ET 主战场已经建立
- 默认传统前端已冻结为 **Variant B = active windows + full-library sinc geometry correction**
- ET 上平均速度—质量排序成立：`ref3 < ref5 < ref7 < ref9 < BP`
- hardest `ref3` families 已明确：`point_cluster`, `line`, `L-shape`
- `learning_handoff_manifest.json` 已生成，可直接用于启动两阶段训练
- 但当前 ET 数据规模仍是 ET-1 reduced set，不满足 master document 的正式训练量级要求

本任务进入：

> **Phase ET-2：论文级第一版正式两阶段学习训练**

---

## 一、任务定位

本任务的唯一目标是：

> 把 shape-family ET 与 Manisali-style random ET 数据扩充到 master-document 要求的训练量级，  
> 并在 true 3D cylindrical simulation + frozen Variant B front-end 下，  
> 正式训练并验证两阶段主方法：  
> **`ref3 coarse volume -> 3D U-Net -> GT amplitude`**。

本任务不是 smoke test，不是小样本试训，而是**论文级第一版正式训练任务**。

---

## 二、必须遵守的上位文档

开始前必须阅读并遵守：

1. `CONTEXT/real_cylindrical_master_document_with_physics_consistency.md`
2. `CONTEXT/simulation_protocol.md`
3. `CONTEXT/reference_surface_strategy.md`
4. `CONTEXT/dataset_protocol.md`
5. `CONTEXT/et_dataset_protocol.md`
6. `CONTEXT/project_brief.md`
7. `CONTEXT/experiment_matrix.md`
8. `PROMPTS/system_rules.md`
9. `PROMPTS/review_checklist.md`
10. `exp/task_real_005_shape_family_et/*/task_real_005_report.md`

此外，**必须继续深入借鉴以下资料**：
11. `Efficient physics-based learned reconstruction methods for real-time 3D near-field MIMO radar imaging.pdf`
12. 已授权可访问的 git 项目：`Efficient-Learned-3D-Near-Field-MIMO-Imaging`

不得绕过这些文档自定协议。

---

## 三、强制硬约束

### 硬约束 1：训练规模必须达到 master-document 要求量级
本任务中，训练数据规模必须达到以下最低要求：

#### A. shape-family ET 主训练集
family 集合固定为：
- `line`
- `cross`
- `L-shape`
- `double-line`
- `small_rect_edge`
- `point_cluster`

每类至少：
- `train >= 5000`
- `val >= 1000`
- `test >= 1000`

推荐正式规模：
- 每类 `train = 5000`
- 每类 `val = 1000`
- 每类 `test = 1000`

即总计：
- shape-family train = `30000`
- shape-family val = `6000`
- shape-family test = `6000`

#### B. Manisali-style random ET 补充训练集
至少：
- `train >= 5000`
- `val >= 1000`
- `test >= 1000`

推荐正式规模：
- random ET train = `5000`
- random ET val = `1000`
- random ET test = `1000`

### 说明
- 若因算力/时间原因无法达到上述规模，必须在报告中明确说明原因与实际完成规模
- 但不得回退到 `task_real_005` 那种 ET-1 reduced scale

---

### 硬约束 2：所有数据必须证明来自 true 3D cylindrical simulation
本任务中任何 dataset / split / train sample，都必须输出：

- `dataset_manifest_shape_family_full.json`
- `dataset_manifest_random_et.json`
- `dataset_protocol_snapshot.md`
- `data_origin_statement.md`

其中 `data_origin_statement.md` 必须明确写出：
- 这是 **true 3D cylindrical simulation data**
- 使用的 forward simulator 入口
- 使用的协议版本
- 使用的重建入口（Variant B `ref3`)
- 明确声明：不是二维代理 family 图样，不是人工糊出的 ref 图像

---

### 硬约束 3：本任务默认物理骨干固定为 `ref3`
本任务的正式主方法必须固定为：

> **`Variant B ref3 coarse volume -> 3D U-Net -> GT amplitude`**

不得把：
- `ref5`
- `ref7`
- `ref9`
- `BP`
当成默认训练输入。

这些方法只允许作为对照或辅助比较存在。

---

### 硬约束 4：必须充分借鉴 Manisali 论文与 git 项目
本任务中，Codex 必须显式写清：

1. 从 Manisali 论文借鉴了哪些第二阶段训练思想
2. 从 git 项目借鉴了哪些：
   - 数据组织方式
   - coarse-to-GT handoff 结构
   - 3D U-Net I/O 形状组织
   - checkpoint / visualization / report 风格
3. 哪些地方不能照搬，为什么
4. 明确指出：
   - Manisali 的 physics-based first stage 在本项目中由 **Variant B cylindrical `ref3`** 替代
   - Manisali 的 second-stage 和 dataset engineering 思路被保留并迁移

不得只在报告里笼统写“参考了 Manisali”。

---

### 硬约束 5：每次实验都必须生成可视化
必须输出并保存：

#### A. 原始数据可视化
- GT 3D occupancy / amplitude 视图
- top / front / side 三视图
- hardest family 代表样本的 slice montage

#### B. 成像 / 预测结果可视化
每个代表样本至少比较：
- GT
- `ref3`
- learned output（M1/M2/M3）
- `ref5`
- `ref7`
- `BP`（可选至少在代表样本中提供）

并输出：
- recon compare 图
- 三正交切片
- absolute error map / difference map

#### C. 指标曲线
必须输出：
- `train_val_loss_M1.png`
- `train_val_loss_M2.png`
- `train_val_loss_M3.png`（若执行）
- `quality_gain_vs_ref3.png`
- `family_metrics_learning.png`
- `failure_mode_improvement.png`

不得只保留 csv/json。

---

### 硬约束 6：必须生成统一命名的任务报告
本任务结束时，必须在产物目录中生成：

- `task_real_006_report.md`

不得使用临时命名风格替代。

---

## 四、严格边界

### 本任务允许做
- 扩容 shape-family ET full-scale 数据
- 生成 Manisali-style random ET supplement
- 构建正式训练 / 验证 / 测试 split
- 训练 `ref3 -> 3D U-Net -> GT amplitude`
- 对 hardest families 做采样强调或 loss weighting
- 生成 family-level 结果与 failure-mode 改善分析
- 更新 `CHANGELOG_DEV.md` 与 `debug.md`

### 本任务禁止做
- 不重新探索传统前端路线
- 不做 physics consistency
- 不接入真实回波
- 不做 complex supervision
- 不做太多复杂输入通道探索
- 不回退到小样本 smoke 任务
- 不修改现有上位协议原文内容

---

## 五、本任务要回答的问题

1. 在 master-document 量级的数据上，`ref3 + 3D U-Net` 是否能稳定优于裸 `ref3`？
2. hardest families（`point_cluster`, `line`, `L-shape`）上是否获得显著改善？
3. learning 是否主要修复了：
   - `F2` edge break / contour fracture
   - `F3` thin-structure disappearance
   - `F4` support fragmentation
4. random ET supplement 是否对泛化有帮助？
5. 当前两阶段主方法是否足以进入下一步 physics-consistency 升级？

---

## 六、任务拆解

---

### Part A：扩容 ET 数据到正式训练规模

#### 目标
把 ET-1 reduced set 升级到 ET-2 full-scale training set。

#### 必做项
1. 按 `et_dataset_protocol.md` 扩容 shape-family 数据到正式规模
2. family 数量与分布必须均衡
3. 生成并保存：
   - GT amplitude volume
   - `ref3` coarse volume
   - sample metadata
   - split metadata
4. 输出 full-scale dataset manifest

#### 建议文件
- `workspace/data/et_shape_family_builder.py` 更新
- `workspace/data/et_dataset_builder.py` 更新

---

### Part B：生成 Manisali-style random ET 补充训练集

#### 目标
引入随机 extended-target supplement，用于训练补充与泛化验证。

#### 必做项
1. 构建随机 ET synthesizer
2. 生成：
   - train >= 5000
   - val >= 1000
   - test >= 1000
3. 保证该数据仍符合 true cylindrical simulation 流程
4. 输出独立 manifest

#### 说明
- random ET 不作为论文主 benchmark
- 只作为训练补充与泛化补充来源

#### 建议文件
- `workspace/data/random_et_builder.py`

---

### Part C：正式构建训练 handoff 数据

#### 目标
生成正式训练使用的 coarse-to-GT handoff。

#### 主方法固定为
- 输入：`Variant B ref3 coarse amplitude volume`
- 标签：`GT amplitude volume`

#### 必做项
1. 生成训练索引
2. 生成验证索引
3. 生成测试索引
4. 保存：
   - coarse path
   - GT path
   - family label
   - split label
   - whether_random_et flag

#### 输出文件
- `learning_handoff_manifest_full.json`

---

### Part D：训练矩阵（正式版）

#### 目标
用尽量小但足够有解释力的矩阵回答关键问题。

#### M0：裸 `ref3`
- 非学习基线
- 从 `task_real_005` ET 主结果继承，不重新训练

#### M1：正式主方法
- `ref3 -> 3D U-Net -> GT amplitude`
- 训练数据：
  - shape-family full-scale
  - + random ET supplement
- 这是本任务主角

#### M2：去掉 random ET supplement 的对照
- `ref3 -> 3D U-Net -> GT amplitude`
- 只用 shape-family full-scale

#### M3：hard-family emphasized 版本
- 在 M1 的基础上
- 对 `point_cluster / line / L-shape` 做采样增强或 loss weighting
- 目的：验证 hardest families 是否值得显式强调

#### 要求
- M1 必做
- M2 强烈建议做
- M3 若资源允许必须做；若实在无法执行，必须在报告中解释

---

### Part E：训练流程要求

#### 目标
避免在 full-scale 数据上直接盲训失败。

#### Stage 1：formal smoke on full-scale pipeline
在 full-scale 数据接口上先做短轮 smoke：
- data loader 检查
- tensor shape 检查
- checkpoint / viz 检查
- train/val loss 是否正常下降

#### Stage 2：正式 full-scale 训练
对 M1 / M2 / M3 跑正式训练。

#### 每组必须输出
- train/val loss 曲线
- best checkpoint
- final metrics
- family-level metrics
- representative visuals
- inference runtime summary

---

### Part F：损失与目标

#### 目标
先把正式主方法练稳，不要过早复杂化。

#### 当前默认监督目标
- `GT amplitude volume`

#### 建议默认损失
- `L1` 或 `SmoothL1`
- 可选加一个 amplitude-NMSE term

#### 本任务不做
- echo consistency loss
- complex-valued supervision
- adversarial loss
- perceptual loss
- 多通道复杂物理辅助输入

这些属于后续 `task_real_007`。

---

### Part G：评测与分析重点

#### 必须评测
1. 相对裸 `ref3` 的整体提升
2. family-level 提升
3. hardest family 提升
4. failure-mode 改善

#### hardest family 重点关注
- `point_cluster`
- `line`
- `L-shape`

#### 重点失败模式
- `F2`: edge break / contour fracture
- `F3`: thin-structure disappearance
- `F4`: support fragmentation

#### 输出文件
- `metrics_M1.json`
- `metrics_M2.json`
- `metrics_M3.json`
- `family_metrics.csv`
- `failure_mode_improvement.csv`

---

### Part H：统一可视化输出

#### 必须创建目录
```text
viz/
├── scene_3d/
├── recon_compare/
├── curves/
└── slices/
````

#### 必须输出的图

1. `train_val_loss_M1.png`
2. `train_val_loss_M2.png`
3. `train_val_loss_M3.png`（若执行）
4. `quality_gain_vs_ref3.png`
5. `family_metrics_learning.png`
6. `failure_mode_improvement.png`

#### 必须输出的代表样本

至少覆盖：

1. hardest family 中明显改善的样本
2. hardest family 中仍失败的样本
3. 普通 family 中典型成功样本

每类都输出：

* GT 3D 图
* `ref3` / learned / `ref5` / `ref7` / `BP` 对比图
* slice / error 图

---

## 七、脚本层要求

请新增或补齐：

1. `scripts/generate_et_fullscale_dataset.sh`
2. `scripts/generate_random_et_dataset.sh`
3. `scripts/build_learning_handoff_full.sh`
4. `scripts/run_two_stage_training_M1.sh`
5. `scripts/run_two_stage_training_M2.sh`
6. `scripts/run_two_stage_training_M3.sh`
7. `scripts/render_learning_viz.sh`

### 脚本要求

* 必须可执行
* 必须把日志落盘
* 必须统一写入本任务 exp 目录
* 不允许手工散跑代替脚本流程

---

## 八、exp 目录规范

请为本任务创建固定产物目录：

```text id="v3r8kd"
exp/task_real_006_two_stage_learning/<timestamp>/
```

至少输出：

1. `task_real_006_report.md`
2. `dataset_manifest_shape_family_full.json`
3. `dataset_manifest_random_et.json`
4. `dataset_protocol_snapshot.md`
5. `data_origin_statement.md`
6. `learning_handoff_manifest_full.json`
7. `training_config_M1.yaml`
8. `training_config_M2.yaml`
9. `training_config_M3.yaml`
10. `metrics_M1.json`
11. `metrics_M2.json`
12. `metrics_M3.json`
13. `family_metrics.csv`
14. `failure_mode_improvement.csv`
15. `tree.txt`
16. `logs/`
17. `viz/`
18. `checkpoints/`

---

## 九、`task_real_006_report.md` 的强制结构

报告必须至少包含以下部分：

1. `Task Goal`
2. `Dataset Scale Upgrade Statement`
3. `Protocol / Context Files Used`
4. `Boundary Statement`
5. `Manisali Borrowing Summary`
6. `Training Matrix`
7. `Dataset Summary`
8. `Key Metrics`
9. `Family-Level Results`
10. `Failure-Mode Improvement`
11. `Visual Outputs`
12. `Remaining Issues`
13. `Ready for Physics-Consistency Stage?`
14. `Suggested Next Task`

并且必须包含固定小节：

### Key file paths for ChatGPT controller

集中列出：

* report 路径
* checkpoints 路径
* metrics 路径
* family tables 路径
* failure-mode 表路径
* curves 路径
* representative visuals 路径
* logs 路径

---

## 十、推荐执行顺序

请按以下顺序推进：

1. 阅读上位文档与 `task_real_005_report.md`
2. 继续审视 Manisali 论文与 git 项目，形成正式 borrowing summary
3. 扩容 shape-family ET 到 full-scale
4. 生成 random ET supplement
5. 构建 `learning_handoff_manifest_full.json`
6. 先做 formal smoke on full-scale pipeline
7. 正式训练 M1
8. 训练 M2 / M3
9. 统计整体、family-level、failure-mode 改善
10. 生成标准化可视化
11. 生成 `task_real_006_report.md`
12. 更新 `CHANGELOG_DEV.md` 与 `debug.md`
13. 确保 git 工作区可提交

---

## 十一、验收标准

本任务只有在以下条件全部满足时才算完成：

1. shape-family 每类训练样本达到 `5000+`
2. random ET 训练样本达到 `5000+`
3. 所有数据都证明来自 true 3D cylindrical simulation
4. M1 正式训练完成并结果可用
5. M2 至少完成
6. M3 若资源允许应完成；若无法完成必须解释
7. M1 明显优于裸 `ref3`
8. hardest families 至少两类上有清晰改善
9. `F2/F3/F4` 至少有明确下降趋势
10. 已输出标准化 3D 图、成像对比图、曲线图
11. 已生成 `task_real_006_report.md`
12. git 工作区保持可提交状态

---

## 十二、最终判断要求

在最终报告中，请明确回答：

1. 是否已达到 master-document 要求的数据量级？
2. `ref3 + 3D U-Net` 是否已经成为第一版可用主方法？
3. hardest families 是否得到显著改善？
4. 当前是否已经 ready for physics-consistency stage？
5. `Ready for physics-consistency stage?` 回答必须是：

   * `yes`
   * `no`
   * `conditional`

---

## 十三、最终终端汇报格式

任务完成后，请按如下格式做最终汇报：

1. `PROJECT_ROOT = ...`
2. `full-scale dataset expansion = pass / partial pass / fail`
3. `true 3D cylindrical data proof = pass / partial pass / fail`
4. `M1 formal training = pass / partial pass / fail`
5. `M2 comparative training = pass / partial pass / fail`
6. `M3 hard-family emphasized training = pass / partial pass / fail`
7. `family-level improvement = pass / partial pass / fail`
8. `failure-mode improvement = pass / partial pass / fail`
9. `visualization outputs = pass / partial pass / fail`
10. `Artifacts = ...`
11. `Ready for physics-consistency stage? = yes / no / conditional`
12. `Suggested next task = task_real_007 (...)`

---

## 十四、提醒

* 这次不是 smoke test
* 这次是论文级第一版正式训练
* 数据量必须对齐 master-document 要求
* 默认物理骨干固定为 `Variant B ref3`
* 必须充分借鉴 Manisali 的 second-stage 与工程组织方式
* 本任务结束后，应进入 `task_real_007`

```
```

