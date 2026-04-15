

````markdown
# task_real_003：忠实快速柱面重建实现 + 点目标径向失配控制验证

你现在服务于项目：

- `PROJECT_ROOT = /home/superws/2026_Projects/Codex_reference_plane_real`
- `CONTEXT = /home/superws/2026_Projects/Codex_reference_plane_real/CONTEXT`
- `workspace = /home/superws/2026_Projects/Codex_reference_plane_real/workspace`

已完成：
- `task_real_001`：项目 bootstrap 与治理冻结
- `task_real_002`：点目标物理链路 smoke 验证

当前已知状态：
- 点目标 true cylindrical forward simulation 已跑通
- `ref3/ref5/ref7/ref9/BP` smoke 链路已跑通
- `RED_ref3 -> 3D U-Net -> GT amplitude` learning smoke 已可训练
- 但当前重建器仍是 analytic point-scene verifier，使用了 deterministic visibility subsampling，runtime 表仍带 proxy，尚不是论文级“忠实快速柱面重建实现”
- 当前还未建立系统的径向失配（radial mismatch）误差曲线

本任务进入 **Phase 1.5 / pre-ET bridge**。

---

## 一、任务定位

本任务不是 extended-target 主实验，也不是 physics consistency 扩展。

本任务的唯一目标是：

> 用更忠实的快速柱面重建实现替换当前 smoke-time analytic verifier，  
> 并建立系统的点目标径向失配控制实验，  
> 从而在进入 ET 主战场之前，得到可信的传统曲线与误差机制证据。

换句话说，本任务要完成：

`true 3D cylindrical point scene -> echo -> faithful fast cylindrical recon / BP -> eval -> radial mismatch curves -> report`

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

不得绕过这些文档自定协议。

---

## 三、你必须执行的新增硬约束

### 硬约束 1：必须证明数据来自真实 3D 柱面仿真
以后本任务中生成的任何 dataset / split / controlled set，都必须同时输出：

- `dataset_manifest.json`
- `dataset_protocol_snapshot.md`
- `data_origin_statement.md`

其中 `data_origin_statement.md` 必须明确写出：
- 是否为 **true 3D cylindrical simulation data**
- 使用的几何协议版本
- 使用的 forward simulator 入口
- 是否经过真正柱面 `ref3/ref5/ref7/ref9/BP` 链路
- 明确声明：不是二维代理图样，不是人工糊出的伪 ref 图像

若无法证明数据来自真实 3D 柱面仿真，本任务不得算通过。

---

### 硬约束 2：每次实验都必须生成可视化
每个实验组都必须生成并保存：

#### A. 原始仿真数据可视化
至少包括若干代表样本的：
- GT 3D scatter / voxel amplitude 视图
- top / front / side 三视图投影
- 必要时中心切片图

#### B. 成像结果可视化
每个代表样本至少比较：
- GT
- `ref3`
- `ref5`
- `ref7`
- `ref9`
- `BP`
- 若本任务包含学习输出，则额外加上 learned result

建议统一输出：
- 3D 可视化
- 三正交切片
- difference map / absolute error map

#### C. 指标曲线
必须输出：
- runtime / speedup 曲线或柱状图
- NMSE / PSNR / SSIM 曲线或柱状图
- `error vs rho_target`
- `error vs radial mismatch distance`
- 若本任务含训练，则额外输出 train/val loss curve

不得只保留 csv/json，不出图。

---

### 硬约束 3：必须生成统一命名的任务报告
本任务结束时，必须在产物目录中生成：

- `task_real_003_report.md`

不得再使用临时命名风格替代。

该报告必须统一汇总：
- 关键实验结论
- 关键指标
- 关键图路径
- 关键数据路径
- 关键日志路径
- 当前限制
- 下一任务建议

这样用户可以直接把 `task_real_003_report.md` 反馈给 ChatGPT 主控窗口。

---

## 四、严格边界

### 本任务允许做
- 用更忠实的快速柱面重建实现替换当前 analytic verifier
- 跑 point-target controlled validation
- 建立系统的 radial mismatch analysis
- 扩大 point-target test 规模
- 重新计算更可信的 runtime / speedup / quality 指标
- 产出统一可视化与任务报告
- 若需要，可做少量 point learning smoke v2，但不是主重点
- 更新 `CHANGELOG_DEV.md` 与 `debug.md`

### 本任务禁止做
- 不进入 shape-family ET 数据集
- 不进入 Manisali-style random ET 数据集
- 不接入真实回波
- 不开展 physics consistency
- 不升级到 explicit MIMO 新口径
- 不重写主文档
- 不把本任务包装成最终论文结论

---

## 五、本任务要回答的科学问题

1. 当前 `ref3/ref5/ref7/ref9/BP` 曲线，在更忠实的快速柱面重建实现下是否仍保持正确趋势？
2. 点目标误差是否随 `rho_target` 与 reference-surface mismatch 系统性变化？
3. 当前 `reference_surface_strategy_v1` 是否已经足够，还是存在明显外缘/特定径向区域脆弱性？
4. 在进入 ET 主战场前，传统曲线与误差机制是否已经“可信”到足以作为论文前端骨架？

---

## 六、任务拆解

---

### Part A：实现更忠实的快速柱面重建器

#### 目标
用更接近 `simulation_protocol.md` 与谭维贤流程的重建实现，替换 `task_real_002` 中的 analytic point-scene verifier。

#### 方向要求
新实现应尽量体现以下关键处理链：
1. echo 数据组织
2. 高度向 Fourier 处理
3. 方位向 Fourier 处理
4. 对每个参考柱面构造匹配函数 / 参考相位项
5. 波数域乘法
6. 距离向聚焦 / 积分
7. 由柱坐标成像结果映射到笛卡尔三维体
8. 输出统一的 amplitude volume

#### 注意
- 不是要求一步做到最终最高效版本
- 但必须明显比 current analytic verifier 更忠实于 protocol
- 不得再以“仅点场景解析验证器”作为主 baseline implementation

#### 建议文件
可自行命名，但建议至少包含：
- `workspace/recon/faithful_cylindrical_fast_recon.py`
- `workspace/recon/faithful_reference_recon.py`
- `workspace/recon/bp_recon.py`
- `workspace/recon/recon_registry.py`

#### 必做输出
- 方法说明文档或实现注释
- 与旧 smoke verifier 的差异说明
- wall-time 实测结果
- 若仍保留 proxy，必须解释 proxy 的角色，但不能让 proxy 取代实测 wall time

---

### Part B：建立 controlled point-target radial mismatch 数据集

#### 目标
在 point-target 协议下，建立专门用于径向失配分析的 controlled dataset。

#### 必须覆盖
1. **单点控制实验**
   - 固定高度在中层
   - 固定方位在代表位置
   - 系统扫描 `rho_target`
   - 覆盖 `[0.00, 0.30] m` 范围
   - 步长可按协议与计算资源合理选取，但必须文档化

2. **方位影响控制实验**
   - 在若干固定半径下
   - 对比不同方位位置，检查 wrap-around/边界效应

3. **高度影响控制实验**
   - 在若干固定半径下
   - 对比中层与边界附近高度位置

4. **可选：双点控制实验**
   - 固定一个点
   - 另一个点在不同 `rho_target` 或间距下扫描
   - 观察分辨与干扰趋势

#### 数据要求
- 这批 controlled set 必须也是 true 3D cylindrical simulation data
- 输出 `dataset_manifest.json`、`dataset_protocol_snapshot.md`、`data_origin_statement.md`

#### 建议文件
- `workspace/data/radial_control_dataset_builder.py`

---

### Part C：系统建立径向失配误差曲线

#### 目标
对 `ref3/ref5/ref7/ref9/BP` 系统计算：

- `error vs rho_target`
- `error vs nearest reference-surface mismatch`
- `quality gain vs reference count`
- `runtime vs reference count`

#### 当前阶段必须保留的指标
- runtime
- speedup vs BP
- magnitude NMSE
- PSNR
- SSIM

#### 建议新增内部诊断量
这些可以做内部分析，不作为论文主指标第一层：
- peak localization error
- nearest reference-surface distance
- optional radial error decomposition

#### 至少要输出的表/曲线
- `runtime_vs_method.png`
- `quality_vs_method.png`
- `nmse_vs_rho_target.png`
- `psnr_vs_rho_target.png`
- `ssim_vs_rho_target.png`
- `error_vs_radial_mismatch.png`

#### 目的
为是否需要 `reference_surface_strategy_v2` 提供证据基础。

---

### Part D：更新 baseline 主结果

#### 目标
在更忠实的重建器上，重新跑：
- `ref3`
- `ref5`
- `ref7`
- `ref9`
- `BP`

#### 要求
1. 必须使用 `reference_surface_strategy.md` 中已冻结的 reference sets
2. 必须重新输出：
   - `baseline_metrics_faithful.json`
   - `runtime_table_faithful.csv`
   - `quality_table_faithful.csv`
3. 必须给出与 `task_real_002` 的差异说明：
   - 哪些变化来自更忠实实现
   - 哪些结论仍然保持不变

---

### Part E：统一可视化输出

#### 目标
建立标准化可视化目录与生成脚本。

#### 必须创建的目录
在本任务 exp 目录中强制包含：

```text
viz/
├── scene_3d/
├── recon_compare/
├── curves/
└── slices/
````

#### 每类至少应包含

* `scene_3d/`：GT 场景 3D 视图
* `recon_compare/`：GT/ref3/ref5/ref7/ref9/BP 对比图
* `curves/`：runtime、quality、radial mismatch 曲线
* `slices/`：中心切片、三正交切片、difference map

#### 命名建议

* `sample_000_gt_3d.png`
* `sample_000_ref3_vs_bp.png`
* `runtime_vs_method.png`
* `nmse_vs_rho_target.png`
* `error_vs_radial_mismatch.png`

---

### Part F：可选的 point learning smoke v2

#### 目标

如果更忠实的重建器输出分布与旧版有明显变化，可做一次小规模 point learning smoke v2。

#### 说明

* 这是可选增强项，不是本任务主重点
* 只有在新前端与旧前端分布差异明显时才做
* 目的只是确认 `RED_ref3 + 3D U-Net` 在 faithful front-end 上依然能训练
* 不追求大规模训练，不追求最优模型

若执行，至少输出：

* `point_learning_smoke_v2_metrics.json`
* `train_val_loss_v2.png`
* 代表样本对比图

---

## 七、脚本层要求

请新增或补齐：

1. `scripts/run_point_faithful_baselines.sh`
2. `scripts/run_radial_mismatch_analysis.sh`
3. `scripts/render_point_viz.sh`
4. 若做 learning v2，则加：

   * `scripts/run_point_learning_smoke_v2.sh`

### 脚本要求

* 必须可执行
* 必须把日志落盘
* 必须统一写入本任务 exp 目录
* 不允许手工散跑代替脚本流程

---

## 八、exp 目录规范

请为本任务创建固定产物目录：

```text
exp/task_real_003_faithful_point_validation/<timestamp>/
```

至少输出：

1. `task_real_003_report.md`
2. `dataset_manifest.json`
3. `dataset_protocol_snapshot.md`
4. `data_origin_statement.md`
5. `baseline_metrics_faithful.json`
6. `runtime_table_faithful.csv`
7. `quality_table_faithful.csv`
8. `radial_mismatch_metrics.json`
9. `tree.txt`
10. `logs/`
11. `viz/`

如执行 learning smoke v2，再增加：

* `point_learning_smoke_v2_metrics.json`

---

## 九、`task_real_003_report.md` 的强制结构

报告必须至少包含以下 10 个部分：

1. **Task Goal**
2. **Protocol / Context Files Used**
3. **Boundary Statement**
4. **Implementation Summary**
5. **Dataset Summary**
6. **Experiment Summary**
7. **Key Metrics**
8. **Visual Outputs**
9. **Issues / Limitations**
10. **Suggested Next Task**

并且必须包含一个固定小节：

### Key file paths for ChatGPT controller

集中列出：

* 报告路径
* metrics 文件路径
* 曲线图路径
* 代表样本图路径
* 日志路径
* 若有模型输出，则其路径

这样用户可直接将此报告反馈给 ChatGPT 主控窗口。

---

## 十、推荐执行顺序

请按以下顺序推进：

1. 阅读上位文档
2. 评估 `task_real_002` 当前重建器实现与限制
3. 实现更忠实的快速柱面重建器
4. 用少量样本做 faithful recon smoke 验证
5. 建立 controlled radial mismatch dataset
6. 运行 `ref3/ref5/ref7/ref9/BP` faithful baselines
7. 统计并绘制 radial mismatch 曲线
8. 生成统一可视化
9. 如必要，做 point learning smoke v2
10. 生成 `task_real_003_report.md`
11. 更新 `CHANGELOG_DEV.md` 与 `debug.md`
12. 确保 git 工作区可提交

---

## 十一、验收标准

本任务只有在以下条件全部满足时才算完成：

1. 当前 analytic verifier 已被更忠实的快速柱面重建实现替换
2. 所有实验数据都能证明来自 true 3D cylindrical simulation
3. `ref3/ref5/ref7/ref9/BP` 在 faithful recon 下全部可执行
4. 已形成更可信的 wall-time 与 quality 表
5. 已系统建立 `error vs rho_target` 与 `error vs radial mismatch` 曲线
6. 已输出标准化 3D 场景图、重建对比图、指标曲线
7. 已生成统一命名的 `task_real_003_report.md`
8. `CHANGELOG_DEV.md` 与 `debug.md` 已更新
9. git 工作区保持可提交状态

---

## 十二、你应如何判断是否可以进入 ET

在最终报告中，请明确回答：

1. 当前 faithful fast cylindrical recon 是否已足够可信？
2. `reference_surface_strategy_v1` 是否已有明显薄弱径向区域？
3. 是否已经具备进入 shape-family ET 主数据集构建的条件？
4. 若尚不具备，缺的是什么？

---

## 十三、最终终端汇报格式

任务完成后，请按如下格式做最终汇报：

1. `PROJECT_ROOT = ...`
2. `faithful fast recon = pass / partial pass / fail`
3. `true 3D cylindrical data proof = pass / partial pass / fail`
4. `baseline faithful chain = pass / partial pass / fail`
5. `radial mismatch analysis = pass / partial pass / fail`
6. `visualization outputs = pass / partial pass / fail`
7. `Artifacts = ...`
8. `Key issues = ...`
9. `Ready for ET? = yes / no / conditional`
10. `Suggested next task = task_real_004 (...)`

---

## 十四、提醒

* 这是进入 ET 之前的桥梁任务
* 核心不是“多跑一些样本”，而是把传统前端骨架变得可信
* 只有当前端 faithful、误差机制可解释，后面的 ET 主战场结果才有说服力

```
```

