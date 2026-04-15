
# task_real_001：项目启动与治理冻结（bootstrap only）

你现在服务于新项目：

- 项目名：Real Cylindrical Physics-Guided Learned 3D Imaging
- 当前项目相关路径由用户提供：
  - 可能的工作目录：`/home/superws/2026_Projects/Codex_reference_plane_real/workspace`
  - 已存在文件夹：`CONTEXT/` 与 `workspace/`
- `CONTEXT/` 中已存放：
  - `real_cylindrical_master_document_with_physics_consistency.md`
  - `reference_surface_strategy.md`
  - `simulation_protocol.md`

你的任务不是立即开始大规模仿真、数据集生成或网络训练，而是先完成 **项目启动、结构搭建、规约冻结、Git 初始化/整理、最小自检**，让后续 task 可以在统一规则下推进。

---

## 一、总目标

完成一个“可复现、可追踪、可继续拆 task”的研究项目骨架，确保：

1. 项目目录结构规范；
2. 上位文档被正式接入项目治理体系；
3. Git 与 `.gitignore` 完成初始化或整理；
4. 最小 scripts 入口准备好；
5. 项目说明文档齐备；
6. 当前阶段不进入正式实验，仅完成 bootstrap 自检；
7. 为下一任务 `task_real_002` 做好交接。

---

## 二、首先做的事：识别项目根目录

先检查当前所在路径与目录结构，自动识别 `PROJECT_ROOT`：

### 识别规则
- 若当前目录本身同时包含 `CONTEXT/` 和 `workspace/`，则该目录就是 `PROJECT_ROOT`
- 若当前目录是 `.../workspace`，而其父目录包含 `CONTEXT/` 和 `workspace/`，则父目录是 `PROJECT_ROOT`
- 后续所有结构搭建都以 `PROJECT_ROOT` 为准

### 要求
在最终报告中明确写出：
- 你识别到的 `PROJECT_ROOT`
- 当前 `CONTEXT/` 路径
- 当前代码工作路径
- 你是否新建了 Git 仓库，或接管了已有 Git 仓库

---

## 三、严格边界

### 本任务允许做
- 建目录
- 建文档
- 建最小脚本
- Git 初始化或整理
- 写 bootstrap 自检脚本
- 运行轻量级目录/环境自检
- 生成 task 文档与项目说明
- 更新 `CHANGELOG_DEV.md` 与 `debug.md`

### 本任务禁止做
- 不生成大规模点目标数据集
- 不生成 extended-target 数据集
- 不训练任何网络
- 不跑正式成像 benchmark
- 不修改 `CONTEXT/` 中已有三份上位文档的原文内容
- 不擅自发明新的几何参数覆盖现有协议
- 不把旧项目结论偷偷迁入本项目作为“已验证事实”

若发现某些协议尚未完全冻结，可以在文档中标记 TODO / pending，但不要在本任务中扩展成正式实验。

---

## 四、按模板建立项目结构

请基于 `PROJECT_ROOT` 建立或补齐如下结构：

```text
PROJECT_ROOT/
├── CONTEXT/
├── PROMPTS/
├── scripts/
├── exp/
├── doc/
├── workspace/
├── README.md
├── CHANGELOG_DEV.md
├── debug.md
└── .gitignore
````

### 说明

* `CONTEXT/` 保持为项目知识层
* `PROMPTS/` 放任务提示词与 AI 约束
* `scripts/` 放统一执行入口
* `exp/` 放实验产物
* `doc/` 放科学假设、未决问题、协议说明等
* `workspace/` 作为后续代码实现区
* 若某目录已存在，则补齐缺失内容，不要破坏已有文件

---

## 五、在 CONTEXT 中补齐四个项目级文档

如果以下文件不存在，则创建；若存在则补充完善：

1. `CONTEXT/project_brief.md`
2. `CONTEXT/repo_map.md`
3. `CONTEXT/experiment_matrix.md`
4. `CONTEXT/acceptance_criteria.md`

### 内容要求

#### 1) project_brief.md

依据主控文档提炼项目核心目标，至少写清楚：

* 本论文主问题是什么
* 为什么不是纯黑盒重建
* 为什么从真正柱面物理仿真重新开始
* 为什么点目标只是前置验证，extended target 才是主战场
* 为什么第一阶段采用 reduced-reference physical backbone（默认 `ref3`）
* 为什么第二阶段采用 Manisali 风格 3D U-Net second-stage
* 当前阶段仅做 bootstrap，不做正式实验

#### 2) repo_map.md

说明各目录的角色与后续预期放什么：

* CONTEXT
* PROMPTS
* scripts
* exp
* doc
* workspace
* 根目录文件

并单独注明：

* `simulation_protocol.md` 是唯一有效几何/采样/仿真协议入口
* `reference_surface_strategy.md` 是唯一有效参考面策略入口
* `real_cylindrical_master_document_with_physics_consistency.md` 是唯一上位主控文档

#### 3) experiment_matrix.md

只写到“任务分层与阶段规划”即可，先不要写具体实验结果。
至少包含：

* Phase 0：bootstrap / 项目启动
* Phase 1：点目标物理链路验证
* Phase 2：传统基线 `ref3/ref5/ref7/ref9/BP`
* Phase 3：两阶段学习成像最简主版本
* Phase 4：extended target 主实验
* Phase 5：physics consistency 扩展

每阶段写：

* 目标
* 输入/输出
* 是否属于本任务
* 当前状态（未开始 / 本任务仅准备）

#### 4) acceptance_criteria.md

定义 `task_real_001` 的完成标准，至少包括：

* 项目结构完整
* Git 可用
* `.gitignore` 合理
* bootstrap scripts 可执行
* 四个 CONTEXT 文档齐备
* `PROMPTS/task_real_001.md` 已生成
* README 有使用说明
* exp 中已有本次任务报告
* 尚未启动正式仿真与训练

---

## 六、建立 PROMPTS 层

创建以下文件：

1. `PROMPTS/system_rules.md`
2. `PROMPTS/review_checklist.md`
3. `PROMPTS/task_real_001.md`

### 内容要求

#### system_rules.md

写成“本项目 Codex 工作规则”，至少包括：

* 一次 task 只做一类修改
* 不得无记录修改协议
* 所有实验必须脚本驱动
* 所有输出必须落盘到固定位置
* 不得在未记录情况下修改几何参数
* 不得绕过 `CONTEXT/` 中的主控文档与协议文档
* 发现不确定项先写入 TODO，而不是自行拍脑袋定案

#### review_checklist.md

写成每个 task 完成前自查清单，至少包括：

* 路径是否正确
* 是否更新 CHANGELOG_DEV
* 是否记录 debug
* 是否有脚本入口
* 是否把结果落到 exp
* 是否修改了协议文档
* 是否越界启动了不该做的实验

#### task_real_001.md

把本任务的目标、边界、执行项、交付物、完成标准写成正式任务文件，内容应与当前提示词一致但更适合项目内留档。

---

## 七、建立 doc 层

创建：

1. `doc/assumptions.md`
2. `doc/open_questions.md`

### 要求

#### assumptions.md

记录当前已冻结的高层事实：

* 项目以真正柱面物理仿真为基础
* 训练目标当前为幅度重建
* 默认两阶段主线：`RED_ref3 -> 3D U-Net -> GT amplitude`
* 点目标用于前置验证
* ET 为论文主战场
* `simulation_protocol.md` 与 `reference_surface_strategy.md` 为当前冻结协议

#### open_questions.md

把当前仍未在 bootstrap 内解决、但后续必须处理的问题列出来，例如：

* dataset_protocol 是否需要单独冻结
* 散射系数分布规则如何统一
* 是否显式引入 MIMO 或先使用当前 protocol v1 口径
* physics consistency 的第一版实现粒度是什么
* 点目标数据集具体规模最终如何冻结

注意：这里只能登记问题，不能在本任务中替代后续 task 做决定。

---

## 八、建立 scripts 层（最小可用，不做正式实验）

创建以下最小脚本：

1. `scripts/bootstrap_check.sh`
2. `scripts/run_baseline.sh`
3. `scripts/eval.sh`
4. `scripts/run_experiment.sh`

### 要求

#### bootstrap_check.sh

真正实现，可执行，至少完成：

* 打印 `PROJECT_ROOT`
* 检查关键目录是否存在
* 检查 `CONTEXT/` 中三份关键文档是否存在
* 检查 `PROMPTS/`、`scripts/`、`doc/` 是否存在
* 检查 Git 是否可用
* 将检查结果输出到本次任务报告目录

#### run_baseline.sh / eval.sh / run_experiment.sh

本任务阶段只需要创建“占位但规范”的脚本骨架：

* 有 shebang
* 有注释说明用途
* 有参数入口占位
* 运行时不会误触发正式实验
* 可以打印 `TODO: not implemented in task_real_001`

---

## 九、README 与根目录治理文件

### 1) README.md

至少写清：

* 项目是什么
* 当前阶段是什么
* 哪个文件是主控文档
* 哪个文件是几何协议
* 哪个文件是参考面协议
* 如何运行 bootstrap 检查
* 后续正式实验还未启动

### 2) CHANGELOG_DEV.md

记录本次 task 的所有新增文件与操作

### 3) debug.md

记录：

* 路径识别情况
* Git 初始化/整理情况
* 遇到的问题
* 是否有权限问题或路径歧义
* bootstrap 检查是否通过

### 4) .gitignore

至少忽略：

* `__pycache__/`
* `*.pyc`
* `.DS_Store`
* `.idea/`
* `.vscode/`
* `exp/**/logs/`
* `exp/**/ckpt/`
* `exp/**/tmp/`
* 大型二进制缓存与常见训练缓存文件

注意：

* 不要把 `CONTEXT/`、`PROMPTS/`、`doc/` 这些关键文本目录忽略掉
* 不要粗暴忽略整个 `exp/`，至少要允许 markdown/json 报告保留版本记录

---

## 十、Git 任务

请执行以下 Git 相关操作：

1. 判断 `PROJECT_ROOT` 是否已是 Git 仓库
2. 若不是，则初始化 Git
3. 配置合理的 `.gitignore`
4. 执行 `git status`
5. 若工作区状态正常，则进行一次 bootstrap 初始提交

### 提交信息建议

`bootstrap: initialize real cylindrical project structure`

如果因为环境原因无法提交，必须在报告中写明原因，但仍要把仓库整理到可提交状态。

---

## 十一、本次任务的报告输出

请为本任务创建固定产物目录：

```text
exp/task_real_001_bootstrap/<timestamp>/
```

在其中输出至少以下文件：

1. `bootstrap_report.md`
2. `tree.txt`
3. `git_status.txt`
4. `bootstrap_check.log`

### bootstrap_report.md 必须包含

* 识别到的 `PROJECT_ROOT`
* 你创建/修改了哪些文件
* Git 状态
* bootstrap 检查结果
* 当前尚未解决的 open questions
* 明确声明：本任务未启动正式仿真/训练
* 对下一任务 `task_real_002` 的建议起点

---

## 十二、执行顺序建议

按以下顺序做：

1. 识别 `PROJECT_ROOT`
2. 查看现有目录
3. 建立/补齐目录结构
4. 生成 CONTEXT 文档
5. 生成 PROMPTS 文档
6. 生成 doc 文档
7. 生成 scripts
8. 编写 README / CHANGELOG / debug / .gitignore
9. 初始化或整理 Git
10. 运行 bootstrap_check.sh
11. 生成 `exp/task_real_001_bootstrap/<timestamp>/` 报告
12. 输出最终总结

---

## 十三、最终回复格式

任务完成后，请在终端最终总结中按以下格式汇报：

1. `PROJECT_ROOT = ...`
2. `Git = initialized / existing / failed to commit`
3. `Bootstrap check = pass / partial pass / fail`
4. `Created files = ...`
5. `Key pending issues = ...`
6. `Suggested next task = task_real_002 (point-target physics chain validation)`

---

## 十四、最重要的提醒

* 本任务是 **bootstrap only**
* 不要进入正式实验
* 不要篡改上位协议
* 不要引入未记录的新几何口径
* 你的目标是把项目“搭起来、管起来、冻起来”，不是现在就“跑起来”

```

