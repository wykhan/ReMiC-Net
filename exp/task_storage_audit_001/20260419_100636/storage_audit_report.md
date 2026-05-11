# Task Goal

对整台服务器做只读磁盘盘点，识别主要空间占用者，并把候选清理对象分为 `SAFE_DELETE`、`REVIEW_FIRST`、`DO_NOT_TOUCH` 三类，为后续手动清理提供依据。本任务未执行任何删除、移动或覆盖操作。

# Overall Disk Status

- 当前项目位于 `/dev/nvme0n1p5` 挂载的根分区 `/`。
- 根分区容量 `961G`，已用 `893G`，剩余 `20G`，使用率 `98%`。
- inode 使用率仅 `6%`，当前瓶颈是容量，不是 inode。
- `df -h` 显示最满的实际持久化分区是 `/dev/nvme0n1p5`。
- 其他 tmpfs 与 `/boot/efi` 不构成当前瓶颈。

# Largest Space Consumers

根目录一级：

- `/home = 853G`
- `/usr = 20G`
- `/var = 14G`
- `/opt = 2.8G`
- `/tmp = 615M`

`/home/superws` 下最大目录：

- `dataset = 541G`
- `2024_Projects = 116G`
- `software = 63G`
- `anaconda3 = 62G`
- `2026_Projects = 27G`
- `下载 = 22G`
- `.cache = 18G`

`/home/superws/2026_Projects` 下最大目录：

- `Codex_reference_plane_real = 16G`
- `Codex_reference_plane = 4.0G`
- `Codex_reference_plane_extended_target = 2.0G`
- `z_backup_PriorModeling_VibeCoding = 2.5G`
- `z_backup_useful_code_store = 979M`

当前项目内部最大目录：

- `exp/task_real_006_two_stage_learning = 13G`
- `exp/task_real_005_shape_family_et = 1.2G`
- `exp/task_real_002_point_chain = 879M`
- `exp/task_real_004c_variantB_confirmation = 600M`
- `exp/task_real_004b_wrap_hardening = 345M`

系统级热点：

- `/var/log = 4.1G`
- `/var/lib/snapd = 8.7G`
- `/usr/local/cuda-12.4 = 4.9G`
- `/opt/nvidia = 2.1G`

# Large File Summary

最显著的大文件与大压缩包包括：

- `/home/superws/dataset/OBE_stand_raw/standard_raw_v01.zip = 39G`
- `/home/superws/dataset/Detectron2_datasets/coco/train2017.zip = 19G`
- `/home/superws/software/Matlab99R2020b_Linux_64.iso = 18G`
- `/home/superws/software/MathWorks.MATLAB.R2018blinux(1).zip = 14G`
- `/home/superws/dataset/SAR_competition_2024.zip = 14G`
- `/home/superws/dataset/S1SLC_CVDL.rar = 13G`
- `/home/superws/dataset/kitti/data_object_image_2.zip = 12G`

历史项目中的大模型文件也非常突出：

- `2024_Projects/DINO-main` 下多份 `2.5G` 级 checkpoint
- `2024_Projects/CenterNet2-master` 下多份 `1.1G` 级 checkpoint

当前项目之外，真正的大头主要是：

- `dataset/` 下的大型原始数据与压缩包
- `2024_Projects/` 下的历史训练项目和 checkpoint
- `software/` 下的安装镜像/压缩包
- `anaconda3/pkgs` 和 `.cache`

Docker 状态：

- `docker` 命令不存在，未发现可直接审计的 Docker runtime。

# Cleanup Classification

`SAFE_DELETE`

- `/home/superws/.cache = 18G`
- `/home/superws/anaconda3/pkgs = 22G`
- `/home/superws/.nv = 1.0G`
- `/tmp = 615M`
- `/home/superws/.torch = 438M`
- `/home/superws/.npm = 339M`
- `/tmp` 下当前项目 smoke 产物与临时 clone

`REVIEW_FIRST`

- `/home/superws/下载 = 22G`
- `software` 下 MATLAB 安装镜像与压缩包
- `dataset` 下超大压缩包
- `2024_Projects/DINO-main = 55G`
- `2024_Projects/CenterNet2-master = 16G`
- `2026_Projects/z_backup_*`
- 当前项目大实验产物，尤其 `exp/task_real_006_two_stage_learning = 13G`
- `/var/log = 4.1G`
- `/var/lib/snapd = 8.7G`

`DO_NOT_TOUCH`

- 当前项目源码、协议文档、MATLAB 原型
- 最新 `task_real_006c` 结论目录
- 当前 MATLAB 安装目录 `/home/superws/software/MATLAB_R2018b`
- `anaconda3/envs`
- 系统关键目录 `/usr`、`/usr/local/cuda-12.4`、`/opt/nvidia`、`/var/lib`
- 未经确认的唯一原始数据目录

# Estimated Reclaimable Space

保守估计：

- `safe only` 可释放约 `42G` 到 `43G`
- `safe + review` 可释放约 `240G` 左右

说明：

- `safe only` 主要来自缓存、conda package cache、NVIDIA cache 和 `/tmp`。
- `safe + review` 的估计按不重复的大目录/大文件保守汇总，主体来自下载目录、安装镜像、历史项目、当前项目旧实验产物与系统日志/snap 内容。

# Recommended Cleanup Order

1. 先处理 `SAFE_DELETE` 中的用户缓存、conda package cache、`/tmp`。
2. 再审查下载目录与安装镜像，优先处理已安装仍保留的 `.iso`、`.zip`、`.rar`。
3. 再审查历史项目中的大 checkpoint 与旧训练目录，尤其 `2024_Projects/DINO-main`、`CenterNet2-master`。
4. 再审查当前项目的大型历史实验目录，重点是 `task_real_006_two_stage_learning`。
5. 最后再考虑系统级 `var/log` 与 `snapd` 内容，避免影响系统排障与包管理。

# Current Project Specific Cleanup Recommendation

必须保留：

- `workspace/`
- `CONTEXT/`
- `PROMPTS/`
- `reference_plane_matlab_Tan/`
- `exp/task_real_006c_formal_validation/`
- 所有关键报告与主表

当前项目内可优先审查的对象：

- `exp/task_real_006_two_stage_learning = 13G`
- `exp/task_real_005_shape_family_et = 1.2G`
- `exp/task_real_002_point_chain = 879M`
- `exp/task_real_004c_variantB_confirmation = 600M`
- `exp/task_real_004b_wrap_hardening = 345M`

判断：

- 当前项目内部几乎没有“高概率绝对安全且大体积”的删除项。
- 只在当前项目内部清理，即使把上述 `REVIEW_FIRST` 对象全部处理掉，回收空间也只有约 `16G`。
- 这不足以支撑 `task_real_006c` formal-scale 数据扩容继续推进，因为服务器当前只剩约 `20G`，而 formal-scale 需要的额外空间明显更大。
- 因此，清理策略不能只盯着当前项目，必须优先动用全服务器级缓存、下载包和历史项目空间。

# Suggested Next Task

建议下一步执行“分级清理任务”，但必须按本报告顺序推进：

1. 先清 `SAFE_DELETE`
2. 再逐项确认 `REVIEW_FIRST` 的大压缩包与历史 checkpoint
3. 清理完成后重新评估剩余空间，再决定是否恢复 `task_real_006c` formal-scale 数据扩容
