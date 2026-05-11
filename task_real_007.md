

````markdown
# task_real_007：physics-consistency controlled upgrade on top of frozen 800-scale baseline

你现在服务于项目：

- `PROJECT_ROOT = /home/superws/2026_Projects/Codex_reference_plane_real`
- `CONTEXT = /home/superws/2026_Projects/Codex_reference_plane_real/CONTEXT`
- `workspace = /home/superws/2026_Projects/Codex_reference_plane_real/workspace`

已完成：
- `task_real_006d`：800/100/100 family-aware formal dataset + OOD credibility validation
- `task_real_006e`：Main Test + 3 OOD 的 six-method 全评测补齐

当前已知状态（来自 `006d/006e`）：
- Frozen Mainline 已冻结为：
  - Front-end = Variant B
  - Physics backbone = ref3
  - Second stage = 3D U-Net
  - Input = ref3 coarse amplitude volume
  - Target = GT amplitude volume
- 800-scale 主集与 3 个 OOD 集已冻结
- `006e` 已证明：Ours 在 Main Test、Unseen-Parameter OOD、Leave-One-Family-Out Focused OOD、Random-ET OOD 上都排 `1/6`
- 当前任务不再重复 six-method 主评测矩阵；007 只做 **baseline vs physics-consistency new model** 的受控比较

本任务进入：

> **Phase ET-3：physics-consistency controlled comparison on frozen 800-scale protocol**

---

## 一、任务定位

本任务的唯一目标是：

> 在不改变数据协议、不改变前端、不更换主结构的前提下，
> 仅在 Frozen Mainline（ref3 + 3D U-Net base）上加入 physics-consistency，
> 构造一个新的模型版本，
> 并与 base 模型做一一受控比较，
> 判断它是否能在某些测试集、某些指标、某些 failure modes 上进一步提升。

本任务不是 six-method 再评测任务，不是新前端任务，不是新数据集任务。

---

## 二、必须遵守的上位文档

开始前必须阅读并遵守：

1. `CONTEXT/real_cylindrical_master_document_with_physics_consistency.md`
2. `CONTEXT/simulation_protocol.md`
3. `CONTEXT/reference_surface_strategy.md`
4. `CONTEXT/dataset_protocol.md`
5. `CONTEXT/et_dataset_protocol.md`
6. `CONTEXT/et_dataset_protocol_800.md`
7. `CONTEXT/visualization_protocol.md`
8. `PROMPTS/system_rules.md`
9. `PROMPTS/review_checklist.md`
10. `exp/task_real_006d_800_formal/*/task_real_006d_report.md`
11. `exp/task_real_006e_comprehensive_eval/*/task_real_006e_report.md`

此外，必须继续参考：
12. `Efficient physics-based learned reconstruction methods for real-time 3D near-field MIMO radar imaging.pdf`
13. `面向雷达学习成像的物理一致性文献检索与研究机会分析报告.md`

不得绕过这些文档自定协议。

---

## 三、核心边界（非常重要）

### 硬约束 1：只比较两个模型
本任务只允许比较以下两个模型：

#### A. Baseline-Ours
- Frozen Mainline
- `Variant B + ref3 + 3D U-Net`
- image-only supervision
- 直接复用 `006d/006e` 的 best checkpoint 作为 baseline 参照

#### B. Ours-PC
- 在 Baseline-Ours 的训练框架上加入 physics-consistency 后得到的新模型
- 仍然是 `Variant B + ref3 + 3D U-Net`
- 只改变训练目标，不改变主前端和主 second-stage 结构

禁止：
- 再引入第三、第四个新模型
- 再回到 M1/M2/M3
- 再做 six-method 全矩阵重跑

---

### 硬约束 2：冻结数据协议与测试集合
必须原样复用 `006d/006e` 的冻结数据：

#### 主集
- `Main Train = 800`
- `Main Val = 100`
- `Main Test = 100`

#### 三类 OOD
- `Unseen-Parameter OOD = 100`
- `Leave-One-Family-Out Focused OOD = 100`
- `Random-ET OOD = 100`

禁止：
- 改 split
- 增删 family
- 重定义 OOD
- 重采样数据

---

### 硬约束 3：不得更换前端或主结构
必须保持：

- Front-end = `Variant B`
- Physics backbone = `ref3`
- Second stage = 当前 `3D U-Net`（UNet3DSmall）
- 输入 = `ref3` coarse amplitude volume
- 监督标签 = GT amplitude volume

禁止：
- 换成 `ref5/ref7/ref9`
- 换 second-stage 主结构
- 换成 transformer / larger U-Net / unrolled network
- 加 complex supervision
- 加多通道几何输入作为本轮主变量

---

### 硬约束 4：physics-consistency 必须走“最小增量”路线
本轮 007 的主变量只能是 **loss 层面的 physics-consistency**。

### 允许的主形式
#### P1（必做）
**sampled forward echo consistency**
- 网络输出 `x_hat`
- 用柱面前向模型 `F_cyl(x_hat)` 得到预测回波 `y_hat`
- 在采样后的 measurement subset `Ω` 上与原始仿真回波 `y` 比较
- 定义 `L_echo` 或 echo-domain NMSE

#### P2（可选增强）
**geometry-aware consistency**
- 在 support / boundary / high-confidence regions 上加权一致性
- 在 P1 已成立时再尝试

### 不允许作为首轮主方法
- full giant differentiable simulator
- surrogate forward model
- over-heavy unrolled framework
- 完全 feature-level latent consistency 作为主 consistency
- 大幅度网络结构改造

---

### 硬约束 5：训练目标必须显式写成
训练目标必须采用：

`L_total = L_image + lambda_pc * L_physics_consistency`

其中：
- `L_image`：当前 baseline 使用的主图像域损失
- `L_physics_consistency`：forward echo consistency
- `lambda_pc`：权重系数

本轮必须把 `lambda_pc`、采样子集策略、是否 geometry-aware 等配置清楚落盘。

---

### 硬约束 6：评测只做 base vs PC 的受控比较
本任务的评测矩阵固定为：

- Baseline-Ours
- Ours-PC

在以下 4 个集合上比较：
- Main Test
- Unseen-Parameter OOD
- Leave-One-Family-Out Focused OOD
- Random-ET OOD

### 指标必须包含
- `NMSE`
- `PSNR`
- `SSIM`
- `runtime`
- `speedup_vs_BP`

### 额外重点统计
- `F2`
- `F3`
- `F4`
- hardest families：
  - `point_cluster`
  - `line`
  - `L-shape`

### 说明
- six-method 基线矩阵不必重跑
- 但报告中必须引用 `006e` 的 frozen six-method 结果作为背景参照

---

### 硬约束 7：必须确认 git 同步更新
本任务结束时必须完成 git 记录更新，至少包括：

1. 更新：
   - `CHANGELOG_DEV.md`
   - `debug.md`
2. `git status` 必须可解释
3. 生成本任务的本地 commit
4. 在最终汇报中明确给出：
   - commit hash
   - `git status` 结果
   - 若配置了远程并允许 push，则执行 push 并说明结果
   - 若未配置远程或不允许 push，必须明确写“local commit only”

### 禁止
- 不记录代码变更来源
- 不汇报 commit hash
- 只改文件不入 git

---

## 四、本任务要回答的问题

1. 在 Main Test 上，physics-consistency 是否优于 baseline？
2. 在 3 个 OOD 集上，physics-consistency 是否优于 baseline？
3. 哪些指标最先受益：
   - NMSE
   - PSNR
   - SSIM
   - F2/F3/F4
4. 哪些 hardest families 最先受益：
   - point_cluster
   - line
   - L-shape
5. 引入 consistency 后，runtime 是否基本保持不变？
6. 是否值得把 physics-consistency 写入论文主方法而不是附录增强项？

---

## 五、任务拆解

---

### Part A：冻结 baseline 与训练输入

#### 目标
明确 Baseline-Ours 的来源，并锁死本轮 comparison 的基线。

#### 必做项
1. 复用 `006d/006e` 的 best checkpoint
2. 记录 baseline checkpoint 路径
3. 记录 baseline 的 main + OOD 指标引用路径
4. 生成 baseline manifest

#### 输出文件
- `baseline_reference_manifest_007.json`

---

### Part B：实现 P1 = sampled forward echo consistency（必做）

#### 目标
在当前训练代码中引入最小可行的一致性项。

#### 必做项
1. 网络输出 `x_hat`
2. 用柱面 forward model 生成 `y_hat`
3. 采样 measurement subset `Ω`
4. 定义：
   - `L_echo = || y_hat_Ω - y_Ω ||^2`
   - 或 echo-domain NMSE
5. 总损失：
   - `L_total = L_image + lambda_pc * L_echo`

#### 必须显式记录
- `lambda_pc`
- 子集采样方式：
  - angles
  - frequencies
  - heights
- 每次采样规模
- 采样是否固定 / 随机
- forward 一致性计算代价

#### 输出文件
- `consistency_config_P1.yaml`

---

### Part C：实现 P2 = geometry-aware consistency（可选增强）

#### 目标
若 P1 有效，再增加 geometry-aware weighting。

#### 可行方式
- 对 support 区域加权
- 对边界区域加权
- 对 high-energy scattering 区域加权
- 对 hardest families 的结构关键区域做加权

#### 要求
- 只能在 P1 已完成基础上做
- 若资源紧张，可不执行
- 若不执行，必须在报告中解释

#### 输出文件
- `consistency_config_P2.yaml`（若执行）

---

### Part D：训练矩阵

#### 必做
- `Baseline-Ours`：直接引用，不重训
- `Ours-PC-P1`：必须训练

#### 可选
- `Ours-PC-P2`：若资源允许再训练

#### 明确说明
- 这不是 recipe search
- 只做“baseline vs consistency”受控比较

---

### Part E：统一评测

#### 目标
在 4 个固定数据集上，比较：
- Baseline-Ours
- Ours-PC-P1
- Ours-PC-P2（若有）

#### 指标
- NMSE
- PSNR
- SSIM
- runtime
- speedup_vs_BP

#### 额外重点统计
- F2/F3/F4
- hardest-family metrics

#### 输出文件
- `metrics_baseline_vs_pc_main.csv`
- `metrics_baseline_vs_pc_unseen_param_ood.csv`
- `metrics_baseline_vs_pc_leave_one_family_out_ood.csv`
- `metrics_baseline_vs_pc_random_et_ood.csv`
- `failure_mode_pc_improvement.csv`
- `hardest_family_pc_improvement.csv`

---

### Part F：可视化

#### 必须遵守
- `visualization_protocol.md`

#### 核心图
1. `baseline_vs_pc_main_metrics.png`
2. `baseline_vs_pc_ood_metrics.png`
3. `baseline_vs_pc_runtime_speedup.png`
4. `baseline_vs_pc_failure_modes.png`
5. `baseline_vs_pc_hardest_families.png`
6. `baseline_vs_pc_frontier_ood.png`
7. `pc_best_case_panel.png`
8. `pc_failure_case_panel.png`

### 说明
- 这次不再做 six-method 大总览图
- 重点是 baseline vs PC 的增量效果图

---

### Part G：git 同步更新

#### 必做项
1. 更新 `CHANGELOG_DEV.md`
2. 更新 `debug.md`
3. 执行 git add / commit
4. 若允许且配置了 remote，则尝试 push
5. 在最终报告中写明：
   - commit hash
   - git status
   - push 是否成功

#### 输出文件
- `git_update_summary.md`

---

## 六、脚本层要求

请新增或补齐：

1. `scripts/run_pc_training_P1.sh`
2. `scripts/run_pc_training_P2.sh`（若执行）
3. `scripts/run_pc_eval_main.sh`
4. `scripts/run_pc_eval_ood.sh`
5. `scripts/render_pc_comparison_viz.sh`
6. `scripts/update_git_and_record_007.sh`

### 脚本要求
- 必须可执行
- 必须把日志落盘
- 必须统一写入本任务 exp 目录
- 不允许手工散跑代替脚本流程

---

## 七、exp 目录规范

请为本任务创建固定产物目录：

```text
exp/task_real_007_physics_consistency/<timestamp>/
````

至少输出：

1. `task_real_007_report.md`
2. `baseline_reference_manifest_007.json`
3. `consistency_config_P1.yaml`
4. `consistency_config_P2.yaml`（若执行）
5. `metrics_baseline_vs_pc_main.csv`
6. `metrics_baseline_vs_pc_unseen_param_ood.csv`
7. `metrics_baseline_vs_pc_leave_one_family_out_ood.csv`
8. `metrics_baseline_vs_pc_random_et_ood.csv`
9. `failure_mode_pc_improvement.csv`
10. `hardest_family_pc_improvement.csv`
11. `git_update_summary.md`
12. `tree.txt`
13. `logs/`
14. `viz/`
15. `checkpoints/`

---

## 八、`task_real_007_report.md` 的强制结构

报告必须至少包含以下部分：

1. `Task Goal`
2. `Frozen Baseline Reused`
3. `Protocol / Context Files Used`
4. `Boundary Statement`
5. `Physics-Consistency Design`
6. `Training Matrix`
7. `Main Test Comparison`
8. `OOD Comparison`
9. `Failure-Mode Improvement`
10. `Hardest-Family Improvement`
11. `Visual Outputs`
12. `Git Update Summary`
13. `Remaining Issues`
14. `Is Physics-Consistency Worth Keeping?`
15. `Suggested Next Task`

并且必须包含固定小节：

### Key file paths for ChatGPT controller

集中列出：

* report 路径
* baseline reference 路径
* consistency config 路径
* metrics 路径
* failure-mode 路径
* family 路径
* curves 路径
* representative visuals 路径
* git summary 路径
* logs 路径

---

## 九、推荐执行顺序

请按以下顺序推进：

1. 阅读 `006d/006e` 报告
2. 冻结 baseline 参照
3. 实现 P1 consistency loss
4. 训练 Ours-PC-P1
5. 在 4 个数据集上做 baseline vs PC 评测
6. 若 P1 有效，再做 P2
7. 生成标准化可视化
8. 更新 git 并记录
9. 生成 `task_real_007_report.md`
10. 确保 git 工作区可提交、可追踪

---

## 十、验收标准

本任务只有在以下条件全部满足时才算完成：

1. Baseline-Ours 与 Ours-PC-P1 完成受控比较
2. 4 个数据集都完成 baseline vs PC 评测
3. 5 个指标都齐全：

   * NMSE
   * PSNR
   * SSIM
   * runtime
   * speedup_vs_BP
4. F2/F3/F4 比较完成
5. hardest-family 比较完成
6. 已输出标准化增量图集
7. git 已更新并可追踪
8. 已生成 `task_real_007_report.md`

---

## 十一、最终判断要求

在最终报告中，请明确回答：

1. P1 是否优于 baseline？
2. P2（若执行）是否进一步优于 P1？
3. 哪些数据集、哪些指标、哪些 failure modes 最先受益？
4. runtime 是否基本保持不变？
5. physics-consistency 是否值得保留为论文主方法组成部分？

---

## 十二、最终终端汇报格式

任务完成后，请按如下格式做最终汇报：

1. `PROJECT_ROOT = ...`
2. `baseline frozen reuse = pass / partial pass / fail`
3. `P1 training = pass / partial pass / fail`
4. `P2 training = pass / partial pass / fail`
5. `main test baseline-vs-pc eval = pass / partial pass / fail`
6. `OOD baseline-vs-pc eval = pass / partial pass / fail`
7. `failure-mode comparison = pass / partial pass / fail`
8. `hardest-family comparison = pass / partial pass / fail`
9. `visualization outputs = pass / partial pass / fail`
10. `git synchronization = pass / partial pass / fail`
11. `Artifacts = ...`
12. `Is Physics-Consistency Worth Keeping? = yes / no / conditional`

---

## 十三、提醒

* 这次只比较 **base vs PC**
* 不再重复 six-method 全矩阵
* 不改数据，不改前端，不换主结构
* 核心是验证：**物理一致性是否能在当前强基线上，再推一步**

```

如果你愿意，我下一条还可以继续给你一版更简短的“极简执行版 007 提示词”，适合直接粘贴到 Codex CLI。
```

