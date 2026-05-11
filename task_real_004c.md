
````markdown 
# task_real_004c：冻结 Variant B 并完成进入 ET 前的最终前端确认

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

当前已知结论（来自 `task_real_004b_report.md`）：
- `ref7/ref9` 交叉主因：geometry correction
- full-library sinc stencil 值得并入默认主路径：`yes`
- dense global tensor 不值得并入默认主路径：`no`
- 默认 accelerated engine 应升级为  
  **Variant B = active windows + full-library sinc geometry correction**
- 当前 front-end / Ready for ET 仍为 `conditional`
- 报告建议：先冻结默认前端配置，再重跑 broader controlled point suite，再进入 shape-family ET

本任务是一个**短任务 / 确认任务**，不是探索任务。

---

## 一、任务定位

本任务的唯一目标是：

> 将 Variant B 正式冻结为默认 accelerated front-end，
> 并在更广的 controlled point suite 上完成最终确认，
> 判断当前前端是否已经足够稳定，可以进入 `task_real_005` 的 shape-family ET 主实验。

本任务不是 ET，不做 physics consistency，不再做 A/B/C/D 路线比较。

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
9. `exp/task_real_004_accelerated_point_validation/*/task_real_004_report.md`
10. `exp/task_real_004b_wrap_hardening/*/task_real_004b_report.md`

不得绕过这些文档自定协议。

---

## 三、强制硬约束

### 硬约束 1：默认 front-end 必须冻结为 Variant B
从本任务开始，当前项目默认 accelerated engine 统一定义为：

> **Variant B = active windows + full-library sinc geometry correction**

不得再以 Variant A 作为默认主路径。  
dense global 只允许作为 audit/debug mode 保留，不得用于本任务主实验。

必须在以下文件中同步反映这一冻结事实：
- `recon/engine_modes.md`
- `CONTEXT/experiment_matrix.md`
- 必要时 `CONTEXT/project_brief.md`
- 以及相关脚本默认参数

---

### 硬约束 2：所有数据必须证明来自 true 3D cylindrical simulation
本任务中任何新增 dataset / controlled set，都必须输出：

- `dataset_manifest.json`
- `dataset_protocol_snapshot.md`
- `data_origin_statement.md`

其中 `data_origin_statement.md` 必须明确写出：
- 这是 **true 3D cylindrical simulation data**
- 使用的 forward simulator 入口
- 使用的协议版本
- 使用的重建入口（默认 Variant B）
- 明确声明：不是二维代理图样，不是人工伪造 ref 图像

---

### 硬约束 3：每次实验都必须生成可视化
必须输出并保存：

#### A. 原始仿真数据可视化
- GT 3D scatter / amplitude 视图
- top / front / side 三视图
- 必要 slice 图

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
- `runtime_vs_method_variantB.png`
- `speedup_vs_bp_variantB.png`
- `quality_vs_method_variantB.png`
- `monotonicity_violations_by_subset.png`
- `wrap_symmetry_error_variantB.png`
- `ref7_ref9_gap_distribution.png`
- `nmse_vs_rho_target_variantB.png`
- `error_vs_radial_mismatch_variantB.png`

不得只保留 csv/json。

---

### 硬约束 4：必须生成统一命名的任务报告
本任务结束时，必须在产物目录中生成：

- `task_real_004c_report.md`

不得使用临时命名风格替代。

---

## 四、严格边界

### 本任务允许做
- 冻结默认前端为 Variant B
- 构建 broader controlled point suite
- 用 Variant B 重跑 `ref3/ref5/ref7/ref9/BP`
- 重新统计速度、质量、monotonicity、wrap symmetry、radial mismatch
- 输出标准化可视化与报告
- 更新 `CHANGELOG_DEV.md` 与 `debug.md`

### 本任务禁止做
- 不再跑 A/B/C/D 四组对照
- 不再尝试 dense global 默认化
- 不进入 shape-family ET
- 不进入 Manisali-style ET
- 不做学习训练
- 不做 physics consistency
- 不接入真实数据
- 不修改现有上位协议原文内容

---

## 五、本任务要回答的问题

1. Variant B 在 broader controlled point suite 上是否依然稳定？
2. `ref3/ref5/ref7/ref9/BP` 的速度—质量排序是否仍然成立？
3. `ref7/ref9` 的交叉是否只是少量 seam 边界残留，而不是系统性现象？
4. radial mismatch 机制是否在 broader suite 上仍然成立？
5. 当前 front-end 是否已经足够稳定，可以进入 `task_real_005` 的 shape-family ET 主实验？

---

## 六、任务拆解

---

### Part A：冻结默认前端配置

#### 目标
正式将 Variant B 写入项目默认实现。

#### 必做项
1. 更新默认 accelerated engine 配置：
   - `tensor_mode = active`
   - `geom_mode = sinc`
2. 明确 dense global 仅保留为：
   - `audit mode`
   - 或 `debug mode`
3. 更新相关文档与代码说明：
   - `recon/engine_modes.md`
   - `CONTEXT/experiment_matrix.md`
   - 必要时 `project_brief.md`
4. 在报告中写明：
   - 当前默认前端已从旧版本升级为 Variant B

#### 验收点
后续脚本若不显式传参，必须默认走 Variant B。

---

### Part B：构建 broader controlled point suite

#### 目标
生成比 `task_real_004b` 的 seam stress set 更广、但仍属于 controlled point validation 的数据集。

#### 建议组成
至少包含以下四组：

##### 1. broader rho sweep
- 全径向 `[0.00, 0.30]`
- 多个高度层
- 多个方位位置
- 不只看 seam 附近

##### 2. broader azimuth control
- seam 附近加密
- 非 seam 区域也取代表点
- 用于判断 `ref7/ref9` 交叉是否只集中在 seam

##### 3. broader height control
- 中层
- 上边界附近
- 下边界附近
- 若资源允许，再加中高层 / 中低层

##### 4. 少量双点 controlled set
- 只需少量
- 目的在于确认 Variant B 下双点场景基本排序不崩

#### 规模建议
- 明显大于 `task_real_004b` 的 6 个样本
- 但不追求大规模，建议控制在 **60–120** 个样本左右
- 关键是“更广地确认稳定性”，不是扩大实验规模

#### 要求
- 所有样本都必须来自 true 3D cylindrical simulation
- 输出：
  - `dataset_manifest.json`
  - `dataset_protocol_snapshot.md`
  - `data_origin_statement.md`

#### 建议文件
- `workspace/data/broader_controlled_point_builder.py`

---

### Part C：重跑 Variant B 下的传统基线

#### 目标
在 broader controlled suite 上，用 Variant B 重新运行：

- `ref3`
- `ref5`
- `ref7`
- `ref9`
- `BP`

#### 要求
1. 所有方法统一走当前默认主路径（Variant B + BP）
2. 输出统一格式：
   - amplitude volume
   - runtime
   - metrics
   - metadata
3. 明确记录：
   - `ref7/ref9` 是否仍有交叉
   - 交叉样本出现在哪些 subset

#### 输出文件
- `baseline_metrics_variantB.json`
- `runtime_table_variantB.csv`
- `quality_table_variantB.csv`

---

### Part D：统计稳定性指标

#### 目标
专门确认 `ref7/ref9` 的残留问题是否还是系统性问题。

#### 必须统计

##### 1. monotonicity violation count
重点统计：
- `ref9` 比 `ref7` 更差的样本数
- 至少对 NMSE / PSNR 两个口径统计

##### 2. violation rate by subset
分别统计：
- seam subset
- non-seam subset
- inner-radius subset
- outer-radius subset
- height-edge subset
- double-point subset（若有）

##### 3. wrap symmetry error
继续统计并画图，但本任务中它是辅助证据，不是唯一主判断标准。

##### 4. ref7-ref9 gap distribution
- 统计 `ref9 - ref7` 的指标差分分布
- 看差值是否大多数为正向改善

##### 5. radial mismatch mechanism
继续输出：
- `error vs rho_target`
- `error vs radial mismatch`

#### 建议输出文件
- `stability_metrics_variantB.json`
- `monotonicity_violations_variantB.csv`

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

1. `runtime_vs_method_variantB.png`
2. `speedup_vs_bp_variantB.png`
3. `quality_vs_method_variantB.png`
4. `monotonicity_violations_by_subset.png`
5. `wrap_symmetry_error_variantB.png`
6. `ref7_ref9_gap_distribution.png`
7. `nmse_vs_rho_target_variantB.png`
8. `error_vs_radial_mismatch_variantB.png`

#### 必须输出的代表样本图

至少选三类代表样本：

1. 正常单调样本
2. seam 边界困难样本
3. 小半径脆弱样本

每类都输出：

* GT 3D 图
* GT / ref7 / ref9 / BP 对比图
* slice / error 图

---

### Part F：最终前端确认与进入 ET 判断

#### 目标

本任务结束时，必须给出明确判断，而不是“再看看”。

#### 必须回答

1. Variant B 是否已经足够稳定？
2. `ref7/ref9` 交叉是否还系统性存在？
3. 目前是否可以进入 shape-family ET？
4. 若仍有残留问题，它是否只限于极少数 seam 边界样本？
5. 当前 front-end 是否已经可以视为：

   * `ready`
   * `conditionally ready`
   * `not ready`

---

## 七、脚本层要求

请新增或补齐：

1. `scripts/run_variantB_broader_point_suite.sh`
2. `scripts/run_variantB_stability_analysis.sh`
3. `scripts/render_variantB_confirmation_viz.sh`

### 脚本要求

* 必须可执行
* 必须把日志落盘
* 必须统一写入本任务 exp 目录
* 默认参数必须走 Variant B
* 不允许手工散跑代替脚本流程

---

## 八、exp 目录规范

请为本任务创建固定产物目录：

```text id="c92q0n"
exp/task_real_004c_variantB_confirmation/<timestamp>/
```

至少输出：

1. `task_real_004c_report.md`
2. `dataset_manifest.json`
3. `dataset_protocol_snapshot.md`
4. `data_origin_statement.md`
5. `baseline_metrics_variantB.json`
6. `runtime_table_variantB.csv`
7. `quality_table_variantB.csv`
8. `stability_metrics_variantB.json`
9. `tree.txt`
10. `logs/`
11. `viz/`

---

## 九、`task_real_004c_report.md` 的强制结构

报告必须至少包含以下部分：

1. `Task Goal`
2. `Default Front-end Freeze Statement`
3. `Protocol / Context Files Used`
4. `Boundary Statement`
5. `Dataset Summary`
6. `Experiment Summary`
7. `Key Metrics`
8. `Stability Analysis`
9. `Visual Outputs`
10. `Remaining Issues`
11. `Ready for ET?`
12. `Suggested Next Task`

并且必须包含固定小节：

### Key file paths for ChatGPT controller

集中列出：

* report 路径
* metrics 路径
* curves 路径
* representative visuals 路径
* logs 路径

---

## 十、推荐执行顺序

请按以下顺序推进：

1. 阅读上位文档与 `task_real_004b_report.md`
2. 冻结默认前端为 Variant B
3. 构建 broader controlled point suite
4. 用 Variant B 重跑 `ref3/ref5/ref7/ref9/BP`
5. 统计速度、质量、monotonicity、symmetry、radial mismatch
6. 生成标准化可视化
7. 做进入 ET 的最终判断
8. 生成 `task_real_004c_report.md`
9. 更新 `CHANGELOG_DEV.md` 与 `debug.md`
10. 确保 git 工作区可提交

---

## 十一、验收标准

本任务只有在以下条件全部满足时才算完成：

1. 默认 front-end 已正式冻结为 Variant B
2. broader controlled point suite 已建立并证明来自 true 3D cylindrical simulation
3. `ref3/ref5/ref7/ref9/BP` 全部在 Variant B 下跑通
4. 速度—质量排序仍然成立
5. `ref7/ref9` 交叉不再系统性出现
6. 若仍有残留交叉，必须证明其只是少量边界残留
7. radial mismatch 曲线仍然成立
8. 已输出标准化 3D 图、成像对比图、曲线图
9. 已生成 `task_real_004c_report.md`
10. git 工作区保持可提交状态

---

## 十二、最终判断要求

在最终报告中，请明确回答：

1. Variant B 是否已经是当前项目的固定默认前端？
2. `ref7/ref9` 交叉是否还系统性存在？
3. 当前 front-end 是否已经足够进入 shape-family ET？
4. `Ready for ET?` 回答必须是：

   * `yes`
   * `no`
   * `conditional`

---

## 十三、最终终端汇报格式

任务完成后，请按如下格式做最终汇报：

1. `PROJECT_ROOT = ...`
2. `Variant B freeze = pass / partial pass / fail`
3. `broader controlled point suite = pass / partial pass / fail`
4. `baseline Variant B chain = pass / partial pass / fail`
5. `stability confirmation = pass / partial pass / fail`
6. `radial mismatch confirmation = pass / partial pass / fail`
7. `visualization outputs = pass / partial pass / fail`
8. `Artifacts = ...`
9. `Ready for ET? = yes / no / conditional`
10. `Suggested next task = task_real_005 (...)`

---

## 十四、提醒

* 这次不再做路线探索
* 这次只做 Variant B 的最终确认
* 目标是回答“现在能不能放心进入 ET”
* 若通过，本任务之后应直接进入 `task_real_005`

```
```

