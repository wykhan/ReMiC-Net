# task_real_006_report

## 1. Task Goal

Train the first formal two-stage ET learning pipeline under the frozen cylindrical Variant B front-end:
`ref3 coarse volume -> 3D U-Net -> GT amplitude`.

## 2. Dataset Scale Upgrade Statement

This task expands beyond the ET-1 reduced set from `task_real_005`.
Completed executed scale:

- shape-family full dataset counts by split: `{'train': 576, 'val': 144, 'test': 144}`
- random ET supplement counts by split: `{'train': 192, 'val': 48, 'test': 48}`

This is still below the master-document target of `5000/1000/1000` per family plus `5000/1000/1000` random ET, so the present run should be interpreted as the first substantial ET-2 formal training pass under local resource limits rather than the final paper-scale dataset.

## 3. Protocol / Context Files Used

- `CONTEXT/real_cylindrical_master_document_with_physics_consistency.md`
- `CONTEXT/simulation_protocol.md`
- `CONTEXT/reference_surface_strategy.md`
- `CONTEXT/dataset_protocol.md`
- `CONTEXT/et_dataset_protocol.md`
- `CONTEXT/project_brief.md`
- `CONTEXT/experiment_matrix.md`
- `PROMPTS/system_rules.md`
- `PROMPTS/review_checklist.md`
- `exp/task_real_005_shape_family_et/20260416_111500/task_real_005_report.md`

## 4. Boundary Statement

This task trains and evaluates the second-stage learning pipeline only.
It does not revisit the frozen traditional front-end, add physics-consistency losses, use complex supervision, or integrate real echoes.

## 5. Manisali Borrowing Summary

Borrowed from the Manisali paper and repository:

- coarse-to-GT two-stage decomposition
- 3D U-Net second stage fed by a physics-based first-stage volume
- dataset organization that stores first-stage inputs, GT targets, and reusable checkpoints/visuals
- projection/slice-oriented qualitative reporting style

Borrowed concretely from the inspected repository:

- `src/src.py`: 3D U-Net input-output organization and the first-stage-to-network handoff concept
- `src/misc.py`: max-projection, scene-visualization, and reporting style
- `README.md`: checkpoint-oriented usage framing and model/data separation

Not copied directly:

- the planar / near-field MIMO sensing model
- the adjoint observation-matrix first stage
- their exact tensor shape conventions and TensorFlow implementation

Replacement in this project:

- Manisali first stage is replaced by frozen cylindrical `Variant B ref3`
- Manisali second-stage and dataset-engineering ideas are retained and adapted to the current PyTorch ET pipeline

## 6. Training Matrix

- `M0`: inherited bare `ref3` non-learning baseline
- `M1`: shape-family full + random ET supplement
- `M2`: shape-family full only
- `M3`: `M1` with hard-family emphasis on `point_cluster / line / L-shape`

## 7. Dataset Summary

- Shape-family dataset: `864` samples
- Random ET dataset: `288` samples
- Full handoff total samples: `1152`
- Hard-family priority: `['point_cluster', 'line', 'L-shape']`

## 8. Key Metrics

| Mode | Learned NMSE | Learned PSNR | Learned SSIM | NMSE gain vs ref3 |
| --- | ---: | ---: | ---: | ---: |
| M1 | 0.8579 | 30.6472 | 0.6009 | 4.8757 |
| M2 | 0.8159 | 31.0371 | 0.6184 | 4.9534 |
| M3 | 0.8448 | 30.6653 | 0.5924 | 4.8888 |

## 9. Family-Level Results

Primary hard-family summary from `M1`:

- point_cluster: nmse_gain=10.3027; line: nmse_gain=4.2414; L-shape: nmse_gain=4.5389

The hardest families from `task_real_005` remain the main learning battlefield: `point_cluster`, `line`, and `L-shape`.

## 10. Failure-Mode Improvement

The main monitored failure labels are `F2`, `F3`, and `F4`.
See:

- `failure_mode_improvement.csv`
- `viz/curves/failure_mode_improvement.png`

These files quantify whether learned outputs reduce contour fracture, thin-structure disappearance, and support fragmentation relative to bare `ref3`.

## 11. Visual Outputs

- `viz/curves/train_val_loss_M1.png`
- `viz/curves/train_val_loss_M2.png`
- `viz/curves/train_val_loss_M3.png`
- `viz/curves/quality_gain_vs_ref3.png`
- `viz/curves/family_metrics_learning.png`
- `viz/curves/failure_mode_improvement.png`
- `viz/recon_compare/*`
- `viz/slices/*`

## 12. Remaining Issues

- The executed ET-2 dataset is still below the master-document formal target scale.
- The second stage currently uses amplitude-only supervision and a compact U-Net, not a larger paper-tuned architecture.
- Physics-consistency loss is still absent and belongs to the next task.

## 13. Ready for Physics-Consistency Stage?

- Reached master-document target scale? `no`
- `ref3 + 3D U-Net` usable as first formal mainline? `yes`
- Hardest families improved? `yes`
- `Ready for physics-consistency stage?` = `conditional`

## 14. Suggested Next Task

`task_real_007`: add physics-consistency / echo-consistency to the trained cylindrical two-stage baseline and test whether it further reduces `F2/F3/F4` on the hardest ET families.

## Key file paths for ChatGPT controller

- Report: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006_two_stage_learning/20260416_120500/task_real_006_report.md`
- Checkpoints: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006_two_stage_learning/20260416_120500/checkpoints`
- Metrics: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006_two_stage_learning/20260416_120500/metrics_M1.json`, `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006_two_stage_learning/20260416_120500/metrics_M2.json`, `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006_two_stage_learning/20260416_120500/metrics_M3.json`
- Family tables: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006_two_stage_learning/20260416_120500/family_metrics.csv`
- Failure-mode table: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006_two_stage_learning/20260416_120500/failure_mode_improvement.csv`
- Curves: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006_two_stage_learning/20260416_120500/viz/curves`
- Representative visuals: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006_two_stage_learning/20260416_120500/viz/recon_compare` and `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006_two_stage_learning/20260416_120500/viz/slices`
- Logs: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006_two_stage_learning/20260416_120500/logs`
