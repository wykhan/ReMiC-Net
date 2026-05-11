
````markdown id="j2r8kf"
# task_real_006d：800/100/100 family-aware formal dataset + OOD credibility validation

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
- `task_real_006`：第一版正式两阶段训练
- `task_real_006b`：Frozen Mainline 统一曲线定位
- `task_real_006c`：formal-scale credibility validation（因 formal-scale 数据门槛未完成而 fail-fast）

当前已知状态：
- Frozen Mainline 已冻结为：
  - Front-end = Variant B
  - Physics backbone = ref3
  - Second stage = 3D U-Net
  - Default training line = ref3 coarse -> GT amplitude
- 当前结果已表明主线可学，但 formal-scale 目标 `5000/1000/1000` 过大，超出现阶段实验能力
- 当前 second stage 参数量约 `85017`
- 参考文献：
  - Manisali synthetic 3D extended-target dataset: `800 / 100 / 100`
  - PnP 3D deep denoiser training set: `800 / 100 / 100`
- 现在决定将**基础正式实验**收敛到与文献同量级的 `800 / 100 / 100`，但必须通过：
  - family-aware 分层设计
  - OOD 测试集
  - split integrity / leakage 检查
来保证鲁棒性与说服力

本任务进入：

> **Phase ET-2d：800/100/100 family-aware formal dataset + OOD credibility validation**

---

## 一、任务定位

本任务的唯一目标是：

> 构建一套与 Manisali / PnP 同量级、但更严格设计的  
> **family-aware shape-family 主训练集（800/100/100）**，  
> 并配套三类 OOD 测试集，  
> 在 true 3D cylindrical simulation 下重新验证 Frozen Mainline 的可信度。

本任务不是 physics-consistency 任务，不引入新方法，不做 recipe 搜索。

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
11. `exp/task_real_006c_formal_validation/*/task_real_006c_report.md`

此外，必须继续参考：
12. `Efficient physics-based learned reconstruction methods for real-time 3D near-field MIMO radar imaging.pdf`
13. `Plug-and-Play_Regularization_on_Magnitude_With_Deep_Priors_for_3D_Near-Field_MIMO_Imaging.pdf`
14. 已授权 git 项目：`Efficient-Learned-3D-Near-Field-MIMO-Imaging`

不得绕过这些文档自定协议。

---

## 三、强制硬约束

### 硬约束 1：基础正式训练集固定为 800 / 100 / 100
本任务中，shape-family 主训练集规模固定为：

- `train = 800`
- `val = 100`
- `test = 100`

不得继续以 `5000/1000/1000` 作为当下执行门槛。  
这次的目标是：**在文献同量级设置下，把数据设计做扎实**。

---

### 硬约束 2：family 不能平均乱抽，必须 family-aware
family 集合固定为：
- `line`
- `cross`
- `L-shape`
- `double-line`
- `small_rect_edge`
- `point_cluster`

训练集 `800` 的推荐配比固定为：

- `point_cluster = 180`
- `line = 160`
- `L-shape = 160`
- `cross = 110`
- `double-line = 100`
- `small_rect_edge = 90`

验证集 `100`：
- `point_cluster = 20`
- `line = 20`
- `L-shape = 20`
- `cross = 15`
- `double-line = 15`
- `small_rect_edge = 10`

测试集 `100`：
- `point_cluster = 20`
- `line = 20`
- `L-shape = 20`
- `cross = 15`
- `double-line = 15`
- `small_rect_edge = 10`

不得擅自平均化，除非在报告中给出非常充分的理由。

---

### 硬约束 3：参数空间必须做分层覆盖，不能纯随机乱撒
本任务中，主数据集必须做 **parameter-stratified sampling**。

每个 family 至少显式覆盖以下通用维度：
- 位置（中心 / 偏中心 / 靠边界）
- 方位角（低 / 中 / 高 / near seam）
- 高度（中层 / 上边界附近 / 下边界附近）
- 尺寸（小 / 中 / 大）
- 强度（弱 / 中 / 强）
- 边界接近程度
- 稀疏度 / 密度

并对 family-specific 参数做分桶设计，例如：
- `line`: 长度、厚度、角度、细线极限
- `point_cluster`: 点数、间距、簇半径、子簇结构
- `L-shape`: 两臂长度比、开口方向、厚度
- `double-line`: 间距、平行性、粗细差
- `cross`: 角度、长度比、中心偏移
- `small_rect_edge`: 边长、长宽比、贴边程度

不得只做模板复制或简单均匀随机。

---

### 硬约束 4：必须额外构建三类 OOD 测试集
除了主测试集 `100` 外，必须再构建以下三类 test-only set：

#### A. unseen-parameter OOD
- 规模：`100`
- 训练中故意不出现的一段参数区间，只在测试中出现

#### B. leave-one-family-out OOD
- 规模：`100`
- 至少对 hardest family 中的一类执行
- 推荐：
  - leave out `line`
  - 或 leave out `point_cluster`

#### C. random-ET OOD
- 规模：`100`
- 借鉴 Manisali 的随机 extended-target 生成思想
- 但必须放入 true cylindrical simulation 链路，而不是二维代理图样

---

### 硬约束 5：所有数据必须证明来自 true 3D cylindrical simulation
本任务中任何主集 / OOD 集 / split 都必须输出：

- `dataset_manifest_main_800_100_100.json`
- `dataset_manifest_unseen_param_ood.json`
- `dataset_manifest_leave_one_family_out_ood.json`
- `dataset_manifest_random_et_ood.json`
- `dataset_protocol_snapshot.md`
- `data_origin_statement.md`

其中 `data_origin_statement.md` 必须明确写出：
- 这是 **true 3D cylindrical simulation data**
- 使用的 forward simulator 入口
- 使用的协议版本
- 使用的重建入口（Variant B / ref3）
- 明确声明：不是二维代理数据集

---

### 硬约束 6：Frozen Mainline 必须保持冻结
本任务中，不允许改动主方法定义：

> **Frozen Mainline = Variant B + ref3 + 3D U-Net + shape-family main training**

不得：
- 更换前端
- 更换 ref3 物理骨干
- 更换 second-stage 架构
- 引入 physics-consistency
- 引入 complex supervision
- 回到 M1/M2/M3 recipe 搜索

---

### 硬约束 7：必须做 split integrity / leakage 检查
至少完成：
1. scene hash 去重
2. parameter-signature 去重
3. train-test 最近邻距离统计
4. 代表样本 nearest-neighbor 可视化

本任务的核心之一就是压低“过拟合 / 过近 split”质疑。

---

### 硬约束 8：必须做 model audit
必须输出：
- 模型总参数量
- 可训练参数量
- 输入输出张量形状
- 显存占用（尽量）
- FLOPs（若可行）

不得再只写“compact U-Net”。

---

### 硬约束 9：每次实验都必须生成可视化
必须输出以下图：

#### 数据集与可信度图
- `dataset_scale_and_family_balance.png`
- `parameter_coverage_main_set.png`
- `train_test_nearest_neighbor_distance.png`
- `split_integrity_visual_check.png`

#### 训练与测试图
- `train_val_loss_frozen_mainline_800.png`
- `runtime_quality_frontier_with_learning_800.png`
- `family_metrics_mainline_vs_baselines_800.png`
- `failure_mode_mainline_vs_baselines_800.png`

#### OOD 图
- `ood_unseen_param_metrics.png`
- `ood_leave_one_family_out_metrics.png`
- `ood_random_et_metrics.png`

#### qualitative 图
- hardest improved case
- hardest failure case
- OOD representative cases

---

### 硬约束 10：必须生成统一命名的任务报告
本任务结束时，必须生成：

- `task_real_006d_report.md`

不得使用临时命名风格替代。

---

## 四、严格边界

### 本任务允许做
- 重新定义并冻结 800/100/100 主数据集
- 构建三类 OOD 测试集
- 构建 Frozen Mainline handoff
- 训练 Frozen Mainline
- 与 `ref3/ref5/ref7/ref9/BP` 做统一比较
- 做 split integrity / leakage 检查
- 做 model audit
- 输出标准化可视化
- 更新 `CHANGELOG_DEV.md` 与 `debug.md`

### 本任务禁止做
- 不进入 physics-consistency
- 不继续发散训练 recipe
- 不更换主方法
- 不接入真实回波
- 不做大规模 formal target 扩容
- 不修改现有上位协议原文内容

---

## 五、本任务要回答的问题

1. 在 800/100/100 family-aware 主数据集上，Frozen Mainline 是否仍显著优于裸 `ref3`？
2. hardest families（`point_cluster / line / L-shape`）上的增益是否仍然稳健？
3. `F2/F3/F4` 是否仍显著下降？
4. 在三类 OOD 测试上，Frozen Mainline 是否仍优于裸 `ref3`？
5. 当前结果是否足以在“文献同量级训练规模”下支撑论文论证？

---

## 六、任务拆解

---

### Part A：冻结 800/100/100 主数据集协议

#### 目标
把 family-aware 主数据集设计写成正式协议，并落盘。

#### 必做项
1. 冻结 6 family 主集
2. 冻结 family 配比
3. 冻结参数维度与分层抽样规则
4. 明确 hardest family 倾斜设计
5. 输出协议说明

#### 产物
- `CONTEXT/et_dataset_protocol_800.md`（新增）
- `dataset_manifest_main_800_100_100.json`

---

### Part B：生成主训练/验证/测试集

#### 目标
真正生成 800/100/100 主数据集，并走 true cylindrical 链路。

#### 必做项
1. 生成 GT amplitude volume
2. 生成 Variant B `ref3` coarse volume
3. 记录 family / 参数 / split 元数据
4. 构建正式 handoff

#### 产物
- `learning_handoff_manifest_main_800_100_100.json`

---

### Part C：构建三类 OOD 测试集

#### C1. unseen-parameter OOD
- train 中留空某些参数区间
- test 中专门放这些区间样本

#### C2. leave-one-family-out OOD
- 至少对 hardest family 中的一类执行

#### C3. random-ET OOD
- 参考 Manisali 的随机生成思想
- 但必须走 true cylindrical chain

#### 产物
- `dataset_manifest_unseen_param_ood.json`
- `dataset_manifest_leave_one_family_out_ood.json`
- `dataset_manifest_random_et_ood.json`

---

### Part D：split integrity / leakage 检查

#### 目标
验证数据集设计确实降低了泄漏与参数过近风险。

#### 必做项
1. scene hash 去重
2. parameter signature 去重
3. train-test nearest-neighbor 距离统计
4. 若发现过近样本，必须在报告中指出

#### 产物
- `split_integrity_report_800.md`
- `duplicate_check_800.json`
- `nearest_neighbor_overlap_800.csv`

---

### Part E：model audit

#### 目标
正式披露 Frozen Mainline second stage 的规模。

#### 产物
- `model_audit_800.json`
- `model_summary_800.txt`

---

### Part F：训练 Frozen Mainline

#### 目标
在 800/100/100 主集上训练唯一主方法。

#### 固定方法
- Front-end: Variant B
- Physics backbone: ref3
- Second stage: 3D U-Net
- Default train set: shape-family main train = 800

#### 产物
- `training_config_frozen_mainline_800.yaml`
- `metrics_frozen_mainline_800.json`
- `checkpoints/`

---

### Part G：统一比较

#### 目标
在主测试集 100 上统一比较：

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
- `mainline_vs_baselines_800.csv`
- `family_metrics_mainline_vs_baselines_800.csv`
- `failure_mode_mainline_vs_baselines_800.csv`

---

### Part H：OOD 评测

#### 目标
验证 Frozen Mainline 不是只会修主分布内样本。

#### 必做项
在三类 OOD 集上都评估：
- Frozen Mainline
- 裸 `ref3`

#### 产物
- `ood_unseen_param_metrics.csv`
- `ood_leave_one_family_out_metrics.csv`
- `ood_random_et_metrics.csv`

---

### Part I：标准化可视化

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

1. `dataset_scale_and_family_balance.png`
2. `parameter_coverage_main_set.png`
3. `train_test_nearest_neighbor_distance.png`
4. `split_integrity_visual_check.png`
5. `train_val_loss_frozen_mainline_800.png`
6. `runtime_quality_frontier_with_learning_800.png`
7. `family_metrics_mainline_vs_baselines_800.png`
8. `failure_mode_mainline_vs_baselines_800.png`
9. `ood_unseen_param_metrics.png`
10. `ood_leave_one_family_out_metrics.png`
11. `ood_random_et_metrics.png`
12. hardest improved / hardest failure / OOD qualitative 图

---

## 七、脚本层要求

请新增或补齐：

1. `scripts/generate_main_800_dataset.sh`
2. `scripts/generate_ood_unseen_param_set.sh`
3. `scripts/generate_ood_leave_one_family_out_set.sh`
4. `scripts/generate_ood_random_et_set.sh`
5. `scripts/build_frozen_mainline_handoff_800.sh`
6. `scripts/run_split_integrity_check_800.sh`
7. `scripts/run_model_audit_800.sh`
8. `scripts/run_frozen_mainline_training_800.sh`
9. `scripts/run_mainline_vs_baselines_800.sh`
10. `scripts/run_ood_suite_800.sh`
11. `scripts/render_800_validation_viz.sh`

### 脚本要求

* 必须可执行
* 必须把日志落盘
* 必须统一写入本任务 exp 目录
* 不允许手工散跑代替脚本流程

---

## 八、exp 目录规范

请为本任务创建固定产物目录：

```text id="zsnqct"
exp/task_real_006d_800_formal/<timestamp>/
```

至少输出：

1. `task_real_006d_report.md`
2. `dataset_manifest_main_800_100_100.json`
3. `dataset_manifest_unseen_param_ood.json`
4. `dataset_manifest_leave_one_family_out_ood.json`
5. `dataset_manifest_random_et_ood.json`
6. `dataset_protocol_snapshot.md`
7. `data_origin_statement.md`
8. `learning_handoff_manifest_main_800_100_100.json`
9. `split_integrity_report_800.md`
10. `duplicate_check_800.json`
11. `nearest_neighbor_overlap_800.csv`
12. `model_audit_800.json`
13. `model_summary_800.txt`
14. `training_config_frozen_mainline_800.yaml`
15. `metrics_frozen_mainline_800.json`
16. `mainline_vs_baselines_800.csv`
17. `family_metrics_mainline_vs_baselines_800.csv`
18. `failure_mode_mainline_vs_baselines_800.csv`
19. `ood_unseen_param_metrics.csv`
20. `ood_leave_one_family_out_metrics.csv`
21. `ood_random_et_metrics.csv`
22. `tree.txt`
23. `logs/`
24. `viz/`
25. `checkpoints/`

---

## 九、`task_real_006d_report.md` 的强制结构

报告必须至少包含以下部分：

1. `Task Goal`
2. `Why 800/100/100 is adopted`
3. `Protocol / Context Files Used`
4. `Boundary Statement`
5. `Frozen Mainline Definition`
6. `Main Dataset Design Summary`
7. `OOD Dataset Design Summary`
8. `Split Integrity / Leakage Check`
9. `Model Audit Summary`
10. `Mainline vs Baselines Results`
11. `OOD / Generalization Results`
12. `Visual Outputs`
13. `Remaining Issues`
14. `Ready for Physics-Consistency Stage?`
15. `Suggested Next Task`

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

1. 阅读上位文档与 `task_real_006b / 006c` 报告
2. 冻结 800/100/100 family-aware 主协议
3. 生成主训练/验证/测试集
4. 生成三类 OOD 测试集
5. 运行 split integrity / leakage 检查
6. 运行 model audit
7. 训练 Frozen Mainline
8. 进行 unified comparison
9. 进行 OOD/generalization 评测
10. 生成标准化可视化
11. 生成 `task_real_006d_report.md`
12. 更新 `CHANGELOG_DEV.md` 与 `debug.md`
13. 确保 git 工作区可提交

---

## 十一、验收标准

本任务只有在以下条件全部满足时才算完成：

1. 主数据集达到 `800/100/100`
2. 三类 OOD 测试集都已生成
3. 所有数据都证明来自 true 3D cylindrical simulation
4. split integrity / leakage 检查完成
5. model audit 完整输出
6. Frozen Mainline 训练完成
7. unified comparison 完成
8. OOD/generalization 评测完成
9. hardest families 上 Frozen Mainline 仍明显优于裸 `ref3`
10. `F2/F3/F4` 继续显著下降
11. 已输出标准化图集
12. 已生成 `task_real_006d_report.md`
13. git 工作区保持可提交状态

---

## 十二、最终判断要求

在最终报告中，请明确回答：

1. 800/100/100 family-aware 主集是否设计合理并完成？
2. 当前 split 是否仍存在明显过近或泄漏问题？
3. 当前 3D U-Net 参数量是多少？
4. Frozen Mainline 在三类 OOD 上是否仍优于裸 `ref3`？
5. 当前结果是否足以支撑进入 `task_real_007`？
6. `Ready for Physics-Consistency Stage?` 回答必须是：

   * `yes`
   * `no`
   * `conditional`

---

## 十三、最终终端汇报格式

任务完成后，请按如下格式做最终汇报：

1. `PROJECT_ROOT = ...`
2. `main 800/100/100 dataset = pass / partial pass / fail`
3. `true 3D cylindrical data proof = pass / partial pass / fail`
4. `split integrity check = pass / partial pass / fail`
5. `model audit = pass / partial pass / fail`
6. `Frozen Mainline training = pass / partial pass / fail`
7. `unified comparison = pass / partial pass / fail`
8. `OOD / generalization validation = pass / partial pass / fail`
9. `visualization outputs = pass / partial pass / fail`
10. `Artifacts = ...`
11. `Ready for Physics-Consistency Stage? = yes / no / conditional`
12. `Suggested next task = task_real_007 (...)`

---

## 十四、提醒

* 这次不是扩大到 49000 样本的任务
* 这次也不是方法创新任务
* 这次的核心是：**用文献同量级但更严格设计的数据，验证 Frozen Mainline 是否可信**
* 若通过，才进入 `task_real_007`

```
```

