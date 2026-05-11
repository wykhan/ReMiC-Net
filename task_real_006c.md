

````markdown id="0v6c9x"
# task_real_006c：formal-scale credibility validation before physics-consistency

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
- `task_real_006`：第一版正式两阶段训练（但仍低于 formal target）
- `task_real_006b`：Frozen Mainline 统一曲线定位（但仍低于 formal target）

当前已知状态（来自 `task_real_006b_report.md`）：
- Frozen Mainline 已冻结为：
  - Front-end = Variant B
  - Physics backbone = ref3
  - Second stage = 3D U-Net
  - Default training data = shape-family full-scale only
- 在当前执行规模下，Frozen Mainline 在 unified curve 上质量位置已最接近 BP 档，且整体优于所有传统 baseline
- 但当前数据规模仍只有：
  - shape-family = `576 / 144 / 144`
  - random ET = `192 / 48 / 48`
- 这仍明显低于 master-document 要求：
  - 每类 family `5000 / 1000 / 1000`
  - random ET `5000 / 1000 / 1000`
- 因此当前结果虽强，但仍存在：
  - formal-scale 证据不足
  - 过拟合 / 分布过窄 / split leakage 嫌疑尚未被严格排除

本任务进入：

> **Phase ET-2c：formal-scale credibility validation before physics-consistency**

---

## 一、任务定位

本任务的唯一目标是：

> 在不引入 physics-consistency 的前提下，  
> 先完成 formal-scale 数据、split integrity、model audit、OOD/generalization 验证，  
> 从而回答：当前 Frozen Mainline 的强结果是否足够可信，  
> 是否真的可以进入 `task_real_007`。

本任务不是新方法任务，不是 recipe 搜索任务，不是 physics-consistency 任务。

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
10. `exp/task_real_006b_fullscale_mainline/*/task_real_006b_report.md`

此外，继续参考：
11. `Efficient physics-based learned reconstruction methods for real-time 3D near-field MIMO radar imaging.pdf`
12. 已授权 git 项目：`Efficient-Learned-3D-Near-Field-MIMO-Imaging`

不得绕过这些文档自定协议。

---

## 三、强制硬约束

### 硬约束 1：在 formal-scale 数据完成之前，不允许开始训练
本任务中，**formal-scale 数据完成是训练的前置条件**。

### 具体要求
#### A. shape-family
family 集合固定为：
- `line`
- `cross`
- `L-shape`
- `double-line`
- `small_rect_edge`
- `point_cluster`

每类必须达到：
- `train = 5000`
- `val = 1000`
- `test = 1000`

总计：
- shape-family train = `30000`
- shape-family val = `6000`
- shape-family test = `6000`

#### B. random ET
必须达到：
- `train = 5000`
- `val = 1000`
- `test = 1000`

### 规则
- 在上述规模完成前，不允许开始 Frozen Mainline 正式训练
- 若 formal-scale 数据未完成，本任务必须记为 **fail**，不得以 `partial pass` 结题
- 不得再以 “under local resource limits” 或 “first substantial pass” 替代 formal target

---

### 硬约束 2：所有数据必须证明来自 true 3D cylindrical simulation
本任务中任何 dataset / split / OOD set，都必须输出：

- `dataset_manifest_shape_family_formal.json`
- `dataset_manifest_random_et_formal.json`
- `dataset_protocol_snapshot.md`
- `data_origin_statement.md`

其中 `data_origin_statement.md` 必须明确写出：
- 这是 **true 3D cylindrical simulation data**
- 使用的 forward simulator 入口
- 使用的协议版本
- 使用的重建入口（Variant B / ref3）
- 明确声明：不是二维代理 family 图样，不是人工糊出的 ref 图像

---

### 硬约束 3：Frozen Mainline 必须保持完全冻结
本任务中主方法定义不得再变化：

> **Frozen Mainline = Variant B + ref3 + 3D U-Net + shape-family main training**

不得：
- 替换前端
- 替换 ref3 物理骨干
- 切换到其他 second-stage 架构
- 引入 physics-consistency loss
- 引入 complex supervision
- 重新发散回 M1/M2/M3 recipe 对比

本任务只允许对 **数据规模、可信度、泛化证据** 做验证。

---

### 硬约束 4：必须做 split integrity / leakage 检查
本任务中必须正式完成：

1. duplicate / near-duplicate 检查
2. family 参数组合重复检查
3. train-test 最近邻相似性检查
4. scene metadata hash 去重检查

不得跳过。

---

### 硬约束 5：必须做 model audit
必须输出当前 second stage 的：

- 模型总参数量
- 可训练参数量
- 输入 tensor 形状
- 输出 tensor 形状
- 训练显存占用（尽量）
- 推理显存占用（尽量）
- 若可行，FLOPs 估计

不得再只写“compact U-Net”。

---

### 硬约束 6：必须做 OOD/generalization 验证
至少完成三类：

#### A. unseen-parameter OOD
同 family 内，留出一段参数区间不参与训练，只在测试时出现，例如：
- 更细 thickness
- 更大 gap
- 更靠边界位置
- 更极端 rotation

#### B. leave-one-family-out OOD
至少对 hardest family 中的一类执行，例如：
- leave out `line`
- 或 leave out `point_cluster`

#### C. random-ET OOD
Frozen Mainline 仅在 shape-family 上训练，然后在 formal random ET test 上评估。

---

### 硬约束 7：每次实验都必须生成可视化
必须输出：

#### A. 数据规模与 split 可信度图
- `dataset_scale_completion.png`
- `train_test_nearest_neighbor_distance.png`
- `parameter_coverage_train_vs_test.png`

#### B. 训练与泛化图
- `train_val_test_loss_frozen_mainline.png`
- `train_val_test_gap_by_family.png`
- `ood_unseen_param_metrics.png`
- `ood_leave_one_family_out_metrics.png`
- `ood_random_et_metrics.png`

#### C. 统一曲线与 qualitative 图
- `runtime_quality_frontier_with_learning_formal.png`
- `family_metrics_mainline_vs_baselines_formal.png`
- `failure_mode_mainline_vs_baselines_formal.png`
- hardest-case improved / hardest-case failure 图

不得只保留 csv/json。

---

### 硬约束 8：必须生成统一命名的任务报告
本任务结束时，必须在产物目录中生成：

- `task_real_006c_report.md`

不得使用临时命名风格替代。

---

## 四、严格边界

### 本任务允许做
- 完成 formal-scale 数据扩容
- 冻结 Frozen Mainline
- 做 split integrity / leakage 检查
- 做 model audit
- 做 OOD/generalization 验证
- 在 formal-scale 数据上重跑 Frozen Mainline 与 unified comparison
- 输出正式可信度报告
- 更新 `CHANGELOG_DEV.md` 与 `debug.md`

### 本任务禁止做
- 不引入 physics-consistency
- 不重新探索传统前端路线
- 不继续做 M1/M2/M3 recipe 对比
- 不换 second-stage 架构
- 不接入真实回波
- 不修改现有上位协议原文内容

---

## 五、本任务要回答的问题

1. 当前 Frozen Mainline 的强结果是否在 formal-scale 数据上仍成立？
2. 当前数据是否存在 train/test 泄漏、近重复、参数空间过近的问题？
3. 当前模型参数量多大，是否与当前样本规模形成明显过拟合风险？
4. Frozen Mainline 在 unseen-parameter、leave-one-family-out、random-ET OOD 上是否仍优于裸 `ref3`？
5. 如果这些都通过，是否真的可以进入 `task_real_007`？

---

## 六、任务拆解

---

### Part A：完成 formal-scale 数据扩容

#### 目标
把当前所有 ET 训练与评测数据扩到 formal target。

#### 必做项
1. shape-family 全部 family 扩到：
   - train = 5000
   - val = 1000
   - test = 1000
2. random ET 扩到：
   - train = 5000
   - val = 1000
   - test = 1000
3. 输出正式 manifest

#### 产物
- `dataset_manifest_shape_family_formal.json`
- `dataset_manifest_random_et_formal.json`

#### 验收
若任何一个规模未达标，本任务直接 fail。

---

### Part B：构建 formal-scale Frozen Mainline handoff

#### 目标
在 formal-scale 数据上构建唯一训练入口。

#### 固定输入输出
- 输入：`Variant B ref3 coarse amplitude volume`
- 标签：`GT amplitude volume`

#### 产物
- `learning_handoff_manifest_frozen_mainline_formal.json`

---

### Part C：split integrity / leakage 检查

#### 目标
排除样本泄漏或参数空间过近导致的“虚高结果”。

#### 必做项
1. metadata hash 去重
2. 参数级去重与近重复检查
3. train-test 最近邻距离统计
4. 对若干 test 样本检索最相似 train 样本并可视化

#### 产物
- `split_integrity_report.md`
- `duplicate_check.json`
- `nearest_neighbor_overlap.csv`

---

### Part D：model audit

#### 目标
完整披露当前 3D U-Net 的规模和训练/推理资源需求。

#### 必做项
1. 统计总参数量
2. 统计可训练参数量
3. 记录输入输出 tensor 形状
4. 记录训练/推理显存
5. 若可行，估计 FLOPs

#### 产物
- `model_audit.json`
- `model_summary.txt`

---

### Part E：formal-scale Frozen Mainline 训练

#### 目标
在 formal-scale 数据上重新训练 Frozen Mainline。

#### 强制要求
- 在 Part A 完成之前不得开始
- 只训练 Frozen Mainline
- 输出：
  - train/val/test curves
  - best checkpoint
  - final metrics
  - family-level metrics
  - hardest-family summary

#### 产物
- `training_config_frozen_mainline_formal.yaml`
- `metrics_frozen_mainline_formal.json`

---

### Part F：formal-scale unified comparison

#### 目标
在 formal-scale test 上重新比较：

- `ref3`
- `ref5`
- `ref7`
- `ref9`
- `BP`
- `Frozen Mainline`

#### 指标
- NMSE
- PSNR
- SSIM
- runtime
- speedup vs BP

#### 产物
- `mainline_vs_baselines_formal.csv`
- `family_metrics_mainline_vs_baselines_formal.csv`
- `failure_mode_mainline_vs_baselines_formal.csv`

---

### Part G：OOD / generalization 验证

#### 目标
验证 Frozen Mainline 不是只会修当前 family manifold。

#### G1. unseen-parameter OOD
- family 内参数区间留出
- 只在 test 中出现

#### G2. leave-one-family-out OOD
- 至少对 hardest family 中的一类执行

#### G3. random-ET OOD
- 只用 shape-family 训练
- 在 formal random-ET test 上评估

#### 产物
- `ood_unseen_param_metrics.csv`
- `ood_leave_one_family_out_metrics.csv`
- `ood_random_et_metrics.csv`

---

### Part H：标准化可视化

#### 必须创建目录
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
````

#### 必须输出的核心图

1. `dataset_scale_completion.png`
2. `train_test_nearest_neighbor_distance.png`
3. `parameter_coverage_train_vs_test.png`
4. `train_val_test_loss_frozen_mainline.png`
5. `train_val_test_gap_by_family.png`
6. `ood_unseen_param_metrics.png`
7. `ood_leave_one_family_out_metrics.png`
8. `ood_random_et_metrics.png`
9. `runtime_quality_frontier_with_learning_formal.png`
10. `family_metrics_mainline_vs_baselines_formal.png`
11. `failure_mode_mainline_vs_baselines_formal.png`
12. hardest improved / hardest failure qualitative 图

---

## 七、脚本层要求

请新增或补齐：

1. `scripts/complete_formal_scale_datasets.sh`
2. `scripts/build_formal_frozen_mainline_handoff.sh`
3. `scripts/run_split_integrity_check.sh`
4. `scripts/run_model_audit.sh`
5. `scripts/run_frozen_mainline_formal_training.sh`
6. `scripts/run_formal_mainline_vs_baselines.sh`
7. `scripts/run_ood_generalization_suite.sh`
8. `scripts/render_formal_validation_viz.sh`

### 脚本要求

* 必须可执行
* 必须把日志落盘
* 必须统一写入本任务 exp 目录
* 不允许手工散跑代替脚本流程

---

## 八、exp 目录规范

请为本任务创建固定产物目录：

```text
exp/task_real_006c_formal_validation/<timestamp>/
```

至少输出：

1. `task_real_006c_report.md`
2. `dataset_manifest_shape_family_formal.json`
3. `dataset_manifest_random_et_formal.json`
4. `dataset_protocol_snapshot.md`
5. `data_origin_statement.md`
6. `learning_handoff_manifest_frozen_mainline_formal.json`
7. `split_integrity_report.md`
8. `duplicate_check.json`
9. `nearest_neighbor_overlap.csv`
10. `model_audit.json`
11. `model_summary.txt`
12. `training_config_frozen_mainline_formal.yaml`
13. `metrics_frozen_mainline_formal.json`
14. `mainline_vs_baselines_formal.csv`
15. `family_metrics_mainline_vs_baselines_formal.csv`
16. `failure_mode_mainline_vs_baselines_formal.csv`
17. `ood_unseen_param_metrics.csv`
18. `ood_leave_one_family_out_metrics.csv`
19. `ood_random_et_metrics.csv`
20. `tree.txt`
21. `logs/`
22. `viz/`
23. `checkpoints/`

---

## 九、`task_real_006c_report.md` 的强制结构

报告必须至少包含以下部分：

1. `Task Goal`
2. `Formal-Scale Dataset Completion Statement`
3. `Protocol / Context Files Used`
4. `Boundary Statement`
5. `Frozen Mainline Definition`
6. `Dataset Summary`
7. `Split Integrity / Leakage Check`
8. `Model Audit Summary`
9. `Formal-Scale Mainline vs Baselines`
10. `OOD / Generalization Results`
11. `Visual Outputs`
12. `Remaining Issues`
13. `Ready for Physics-Consistency Stage?`
14. `Suggested Next Task`

并且必须包含固定小节：

### Key file paths for ChatGPT controller

集中列出：

* report 路径
* manifests 路径
* split integrity 路径
* model audit 路径
* metrics 路径
* OOD 路径
* curves 路径
* representative visuals 路径
* logs 路径

---

## 十、推荐执行顺序

请按以下顺序推进：

1. 阅读上位文档与 `task_real_006b_report.md`
2. 完成 formal-scale 数据扩容
3. 构建 formal-scale Frozen Mainline handoff
4. 运行 split integrity / leakage 检查
5. 运行 model audit
6. 在 formal-scale 数据上训练 Frozen Mainline
7. 重跑 unified comparison
8. 运行 OOD/generalization suite
9. 生成标准化可视化
10. 生成 `task_real_006c_report.md`
11. 更新 `CHANGELOG_DEV.md` 与 `debug.md`
12. 确保 git 工作区可提交

---

## 十一、验收标准

本任务只有在以下条件全部满足时才算完成：

1. shape-family 达到每类 `5000/1000/1000`
2. random ET 达到 `5000/1000/1000`
3. 所有数据都证明来自 true 3D cylindrical simulation
4. split integrity / leakage 检查通过
5. model audit 完整输出
6. Frozen Mainline 在 formal-scale 数据上训练完成
7. formal-scale unified comparison 完成
8. OOD/generalization 结果完成
9. hardest families 上 Frozen Mainline 仍明显优于裸 `ref3`
10. 已输出标准化 3D 图、比较图、可信度图
11. 已生成 `task_real_006c_report.md`
12. git 工作区保持可提交状态

---

## 十二、最终判断要求

在最终报告中，请明确回答：

1. formal-scale 数据是否真正完成？
2. 当前是否发现 train/test 泄漏或近重复问题？
3. 当前 3D U-Net 参数量是多少？
4. Frozen Mainline 在 OOD 上是否仍明显优于裸 `ref3`？
5. formal-scale 下，Frozen Mainline 是否仍位于 BP 档附近？
6. 当前是否已经 ready for `task_real_007`？
7. `Ready for Physics-Consistency Stage?` 回答必须是：

   * `yes`
   * `no`
   * `conditional`

---

## 十三、最终终端汇报格式

任务完成后，请按如下格式做最终汇报：

1. `PROJECT_ROOT = ...`
2. `formal-scale dataset completion = pass / fail`
3. `true 3D cylindrical data proof = pass / partial pass / fail`
4. `split integrity check = pass / partial pass / fail`
5. `model audit = pass / partial pass / fail`
6. `Frozen Mainline formal training = pass / partial pass / fail`
7. `formal unified comparison = pass / partial pass / fail`
8. `OOD / generalization validation = pass / partial pass / fail`
9. `visualization outputs = pass / partial pass / fail`
10. `Artifacts = ...`
11. `Ready for Physics-Consistency Stage? = yes / no / conditional`
12. `Suggested next task = task_real_007 (...)`

---

## 十四、提醒

* 这次不是方法创新任务
* 这次的主问题是：当前强结果是否可信
* 在 formal-scale 数据完成前，禁止开始训练
* 若 formal-scale 未完成，本任务直接 fail，不允许以 `partial pass` 结题
* 本任务完成后，才允许进入 `task_real_007`

```
```

