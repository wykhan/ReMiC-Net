
````markdown id="x6e2pm"
# task_real_006e：comprehensive evaluation completion on main test + 3 OOD sets

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
- `task_real_006c`：formal-scale credibility validation（fail-fast）
- `task_real_006d`：800/100/100 family-aware formal dataset + OOD credibility validation

当前已知状态（来自 `task_real_006d_report.md`）：
- 主数据集 `800/100/100` 已冻结
- 三类 OOD 测试集已生成：
  - unseen-parameter OOD
  - leave-one-family-out focused OOD
  - random-ET OOD
- Frozen Mainline 已在主 test 和三类 OOD 上证明优于裸 `ref3`
- 但当前 OOD 结果还缺少与 `ref5/ref7/ref9/BP` 的**完整统一评测**
- 目前最需要补齐的是：
  - 所有方法在 main test + 3 OOD 上的完整指标
  - `NMSE / PSNR / SSIM / runtime / speedup_vs_BP`
  - 对应论文级可视化结果

本任务进入：

> **Phase ET-2e：comprehensive evaluation completion before physics-consistency**

---

## 一、任务定位

本任务的唯一目标是：

> 在不改变模型、不重新训练、不修改数据协议的前提下，  
> 把以下 6 个方法：
> - `ref3`
> - `ref5`
> - `ref7`
> - `ref9`
> - `BP`
> - `Frozen Mainline (ref3 + 3D U-Net)`
>
> 在以下 4 个测试集合：
> - main test
> - unseen-parameter OOD
> - leave-one-family-out focused OOD
> - random-ET OOD
>
> 上的完整评测补齐，并输出统一主表、统一图集和论文候选图。

本任务是一个 **evaluation-only task**，不是训练任务，不是 physics-consistency 任务。

---

## 二、必须遵守的上位文档

开始前必须阅读并遵守：

1. `CONTEXT/real_cylindrical_master_document_with_physics_consistency.md`
2. `CONTEXT/simulation_protocol.md`
3. `CONTEXT/reference_surface_strategy.md`
4. `CONTEXT/dataset_protocol.md`
5. `CONTEXT/et_dataset_protocol.md`
6. `CONTEXT/et_dataset_protocol_800.md`
7. `CONTEXT/project_brief.md`
8. `CONTEXT/experiment_matrix.md`
9. `CONTEXT/visualization_protocol.md`
10. `PROMPTS/system_rules.md`
11. `PROMPTS/review_checklist.md`
12. `exp/task_real_006d_800_formal/*/task_real_006d_report.md`

不得绕过这些文档自定协议。

---

## 三、强制硬约束

### 硬约束 1：本任务不得重新训练
禁止：
- 重新训练 Frozen Mainline
- 替换 checkpoint
- 调整网络
- 调整 loss
- 调整 recipe
- 引入 physics-consistency
- 修改数据集

### 允许
- 直接复用 `task_real_006d` 的最佳 Frozen Mainline checkpoint
- 补跑 baseline 和 OOD 上的统一评测

---

### 硬约束 2：方法集合必须固定为 6 个
必须统一评测以下 6 个方法：

1. `ref3`
2. `ref5`
3. `ref7`
4. `ref9`
5. `BP`
6. `Ours`（Frozen Mainline）

#### 说明
- `Ours` = Variant B + ref3 + 3D U-Net
- 禁止继续使用 `M1/M2/M3` 作为方法名
- 所有图表中统一用：
  - `Ref3`
  - `Ref5`
  - `Ref7`
  - `Ref9`
  - `BP`
  - `Ours`

---

### 硬约束 3：测试集合必须固定为 4 个
必须统一评测以下 4 个测试集合：

1. `Main Test`
2. `Unseen-Parameter OOD`
3. `Leave-One-Family-Out Focused OOD`
4. `Random-ET OOD`

不得只比较 `ref3` 和 `Ours`。

---

### 硬约束 4：指标必须固定为 5 个
对每个测试集合、每个方法，必须输出：

- `NMSE`
- `PSNR`
- `SSIM`
- `runtime`
- `speedup_vs_BP`

### 强烈建议
同时保留：
- mean
- std
- median
- per-sample values

以便后续画分布图和挑案例。

---

### 硬约束 5：所有评测必须统一协议
必须确保：
- 所有方法在同一测试样本集合上评测
- 统一 GT
- 统一度量函数
- 统一 runtime 统计口径
- `speedup_vs_BP` 一律相对于同一数据集上的 `BP runtime mean`

不得出现不同方法在不同测试切片、不同样本子集上的比较。

---

### 硬约束 6：每次评测都必须生成标准化可视化
必须按 `visualization_protocol.md` 输出：

#### A. 主测试集完整比较图
- `main_test_unified_metrics.png`

#### B. OOD 完整比较图
至少输出：
- `ood_nmse_unified.png`
- `ood_psnr_unified.png`
- `ood_ssim_unified.png`

#### C. runtime / speedup 图
- `runtime_speedup_across_datasets.png`

#### D. frontier 图
- `frontier_main_and_ood.png`

#### E. 分布图
至少输出：
- `nmse_distribution_across_datasets.png`
- `psnr_distribution_across_datasets.png`
- `ssim_distribution_across_datasets.png`

#### F. OOD qualitative 图
至少输出：
- `ood_unseen_param_case_panel.png`
- `ood_leave_one_family_case_panel.png`
- `ood_random_et_case_panel.png`

不得只保留 csv/json。

---

### 硬约束 7：必须生成统一命名的任务报告
本任务结束时，必须生成：

- `task_real_006e_report.md`

不得使用临时命名风格替代。

---

## 四、严格边界

### 本任务允许做
- 复用 `006d` 的数据和 checkpoint
- 对 6 个方法做 4 个测试集的统一评测
- 统计 5 类指标
- 输出表格、分布图、前沿图、论文候选图
- 更新 `CHANGELOG_DEV.md` 与 `debug.md`

### 本任务禁止做
- 不重新训练
- 不引入 physics-consistency
- 不修改数据集
- 不再做 split integrity 主体工作
- 不再做 model audit 主体工作
- 不引入新方法

---

## 五、本任务要回答的问题

1. 在 Main Test 上，`Ours` 相对 `ref3/ref5/ref7/ref9/BP` 的位置是什么？
2. 在 3 个 OOD 集合上，`Ours` 相对 `ref3/ref5/ref7/ref9/BP` 的位置是什么？
3. `Ours` 是否只是在 OOD 上优于 `ref3`，还是仍然接近 / 超过 `ref5/ref7/ref9/BP`？
4. runtime 是否在 main + OOD 上都保持在 `ref3` 档附近？
5. 现在是否已经拥有足够完整的评测证据进入 `task_real_007`？

---

## 六、任务拆解

---

### Part A：固定评测对象与输入

#### 目标
把 `006d` 的 frozen setting 原样复用到统一评测流程。

#### 必做项
1. 固定方法集合：
   - Ref3
   - Ref5
   - Ref7
   - Ref9
   - BP
   - Ours
2. 固定测试集合：
   - Main Test
   - Unseen-Parameter OOD
   - Leave-One-Family-Out Focused OOD
   - Random-ET OOD
3. 固定 Ours checkpoint：
   - 使用 `006d` best checkpoint

#### 输出文件
- `evaluation_manifest_006e.json`

---

### Part B：统一主表评测

#### 目标
在 4 个测试集合上，为 6 个方法统一统计 5 个指标。

#### 必做项
对每个 dataset × method 输出：
- `NMSE mean / std / median`
- `PSNR mean / std / median`
- `SSIM mean / std / median`
- `runtime mean / std / median`
- `speedup_vs_BP`

#### 输出文件
- `main_test_metrics_all_methods.csv`
- `ood_unseen_param_metrics_all_methods.csv`
- `ood_leave_one_family_out_metrics_all_methods.csv`
- `ood_random_et_metrics_all_methods.csv`
- `mainline_vs_baselines_all_datasets.csv`

---

### Part C：逐样本指标输出

#### 目标
为后续分布图、异常样本分析、论文补充材料提供基础。

#### 必做项
按样本保存：
- dataset
- family（若适用）
- sample_id
- method
- NMSE
- PSNR
- SSIM
- runtime

#### 输出文件
- `per_sample_metrics_all_datasets.csv`

---

### Part D：档位判断（positioning）

#### 目标
不是只给表，而是明确给出 `Ours` 在每个数据集中的位置判断。

#### 必做项
对 Main Test 和 3 个 OOD，分别回答：
- Ours 更接近 `Ref5` / `Ref7` / `Ref9` / `BP` 哪一档
- 是否整体超过某些 baseline
- 是否仍保持 `ref3` 档速度

#### 输出文件
- `positioning_summary.md`

---

### Part E：标准化可视化

#### 目标
输出可以直接服务论文写作的图。

#### 必须遵守
- `visualization_protocol.md`
- 同一 colormap
- 同一 normalization
- 同一 slice rule
- 统一方法命名
- 论文候选图与进展图同时生成

#### 必须输出的图

##### 1. Main Test 完整比较图
- `main_test_unified_metrics.png`

##### 2. OOD 完整比较图
- `ood_nmse_unified.png`
- `ood_psnr_unified.png`
- `ood_ssim_unified.png`

##### 3. runtime / speedup 图
- `runtime_speedup_across_datasets.png`

##### 4. frontier 图
- `frontier_main_and_ood.png`

##### 5. 分布图
- `nmse_distribution_across_datasets.png`
- `psnr_distribution_across_datasets.png`
- `ssim_distribution_across_datasets.png`

##### 6. OOD qualitative 图
- `ood_unseen_param_case_panel.png`
- `ood_leave_one_family_case_panel.png`
- `ood_random_et_case_panel.png`

##### 7. 论文候选五图
必须自动给出并登记：
- `fig_main_frontier.png`
- `fig_main_metrics.png`
- `fig_ood_metrics.png`
- `fig_ood_case_best.png`
- `fig_ood_case_failure.png`

---

### Part F：报告整理

#### 目标
形成完整的评测补齐报告。

#### 报告必须回答
1. Main Test 上 Ours 的位置
2. 三类 OOD 上 Ours 的位置
3. Ours 是否仍超过 `ref5/ref7/ref9/BP`
4. runtime 是否保持 `ref3` 档
5. 现有证据是否足以进入 007

---

## 七、脚本层要求

请新增或补齐：

1. `scripts/run_main_test_all_methods_eval.sh`
2. `scripts/run_ood_unseen_param_all_methods_eval.sh`
3. `scripts/run_ood_leave_one_family_all_methods_eval.sh`
4. `scripts/run_ood_random_et_all_methods_eval.sh`
5. `scripts/merge_all_dataset_metrics.sh`
6. `scripts/render_006e_comprehensive_eval_viz.sh`

### 脚本要求
- 必须可执行
- 必须把日志落盘
- 必须统一写入本任务 exp 目录
- 不允许手工散跑代替脚本流程

---

## 八、exp 目录规范

请为本任务创建固定产物目录：

```text id="0n4m1i"
exp/task_real_006e_comprehensive_eval/<timestamp>/
````

至少输出：

1. `task_real_006e_report.md`
2. `evaluation_manifest_006e.json`
3. `main_test_metrics_all_methods.csv`
4. `ood_unseen_param_metrics_all_methods.csv`
5. `ood_leave_one_family_out_metrics_all_methods.csv`
6. `ood_random_et_metrics_all_methods.csv`
7. `mainline_vs_baselines_all_datasets.csv`
8. `per_sample_metrics_all_datasets.csv`
9. `positioning_summary.md`
10. `tree.txt`
11. `logs/`
12. `viz/`

---

## 九、`task_real_006e_report.md` 的强制结构

报告必须至少包含以下部分：

1. `Task Goal`
2. `Frozen Inputs Reused`
3. `Protocol / Context Files Used`
4. `Boundary Statement`
5. `Evaluation Matrix`
6. `Main Test Results`
7. `OOD Results`
8. `Positioning of Ours vs Baselines`
9. `Visual Outputs`
10. `Remaining Issues`
11. `Ready for Physics-Consistency Stage?`
12. `Suggested Next Task`

并且必须包含固定小节：

### Key file paths for ChatGPT controller

集中列出：

* report 路径
* all metrics 路径
* per-sample 路径
* positioning 路径
* curves 路径
* representative visuals 路径
* logs 路径

---

## 十、推荐执行顺序

请按以下顺序推进：

1. 阅读 `task_real_006d_report.md`
2. 固定 6 方法 × 4 数据集评测矩阵
3. 补跑 4 个数据集上的全方法评测
4. 合并 all-dataset metrics
5. 生成 positioning summary
6. 生成标准化可视化
7. 生成 `task_real_006e_report.md`
8. 更新 `CHANGELOG_DEV.md` 与 `debug.md`
9. 确保 git 工作区可提交

---

## 十一、验收标准

本任务只有在以下条件全部满足时才算完成：

1. 4 个测试集合都完成 6 方法统一评测
2. 5 个指标都齐全：

   * NMSE
   * PSNR
   * SSIM
   * runtime
   * speedup_vs_BP
3. per-sample 指标已保存
4. Main Test + 3 OOD 都有可视化
5. 报告中明确给出 Ours 在每个数据集中的位置判断
6. 已输出论文候选五图
7. 已生成 `task_real_006e_report.md`
8. git 工作区保持可提交状态

---

## 十二、最终判断要求

在最终报告中，请明确回答：

1. 在 Main Test 上，Ours 相对 `ref3/ref5/ref7/ref9/BP` 的位置是什么？
2. 在 3 个 OOD 集合上，Ours 相对 `ref3/ref5/ref7/ref9/BP` 的位置是什么？
3. Ours 是否仍整体保持 `ref3` 档速度？
4. 当前是否已经具备进入 `task_real_007` 的完整评测证据？
5. `Ready for Physics-Consistency Stage?` 回答必须是：

   * `yes`
   * `no`
   * `conditional`

---

## 十三、最终终端汇报格式

任务完成后，请按如下格式做最终汇报：

1. `PROJECT_ROOT = ...`
2. `main test all-method evaluation = pass / partial pass / fail`
3. `OOD all-method evaluation = pass / partial pass / fail`
4. `full metrics completion = pass / partial pass / fail`
5. `positioning summary = pass / partial pass / fail`
6. `visualization outputs = pass / partial pass / fail`
7. `Artifacts = ...`
8. `Ready for Physics-Consistency Stage? = yes / no / conditional`
9. `Suggested next task = task_real_007 (...)`

---

## 十四、提醒

* 这次不训练新模型
* 这次不改变任何协议
* 这次只做一件事：**把完整评测补齐**
* 只有补齐后，进入 `007` 才更有说服力

```
```

