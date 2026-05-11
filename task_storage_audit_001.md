````markdown
# task_storage_audit_001：全服务器磁盘空间盘点与可删性分级（只审计，不删除）

你现在服务于项目：

- `PROJECT_ROOT = /home/superws/2026_Projects/Codex_reference_plane_real`

当前背景：
- `task_real_006c` 已因 formal-scale 数据未完成而 fail
- 当前 blocker 不只是计算量，更是磁盘空间不足
- 审计报告中记录：当时文件系统剩余空间约 `20 GB`
- 当前需要先对**整个服务器**做系统盘点，找出主要空间占用者，并给出清理建议
- **本任务第一阶段只做审计，不做任何删除**

---

## 一、任务定位

本任务的唯一目标是：

> 对整个服务器做一次全局磁盘空间盘点，  
> 识别当前实验之外占空间最大的目录 / 项目 / 任务 / 大文件，  
> 并把它们分成：
> - `SAFE_DELETE`
> - `REVIEW_FIRST`
> - `DO_NOT_TOUCH`
> 三类，  
> 为后续手动或半自动清理提供依据。

本任务不是清理任务，不得删除任何文件。

---

## 二、强制硬约束

### 硬约束 1：本任务只允许审计，不允许删除
禁止执行任何具有清理、副作用或回收性质的操作，包括但不限于：

- `rm`
- `mv`
- `trash`
- `find ... -delete`
- `docker system prune`
- `apt clean`
- `pip cache purge`
- `conda clean`
- 修改权限
- 清空日志
- 覆盖或移动文件

你只能盘点、统计、分类、落报告。

---

### 硬约束 2：审计范围是全服务器，而不是只看当前项目
必须尽量覆盖全服务器主要可读挂载点和大目录，而不仅限于：

- `/home/superws/2026_Projects`

### 重点盘点路径（如存在且可读）
- `/home`
- `/var`
- `/opt`
- `/usr/local`
- `/tmp`
- `/mnt`
- `/data`
- `/srv`
- `/root`（如有权限）
- 其他可读的大型挂载点

### 明确跳过的路径
不要深度扫描这些虚拟/系统路径：
- `/proc`
- `/sys`
- `/dev`
- `/run`

可以记录“跳过此路径”，但不要在这些路径中做深度 `du` 扫描。

---

### 硬约束 3：所有候选项必须分级
对每个主要空间占用对象，必须给出以下三级分类之一：

#### `SAFE_DELETE`
高概率可删，通常包括：
- 缓存
- 临时目录
- 可再生中间实验产物
- 失败任务的占位文件
- 非最佳 checkpoint 副本
- 冗余 progress 图
- 解压后仍保留的压缩包副本

#### `REVIEW_FIRST`
可能可删，但需要用户确认，通常包括：
- 历史项目目录
- 旧数据集
- 旧模型
- 大 checkpoint
- 大型压缩包
- Docker 镜像/卷
- conda env / package cache
- 下载目录中的大文件

#### `DO_NOT_TOUCH`
不建议删除，通常包括：
- 当前项目源码
- 协议文档
- 唯一原始数据
- 当前使用中的环境
- MATLAB 原型代码
- 当前项目报告和关键表格
- 系统关键目录

不得只给“大小”，不做分级。

---

## 三、审计内容

---

### Part A：总体磁盘状态

#### 目标
识别当前服务器的磁盘占用全貌。

#### 必做
1. 输出所有挂载点的磁盘占用情况
2. 识别：
   - 哪个分区最满
   - 当前项目位于哪个分区
   - 当前分区剩余空间
3. 同时检查 inode 使用情况

#### 建议命令
- `df -h`
- `df -i`

#### 产物
- `disk_overview.txt`

---

### Part B：根目录一级大目录盘点

#### 目标
找出 `/` 下哪些一级目录最占空间。

#### 必做
对根目录一级大目录做体积统计，例如：
- `/home`
- `/var`
- `/opt`
- `/usr`
- `/tmp`
- `/mnt`
- `/data`
- `/srv`

#### 建议命令
- `du -xh --max-depth=1 / 2>/dev/null | sort -h`

#### 产物
- `root_level_usage.txt`

---

### Part C：重点路径深入盘点

#### 目标
对最大的几个一级目录继续展开，定位具体占空间对象。

#### 至少必须展开以下路径（如存在且可读）
- `/home`
- `/var`
- `/opt`
- `/usr/local`
- `/tmp`
- `/mnt`
- `/data`
- `/home/superws`

#### 对 `/home/superws` 必须继续展开
至少细分到：
- `2026_Projects`
- 历史项目目录
- 下载目录
- `.cache`
- `.conda`
- `.local`
- 其他大体积隐藏目录

#### 建议命令
- `du -xh --max-depth=2 /home 2>/dev/null | sort -h`
- `du -xh --max-depth=2 /var 2>/dev/null | sort -h`
- `du -xh --max-depth=2 /home/superws 2>/dev/null | sort -h`

#### 产物
- `home_usage.txt`
- `var_usage.txt`
- `superws_usage.txt`
- `top_paths_by_size.txt`

---

### Part D：大文件清单

#### 目标
找出真正占空间的大文件，而不是只看目录。

#### 必做
列出可读范围内：
- 大于 `500 MB` 的文件
- 大于 `1 GB` 的文件
- 若数量过多，则额外给出 Top 100 大文件

#### 注意
- 必须跳过 `/proc /sys /dev /run`
- 尽量避免无意义路径

#### 产物
- `large_files_over_500MB.txt`
- `large_files_over_1GB.txt`
- `top100_large_files.txt`

---

### Part E：可删性专项盘点

#### 目标
把“空间占用”转换成“清理建议”。

#### 必查类别

##### 1. 实验产物目录
重点找：
- 历史 `exp/`
- 旧任务目录
- 大量逐样本 GT / coarse / echo / recon 体数据
- 旧可视化 progress 图
- 冗余切片图
- 失败任务的占位输出
- 非最佳 checkpoint
- 重复 checkpoint

##### 2. Python / pip / conda 缓存
例如：
- `~/.cache`
- `~/.cache/pip`
- `~/.conda`
- conda pkgs
- wheel cache
- torch / huggingface / model cache（如存在）

##### 3. Docker / 容器相关
如可用且有权限，检查：
- images
- stopped containers
- build cache
- volumes
- overlay / layers

若无 Docker 或无权限，要在报告中说明。

##### 4. 系统日志与临时文件
例如：
- `/var/log`
- journal logs
- `/tmp`
- crash dump
- apt cache

##### 5. 下载与压缩包
例如：
- `*.zip`
- `*.tar`
- `*.tar.gz`
- 已解压但仍保留的压缩包
- 重复副本

##### 6. 重复数据集 / 冗余副本
若发现：
- 同一数据集多份拷贝
- 同一项目多份复制目录
- 历史迁移副本
必须单独列出。

#### 产物
- `cleanup_candidates_safe.txt`
- `cleanup_candidates_review.txt`
- `do_not_touch.txt`

---

### Part F：当前项目专属清理建议

#### 目标
单独评估当前项目目录：
`/home/superws/2026_Projects/Codex_reference_plane_real`

#### 必做
给出一节专门报告：

### `Current project specific cleanup recommendation`

说明：

1. 当前项目中必须保留的内容
2. 可删的旧任务产物
3. 可删的失败任务占位输出
4. 可删的中间体数据（如大规模逐样本 tensor / echo / recon 体）
5. 可删的 progress 图
6. 哪些 checkpoint 只需保留最佳一个
7. 预计可释放空间

#### 注意
仍然**只做建议，不执行删除**。

---

## 四、输出目录规范

请为本任务创建固定目录：

```text
/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_storage_audit_001/<timestamp>/
````

至少输出：

1. `disk_overview.txt`
2. `root_level_usage.txt`
3. `home_usage.txt`
4. `var_usage.txt`
5. `superws_usage.txt`
6. `top_paths_by_size.txt`
7. `large_files_over_500MB.txt`
8. `large_files_over_1GB.txt`
9. `top100_large_files.txt`
10. `cleanup_candidates_safe.txt`
11. `cleanup_candidates_review.txt`
12. `do_not_touch.txt`
13. `storage_audit_report.md`
14. `tree.txt`

---

## 五、`storage_audit_report.md` 的强制结构

报告必须至少包含以下部分：

1. `Task Goal`
2. `Overall Disk Status`
3. `Largest Space Consumers`
4. `Large File Summary`
5. `Cleanup Classification`
6. `Estimated Reclaimable Space`
7. `Recommended Cleanup Order`
8. `Current Project Specific Cleanup Recommendation`
9. `Suggested Next Task`

---

## 六、报告必须明确回答的问题

### 1. Overall disk status

* 当前各挂载点剩余空间
* 哪个分区最满
* 当前项目在哪个分区

### 2. Largest space consumers

* 全服务器 Top N 大目录
* `/home/superws` 下 Top N 大目录
* 当前实验之外占空间最大的项目/目录

### 3. Large-file summary

* Top 100 大文件
* 是否存在明显可删的大压缩包、旧 checkpoint、旧数据副本

### 4. Cleanup classification

按三类输出：

* `SAFE_DELETE`
* `REVIEW_FIRST`
* `DO_NOT_TOUCH`

### 5. Estimated reclaimable space

至少给两个估计：

* 只删 safe 项，预计可释放多少
* safe + review 一起处理，预计可释放多少

### 6. Recommended cleanup order

必须给出建议顺序，例如：

1. 先清缓存 / tmp / 日志
2. 再清历史 exp 中间产物
3. 再审查旧 checkpoint / 旧项目
4. 最后才考虑 Docker / 环境级项目

### 7. Current project specific cleanup recommendation

专门说明当前项目里：

* 哪些内容必须保留
* 哪些内容可以先删
* 清理这些后预计能释放多少
* 是否足以支持 `006c` formal-scale 继续推进

---

## 七、终端最终汇报格式

任务完成后，请按如下格式汇报：

1. `Current filesystem status = ...`
2. `Most space-consuming mount = ...`
3. `Top large directories outside current experiment = ...`
4. `Top large files = ...`
5. `SAFE_DELETE candidates = ...`
6. `REVIEW_FIRST candidates = ...`
7. `Estimated reclaimable space (safe only) = ...`
8. `Estimated reclaimable space (safe + review) = ...`
9. `Recommended next step = ...`
10. `Artifacts = ...`

---

## 八、禁止事项

* 不要删除任何文件
* 不要清空任何缓存
* 不要 prune Docker
* 不要修改权限
* 不要移动文件
* 不要用“猜测可删”代替实际盘点
* 不要只盘点 `/home/superws/2026_Projects`

---

## 九、提醒

这次任务的重点不是“马上清”，而是：

> **先看清整个服务器上真正占空间的是谁，再分级做安全清理。**

当前 `006c` 的资源瓶颈已经明确存在，因此这份审计报告会直接决定后续清理策略与 formal-scale 数据扩容可行性。

```
```

