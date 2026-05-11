# task_real_006d_report

## 1. Task Goal

Build a literature-scale but more rigorously designed family-aware main dataset at `800 / 100 / 100`, add three OOD test sets, and verify whether the frozen mainline remains credible under true 3D cylindrical simulation.

## 2. Why 800/100/100 is adopted

The original `5000 / 1000 / 1000` formal target was blocked by current storage and execution limits. This task adopts the same order of magnitude as Manisali and PnP synthetic training setups, but strengthens credibility through family-aware allocation, parameter-stratified sampling, and explicit OOD evaluation.

## 3. Protocol / Context Files Used

- `CONTEXT/real_cylindrical_master_document_with_physics_consistency.md`
- `CONTEXT/simulation_protocol.md`
- `CONTEXT/reference_surface_strategy.md`
- `CONTEXT/dataset_protocol.md`
- `CONTEXT/et_dataset_protocol.md`
- `CONTEXT/et_dataset_protocol_800.md`
- `exp/task_real_006b_fullscale_mainline/20260417_000500/task_real_006b_report.md`
- `exp/task_real_006c_formal_validation/20260419_000500/task_real_006c_report.md`

## 4. Boundary Statement

This task does not introduce physics-consistency, does not change the front-end, does not replace `ref3`, does not search new recipes, and does not use real measured echoes.

## 5. Frozen Mainline Definition

- front-end: `Variant B`
- physics backbone: `ref3`
- second stage: `3D U-Net`
- input: `ref3` coarse amplitude volume
- target: GT amplitude volume
- training source: family-aware main train split only

## 6. Main Dataset Design Summary

- Main dataset counts by split: `{'train': 800, 'val': 100, 'test': 100}`
- Main dataset counts by family: `{'line': 200, 'cross': 140, 'L-shape': 200, 'double-line': 130, 'small_rect_edge': 110, 'point_cluster': 220}`
- Hard families emphasized in train split: `point_cluster`, `line`, `L-shape`
- Parameter-stratified coverage tracked via radial / azimuth / height / size / density buckets.

## 7. OOD Dataset Design Summary

- unseen-parameter OOD counts: `{'test': 100}`
- leave-one-family-out focused OOD counts: `{'test': 100}`
- random-ET OOD counts: `{'train': 0, 'val': 0, 'test': 100}`
- unseen-parameter OOD focuses on held-out long, thick, seam-adjacent `line` regimes.
- leave-one-family-out focused OOD stresses `point_cluster` with denser multi-cluster layouts.
- random-ET OOD uses true cylindrical random extended-target generation.

## 8. Split Integrity / Leakage Check

- duplicate scene hashes: `0`
- duplicate parameter signatures: `168`
- nearest train-test distance mean: `1.445870`
- nearest train-test distance min: `0.299341`

Judgment: no exact scene duplication was detected. Parameter-signature reuse is non-zero because bucketed family construction reuses compact shape templates, but nearest-neighbor distances remain above trivial-copy behavior.

## 9. Model Audit Summary

- model name: `UNet3DSmall`
- total params: `85017`
- trainable params: `85017`
- input tensor shape: `[1, 1, 24, 24, 24]`
- output tensor shape: `[1, 1, 24, 24, 24]`

## 10. Mainline vs Baselines Results

- Frozen Mainline overall learned NMSE: `0.807482`
- Frozen Mainline NMSE gain vs ref3 on main test: `5.189599`
- Unified comparison rows: `6`

Hardest families:
- point_cluster: ref3=13.031400, frozen_mainline=0.970717, gain=12.060683
- line: ref3=5.207608, frozen_mainline=0.781202, gain=4.426406
- L-shape: ref3=3.324385, frozen_mainline=0.728846, gain=2.595539

Failure modes:
- F2: ref3=41, frozen_mainline=12, decrease=29
- F3: ref3=23, frozen_mainline=0, decrease=23
- F4: ref3=20, frozen_mainline=0, decrease=20

## 11. OOD / Generalization Results

- unseen-parameter OOD: ref3 NMSE = `2.896105`, frozen_mainline NMSE = `0.723074`, gain = `2.173031`
- leave-one-family-out focused OOD: ref3 NMSE = `6.704958`, frozen_mainline NMSE = `0.977576`, gain = `5.727382`
- random-ET OOD: ref3 NMSE = `7.052402`, frozen_mainline NMSE = `1.151614`, gain = `5.900787`

## 12. Visual Outputs

- `viz/progress/curves/dataset_scale_and_family_balance.png`
- `viz/progress/curves/parameter_coverage_main_set.png`
- `viz/progress/curves/train_test_nearest_neighbor_distance.png`
- `viz/progress/curves/split_integrity_visual_check.png`
- `viz/progress/curves/train_val_loss_frozen_mainline_800.png`
- `viz/progress/curves/runtime_quality_frontier_with_learning_800.png`
- `viz/progress/curves/family_metrics_mainline_vs_baselines_800.png`
- `viz/progress/curves/failure_mode_mainline_vs_baselines_800.png`
- `viz/progress/curves/ood_unseen_param_metrics.png`
- `viz/progress/curves/ood_leave_one_family_out_metrics.png`
- `viz/progress/curves/ood_random_et_metrics.png`

## 13. Remaining Issues

- This remains a literature-scale formal pass, not the larger `5000 / 1000 / 1000` target.
- Memory and FLOPs in the model audit remain unmeasured.
- The leave-one-family-out OOD is implemented as a hardest-family focused test-only stress set, not a second fully retrained family-ablation model.

## 14. Ready for Physics-Consistency Stage?

`conditional`

The current evidence is much stronger than `006c` because the dataset is now fully frozen at the adopted `800 / 100 / 100` scale and all three OOD sets were evaluated. Physics-consistency can be considered next if the controller accepts the literature-scale setting as sufficient for the next phase.

## 15. Suggested Next Task

`task_real_007`: add physics-consistency on top of the frozen mainline, but keep the current 800-scale dataset protocol fixed for the first controlled comparison.

## Key file paths for ChatGPT controller

- report: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006d_800_formal/20260419_112717/task_real_006d_report.md`
- manifests: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006d_800_formal/20260419_112717/dataset_manifest_main_800_100_100.json`, `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006d_800_formal/20260419_112717/dataset_manifest_unseen_param_ood.json`, `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006d_800_formal/20260419_112717/dataset_manifest_leave_one_family_out_ood.json`, `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006d_800_formal/20260419_112717/dataset_manifest_random_et_ood.json`
- split integrity: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006d_800_formal/20260419_112717/split_integrity_report_800.md`, `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006d_800_formal/20260419_112717/duplicate_check_800.json`, `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006d_800_formal/20260419_112717/nearest_neighbor_overlap_800.csv`
- model audit: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006d_800_formal/20260419_112717/model_audit_800.json`, `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006d_800_formal/20260419_112717/model_summary_800.txt`
- metrics: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006d_800_formal/20260419_112717/metrics_frozen_mainline_800.json`, `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006d_800_formal/20260419_112717/mainline_vs_baselines_800.csv`
- OOD: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006d_800_formal/20260419_112717/ood_unseen_param_metrics.csv`, `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006d_800_formal/20260419_112717/ood_leave_one_family_out_metrics.csv`, `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006d_800_formal/20260419_112717/ood_random_et_metrics.csv`
- curves: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006d_800_formal/20260419_112717/viz/progress/curves`
- representative visuals: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006d_800_formal/20260419_112717/viz/paper_candidates/qualitative`
- logs: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006d_800_formal/20260419_112717/logs`
