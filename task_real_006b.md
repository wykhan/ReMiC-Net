
````markdown 
# task_real_006b：full-scale dataset expansion + frozen mainline comparison against ref3/5/7/9/BP

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
- `task_real_006`：第一版正式两阶段学习训练（但数据规模仍低于 master-document 目标）

当前已知状态（来自 `task_real_006_report.md`）：
- `ref3 -> 3D U-Net -> GT amplitude` 已被证明有效
- hardest families（`point_cluster / line / L-shape`）和 `F2/F3/F4` 失败模式都出现了清晰改善
- 但当前训练数据规模仅为：
  - shape-family = `576 / 144 / 144`
  - random ET = `192 / 48 / 48`
- 这仍低于 master-document 要求的正式训练规模，因此 `task_real_006` 只能算 first substantial ET-2 training pass，而不是最终论文级比较

本任务进入：

> **Phase ET-2b：正式规模数据扩容 + 固定主方法的统一曲线定位**

---

## 一、任务定位

本任务的唯一目标是：

> 把 ET 数据扩充到 master-document 要求的正式规模，  
> 冻结一个唯一主方法版本，  
> 然后正式回答它在  
> `ref3 / ref5 / ref7 / ref9 / BP`  
> 速度–质量曲线中的位置。

本任务不是继续探索 M1/M2/M3 的细微差异，也不是 physics-consistency 任务。

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
10. `exp/task_real_006_two_stage_learning/*/task_real_006_report.md`

此外，继续参考：
11. `Efficient physics-based learned reconstruction methods for real-time 3D near-field MIMO radar imaging.pdf`
12. 已授权 git 项目：`Efficient-Learned-3D-Near-Field-MIMO-Imaging`

不得绕过这些文档自定协议。

---

## 三、强制硬约束

### 硬约束 1：shape-family 数据必须达到正式规模
family 集合固定为：
- `line`
- `cross`
- `L-shape`
- `double-line`
- `small_rect_edge`
- `point_cluster`

每类必须至少达到：
- `train >= 5000`
- `val >= 1000`
- `test >= 1000`

推荐直接冻结为：
- `train = 5000`
- `val = 1000`
- `test = 1000`

即总计：
- shape-family train = `30000`
- shape-family val = `6000`
- shape-family test = `6000`

若未达到，任务不得记为完全通过。

---

### 硬约束 2：random ET 也必须达到正式规模
Manisali-style random ET supplement 至少达到：
- `train >= 5000`
- `val >= 1000`
- `test >= 1000`

推荐直接冻结为：
- `train = 5000`
- `val = 1000`
- `test = 1000`

### 说明
- random ET 在本任务中保留为补充训练 / 泛化资源
- 但本任务的**默认主方法训练**不必强制使用 random ET
- 你必须把它生成并落盘，供后续扩展和附加实验使用

---

### 硬约束 3：所有数据必须证明来自 true 3D cylindrical simulation
本任务中任何 dataset / split / sample，都必须输出：

- `dataset_manifest_shape_family_full.json`
- `dataset_manifest_random_et.json`
- `dataset_protocol_snapshot.md`
- `data_origin_statement.md`

其中 `data_origin_statement.md` 必须明确写出：
- 这是 **true 3D cylindrical simulation data**
- 使用的 forward simulator 入口
- 使用的协议版本
- 使用的重建入口（Variant B / `ref3`)
- 明确声明：不是二维代理 family 图样，不是人工糊出的 ref 图像

---

### 硬约束 4：冻结唯一主方法，不再继续发散
本任务中，必须冻结唯一主方法为：

> **Frozen Mainline = Variant B `ref3` coarse volume -> 3D U-Net -> GT amplitude**

#### 具体冻结如下
- 前端：**Variant B**
- 物理骨干：**`ref3`**
- second stage：当前最好且最简洁的主方法版本
- 训练数据默认：**shape-family full-scale only**

### 说明
- 这相当于把 `task_real_006` 中表现最干净的 **M2 风格**冻结为默认主方法
- `M1/M3` 在本任务中降级为附加/可选比较，不再是主问题
- 本任务的核心不是“哪个 training recipe 好 0.03”，而是“冻结主方法后，它位于传统曲线哪一档”

---

### 硬约束 5：必须与 `ref3/ref5/ref7/ref9/BP` 做统一正式比较
本任务最终必须输出包含以下方法的统一主表：

- `ref3`
- `ref5`
- `ref7`
- `ref9`
- `BP`
- `ref3 + learning`（Frozen Mainline）

并统一比较：
- NMSE
- PSNR
- SSIM
- runtime
- speedup vs BP

---

### 硬约束 6：每次实验都必须生成可视化
必须输出并保存：

#### A. 原始数据可视化
- GT 3D occupancy / amplitude 视图
- top / front / side 三视图
- hardest family 代表样本的 slice montage

#### B. 结果对比可视化
每个代表样本至少比较：
- GT
- `ref3`
- `ref5`
- `ref7`
- `ref9`
- `BP`
- `ref3 + learning`

并输出：
- recon compare 图
- 三正交切片
- absolute error map / difference map

#### C. 指标曲线
必须输出：
- `runtime_quality_frontier_with_learning.png`
- `family_metrics_mainline_vs_baselines.png`
- `failure_mode_mainline_vs_baselines.png`
- `hardest_family_case_gallery.png`

不得只保留 csv/json。

---

### 硬约束 7：必须生成统一命名的任务报告
本任务结束时，必须在产物目录中生成：

- `task_real_006b_report.md`

不得使用临时命名风格替代。

---

## 四、严格边界

### 本任务允许做
- shape-family 数据扩容到正式规模
- random ET 数据扩容到正式规模
- 构建 full-scale handoff
- 训练 Frozen Mainline
- 与 `ref3/ref5/ref7/ref9/BP` 做统一正式比较
- 做少量附加比较（可选，如复跑 M1/M3 风格）但不得喧宾夺主
- 输出 family-level 与 failure-mode 分析
- 更新 `CHANGELOG_DEV.md` 与 `debug.md`

### 本任务禁止做
- 不重新探索传统前端路线
- 不做 physics consistency
- 不接入真实回波
- 不做 complex supervision
- 不做大量训练 recipe 搜索
- 不修改现有上位协议原文内容

---

## 五、本任务要回答的问题

1. 当数据达到正式规模后，Frozen Mainline 是否稳定成立？
2. Frozen Mainline 相比裸 `ref3` 是否显著提升？
3. Frozen Mainline 在统一曲线中更接近：
   - `ref5`
   - `ref7`
   - `ref9`
   - 还是部分 family 上逼近 `BP`
4. hardest families（`point_cluster / line / L-shape`）上是否依然存在清晰增益？
5. `F2/F3/F4` 是否在正式规模下继续下降？
6. 当前是否具备进入 `task_real_007` 的条件？

---

## 六、任务拆解

---

### Part A：把 shape-family 扩到正式规模

#### 目标
将当前 ET-1 / ET-2 小规模数据升级到论文正式规模。

#### 必做项
1. 按 `et_dataset_protocol.md` 扩容全部 6 类 family
2. 每类达到：
   - train = 5000
   - val = 1000
   - test = 1000
3. 继续保存：
   - GT amplitude volume
   - `ref3` coarse volume
   - scene metadata
   - split metadata

#### 输出文件
- `dataset_manifest_shape_family_full.json`

#### 注意
这一步是本任务第一优先级。若没有达到这个规模，本任务不能算完成。

---

### Part B：把 random ET supplement 扩到正式规模

#### 目标
生成论文级 random ET supplement。

#### 必做项
1. 构建 random ET full-scale 数据
2. 达到：
   - train = 5000
   - val = 1000
   - test = 1000
3. 保持 true cylindrical simulation 流程
4. 单独输出 manifest

#### 输出文件
- `dataset_manifest_random_et.json`

#### 说明
- 本任务中它主要作为资源与附加训练对照来源
- 默认主方法训练可以先不使用它
- 但它必须被正式生成并整理好

---

### Part C：构建 full-scale frozen mainline handoff

#### 目标
生成论文级训练 handoff。

#### 固定输入输出
- 输入：`Variant B ref3 coarse amplitude volume`
- 标签：`GT amplitude volume`

#### 必做项
1. 构建 full-scale train/val/test 索引
2. 保存：
   - coarse path
   - GT path
   - family label
   - split label
   - whether_random_et flag
3. 输出正式 handoff 清单

#### 输出文件
- `learning_handoff_manifest_frozen_mainline.json`

---

### Part D：训练 Frozen Mainline

#### 目标
正式训练唯一主方法。

#### 固定主方法
- **Frozen Mainline = Variant B `ref3` + 3D U-Net**
- 默认训练数据：**shape-family full-scale only**

#### 要求
1. 不再把 M1/M2/M3 当成平级主角
2. 本任务主结果必须围绕 Frozen Mainline 展开
3. 训练必须输出：
   - train/val loss 曲线
   - best checkpoint
   - final metrics
   - family-level metrics
   - representative visuals
   - inference runtime summary

#### 输出文件
- `metrics_frozen_mainline.json`
- `training_config_frozen_mainline.yaml`

---

### Part E：与 `ref3/ref5/ref7/ref9/BP` 做统一主比较

#### 目标
回答 Frozen Mainline 在传统曲线中的位置。

#### 必做项
把以下方法统一放入主表：
- `ref3`
- `ref5`
- `ref7`
- `ref9`
- `BP`
- `ref3 + learning`（Frozen Mainline）

#### 统一指标
- NMSE
- PSNR
- SSIM
- runtime
- speedup vs BP

#### 必须输出
- overall 平均
- family-level 平均
- hardest-family 子集结果
- per-sample 查询能力

#### 输出文件
- `mainline_vs_baselines_table.csv`
- `family_metrics_mainline_vs_baselines.csv`

---

### Part F：重点分析 hardest families 与 failure modes

#### 目标
不只回答 overall mean，要回答结构性改进是否仍成立。

#### hardest families
重点分析：
- `point_cluster`
- `line`
- `L-shape`

#### 重点 failure modes
继续重点统计：
- `F2`: edge break / contour fracture
- `F3`: thin-structure disappearance
- `F4`: support fragmentation

#### 必须输出
- `failure_mode_mainline_vs_baselines.csv`
- `hardest_family_summary.json`

---

### Part G：可选附加比较（降级为附加项）

#### 目标
如果资源允许，可补做附加比较，但不得喧宾夺主。

#### 可选项
1. 用 full-scale 数据复跑 `M1` 风格（shape-family + random ET）
2. 用 full-scale 数据复跑 `M3` 风格（hard-family emphasis）

#### 说明
- 这些仅用于补充判断
- 不得影响 Frozen Mainline 作为唯一主方法的主叙事
- 若不做，不影响本任务完成，只需在报告中说明

---

## 七、脚本层要求

请新增或补齐：

1. `scripts/generate_shape_family_fullscale.sh`
2. `scripts/generate_random_et_fullscale.sh`
3. `scripts/build_frozen_mainline_handoff.sh`
4. `scripts/run_frozen_mainline_training.sh`
5. `scripts/run_mainline_vs_baselines_comparison.sh`
6. `scripts/render_mainline_vs_baselines_viz.sh`

若做附加项，再增加：
- `scripts/run_optional_random_supplement_retrain.sh`
- `scripts/run_optional_hardfamily_retrain.sh`

### 脚本要求
- 必须可执行
- 必须把日志落盘
- 必须统一写入本任务 exp 目录
- 不允许手工散跑代替脚本流程

---

## 八、exp 目录规范

请为本任务创建固定产物目录：

```text
exp/task_real_006b_fullscale_mainline/<timestamp>/
````

至少输出：

1. `task_real_006b_report.md`
2. `dataset_manifest_shape_family_full.json`
3. `dataset_manifest_random_et.json`
4. `dataset_protocol_snapshot.md`
5. `data_origin_statement.md`
6. `learning_handoff_manifest_frozen_mainline.json`
7. `training_config_frozen_mainline.yaml`
8. `metrics_frozen_mainline.json`
9. `mainline_vs_baselines_table.csv`
10. `family_metrics_mainline_vs_baselines.csv`
11. `failure_mode_mainline_vs_baselines.csv`
12. `hardest_family_summary.json`
13. `tree.txt`
14. `logs/`
15. `viz/`
16. `checkpoints/`

---

## 九、`task_real_006b_report.md` 的强制结构

报告必须至少包含以下部分：

1. `Task Goal`
2. `Formal-Scale Dataset Completion Statement`
3. `Protocol / Context Files Used`
4. `Boundary Statement`
5. `Frozen Mainline Definition`
6. `Dataset Summary`
7. `Key Metrics`
8. `Mainline vs Baselines Positioning`
9. `Family-Level Results`
10. `Failure-Mode Results`
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
* mainline vs baseline 表路径
* family 表路径
* failure-mode 表路径
* curves 路径
* representative visuals 路径
* logs 路径

---

## 十、推荐执行顺序

请按以下顺序推进：

1. 阅读上位文档与 `task_real_006_report.md`
2. 冻结 Frozen Mainline 定义
3. 把 shape-family 扩容到正式规模
4. 把 random ET 扩容到正式规模
5. 构建 `learning_handoff_manifest_frozen_mainline.json`
6. 训练 Frozen Mainline
7. 与 `ref3/ref5/ref7/ref9/BP` 做统一比较
8. 统计 hardest-family 与 failure-mode 结果
9. 生成标准化可视化
10. 生成 `task_real_006b_report.md`
11. 更新 `CHANGELOG_DEV.md` 与 `debug.md`
12. 确保 git 工作区可提交

---

## 十一、验收标准

本任务只有在以下条件全部满足时才算完成：

1. shape-family 每类达到 `5000/1000/1000`
2. random ET 达到 `5000/1000/1000`
3. 所有数据都证明来自 true 3D cylindrical simulation
4. Frozen Mainline 训练完成并结果可用
5. 与 `ref3/ref5/ref7/ref9/BP` 的正式比较完成
6. hardest families 上 Frozen Mainline 明显优于裸 `ref3`
7. `F2/F3/F4` 继续有清晰下降
8. 能明确判断 Frozen Mainline 位于传统曲线哪一档
9. 已输出标准化 3D 图、成像对比图、曲线图
10. 已生成 `task_real_006b_report.md`
11. git 工作区保持可提交状态

---

## 十二、最终判断要求

在最终报告中，请明确回答：

1. 是否已达到 master-document 要求的数据量级？
2. Frozen Mainline 是否已经成为正式可用主方法？
3. Frozen Mainline 在统一曲线中更接近 `ref5`、`ref7`、`ref9` 还是局部逼近 `BP`？
4. 当前是否已经 ready for physics-consistency stage？
5. `Ready for physics-consistency stage?` 回答必须是：

   * `yes`
   * `no`
   * `conditional`

---

## 十三、最终终端汇报格式

任务完成后，请按如下格式做最终汇报：

1. `PROJECT_ROOT = ...`
2. `formal-scale dataset completion = pass / partial pass / fail`
3. `true 3D cylindrical data proof = pass / partial pass / fail`
4. `Frozen Mainline training = pass / partial pass / fail`
5. `mainline vs baselines comparison = pass / partial pass / fail`
6. `family-level positioning = pass / partial pass / fail`
7. `failure-mode positioning = pass / partial pass / fail`
8. `visualization outputs = pass / partial pass / fail`
9. `Artifacts = ...`
10. `Ready for physics-consistency stage? = yes / no / conditional`
11. `Suggested next task = task_real_007 (...)`

---

## 十四、提醒

* 这次不再以 M1/M2/M3 差异为主问题
* 这次的主问题是：正式规模 + 固定主方法 + 统一曲线定位
* Frozen Mainline 默认采用：

  * Variant B
  * `ref3`
  * shape-family full-scale only
* 本任务结束后，才适合进入 `task_real_007`

```
```

