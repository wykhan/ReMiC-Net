# task_real_008：build and evaluate ReMiC-Net on frozen datasets

你现在服务于项目：

- `PROJECT_ROOT = /home/superws/2026_Projects/Codex_reference_plane_real`
- 当前仓库分支：`master`
- 当前版本锚点提交：`8940642`
- 当前 Codex 默认模型：`gpt-5.4`
- 本轮为保证实验一致性，继续沿用 `gpt-5.4`，不得擅自切换模型版本

已完成的主线阶段（只作为背景，不要重跑）：
- `task_real_004 / 004b / 004c`：accelerated cylindrical front-end, wrap hardening, Variant B freeze
- `task_real_005 / 006 / 006b / 006c / 006d / 006e`：ET 主实验、Frozen Mainline、800/100/100 formal 协议、Main Test + 3 OOD 完整评测
- `task_real_007 / 007b`：physics-consistency P1 / geometry-aware P2 分支探索

当前新任务进入：

> **Phase ReMiC-1：build and evaluate ReMiC-Net on frozen datasets**

---

## 一、任务定位

本任务的唯一目标是：

> 在既有 frozen datasets 和 Frozen Mainline 基线上，
> 构建 **ReMiC-Net with RSB-FiLM**，
> 并与 **原始 residual 3D U-Net baseline** 做一一受控比较，
> 判断 ReMiC-Net 是否能在 Main Test 与既有 OOD 集上取得更好的性能，
> 尤其是在 reference-surface mismatch 更强的区域取得更明显收益。

本任务不是：
- six-method 全矩阵任务
- physics-consistency 任务
- 新数据集任务
- 更大 backbone 搜索任务

---

## 二、必须遵守的上位文档

开始前必须阅读并遵守：

1. `CONTEXT/real_cylindrical_master_document_rsb_film_updated20260510.md`
2. `CONTEXT/model_structure_rsb_film_updated20260510.md`
3. `CONTEXT/reference_surface_strategy_rsb_film_updated20260510.md`
4. `CONTEXT/simulation_protocol_rsb_film_updated20260510.md`
5. `CONTEXT/visualization_protocol.md`（若存在）
6. `PROMPTS/system_rules.md`
7. `PROMPTS/review_checklist.md`

并且必须复用现有实验产物：
8. `exp/task_real_006d_800_formal/...`
9. `exp/task_real_006e_comprehensive_eval/...`
10. `exp/task_real_007_physics_consistency/...`
11. `exp/task_real_007b_geometry_aware_consistency/...`

不得绕过这些文档自定协议。

---

## 三、核心边界（必须严格遵守）

### 硬约束 1：数据协议完全冻结
本任务必须原样复用既有已建好的 frozen datasets，不允许重新设计或重采样。

优先采用当前最正式且最可复现实验协议：
- Main Train / Val / Test
- 既有 OOD 集合（若已冻结）
- 既有 `X_ref3`
- 既有 GT amplitude labels

禁止：
- 改 split
- 增删 family
- 重新构建主训练集
- 重定义 OOD
- 混用不同任务中的不兼容 split

若存在多套历史可用数据协议，必须在报告中明确写明本轮采用的唯一协议来源。

---

### 硬约束 2：物理骨干完全冻结
本任务必须保持：

- Front-end / physics backbone = `ref3`
- 主输入图像 = `X_ref3`
- 不允许切换为 `ref5/ref7/ref9`
- 不允许从 raw echo 端到端直接训练黑盒网络

---

### 硬约束 3：本轮只比较两个模型
本任务只允许比较：

#### A. Baseline-U-Net
- `ref3 + residual 3D U-Net`
- 无 Geometry branch
- 无 FiLM / RSB-FiLM
- 优先复用既有 Frozen Mainline checkpoint
- 若必须重训，必须说明原因，并严格保持训练协议对齐

#### B. ReMiC-Net
- `ref3 + [Mshell, δρ, Pcyc] + residual 3D U-Net + RSB-FiLM`
- 当前唯一有效版本为 **RSB-FiLM**
- 输出仅为 residual head

禁止：
- 引入第三、第四个新模型作为主比较
- 再引入 generic FiLM 作为本轮主结果模型
- 引入 support head / Dice / BCE / valid FOV mask / support prior
- 引入 physics-consistency
- 更换 backbone 或扩大网络规模

---

### 硬约束 4：δρ 输入必须使用 raw
用户已显式裁决：

> **`δρ` 网络输入一律使用 raw signed deviation in meter。**

因此本任务必须采用：

- `delta_rho_input(v) = delta_rho_raw(v)`

同时：
- `Pcyc` 仍由 `delta_rho_raw` 计算
- 不允许把 `δρ` 归一化到 `[-1, 1]`
- 所有 config / 代码 / 报告都必须显式写明：
  - `delta_rho_input = raw_meter`

---

### 硬约束 5：Geometry branch metadata 必须严格按冻结规则生成
必须使用：

- `Mshell`
- `delta_rho_raw`
- `Pcyc`

其中：

#### `Mshell`
- 对 `ref3` 使用 3-channel one-hot shell allocation map

#### `delta_rho_raw`
- 定义：
  - `delta_rho(v) = rho(v) - rho_ref_star(v)`
- 单位：meter
- 直接作为网络输入

#### `Pcyc`
- 按冻结公式由 `delta_rho_raw` 生成
- 必须复用 protocol 中冻结的：
  - `fc`
  - `lambda_c`
  - `k_c^(2w)`

不得用旧版 metadata 或隐式替代。

---

### 硬约束 6：ReMiC-Net 结构必须严格冻结
本任务必须实现当前冻结版 ReMiC-Net：

#### 输入
- 主输入：`X_ref3`
- Geometry branch：`[Mshell, delta_rho_raw, Pcyc]`

#### 核心结构
- 主干：Residual 3D U-Net
- Geometry branch encoder
- Fusion：**RSB-FiLM**
- 输出：Residual head only

#### 输出
- `Δx_hat`
- 最终：
  - `x_hat = X_ref3 + Δx_hat`

禁止：
- final residual physical gate
- support mask head
- 多输出头
- valid FOV mask 输入
- support prior 输入

---

### 硬约束 7：RSB-FiLM 必须严格按冻结口径实现
必须使用：

- bounded affine modulation
- deterministic phase-mismatch envelope

默认参数：
- `epsilon_m = 0.05`
- `alpha_gamma = 0.5`
- `alpha_beta = 0.1`

默认放置层级：
- `E2`
- `E3`
- `B`
- `D3`
- `D2`

不得：
- 调制浅层 `E0/E1`
- 调制输出附近 `D1/D0`
- 直接调制 skip tensors
- 悄悄改动默认 envelope 公式

如工程上必须偏离默认设置，必须先在报告中解释，再执行。

---

### 硬约束 8：训练目标保持当前冻结主损失
默认主损失：

#### 简版（优先）
- `L = ||Δx_hat - Δx*||_1`

#### 可选正式版
- `L = lambda_res * L1 + lambda_ssim * (1 - SSIM)`

本轮不允许加入：
- support BCE / Dice
- echo consistency
- gamma/beta regularization loss
- complex echo-domain loss

---

### 硬约束 9：评测重点是 ReMiC-Net vs Baseline-U-Net
本轮不重复 six-method 全矩阵。

必须至少在以下集合上比较：

- Main Test
- 若已有 OOD，则全部复用：
  - Unseen-Parameter OOD
  - Leave-One-Family-Out Focused OOD
  - Random-ET OOD

#### 主指标必须包含
- `NMSE`
- `PSNR`
- `SSIM`
- `runtime`
- `speedup_vs_BP`

#### 额外必须做的诊断分析
- 按 `|delta_rho|` 分组的 NMSE / PSNR / SSIM
- 按 `|Pcyc|` 分组的 NMSE / PSNR / SSIM
- `|Pcyc| <= 0.25` vs `|Pcyc| > 0.25` 的误差对比
- hardest families（若标签可用）：
  - `point_cluster`
  - `line`
  - `L-shape`

本轮核心不是只看 overall mean，而是看：

> ReMiC-Net 是否在 reference-surface mismatch 更强的区域更有优势。

---

### 硬约束 10：必须更新 git 记录
本任务结束时必须完成 git 记录更新，至少包括：

1. 更新：
   - `CHANGELOG_DEV.md`
   - `debug.md`
2. `git status` 必须可解释
3. 生成本任务本地 commit
4. 在最终汇报中明确写：
   - commit hash
   - git status
   - 若无远端：`local commit only`
   - 若有远端且允许 push：说明 push 结果

---

## 四、本任务要回答的问题

1. ReMiC-Net 是否优于原始 residual 3D U-Net baseline？
2. 提升是否主要集中在：
   - 高 `|delta_rho|` 区域
   - 高 `|Pcyc|` 区域
   - `|Pcyc| > 0.25` 区域
3. ReMiC-Net 是否在 hardest families 上更有优势？
4. RSB-FiLM 是否在不显著增加推理时间的前提下带来收益？
5. 结果是否支持把 ReMiC-Net 作为论文主方法，而 plain residual 3D U-Net 作为 baseline？

---

## 五、任务拆解

### Part A：冻结 baseline 引用与训练协议
#### 目标
明确本轮比较所用的 baseline 版本。

#### 必做项
1. 定位 Baseline-U-Net 的代码实现 / config / checkpoint
2. 若已有 best checkpoint，则直接复用
3. 若无可直接复用 checkpoint，则在完全相同训练协议下补训 baseline
4. 生成 baseline reference manifest

#### 输出文件
- `baseline_reference_manifest_008.json`

---

### Part B：构建 ReMiC-Net 数据输入
#### 目标
在既有数据集上生成 ReMiC-Net 所需输入。

#### 必做项
1. 复用既有 `X_ref3`
2. 为每个样本生成：
   - `Mshell`
   - `delta_rho_raw`
   - `Pcyc`
3. 明确记录：
   - `delta_rho_input = raw_meter`
4. 检查 shape / dtype / channel order
5. 生成 metadata manifest

#### 输出文件
- `remicnet_input_manifest_008.json`

---

### Part C：实现 ReMiC-Net with RSB-FiLM
#### 目标
把当前冻结版 ReMiC-Net 真正落到代码中。

#### 必做项
1. 保留 residual 3D U-Net 主体
2. 新增 Geometry branch encoder
3. 新增 RSB-FiLM module
4. 按冻结位置插入：
   - `E2`
   - `E3`
   - `B`
   - `D3`
   - `D2`
5. 输出 residual only

#### 输出文件
- `remicnet_config_008.yaml`

---

### Part D：训练 ReMiC-Net
#### 目标
在与 baseline 对齐的协议下训练 ReMiC-Net。

#### 必做项
1. 与 baseline 使用一致的 train/val/test
2. 尽量保持：
   - optimizer
   - epoch 数
   - early stopping 规则
   - batch size
   - 数据增强口径
   对齐
3. 保存 best checkpoint
4. 落盘训练曲线

#### 输出文件
- `metrics_remicnet_trainval_008.json`
- `checkpoints/remicnet/best.pt`

---

### Part E：统一评测
#### 目标
对 Baseline-U-Net 和 ReMiC-Net 做受控比较。

#### 数据集
- Main Test
- 所有既有 OOD（若存在）

#### 指标
- NMSE
- PSNR
- SSIM
- runtime
- speedup_vs_BP

#### 诊断
- grouped by `|delta_rho|`
- grouped by `|Pcyc|`
- grouped by `|Pcyc| <= 0.25` vs `> 0.25`
- hardest-family metrics（若数据集含 family 标签）

#### 输出文件
- `metrics_baseline_vs_remicnet_main.csv`
- `metrics_baseline_vs_remicnet_unseen_param_ood.csv`
- `metrics_baseline_vs_remicnet_leave_one_family_out_ood.csv`
- `metrics_baseline_vs_remicnet_random_et_ood.csv`
- `grouped_metrics_by_abs_delta_rho.csv`
- `grouped_metrics_by_abs_pcyc.csv`
- `grouped_metrics_by_pcyc_quarter_pi.csv`
- `hardest_family_baseline_vs_remicnet.csv`

---

### Part F：可视化
#### 必须遵守
- 若已有 `visualization_protocol.md`，必须遵守
- 统一 normalization / colormap / slice rule

#### 核心图
1. `baseline_vs_remicnet_main_metrics.png`
2. `baseline_vs_remicnet_ood_metrics.png`
3. `baseline_vs_remicnet_runtime_speedup.png`
4. `grouped_error_by_abs_delta_rho.png`
5. `grouped_error_by_abs_pcyc.png`
6. `grouped_error_by_pcyc_quarter_pi.png`
7. `baseline_vs_remicnet_hardest_families.png`
8. `remicnet_best_case_panel.png`
9. `remicnet_failure_case_panel.png`

重点不是 six-method 大总览，而是：

> ReMiC-Net 相比 plain residual 3D U-Net，是否在 mismatch-aware 区域更强。

---

### Part G：git 同步更新
#### 必做项
1. 更新 `CHANGELOG_DEV.md`
2. 更新 `debug.md`
3. 执行 git add / commit
4. 若允许且配置了 remote，则尝试 push
5. 记录 git 结果

#### 输出文件
- `git_update_summary_008.md`

---

## 六、脚本层要求

请新增或补齐：

1. `scripts/build_remicnet_inputs_008.sh`
2. `scripts/run_remicnet_training_008.sh`
3. `scripts/run_remicnet_eval_main.sh`
4. `scripts/run_remicnet_eval_ood.sh`
5. `scripts/render_remicnet_comparison_viz.sh`
6. `scripts/update_git_and_record_008.sh`

### 脚本要求
- 必须可执行
- 必须把日志落盘
- 必须统一写入本任务 exp 目录
- 不允许手工散跑代替脚本流程

---

## 七、exp 目录规范

请为本任务创建固定产物目录：

`exp/task_real_008_remicnet_eval/<timestamp>/`

至少输出：

1. `task_real_008_report.md`
2. `baseline_reference_manifest_008.json`
3. `remicnet_input_manifest_008.json`
4. `remicnet_config_008.yaml`
5. `metrics_remicnet_trainval_008.json`
6. `metrics_baseline_vs_remicnet_main.csv`
7. `metrics_baseline_vs_remicnet_unseen_param_ood.csv`
8. `metrics_baseline_vs_remicnet_leave_one_family_out_ood.csv`
9. `metrics_baseline_vs_remicnet_random_et_ood.csv`
10. `grouped_metrics_by_abs_delta_rho.csv`
11. `grouped_metrics_by_abs_pcyc.csv`
12. `grouped_metrics_by_pcyc_quarter_pi.csv`
13. `hardest_family_baseline_vs_remicnet.csv`
14. `git_update_summary_008.md`
15. `tree.txt`
16. `logs/`
17. `viz/`
18. `checkpoints/`

---

## 八、`task_real_008_report.md` 的强制结构

报告必须至少包含以下部分：

1. `Task Goal`
2. `Frozen Baseline Reused`
3. `Protocol / Context Files Used`
4. `Boundary Statement`
5. `ReMiC-Net Construction`
6. `Input Metadata Construction`
7. `Training Setup`
8. `Main Test Comparison`
9. `OOD Comparison`
10. `Mismatch-Aware Diagnostic Results`
11. `Hardest-Family Results`
12. `Visual Outputs`
13. `Git Update Summary`
14. `Remaining Issues`
15. `Is ReMiC-Net Worth Keeping as Main Method?`
16. `Suggested Next Task`

并且必须包含固定小节：

### Key file paths for ChatGPT controller
集中列出：
- report 路径
- baseline 路径
- remicnet config 路径
- input manifest 路径
- metrics 路径
- grouped diagnosis 路径
- figures 路径
- git summary 路径
- logs 路径

---

## 九、推荐执行顺序

请按以下顺序推进：

1. 阅读四份新版冻结文档
2. 锁定 baseline 引用
3. 构建 `Mshell + delta_rho_raw + Pcyc`
4. 实现 ReMiC-Net with RSB-FiLM
5. 训练 ReMiC-Net
6. 在 Main Test + 既有 OOD 上做 baseline vs ReMiC-Net 比较
7. 输出 `|delta_rho| / |Pcyc|` 诊断图表
8. 生成标准化图集
9. 更新 git 并记录
10. 生成 `task_real_008_report.md`

---

## 十、验收标准

本任务只有在以下条件全部满足时才算完成：

1. Baseline 与 ReMiC-Net 完成受控比较
2. `delta_rho_input = raw_meter` 已显式落实
3. Main Test 评测完成
4. 若 OOD 已存在，则 OOD 评测完成
5. 主指标齐全：
   - NMSE
   - PSNR
   - SSIM
   - runtime
   - speedup_vs_BP
6. `|delta_rho| / |Pcyc|` 诊断完成
7. hardest-family 比较完成（若数据集支持）
8. 已输出标准化图集
9. git 已更新并可追踪
10. 已生成 `task_real_008_report.md`

---

## 十一、最终判断要求

在最终报告中，请明确回答：

1. ReMiC-Net 是否优于 Baseline-U-Net？
2. 提升是否主要集中在高 mismatch 区域？
3. `Pcyc + RSB-FiLM` 是否带来可解释收益？
4. runtime 是否基本保持不变？
5. ReMiC-Net 是否值得作为论文主方法？

---

## 十二、最终终端汇报格式

任务完成后，请按如下格式做最终汇报：

1. `PROJECT_ROOT = ...`
2. `baseline frozen reuse = pass / partial pass / fail`
3. `remicnet input construction = pass / partial pass / fail`
4. `delta_rho raw-input freeze = pass / partial pass / fail`
5. `ReMiC-Net training = pass / partial pass / fail`
6. `main test baseline-vs-remicnet eval = pass / partial pass / fail`
7. `OOD baseline-vs-remicnet eval = pass / partial pass / fail`
8. `mismatch-aware diagnosis = pass / partial pass / fail`
9. `hardest-family comparison = pass / partial pass / fail`
10. `visualization outputs = pass / partial pass / fail`
11. `git synchronization = pass / partial pass / fail`
12. `Artifacts = ...`
13. `Is ReMiC-Net Worth Keeping as Main Method? = yes / no / conditional`

---

## 十三、提醒

- 这次只做 **Baseline-U-Net vs ReMiC-Net**
- 不再重复 six-method 全矩阵
- 不改数据，不改前端，不换主结构
- `δρ` 输入必须用 raw
- 当前唯一有效版本是 **RSB-FiLM**
- 核心是验证：**ReMiC-Net 是否能在既有 Frozen Mainline 基础上，凭借 reference-surface-aware metadata + RSB-FiLM 取得更强的 mismatch compensation**
