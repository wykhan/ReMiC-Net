
````markdown
# task_real_002：点目标物理链路验证（Phase 1）

你现在服务于项目：

- `PROJECT_ROOT = /home/superws/2026_Projects/Codex_reference_plane_real`
- `CONTEXT = /home/superws/2026_Projects/Codex_reference_plane_real/CONTEXT`
- `workspace = /home/superws/2026_Projects/Codex_reference_plane_real/workspace`

bootstrap 已完成，当前仓库治理结构、脚本入口、CONTEXT/PROMPTS/doc 层已经具备。
本任务进入 **Phase 1：point-target physics chain validation**。

---

## 一、任务定位

本任务不是 extended-target 主实验，也不是 physics consistency 扩展，更不是正式论文主结果生产。

本任务的唯一目标是：

> 在真正柱面协议下，打通并验证  
> `scene -> echo -> ref3/ref5/ref7/ref9/BP -> eval -> minimal learning smoke`
> 这一完整链路是否成立、趋势是否正确、接口是否可继续扩展。

你要完成的是“物理链路验证”，不是“追求最好指标”。

---

## 二、必须遵守的上位文档

在开始任何实现前，必须先阅读并遵守：

1. `CONTEXT/real_cylindrical_master_document_with_physics_consistency.md`
2. `CONTEXT/simulation_protocol.md`
3. `CONTEXT/reference_surface_strategy.md`
4. `CONTEXT/project_brief.md`
5. `CONTEXT/experiment_matrix.md`
6. `PROMPTS/system_rules.md`
7. `PROMPTS/review_checklist.md`

不得绕过这些文档自定协议。

---

## 三、严格边界

### 本任务允许做
- 冻结点目标数据协议
- 实现点目标场景生成
- 实现真正柱面 forward simulation
- 实现并运行 `ref3/ref5/ref7/ref9/BP`
- 实现统一评测与 runtime 统计
- 做 learning smoke test：`RED_ref3 -> 3D U-Net -> GT amplitude`
- 生成本任务报告与图表
- 更新 `CHANGELOG_DEV.md` 与 `debug.md`

### 本任务禁止做
- 不进入 shape-family ET 数据集
- 不进入 Manisali-style random ET 数据集
- 不接入真实人体/真实回波
- 不开展 physics consistency
- 不做大规模消融
- 不擅自升级协议到显式 MIMO 新口径
- 不修改已有上位协议原文内容
- 不把本任务写成最终论文结论

若发现协议有未决问题，可在 `doc/open_questions.md` 中追加记录，但不要在本任务越权扩展。

---

## 四、总体交付目标

本任务完成后，应能回答以下问题：

1. 点目标场景是否能按 protocol v1 正确生成柱面回波？
2. `ref3/ref5/ref7/ref9/BP` 是否都能在统一脚本入口下运行？
3. 参考面数量变化带来的速度-质量 trade-off 是否符合物理预期？
4. `RED_ref3 -> 3D U-Net -> GT amplitude` 是否具备最基本可训练性？

---

## 五、任务拆解

---

### Part A：冻结点目标数据协议

#### 目标
新增：

- `CONTEXT/dataset_protocol.md`

用于正式冻结本项目点目标数据集协议。

#### 该文件至少要写清楚

1. **本任务只冻结 point-target 协议**
   - ET 协议后续单独冻结
   - 本文件不替代未来 ET dataset protocol

2. **数据划分**
   建议正式目标规模：
   - train = 6000
   - val = 1000
   - test = 1000

   同时允许先生成一个 smoke 子集，例如：
   - smoke_train = 64
   - smoke_val = 16
   - smoke_test = 16

3. **场景类型覆盖**
   必须覆盖：
   - 单点
   - 双点
   - 少量多点（例如 3~5 点）

4. **空间覆盖**
   必须显式覆盖：
   - 不同半径位置
   - 不同高度位置
   - 不同方位位置
   - 不同点间距
   - 靠近边界与非边界位置

5. **GT 定义**
   - GT 为体素真值幅度体
   - 当前阶段不做复数监督
   - 不以 BP 图像作为训练标签

6. **散射系数规则**
   本任务先冻结一个简单一致版本，例如：
   - 幅度为有界随机值或固定值
   - 相位先关闭随机化或统一置零
   - 该选择必须在 protocol 中写清楚

7. **体素网格与场景包络**
   - 必须与 `simulation_protocol.md` 保持一致
   - 不得私自发明新几何范围

#### 要求
- 该文件必须写成“项目协议”，不是临时注释
- 后续代码实现必须严格引用此文件

---

### Part B：实现点目标场景生成器

#### 目标
在 `workspace/` 下新增 point-target scene generator，实现：
- 生成场景元数据
- 生成点目标稀疏 reflectivity 体
- 保存样本描述文件

#### 必做要求
1. 场景生成必须脚本驱动，不允许手工散跑
2. 支持生成：
   - smoke 数据集
   - 正式 train/val/test 数据集
3. 每个样本至少记录：
   - 点数
   - 每个点的位置
   - 散射系数
   - split 信息
   - seed
4. 输出必须落盘到规范目录，例如：
   - `exp/task_real_002_point_chain/<timestamp>/dataset/...`

#### 建议文件
可自行命名，但建议包含：
- `workspace/data/point_scene_generator.py`
- `workspace/data/point_dataset_builder.py`

---

### Part C：实现 protocol v1 的真正柱面前向仿真

#### 目标
实现 point-target echo generator，遵守 `simulation_protocol.md`。

#### 必须遵守的冻结口径
按照 `simulation_protocol.md` 执行，不得改动：
- 柱面扫描半径、场景半径、高度范围
- 频段与波数定义
- 方位/高度/频率采样
- 可见性约束
- 双程相位口径
- 当前 protocol v1 的 forward simulation 范式

#### 必做要求
1. 先做单样本 smoke 验证
2. 再支持批量样本生成
3. 输出 echo 张量及必要元数据
4. 明确数据维度与坐标对应关系
5. 对异常样本给出日志，不可 silent fail

#### 建议文件
可自行命名，但建议包含：
- `workspace/sim/forward_cylindrical_point.py`
- `workspace/sim/sim_utils.py`

---

### Part D：实现五个传统重建入口

#### 目标
实现并统一运行以下方法：
- `ref3`
- `ref5`
- `ref7`
- `ref9`
- `BP`

#### 必须遵守的参考面定义
严格按 `reference_surface_strategy.md` 执行，不得自行改 reference sets。

#### 要求
1. 所有方法必须走统一接口
2. 输入统一为 protocol-compliant echo
3. 输出统一为：
   - reconstruction volume
   - runtime
   - method metadata
4. `BP` 作为高精度传统基线
5. `ref3` 作为 reduced-reference physical backbone

#### 建议文件
可自行命名，但建议包含：
- `workspace/recon/reference_recon.py`
- `workspace/recon/bp_recon.py`
- `workspace/recon/recon_registry.py`

---

### Part E：统一评测模块

#### 目标
建立统一评测脚本，对五个传统基线进行质量和速度统计。

#### 当前阶段必须支持的指标
- runtime
- speedup vs BP
- magnitude NMSE
- PSNR
- SSIM

#### 要求
1. 评测只针对幅度体
2. 输出 json/csv/markdown 三种可读结果至少两种
3. 所有指标必须能批量汇总 split 级均值
4. 同时保留 per-sample 结果，方便查异常

#### 建议文件
- `workspace/eval/metrics_3d.py`
- `workspace/eval/eval_point_baselines.py`

---

### Part F：learning smoke test

#### 目标
做最小学习验证：

- 输入：`RED_ref3` 粗重建幅度体
- 标签：GT 幅度体
- 模型：轻量级 3D U-Net
- 目标：验证链路可训练，不追求论文最优

#### 严格要求
1. 这是 smoke test，不是正式训练
2. 不引入复杂多通道输入
3. 不引入 physics consistency
4. 不做复杂网络搜索
5. 训练规模可先使用 smoke 子集或小规模 train 子集
6. 至少给出：
   - train/val loss 变化
   - 预测样例
   - 与裸 `ref3` 的简单对比

#### 建议文件
- `workspace/models/unet3d_small.py`
- `workspace/train/train_point_smoke.py`

---

## 六、脚本层要求

在 `scripts/` 中新增或补齐以下脚本：

1. `scripts/generate_point_dataset.sh`
2. `scripts/run_point_baselines.sh`
3. `scripts/run_point_learning_smoke.sh`

### 脚本要求
- 必须可执行
- 有清晰参数说明
- 默认把输出落到本任务 exp 目录
- 不允许手工散跑替代脚本流程
- 运行日志要保存到 exp 目录

---

## 七、推荐执行顺序

请按以下顺序推进：

1. 阅读上位文档
2. 新增并冻结 `CONTEXT/dataset_protocol.md`
3. 实现 point-target scene generator
4. 实现 forward simulation
5. 做单样本 smoke 验证
6. 实现五个重建入口
7. 跑小规模 baseline smoke
8. 实现统一评测
9. 跑正式 point-baseline 评测
10. 实现 learning smoke test
11. 生成完整报告
12. 更新 `CHANGELOG_DEV.md` 与 `debug.md`

---

## 八、exp 目录规范

请为本任务创建固定产物目录：

```text
exp/task_real_002_point_chain/<timestamp>/
````

至少输出：

1. `point_chain_report.md`
2. `dataset_protocol_snapshot.md`
3. `dataset_summary.json`
4. `baseline_metrics.json`
5. `runtime_table.csv`
6. `quality_table.csv`
7. `point_learning_smoke_metrics.json`
8. `tree.txt`
9. `logs/`
10. `sample_visuals/`

### point_chain_report.md 必须包含

* 本任务目标
* 使用的协议文件
* 点目标数据协议摘要
* scene/echo/recon/eval 链路说明
* baseline 结果摘要
* learning smoke 结果摘要
* 发现的问题
* 明确声明：本任务未进入 ET 主实验
* 建议下一任务

---

## 九、验收标准

本任务只有在以下条件全部满足时才算完成：

1. `CONTEXT/dataset_protocol.md` 已创建并冻结
2. point-target scene generator 已实现并可批量生成
3. protocol v1 的柱面 forward simulation 已跑通
4. `ref3/ref5/ref7/ref9/BP` 全部可执行
5. baseline 评测结果已汇总输出
6. 已形成第一版速度-质量曲线或等价表格
7. learning smoke test 可运行并给出合理日志
8. 所有操作都通过脚本完成并落盘到 `exp/task_real_002_point_chain/<timestamp>/`
9. `CHANGELOG_DEV.md` 与 `debug.md` 已更新
10. Git 工作区保持可提交状态

---

## 十、实现原则

1. 优先保证链路正确，再考虑速度优化
2. 优先保证协议一致，再考虑代码美观
3. 优先让 smoke 跑通，再扩大正式集
4. 遇到未决问题先落到文档，不要静默拍板
5. 不要让学习部分喧宾夺主，本任务主角是物理链路验证

---

## 十一、最终终端汇报格式

任务完成后，请按如下格式做最终汇报：

1. `PROJECT_ROOT = ...`
2. `dataset_protocol = created / updated`
3. `forward simulation = pass / partial pass / fail`
4. `baseline chain = pass / partial pass / fail`
5. `learning smoke = pass / partial pass / fail`
6. `Artifacts = ...`
7. `Key issues = ...`
8. `Suggested next task = task_real_003 (...)`

---

## 十二、提醒

* 这是 **Phase 1：point-target physics chain validation**
* 不是 ET 主战场
* 不是 physics consistency
* 不是最终论文结果
* 你的任务是把“新项目的物理骨架、trade-off 曲线、最小学习入口”全部验证为活的

```


