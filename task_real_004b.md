

````markdown id="8p4xk1"
# task_real_004b：azimuth-wrap 稳定化 + MATLAB 一致性强化

你现在服务于项目：

- `PROJECT_ROOT = /home/superws/2026_Projects/Codex_reference_plane_real`
- `CONTEXT = /home/superws/2026_Projects/Codex_reference_plane_real/CONTEXT`
- `workspace = /home/superws/2026_Projects/Codex_reference_plane_real/workspace`

已完成：
- `task_real_001`：bootstrap / 治理冻结
- `task_real_002`：true 3D cylindrical point chain smoke
- `task_real_003`：faithful point validation + radial mismatch evidence
- `task_real_004`：accelerated cylindrical reference-surface engine + controlled point rerun

当前已知状态（来自 `task_real_004_report.md`）：
- accelerated engine 已建立，且 wall time 已显著拉开
- MATLAB 原型已实际审计与运行
- speed-quality story 基本成立，可作为 ET 前端 skeleton
- 但仍存在三类隐患：
  1. accelerated engine 仍使用 local active azimuth-height windows，而不是 dense global `1101 x 501` tensor
  2. geometry correction 仍是 reduced reference sets 上的 linear interpolation，而不是 MATLAB full-library sinc stencil
  3. azimuth wrap 边界附近，少数控制样本仍出现 `ref7/ref9` 交叉

本任务的目的不是进入 ET，而是先把这些隐患定量定位，并尽量修复到“publication-stable”水平。

---

## 一、任务定位

本任务的唯一目标是：

> 对 accelerated front-end 做一次“边界稳定化 + MATLAB 一致性强化”硬化，
> 精确定位 azimuth-wrap 异常来源，
> 比较 full-library sinc stencil 与 dense global tensor 的收益/代价，
> 并决定当前默认主路径应如何升级。

这是一个 **pre-ET hardening task**，不是 ET 主实验，也不是 physics consistency。

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
10. `doc/task_real_004_algorithm_audit.md`
11. `doc/matlab_to_python_mapping.md`

不得绕过这些文档自定协议。

---

## 三、强制硬约束

### 硬约束 1：所有数据必须证明来自 true 3D cylindrical simulation
本任务中任何新增 dataset / controlled set / stress set，都必须输出：

- `dataset_manifest.json`
- `dataset_protocol_snapshot.md`
- `data_origin_statement.md`

其中 `data_origin_statement.md` 必须明确写出：
- 这是 **true 3D cylindrical simulation data**
- 使用的 forward simulator 入口
- 使用的协议版本
- 使用的重建入口
- 明确声明：不是二维代理图样，不是人工伪造 ref 图像

---

### 硬约束 2：每次实验都必须生成可视化
必须输出并保存：

#### A. 原始仿真数据可视化
- GT 3D scatter / amplitude 视图
- top / front / side 三视图
- 必要 slice 图

#### B. 成像结果可视化
每个代表样本至少比较：
- GT
- `ref7`
- `ref9`
- `BP`
- 以及本任务的各个 ablation 版本（见下文 A/B/C/D）

并输出：
- recon compare 图
- 三正交切片
- absolute error map / difference map

#### C. 指标曲线
必须输出：
- `runtime vs variant`
- `memory vs variant`（若可测）
- `wrap symmetry error vs azimuth offset`
- `monotonicity violations by variant`
- `NMSE / PSNR / SSIM on edge subset`
- `error vs radial mismatch`

不得只保留 csv/json。

---

### 硬约束 3：必须生成统一命名的任务报告
本任务结束时，必须在产物目录中生成：

- `task_real_004b_report.md`

不得使用临时命名风格替代。

---

## 四、严格边界

### 本任务允许做
- 新建 azimuth-edge stress set
- 比较 active windows / dense global tensor
- 比较 linear correction / full-library sinc stencil
- 定位并修复 `ref7/ref9` 交叉问题
- 测试 runtime 与 memory 代价
- 输出标准化可视化与报告
- 必要时修补 accelerated engine 默认配置
- 更新 `CHANGELOG_DEV.md` 与 `debug.md`

### 本任务禁止做
- 不进入 shape-family ET
- 不进入 Manisali-style ET
- 不接入真实回波
- 不开展 physics consistency
- 不升级到 explicit MIMO v2
- 不修改现有上位协议原文内容
- 不把本任务写成最终论文结论

---

## 五、本任务要回答的问题

1. azimuth-wrap 边界上的 `ref7/ref9` 交叉，主因是 geometry correction、active windows，还是二者共同作用？
2. full-library sinc stencil 是否足以显著缓解 wrap 边界异常？
3. dense global tensor 是否真有必要作为默认主路径，还是只需要保留为 strict MATLAB / audit mode？
4. 当前 accelerated engine 的默认配置应如何升级，才能放心进入 ET 主实验？

---

## 六、任务拆解

---

### Part A：构造 azimuth-edge stress set

#### 目标
建立专门用于 seam / wrap 稳定性分析的 stress dataset。

#### 必须覆盖
1. 半径至少三组：
   - 小半径
   - 中半径
   - 外缘半径

2. 高度至少三组：
   - 中层
   - 上边界附近
   - 下边界附近

3. 方位采样围绕 seam 对称展开：
   - `-π`
   - `-π + 1du`
   - `-π + 2du`
   - `π - 2du`
   - `π - 1du`
   - `π`
   - 必要时再加更细 offset

4. 可以增加少量双点 stress，但优先保证单点分析干净清楚

#### 说明
- 这批样本不是为了扩大数据量，而是为了专门放大 wrap 边界异常
- 数据仍必须是 true 3D cylindrical simulation

#### 建议文件
- `workspace/data/azimuth_edge_stress_builder.py`

#### 必须产物
- `dataset_manifest.json`
- `dataset_protocol_snapshot.md`
- `data_origin_statement.md`

---

### Part B：建立四组关键 ablation

#### 目标
只改最关键的两个变量，形成四组对照，回答异常来源。

#### 四组定义

##### Variant A：当前默认 accelerated engine
- active windows
- linear geometry correction

##### Variant B：只换 geometry correction
- active windows
- **full-library sinc stencil**

##### Variant C：只换 tensor 模式
- **dense global tensor**
- linear geometry correction

##### Variant D：两者都换
- **dense global tensor**
- **full-library sinc stencil**

#### 要求
1. 所有 variant 必须共享同一 true cylindrical echo 输入
2. `ref7/ref9/BP` 至少都要在这四组上比较
3. 若代价允许，`ref3/ref5` 也可补充，但主问题集中在 `ref7/ref9`

#### 说明
这是本任务的核心，不允许跳过。

---

### Part C：实现 full-library sinc stencil correction

#### 目标
把 geometry correction 做到更接近 MATLAB 原型。

#### 必做项
1. 明确 MATLAB 中 geometry correction / image arrangement 的关键方式
2. 在当前 accelerated engine 中新增 **full-library sinc stencil** 版本
3. 保留现有 linear interpolation 版本，供 A/B 对照
4. 输出实现说明：
   - stencil 的定义
   - 插值支持范围
   - 与 reduced reference linear interpolation 的差异
   - 数值稳定性注意事项

#### 建议文件
- `workspace/recon/geometry_correction_sinc.py`
- `workspace/recon/geometry_correction.py` 更新

#### 目标
优先看它是否能显著改善 wrap 边界异常。

---

### Part D：实现 dense global tensor mode（可切换模式）

#### 目标
让当前 engine 支持 **strict MATLAB / dense global tensor mode**，但不预设为默认。

#### 必做项
1. 保持当前 active windows mode
2. 新增 dense global mode
3. 两种模式都走 accelerated 主路径
4. 输出：
   - tensor 形状
   - active coverage ratio
   - peak memory
   - wall time

#### 强制要求
- dense global mode 必须是真正的全局 `1101 x 501` 口径，或与你当前 protocol grid 一致的全局张量实现
- 不允许打着 dense global 的名义仍局部裁剪

#### 建议文件
- `workspace/recon/cyl_fast_reference_engine.py` 更新
- `workspace/recon/engine_modes.md`

#### 说明
dense global 的任务是帮助判断是否“必须默认启用”，不是预设一定更好。

---

### Part E：构建四类诊断指标

#### 目标
不要只看平均 NMSE，要专门针对 wrap 异常做诊断。

#### 必须新增以下指标

1. **Monotonicity violation count**
   - 统计 `ref9` 比 `ref7` 更差的样本数
   - 至少对 NMSE/PSNR 两个指标统计

2. **Wrap symmetry error**
   - 比较 `-π + δ` 与 `π - δ` 的结果差异
   - 对称样本的误差越小越好

3. **Edge-only metrics**
   - 单独统计 seam / edge subset 的：
     - NMSE
     - PSNR
     - SSIM

4. **Runtime / memory delta**
   - 比较 A/B/C/D 的 wall time
   - 若可行，统计 peak memory

#### 建议输出文件
- `wrap_stability_metrics.json`
- `monotonicity_violations.csv`
- `runtime_memory_by_variant.csv`

---

### Part F：统一曲线与可视化输出

#### 目标
输出可以直接用于主控窗口判断的图和表。

#### 必须输出的图
1. `monotonicity_violations_by_variant.png`
2. `wrap_symmetry_error_by_variant.png`
3. `edge_nmse_by_variant.png`
4. `edge_psnr_by_variant.png`
5. `runtime_by_variant.png`
6. `memory_by_variant.png`（若可测）
7. `error_vs_radial_mismatch_edge_subset.png`

#### 必须输出的对比图
对若干 seam 代表样本，输出：
- GT / ref7 / ref9 / BP / variant A/B/C/D compare
- 三正交切片
- difference map

#### 必须创建的目录
```text
viz/
├── scene_3d/
├── recon_compare/
├── curves/
└── slices/
````

---

### Part G：决定默认主路径

#### 目标

本任务结束时，必须给出工程决策，而不是只交一堆图。

#### 必须明确回答

1. 默认 accelerated engine 是否应升级为：

   * active windows + linear
   * active windows + sinc
   * dense global + linear
   * dense global + sinc

2. dense global 是否只保留为：

   * audit mode
   * debug mode
   * default mode

3. geometry correction 是否正式升级为 full-library sinc stencil

#### 要求

* 给出理由
* 给出收益与代价
* 不能只说“都有优缺点”

---

## 七、脚本层要求

请新增或补齐：

1. `scripts/run_azimuth_edge_stress_set.sh`
2. `scripts/run_wrap_ablation_variants.sh`
3. `scripts/run_wrap_stability_analysis.sh`
4. `scripts/render_wrap_viz.sh`

如需区分模式，可在脚本中加：

* `--tensor_mode active|dense_global`
* `--geom_mode linear|sinc`

### 脚本要求

* 必须可执行
* 必须把日志落盘
* 必须统一写入本任务 exp 目录
* 不允许手工散跑代替脚本流程

---

## 八、exp 目录规范

请为本任务创建固定产物目录：

```text id="xq9j0w"
exp/task_real_004b_wrap_hardening/<timestamp>/
```

至少输出：

1. `task_real_004b_report.md`
2. `dataset_manifest.json`
3. `dataset_protocol_snapshot.md`
4. `data_origin_statement.md`
5. `wrap_stability_metrics.json`
6. `monotonicity_violations.csv`
7. `runtime_memory_by_variant.csv`
8. `tree.txt`
9. `logs/`
10. `viz/`

如实现了 dense global mode 的专门说明，再增加：

* `dense_global_mode_notes.md`

---

## 九、`task_real_004b_report.md` 的强制结构

报告必须至少包含以下部分：

1. `Task Goal`
2. `Protocol / Context Files Used`
3. `Boundary Statement`
4. `Implementation Summary`
5. `Stress Dataset Summary`
6. `A/B/C/D Variant Definition`
7. `Key Metrics`
8. `Visual Outputs`
9. `Root Cause Analysis`
10. `Engineering Decision`
11. `Issues / Limitations`
12. `Ready for ET?`
13. `Suggested Next Task`

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

1. 阅读上位文档与 `task_real_004_report.md`
2. 构造 azimuth-edge stress set
3. 实现 full-library sinc stencil correction
4. 实现 dense global mode（可切换）
5. 定义并跑 A/B/C/D 四组对照
6. 统计 monotonicity / symmetry / edge-only 指标
7. 输出 runtime / memory 对比
8. 生成标准化可视化
9. 给出默认主路径决策
10. 生成 `task_real_004b_report.md`
11. 更新 `CHANGELOG_DEV.md` 与 `debug.md`
12. 确保 git 工作区可提交

---

## 十一、验收标准

本任务只有在以下条件全部满足时才算完成：

1. azimuth-edge stress set 已建立并证明来自 true 3D cylindrical simulation
2. A/B/C/D 四组关键对照全部完成
3. full-library sinc stencil 已实现并可运行
4. dense global mode 已实现并可运行
5. 已量化 `ref7/ref9` 交叉的发生频率
6. 已量化 wrap symmetry error
7. 已量化 dense global 与 sinc 的 runtime / memory 代价
8. 已输出标准化 3D 图、重建对比图、曲线图
9. 已明确给出默认 accelerated engine 的工程决策
10. 已生成 `task_real_004b_report.md`
11. git 工作区保持可提交状态

---

## 十二、最终判断要求

在最终报告中，请明确回答：

1. `ref7/ref9` 交叉的主因是什么？
2. full-library sinc stencil 是否值得并入默认主路径？
3. dense global tensor 是否值得并入默认主路径？
4. 当前 front-end 是否已经 publication-stable？
5. 是否 ready for shape-family ET？回答必须是：

   * `yes`
   * `no`
   * `conditional`

---

## 十三、最终终端汇报格式

任务完成后，请按如下格式做最终汇报：

1. `PROJECT_ROOT = ...`
2. `azimuth-edge stress set = pass / partial pass / fail`
3. `full-library sinc stencil = pass / partial pass / fail`
4. `dense global mode = pass / partial pass / fail`
5. `wrap root-cause analysis = pass / partial pass / fail`
6. `monotonicity stabilization = pass / partial pass / fail`
7. `visualization outputs = pass / partial pass / fail`
8. `Engineering decision = ...`
9. `Artifacts = ...`
10. `Ready for ET? = yes / no / conditional`
11. `Suggested next task = task_real_005 (...)`

---

## 十四、提醒

* 这次不是扩大实验规模
* 这次是定点修边界隐患
* 优先修复异常，再决定是否值得为 MATLAB 一致性付出更大代价
* 本任务结束后，必须能明确回答“现在能不能放心进入 ET”

```
```

