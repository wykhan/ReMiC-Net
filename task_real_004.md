
````markdown id="0h3l6v"
# task_real_004：实现真正的柱面孔径参考面近似快速算法，并重跑点目标受控验证

你现在服务于项目：

- `PROJECT_ROOT = /home/superws/2026_Projects/Codex_reference_plane_real`
- `CONTEXT = /home/superws/2026_Projects/Codex_reference_plane_real/CONTEXT`
- `workspace = /home/superws/2026_Projects/Codex_reference_plane_real/workspace`

已完成：
- `task_real_001`：bootstrap / 治理冻结
- `task_real_002`：true 3D cylindrical point chain smoke
- `task_real_003`：faithful point validation + radial mismatch evidence

当前已知限制：
- `task_real_003` 已证明质量趋势与径向失配机制可信
- 但当前 faithful recon 仍不是真正的 accelerated cylindrical reference-surface engine
- wall time 几乎未在 `ref3/ref5/ref7/ref9/BP` 间拉开，因此 speed-quality story 还不够强，不能作为 ET 主实验前端最终版本

用户已新增关键条件：
- 谭维贤 MATLAB 源码已放在  
  `/home/superws/2026_Projects/Codex_reference_plane_real/reference_plane_matlab_Tan`
- 你可以直接运行这些 MATLAB 代码
- 本任务中 **务必实现柱面孔径参考面近似快速算法**
- 不再接受“faithful 但不够 fast”的折中实现

---

## 一、任务定位

本任务的唯一目标是：

> 以谭维贤 MATLAB 源码为直接参照，  
> 在当前 protocol v1 下实现真正的柱面孔径参考面近似快速算法，  
> 并重新完成点目标 controlled validation，  
> 建立可信的 wall-time separation、quality trend 和 radial mismatch evidence。

本任务不是 ET 主实验，也不是 physics consistency。

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
9. `exp/task_real_003_faithful_point_validation/*/task_real_003_report.md`

不得绕过这些文档自定协议。

---

## 三、强制硬约束

### 硬约束 1：必须直接审计并运行 MATLAB 原型
本任务中，你必须直接使用：

`/home/superws/2026_Projects/Codex_reference_plane_real/reference_plane_matlab_Tan`

中的 MATLAB 源码，完成：
- 代码阅读
- 关键流程审计
- 至少一次可运行验证
- 与当前项目 protocol v1 的映射说明

不得只“口头参考” MATLAB，而不真正运行或审计。

---

### 硬约束 2：必须实现不打折扣的快速算法主路径
本任务不再接受以下做法充当主 baseline：
- local ROI echo-driven matched filtering 近似器
- analytic verifier
- faithful but not accelerated 替代版
- 仅用 proxy 解释速度结论

必须形成一个真正的 accelerated cylindrical reference-surface reconstruction engine。

---

### 硬约束 3：所有实验数据必须证明来自 true 3D cylindrical simulation
本任务中任何 dataset / split / controlled set，都必须输出：

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

### 硬约束 4：每次实验都必须生成可视化
必须输出并保存：

#### A. 原始仿真数据可视化
- GT 3D scatter / amplitude 视图
- top / front / side 三视图
- 必要的 slice 图

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
- runtime vs method
- speedup vs BP
- NMSE / PSNR / SSIM vs method
- `error vs rho_target`
- `error vs radial mismatch`

不得只保留 csv/json。

---

### 硬约束 5：必须生成统一命名的任务报告
本任务结束时，必须在产物目录中生成：

- `task_real_004_report.md`

不得使用临时命名风格替代。

---

## 四、严格边界

### 本任务允许做
- MATLAB 原型审计与运行
- accelerated cylindrical reference-surface engine 实现
- controlled point-target faithful rerun
- wall-time benchmarking
- radial mismatch analysis rerun
- 标准化可视化与报告
- 若需要，可做少量 sanity smoke
- 更新 `CHANGELOG_DEV.md` 与 `debug.md`

### 本任务禁止做
- 不进入 shape-family ET
- 不进入 Manisali-style ET
- 不接入真实回波
- 不开展 physics consistency
- 不升级到 explicit MIMO v2
- 不修改已有上位协议原文内容
- 不把本任务写成最终论文结论

---

## 五、本任务要回答的问题

1. 当前项目是否已经拥有真正的 protocol-v1 accelerated cylindrical reference-surface engine？
2. `ref3/ref5/ref7/ref9/BP` 的 wall time 是否终于显著拉开？
3. `task_real_003` 中的质量趋势和径向失配机制，在真正快算法下是否仍然成立？
4. 当前是否已经 ready for shape-family ET 主实验？

---

## 六、任务拆解

---

### Part A：MATLAB 原型审计与映射冻结

#### 目标
把谭维贤 MATLAB 原型转换成当前项目的“实现基准”。

#### 必做项
1. 运行 `reference_plane_matlab_Tan` 中的关键脚本
2. 识别并记录：
   - 输入回波格式
   - FFT 顺序
   - `rho_ref` 与参考面库定义
   - 匹配函数构造方式
   - 距离向积分 / 聚焦逻辑
   - 高度向逆变换
   - 最终几何校正 / 图像排列方式
3. 与 `simulation_protocol.md` 做逐项映射
4. 明确指出：
   - MATLAB 主流程中哪些步骤在当前 Python 路径缺失
   - 哪些步骤必须原样保留
   - 哪些可以工程上重构，但不能改变算法本质

#### 产物
- `doc/task_real_004_algorithm_audit.md`
- `doc/matlab_to_python_mapping.md`

#### 验收点
必须能明确回答：
> 这次 Python/工程实现，到底严格复现了 MATLAB 快速算法的哪几步。

---

### Part B：实现真正的 accelerated cylindrical reference-surface engine

#### 目标
实现 protocol-v1 下真正的快速柱面参考面引擎，作为项目主 baseline。

#### 必须实现的核心主流程
1. 从保存的 true cylindrical echo 读入
2. 对同一 echo 执行公共 FFT 预处理：
   - 高度向 FFT
   - 方位向 FFT
3. 基于完整参考面库建立 reference-surface matching engine
4. `ref3/ref5/ref7/ref9` 仅是完整参考面库的不同抽样
5. 在波数域完成匹配、乘法与距离向聚焦
6. 高度向逆变换
7. 几何校正到 protocol 一致的笛卡尔 `(x, y, z)` 输出体
8. 输出统一 amplitude volume

#### 强制要求
- 不允许再以 local ROI echo-driven matched filtering 充当主 baseline path
- 不允许不同 `refK` 走不同算法路径
- 允许先做 NumPy / MATLAB wrapper 版本，再逐步重构，但主路径必须已经是 accelerated engine

#### 技术路线允许两种方案
你可选择其中之一，或二者结合：

##### 方案 A：直接封装 MATLAB 快速算法为当前项目主 baseline
- 通过脚本调用 MATLAB 代码
- 导出标准化重建结果
- 接入当前 Python 评测、可视化、报告体系
- 这是最直接、最不打折扣的方案

##### 方案 B：基于 MATLAB 审计结果，在 Python 中 faithful port
- 但必须真正实现 accelerated path
- 不得回退到简化 verifier 逻辑

#### 选择原则
- 优先保证“不打折扣的快速算法”
- 不要求本任务就把所有代码都纯 Python 化
- 若直接调用 MATLAB 更快更稳，应优先采用

#### 建议文件
- `workspace/recon/cyl_fast_reference_engine.py`
- `workspace/recon/reference_surface_kernels.py`
- `workspace/recon/geometry_correction.py`
- 若采用 MATLAB wrapper：
  - `workspace/recon/matlab_fast_recon_wrapper.py`

---

### Part C：重建入口统一化

#### 目标
将以下方法统一到同一主路径下：
- `ref3`
- `ref5`
- `ref7`
- `ref9`
- `BP`

#### 要求
1. `ref3/ref5/ref7/ref9` 必须共享 accelerated reference-surface engine
2. `BP` 作为高精度传统对照
3. 所有方法统一输出：
   - amplitude volume
   - runtime
   - metadata

#### 参考面定义
严格遵守 `reference_surface_strategy.md`，不得改动 `ref3/ref5/ref7/ref9`。

---

### Part D：可信 wall-time benchmarking

#### 目标
重建真正可信的速度证据。

#### 必做项
1. 对同一批 controlled point samples，重复运行：
   - `ref3`
   - `ref5`
   - `ref7`
   - `ref9`
   - `BP`
2. 统计：
   - mean
   - std
   - median
   - warmup 后 wall time
3. wall time 必须是主速度指标
4. proxy 只能作为辅助诊断，不能再替代主速度结论

#### 通过标准
至少要看到：
- `ref3` 明显快于 `ref9`
- `ref9` 明显快于 `BP`
- 不再出现几乎等时的状态

#### 产物
- `runtime_table_accelerated.csv`
- `runtime_repeats.json`
- `viz/curves/runtime_vs_method_accelerated.png`

---

### Part E：重跑 controlled point validation

#### 目标
在真正 accelerated engine 上，重跑 `task_real_003` 的 controlled radial validation。

#### 必做项
1. 使用 true 3D cylindrical controlled dataset
2. 重跑：
   - `rho_sweep`
   - `azimuth_control`
   - `height_control`
3. 重新计算：
   - NMSE
   - PSNR
   - SSIM
   - `error vs rho_target`
   - `error vs radial mismatch`

#### 要看什么
1. 质量排序是否仍是  
   `ref3 < ref5 < ref7 < ref9 < BP`
2. 小半径脆弱性是否仍存在
3. 若机制保持，则说明：
   - `task_real_003` 的质量机制不是旧实现伪影
   - `reference_surface_strategy_v1` 的薄弱区是真的

#### 产物
- `baseline_metrics_accelerated.json`
- `quality_table_accelerated.csv`
- `radial_mismatch_metrics_accelerated.json`
- `viz/curves/nmse_vs_rho_target_accelerated.png`
- `viz/curves/error_vs_radial_mismatch_accelerated.png`

---

### Part F：标准化可视化输出

#### 目标
所有结果统一进标准化 viz 目录。

#### 必须创建的目录
```text
viz/
├── scene_3d/
├── recon_compare/
├── curves/
└── slices/
````

#### 至少包括

* `scene_3d/`：GT 3D 场景图与三视图
* `recon_compare/`：GT/ref3/ref5/ref7/ref9/BP 对比图
* `curves/`：runtime、quality、radial mismatch 曲线
* `slices/`：三正交切片、error map

#### 命名建议

* `sample_000_gt_3d.png`
* `sample_000_ref3_vs_bp.png`
* `runtime_vs_method_accelerated.png`
* `nmse_vs_rho_target_accelerated.png`
* `error_vs_radial_mismatch_accelerated.png`

---

### Part G：任务报告与主控交接

#### 目标

生成统一报告，便于用户反馈给主控窗口。

#### 必须生成

* `task_real_004_report.md`

#### 强制结构

至少包含：

1. `Task Goal`
2. `Protocol / Context Files Used`
3. `Boundary Statement`
4. `Implementation Summary`
5. `MATLAB Audit Summary`
6. `Dataset Summary`
7. `Experiment Summary`
8. `Key Metrics`
9. `Visual Outputs`
10. `Issues / Limitations`
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
* 若使用 MATLAB wrapper，则 wrapper 配置与输出路径

---

## 七、脚本层要求

请新增或补齐：

1. `scripts/run_matlab_reference_plane_audit.sh`
2. `scripts/run_point_accelerated_baselines.sh`
3. `scripts/run_accelerated_radial_mismatch_analysis.sh`
4. `scripts/render_point_viz_accelerated.sh`

若采用 MATLAB wrapper，还应有：

* `scripts/run_matlab_fast_recon_wrapper.sh`

### 脚本要求

* 必须可执行
* 必须把日志落盘
* 必须统一写入本任务 exp 目录
* 不允许手工散跑代替脚本流程

---

## 八、exp 目录规范

请为本任务创建固定产物目录：

```text id="vx81y3"
exp/task_real_004_accelerated_point_validation/<timestamp>/
```

至少输出：

1. `task_real_004_report.md`
2. `dataset_manifest.json`
3. `dataset_protocol_snapshot.md`
4. `data_origin_statement.md`
5. `runtime_table_accelerated.csv`
6. `runtime_repeats.json`
7. `baseline_metrics_accelerated.json`
8. `quality_table_accelerated.csv`
9. `radial_mismatch_metrics_accelerated.json`
10. `tree.txt`
11. `logs/`
12. `viz/`

若采用 MATLAB wrapper，还应输出：

* `matlab_engine_notes.md`

---

## 九、推荐执行顺序

请按以下顺序推进：

1. 阅读上位文档与 `task_real_003_report.md`
2. 审计并运行 MATLAB 原型
3. 形成 `algorithm_audit` 与 `matlab_to_python_mapping`
4. 实现 accelerated reference-surface engine（或 MATLAB wrapper 主路径）
5. 用少量 controlled samples 做 accelerated smoke
6. 验证 wall-time separation 是否出现
7. 重跑完整 controlled point validation
8. 生成标准化可视化
9. 生成 `task_real_004_report.md`
10. 更新 `CHANGELOG_DEV.md` 与 `debug.md`
11. 确保 git 工作区可提交

---

## 十、验收标准

本任务只有在以下条件全部满足时才算完成：

1. MATLAB 原型已被真正运行并审计
2. 已形成当前项目可调用的 accelerated cylindrical reference-surface engine
3. 所有实验数据都能证明来自 true 3D cylindrical simulation
4. `ref3/ref5/ref7/ref9/BP` 在 accelerated 主路径下全部可执行
5. wall time 已显著拉开，不再弱分离
6. 质量排序仍然正确
7. radial mismatch 曲线仍然成立
8. 已输出标准化 3D 场景图、成像对比图、指标曲线
9. 已生成 `task_real_004_report.md`
10. git 工作区保持可提交状态

---

## 十一、最终判断要求

在最终报告中，请明确回答：

1. 当前 accelerated engine 是否已经足够“真正快”？
2. 当前是否可以把 speed-quality story 作为 ET 主实验前端骨架？
3. `reference_surface_strategy_v1` 是否仍显示小半径薄弱性？
4. 是否 ready for shape-family ET？回答必须是：

   * `yes`
   * `no`
   * `conditional`

---

## 十二、最终终端汇报格式

任务完成后，请按如下格式做最终汇报：

1. `PROJECT_ROOT = ...`
2. `MATLAB audit = pass / partial pass / fail`
3. `accelerated fast recon = pass / partial pass / fail`
4. `true 3D cylindrical data proof = pass / partial pass / fail`
5. `wall-time separation = pass / partial pass / fail`
6. `baseline accelerated chain = pass / partial pass / fail`
7. `radial mismatch analysis = pass / partial pass / fail`
8. `visualization outputs = pass / partial pass / fail`
9. `Artifacts = ...`
10. `Ready for ET? = yes / no / conditional`
11. `Suggested next task = task_real_005 (...)`

---

## 十三、提醒

* 这次不接受折中版
* 必须真正使用谭维贤 MATLAB 原型
* 必须把“快速算法”做成当前项目主 baseline
* 只有 wall-time separation 真正出现，ET 主实验前端才算站稳

```
```

