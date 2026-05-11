

# task_real_007b：geometry-aware physics-consistency refinement on frozen 800-scale protocol

你现在服务于项目：

- `PROJECT_ROOT = /home/superws/2026_Projects/Codex_reference_plane_real`
- `CONTEXT = /home/superws/2026_Projects/Codex_reference_plane_real/CONTEXT`
- `workspace = /home/superws/2026_Projects/Codex_reference_plane_real/workspace`

已完成：
- `task_real_006d`：800/100/100 family-aware formal dataset + OOD credibility validation
- `task_real_006e`：Main Test + 3 OOD 的 six-method 完整评测
- `task_real_007`：P1 sampled forward echo consistency on top of frozen baseline

当前已知状态（来自 `task_real_007_report.md`）：
- Baseline-Ours（Frozen Mainline）仍是当前默认主线
- P1 = sampled forward echo consistency 已证明：
  - Main Test aggregate 有很小提升
  - Leave-One-Family-Out / Random-ET OOD 有小幅改善
  - F2/F3/F4 在 Main Test 和 Unseen-Parameter OOD 上显著下降
- 但 P1 还不足以直接取代 Frozen Mainline 默认主线
- 下一步最自然的方向是：
  - **geometry-aware / support-aware consistency**
  - 在 hardest families / OOD / structure failures 上进一步推进

本任务进入：

> **Phase ET-3b：geometry-aware physics-consistency refinement on frozen 800-scale baseline**

---

## 一、任务定位

本任务的唯一目标是：

> 在完全冻结的数据协议、前端、物理骨干和主 second-stage 结构下，
> 把 `task_real_007` 的 P1 sampled forward echo consistency
> 升级为 **P2 = geometry-aware / support-aware consistency**，
> 并继续做 **baseline vs P1 vs P2** 的受控比较，
> 判断 P2 是否能把 007 已观察到的结构性收益，
> 进一步转化成更稳定的 hardest-family / OOD / 主指标收益。

本任务不是 six-method 任务，不是新前端任务，不是新数据集任务，不是大规模结构搜索任务。

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
12. `exp/task_real_007_physics_consistency/*/task_real_007_report.md`

此外，必须继续参考：
13. `面向雷达学习成像的物理一致性文献检索与研究机会分析报告.md`
14. `Efficient physics-based learned reconstruction methods for real-time 3D near-field MIMO radar imaging.pdf`

不得绕过这些文档自定协议。

---

## 三、核心边界（必须严格遵守）

### 硬约束 1：数据协议完全冻结
本任务必须原样复用 `006d/006e/007` 的冻结数据协议：

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
- 改 family 集
- 改 OOD 定义
- 增删样本
- 重新设计数据

---

### 硬约束 2：前端与主结构完全冻结
本任务必须保持：

- Front-end = `Variant B`
- Physics backbone = `ref3`
- Second stage = 当前 `3D U-Net`（UNet3DSmall）
- 输入 = `ref3` coarse amplitude volume
- 标签 = GT amplitude volume

禁止：
- 换成 `ref5/ref7/ref9`
- 更换 U-Net 主结构
- 增加更大网络
- 改成 transformer / unrolled / complex branch
- 引入多通道几何输入作为主变量

---

### 硬约束 3：本轮只比较三种模型
本任务只允许比较：

#### A. Baseline-Ours
- `ref3 + 3D U-Net`
- image-only supervision
- 直接复用 `006d/006e` 的 frozen baseline

#### B. Ours-PC-P1
- `007` 已完成的 sampled forward echo consistency 版本
- 原则上复用 `007` best checkpoint，不建议重训

#### C. Ours-PC-P2
- 本轮唯一新增模型
- 在 P1 基础上引入 geometry-aware / support-aware consistency

禁止：
- 增加第四个以上新模型
- 再回到 M1/M2/M3
- 再做 six-method 全矩阵重跑

---

### 硬约束 4：P2 只能是 loss / weighting 层面的增强
P2 必须保持主结构不变，只能在 consistency loss 上做增强。

### 允许的 P2 方向
#### P2-A（推荐，必做）
**support-mask weighted consistency**
- 从预测体 `x_hat` 构造 support mask
- 对 support 区域及其轻量膨胀边界对应的 forward error 加权
- 目标：进一步缓解 support fragmentation / cluster collapse / support shift

#### P2-B（可选增强）
**boundary-aware consistency**
- 对边界 / contour 区域对应的 forward error 加权
- 目标：进一步缓解 F2/F3，尤其是 thin line / edge break

#### P2-C（可选，若资源允许）
**family-aware geometry weighting**
- 对 hardest families 的结构关键区域使用不同权重模板
- 仍然只能体现为 loss weighting，而不是新结构分支

### 不允许作为本轮主方案
- full giant differentiable simulator
- surrogate forward model
- new backbone
- feature-level latent consistency 作为主 loss
- 大型结构搜索

---

### 硬约束 5：训练目标必须显式写成
必须采用：

`L_total = L_image + lambda_pc * L_echo_geo`

其中：
- `L_image` = 当前 baseline 的图像域主损失
- `L_echo_geo` = 带 geometry-aware / support-aware weighting 的 echo consistency
- `lambda_pc` = 一致性权重

必须显式记录：
- `lambda_pc`
- weighting 策略
- support/boundary 构造方式
- measurement subset 采样策略
- 是否使用固定子集或随机子集
- consistency 额外开销

---

### 硬约束 6：评测只做 baseline / P1 / P2
必须只在以下 4 个集合上比较：

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

### 必须额外统计
- `F2`
- `F3`
- `F4`
- hardest families：
  - `point_cluster`
  - `line`
  - `L-shape`

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
   - 若配置了远端并允许 push，则执行 push 并说明结果
   - 若未配置远端或不允许 push，必须明确写 `local commit only`

---

## 四、本任务要回答的问题

1. P2 是否比 Baseline-Ours 更好？
2. P2 是否比 P1 更进一步？
3. 哪些测试集最先从 P2 受益：
   - Main Test
   - Unseen-Parameter OOD
   - Leave-One-Family-Out Focused OOD
   - Random-ET OOD
4. 哪些 hardest families 最先受益：
   - point_cluster
   - line
   - L-shape
5. 哪些 failure modes 最先受益：
   - F2
   - F3
   - F4
6. P2 是否值得把 physics-consistency 从“可选增强”推进为更强的主方法组成部分？

---

## 五、任务拆解

---

### Part A：冻结 baseline / P1 参照

#### 目标
明确并锁死本轮 comparison 的参照对象。

#### 必做项
1. 复用 `006d/006e` Baseline checkpoint
2. 复用 `007` 的 P1 best checkpoint
3. 记录它们的来源与引用路径
4. 生成本轮 baseline/P1 reference manifest

#### 输出文件
- `baseline_p1_reference_manifest_007b.json`

---

### Part B：实现 P2-A（必做）

#### 目标
在 P1 基础上引入 **support-mask weighted consistency**。

#### 必做项
1. 从预测体 `x_hat` 构造 support mask
2. 对 support 区域及其轻量扩张边界区域定义 higher weighting
3. 在 measurement subset `Ω` 上定义：
   - `L_echo_geo = sum w(Ω) * error(Ω)`
4. 总损失：
   - `L_total = L_image + lambda_pc * L_echo_geo`

#### 必须显式记录
- support 阈值
- dilation / boundary 扩张规则
- weighting 规则
- `lambda_pc`
- subset 采样方式
- 是否固定 mask / 动态 mask

#### 输出文件
- `consistency_config_P2A.yaml`

---

### Part C：实现 P2-B（可选）

#### 目标
在 P2-A 已有效的基础上，引入 **boundary-aware consistency**。

#### 必做项（若执行）
1. 构造 boundary / contour emphasis region
2. 在 boundary 对应的 forward error 上进一步加权
3. 明确与 P2-A 的差异

#### 说明
- 若资源紧张，可不执行
- 若不执行，必须在报告中解释

#### 输出文件
- `consistency_config_P2B.yaml`（若执行）

---

### Part D：训练矩阵

#### 必做
- `Baseline-Ours`：复用，不重训
- `Ours-PC-P1`：复用，不重训
- `Ours-PC-P2A`：新训练

#### 可选
- `Ours-PC-P2B`：若执行再训练

#### 说明
本轮不是 recipe search，只是 baseline / P1 / P2 的单变量延续比较。

---

### Part E：统一评测

#### 目标
在 4 个固定数据集上比较：
- Baseline-Ours
- Ours-PC-P1
- Ours-PC-P2A
- Ours-PC-P2B（若执行）

#### 指标
- NMSE
- PSNR
- SSIM
- runtime
- speedup_vs_BP

#### 必须额外统计
- F2/F3/F4
- hardest-family metrics

#### 输出文件
- `metrics_baseline_p1_p2_main.csv`
- `metrics_baseline_p1_p2_unseen_param_ood.csv`
- `metrics_baseline_p1_p2_leave_one_family_out_ood.csv`
- `metrics_baseline_p1_p2_random_et_ood.csv`
- `failure_mode_p2_improvement.csv`
- `hardest_family_p2_improvement.csv`

---

### Part F：可视化

#### 必须遵守
- `visualization_protocol.md`

#### 核心图
1. `baseline_p1_p2_main_metrics.png`
2. `baseline_p1_p2_ood_metrics.png`
3. `baseline_p1_p2_runtime_speedup.png`
4. `baseline_p1_p2_failure_modes.png`
5. `baseline_p1_p2_hardest_families.png`
6. `baseline_p1_p2_frontier_ood.png`
7. `p2_best_case_panel.png`
8. `p2_failure_case_panel.png`

### 说明
- 重点不是 six-method 大总览
- 重点是：P2 相对 baseline / P1 的增量效果

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
- `git_update_summary_007b.md`

---

## 六、脚本层要求

请新增或补齐：

1. `scripts/run_pc_training_P2A.sh`
2. `scripts/run_pc_training_P2B.sh`（若执行）
3. `scripts/run_p2_eval_main.sh`
4. `scripts/run_p2_eval_ood.sh`
5. `scripts/render_p2_comparison_viz.sh`
6. `scripts/update_git_and_record_007b.sh`

### 脚本要求
- 必须可执行
- 必须把日志落盘
- 必须统一写入本任务 exp 目录
- 不允许手工散跑代替脚本流程

---

## 七、exp 目录规范

请为本任务创建固定产物目录：

```text
exp/task_real_007b_geometry_aware_consistency/<timestamp>/
````

至少输出：

1. `task_real_007b_report.md`
2. `baseline_p1_reference_manifest_007b.json`
3. `consistency_config_P2A.yaml`
4. `consistency_config_P2B.yaml`（若执行）
5. `metrics_baseline_p1_p2_main.csv`
6. `metrics_baseline_p1_p2_unseen_param_ood.csv`
7. `metrics_baseline_p1_p2_leave_one_family_out_ood.csv`
8. `metrics_baseline_p1_p2_random_et_ood.csv`
9. `failure_mode_p2_improvement.csv`
10. `hardest_family_p2_improvement.csv`
11. `git_update_summary_007b.md`
12. `tree.txt`
13. `logs/`
14. `viz/`
15. `checkpoints/`

---

## 八、`task_real_007b_report.md` 的强制结构

报告必须至少包含以下部分：

1. `Task Goal`
2. `Frozen Baseline / P1 Reused`
3. `Protocol / Context Files Used`
4. `Boundary Statement`
5. `Geometry-Aware Consistency Design`
6. `Training Matrix`
7. `Main Test Comparison`
8. `OOD Comparison`
9. `Failure-Mode Improvement`
10. `Hardest-Family Improvement`
11. `Visual Outputs`
12. `Git Update Summary`
13. `Remaining Issues`
14. `Is Geometry-Aware Consistency Worth Keeping?`
15. `Suggested Next Task`

并且必须包含固定小节：

### Key file paths for ChatGPT controller

集中列出：

* report 路径
* baseline/P1 reference 路径
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

1. 阅读 `006d/006e/007` 报告
2. 冻结 baseline 与 P1 参照
3. 实现 P2-A consistency
4. 训练 Ours-PC-P2A
5. 在 4 个数据集上做 baseline / P1 / P2 比较
6. 若 P2-A 有效，再做 P2-B
7. 生成标准化可视化
8. 更新 git 并记录
9. 生成 `task_real_007b_report.md`
10. 确保 git 工作区可提交、可追踪

---

## 十、验收标准

本任务只有在以下条件全部满足时才算完成：

1. Baseline / P1 / P2A 完成受控比较
2. 4 个数据集都完成 baseline / P1 / P2 评测
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
8. 已生成 `task_real_007b_report.md`

---

## 十一、最终判断要求

在最终报告中，请明确回答：

1. P2A 是否优于 baseline？
2. P2A 是否优于 P1？
3. P2B（若执行）是否进一步优于 P2A？
4. 哪些数据集、哪些指标、哪些 failure modes 最先受益？
5. runtime 是否基本保持不变？
6. geometry-aware consistency 是否值得保留为更强的主方法组成部分？

---

## 十二、最终终端汇报格式

任务完成后，请按如下格式做最终汇报：

1. `PROJECT_ROOT = ...`
2. `baseline/p1 frozen reuse = pass / partial pass / fail`
3. `P2A training = pass / partial pass / fail`
4. `P2B training = pass / partial pass / fail`
5. `main test baseline-p1-p2 eval = pass / partial pass / fail`
6. `OOD baseline-p1-p2 eval = pass / partial pass / fail`
7. `failure-mode comparison = pass / partial pass / fail`
8. `hardest-family comparison = pass / partial pass / fail`
9. `visualization outputs = pass / partial pass / fail`
10. `git synchronization = pass / partial pass / fail`
11. `Artifacts = ...`
12. `Is Geometry-Aware Consistency Worth Keeping? = yes / no / conditional`

---

## 十三、提醒

* 这次只做 **baseline / P1 / P2** 的延续比较
* 不再重复 six-method 全矩阵
* 不改数据，不改前端，不换主结构
* 核心是验证：**geometry-aware consistency 能否把 007 已观察到的结构性收益，再向前推一步**

```
```

