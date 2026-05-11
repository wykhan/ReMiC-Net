# CHANGELOG_DEV

## 2026-04-15 task_real_001

- Identified `PROJECT_ROOT` as `/home/superws/2026_Projects/Codex_reference_plane_real`
- Confirmed the repository already contains a `.git/` directory and had no prior commit
- Added project governance directories: `PROMPTS/`, `scripts/`, `exp/`, `doc/`
- Added repository governance files: `README.md`, `.gitignore`, `CHANGELOG_DEV.md`, `debug.md`
- Added four project-level `CONTEXT/` documents:
  - `project_brief.md`
  - `repo_map.md`
  - `experiment_matrix.md`
  - `acceptance_criteria.md`
- Added prompt-layer records:
  - `PROMPTS/system_rules.md`
  - `PROMPTS/review_checklist.md`
  - `PROMPTS/task_real_001.md`
- Added project notes:
  - `doc/assumptions.md`
  - `doc/open_questions.md`
- Added minimal script entry points:
  - `scripts/bootstrap_check.sh`
  - `scripts/run_baseline.sh`
  - `scripts/eval.sh`
  - `scripts/run_experiment.sh`
- Ran bootstrap self-check and generated task report artifacts under `exp/task_real_001_bootstrap/`

## 2026-04-15 task_real_002

- Added `CONTEXT/dataset_protocol.md` to freeze point-target dataset rules for Phase 1
- Added Python workspace packages and modules for:
  - shared protocol constants and IO helpers
  - point-target scene generation and dataset building
  - cylindrical point forward simulation
  - reduced-reference and BP reconstruction entry points
  - 3D metrics and baseline evaluation
  - minimal 3D U-Net smoke training
- Added task scripts:
  - `scripts/generate_point_dataset.sh`
  - `scripts/run_point_baselines.sh`
  - `scripts/run_point_learning_smoke.sh`
- Generated `task_real_002` artifacts under `exp/task_real_002_point_chain/20260415_154500/`
- Ran smoke point-target dataset generation, sparse echo simulation, baseline evaluation, and minimal learning smoke

## 2026-04-15 task_real_003

- Added controlled radial mismatch dataset builder and hard proof files for true 3D cylindrical simulation origin
- Added faithful echo-driven reconstruction modules to replace the old point-scene analytic verifier as the main validation path
- Added faithful baseline evaluation, radial mismatch analysis, and standardized visualization renderers
- Added scripts:
  - `scripts/run_point_faithful_baselines.sh`
  - `scripts/run_radial_mismatch_analysis.sh`
  - `scripts/render_point_viz.sh`
- Generated `task_real_003` artifacts under `exp/task_real_003_faithful_point_validation/20260415_165500/`
- Verified faithful `ref3/ref5/ref7/ref9/BP` chain on the controlled point dataset and produced standardized curves and sample visualizations

## 2026-04-15 task_real_004

- Audited `reference_plane_matlab_Tan/points_4_202406.m` and ran a MATLAB R2018b audit replay through `scripts/run_matlab_reference_plane_audit.sh`
- Added accelerated reconstruction engine in `workspace/recon/cyl_fast_reference_engine.py` following the MATLAB fast-chain structure:
  - height FFT
  - azimuth FFT
  - reference-surface matching in transformed space
  - height inverse FFT
  - cylindrical-to-Cartesian geometry correction
- Added accelerated task wrappers and evaluators:
  - `workspace/data/radial_control_dataset_builder_accelerated.py`
  - `workspace/eval/eval_accelerated_point_baselines.py`
  - `workspace/eval/radial_mismatch_analysis_accelerated.py`
  - `workspace/eval/render_point_viz_accelerated.py`
- Added task scripts:
  - `scripts/run_matlab_reference_plane_audit.sh`
  - `scripts/run_point_accelerated_baselines.sh`
  - `scripts/run_accelerated_radial_mismatch_analysis.sh`
  - `scripts/render_point_viz_accelerated.sh`
- Added audit documents:
  - `doc/task_real_004_algorithm_audit.md`
  - `doc/matlab_to_python_mapping.md`
- Generated `task_real_004` artifacts under `exp/task_real_004_accelerated_point_validation/20260415_190000/`
- Verified strong wall-time separation for `ref3/ref5/ref7/ref9/BP` and regenerated standardized curves, metrics, and visualization outputs

## 2026-04-15 task_real_004b

- Added seam-focused stress dataset builder:
  - `workspace/data/azimuth_edge_stress_builder.py`
- Hardened accelerated engine with explicit mode switches:
  - `tensor_mode = active | dense_global`
  - `geom_mode = linear | sinc`
- Added MATLAB-inspired geometry correction utilities in:
  - `workspace/recon/geometry_correction.py`
  - `workspace/recon/engine_modes.md`
- Added wrap-hardening evaluation, analysis, visualization, and reporting modules:
  - `workspace/eval/wrap_ablation_variants.py`
  - `workspace/eval/wrap_stability_analysis.py`
  - `workspace/eval/render_wrap_viz.py`
  - `workspace/eval/generate_task_real_004b_report.py`
- Added task scripts:
  - `scripts/run_azimuth_edge_stress_set.sh`
  - `scripts/run_wrap_ablation_variants.sh`
  - `scripts/run_wrap_stability_analysis.sh`
  - `scripts/render_wrap_viz.sh`
- Generated `task_real_004b` artifacts under `exp/task_real_004b_wrap_hardening/20260415_210500/`
- Quantified seam monotonicity and symmetry behavior across A/B/C/D and chose `active + sinc` as the default front-end upgrade while retaining `dense_global` only as audit mode

## 2026-04-16 task_real_004c

- Froze the default accelerated front-end as Variant B in code and docs:
  - `workspace/recon/cyl_fast_reference_engine.py`
  - `workspace/recon/engine_modes.md`
  - `CONTEXT/experiment_matrix.md`
  - `CONTEXT/project_brief.md`
- Added broader controlled point-suite builder:
  - `workspace/data/broader_controlled_point_builder.py`
- Added Variant B evaluation, stability-analysis, visualization, and reporting modules:
  - `workspace/eval/eval_variantB_broader_suite.py`
  - `workspace/eval/variantB_stability_analysis.py`
  - `workspace/eval/render_variantB_confirmation_viz.py`
  - `workspace/eval/generate_task_real_004c_report.py`
- Added task scripts:
  - `scripts/run_variantB_broader_point_suite.sh`
  - `scripts/run_variantB_stability_analysis.sh`
  - `scripts/render_variantB_confirmation_viz.sh`
- Generated `task_real_004c` artifacts under `exp/task_real_004c_variantB_confirmation/20260416_003500/`
- Confirmed Variant B preserves average speed-quality ordering, but broader-suite monotonicity violations show `ref7/ref9` crossing is not yet seam-only

## 2026-04-16 task_real_005

- Added the frozen ET protocol document:
  - `CONTEXT/et_dataset_protocol.md`
- Added the ET shape-family builder and supporting GT export:
  - `workspace/data/et_shape_family_builder.py`
- Added ET baseline evaluation, failure taxonomy, visualization, learning handoff, and report generators:
  - `workspace/eval/eval_et_baselines_variantB.py`
  - `workspace/eval/render_et_viz.py`
  - `workspace/eval/build_learning_handoff.py`
  - `workspace/eval/generate_task_real_005_report.py`
- Added ET task scripts:
  - `scripts/generate_et_shape_family_dataset.sh`
  - `scripts/run_et_baselines_variantB.sh`
  - `scripts/render_et_viz.sh`
  - `scripts/build_learning_handoff.sh`
- Generated `task_real_005` artifacts under `exp/task_real_005_shape_family_et/20260416_111500/`
- Built the first Phase ET-1 true cylindrical shape-family dataset with six frozen families and balanced splits
- Ran frozen Variant B and BP on the ET dataset, generated family-group metrics, failure taxonomy, representative visuals, and a learning handoff manifest

## 2026-04-16 task_real_006

- Added the random ET supplement builder:
  - `workspace/data/random_et_builder.py`
- Added the full learning handoff builder for shape-family ET plus random ET:
  - `workspace/eval/build_learning_handoff_full.py`
- Added the formal two-stage ET training/evaluation pipeline:
  - `workspace/train/train_two_stage_et.py`
  - `workspace/eval/render_learning_viz.py`
  - `workspace/eval/generate_task_real_006_report.py`
- Added task scripts:
  - `scripts/generate_et_fullscale_dataset.sh`
  - `scripts/generate_random_et_dataset.sh`
  - `scripts/build_learning_handoff_full.sh`
  - `scripts/run_two_stage_training_M1.sh`
  - `scripts/run_two_stage_training_M2.sh`
  - `scripts/run_two_stage_training_M3.sh`
  - `scripts/render_learning_viz.sh`
- Generated `task_real_006` artifacts under `exp/task_real_006_two_stage_learning/20260416_120500/`
- Expanded ET training data beyond ET-1 reduced scale:
  - shape-family ET = `864`
  - random ET supplement = `288`
  - full handoff total = `1152`
- Trained and evaluated `M1/M2/M3` for the frozen `ref3 -> 3D U-Net -> GT amplitude` pipeline and generated checkpoints, family metrics, failure-mode improvement tables, representative visuals, and the formal task report

## 2026-04-17 task_real_006b

- Added the frozen-mainline handoff builder:
  - `workspace/eval/build_frozen_mainline_handoff.py`
- Added the frozen-mainline training wrapper:
  - `workspace/train/train_frozen_mainline.py`
- Added unified comparison, visualization, and reporting modules for Frozen Mainline vs `ref3/ref5/ref7/ref9/BP`:
  - `workspace/eval/compare_frozen_mainline_vs_baselines.py`
  - `workspace/eval/render_mainline_vs_baselines_viz.py`
  - `workspace/eval/generate_task_real_006b_report.py`
- Added task scripts:
  - `scripts/generate_shape_family_fullscale.sh`
  - `scripts/generate_random_et_fullscale.sh`
  - `scripts/build_frozen_mainline_handoff.sh`
  - `scripts/run_frozen_mainline_training.sh`
  - `scripts/run_mainline_vs_baselines_comparison.sh`
  - `scripts/render_mainline_vs_baselines_viz.sh`
- Generated `task_real_006b` artifacts under `exp/task_real_006b_fullscale_mainline/20260417_000500/`
- Froze the default learned mainline as:
  - `Variant B`
  - `ref3`
  - `3D U-Net`
  - `shape-family full-scale only`
- Completed the formal unified comparison against `ref3/ref5/ref7/ref9/BP` on the shape-family full test split and produced:
  - overall mainline-vs-baselines table
  - family-level positioning table
  - failure-mode comparison table
  - frontier and case-gallery visualizations

## 2026-04-19 task_real_006c

- Added the formal-scale credibility-validation module:
  - `workspace/eval/formal_scale_validation.py`
- Added task scripts:
  - `scripts/complete_formal_scale_datasets.sh`
  - `scripts/build_formal_frozen_mainline_handoff.sh`
  - `scripts/run_split_integrity_check.sh`
  - `scripts/run_model_audit.sh`
  - `scripts/run_frozen_mainline_formal_training.sh`
  - `scripts/run_formal_mainline_vs_baselines.sh`
  - `scripts/run_ood_generalization_suite.sh`
  - `scripts/render_formal_validation_viz.sh`
- Generated `task_real_006c` artifacts under `exp/task_real_006c_formal_validation/20260419_000500/`
- Produced a formal fail-fast credibility package because the dataset did not meet the hard formal-scale gate:
  - shape-family remained `576 / 144 / 144`
  - random ET remained `192 / 48 / 48`
- Completed the parts that remain valid before training is allowed:
  - formal-scale completion audit
  - split-integrity / duplicate / nearest-neighbor checks on the currently available shape-family set
  - model audit for the frozen 3D U-Net

## 2026-05-11 task_real_008

- Added frozen ReMiC-Net metadata utilities:
  - `workspace/common/remic_metadata.py`
- Added ReMiC-Net with RSB-FiLM and residual baseline models:
  - `workspace/models/remicnet_rsb_film.py`
- Added the `task_real_008` build/train/eval/render pipeline:
  - `workspace/eval/task_real_008_pipeline.py`
- Added task scripts:
  - `scripts/build_remicnet_inputs_008.sh`
  - `scripts/run_remicnet_training_008.sh`
  - `scripts/run_remicnet_eval_main.sh`
  - `scripts/run_remicnet_eval_ood.sh`
  - `scripts/render_remicnet_comparison_viz.sh`
  - `scripts/update_git_and_record_008.sh`
- Generated `task_real_008` artifacts under `exp/task_real_008_remicnet_eval/20260511_082329/`
- Built frozen `Mshell + delta_rho_raw + Pcyc` metadata with explicit `delta_rho_input = raw_meter`
- Retrained an aligned residual 3D U-Net baseline and a ReMiC-Net with RSB-FiLM under the same frozen `ref3` protocol
- Completed Main Test + 3 OOD baseline-vs-remic comparison, grouped mismatch diagnostics, hardest-family summaries, qualitative panels, and git-record artifacts
  - placeholder not-run outputs for forbidden downstream stages
- Concluded that `task_real_006c` fails at the formal-scale gate and that `task_real_007` should not start yet

## 2026-04-19 task_real_006d

- Added `CONTEXT/et_dataset_protocol_800.md` and `workspace/eval/task_real_006d_pipeline.py`.
- Added dedicated task_real_006d scripts for main dataset, OOD generation, handoff, split-integrity, audit, training, comparison, OOD, and visualization.
- Generated literature-scale family-aware artifacts under `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006d_800_formal/20260419_112717`.
- Completed 800/100/100 main dataset generation, three OOD sets, split-integrity audit, frozen-mainline training, unified comparison, and OOD evaluation.

## 2026-04-19 task_real_006e

- Added comprehensive six-method evaluation completion on main test and all three OOD datasets.
- Artifacts: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006e_comprehensive_eval/20260419_190046`.

## 2026-04-19 task_real_007

- Added minimal physics-consistency support on top of the frozen 800-scale baseline:
  - `workspace/train/physics_consistency.py`
  - `workspace/train/train_pc_p1.py`
  - `workspace/eval/task_real_007_pc_comparison.py`
- Added task scripts:
  - `scripts/run_pc_training_P1.sh`
  - `scripts/run_pc_training_P2.sh`
  - `scripts/run_pc_eval_main.sh`
  - `scripts/run_pc_eval_ood.sh`
  - `scripts/render_pc_comparison_viz.sh`
  - `scripts/update_git_and_record_007.sh`
- Reused frozen baseline artifacts from `task_real_006d` and comprehensive six-method positioning from `task_real_006e`.
- Scoped the comparison strictly to `Baseline-Ours` vs `Ours-PC-P1`, with no front-end or backbone changes.

## 2026-04-19 task_real_007b

- Added geometry-aware support-weighted consistency refinement on top of the frozen 800-scale baseline:
  - `workspace/train/train_pc_p2a.py`
  - `workspace/eval/task_real_007b_geometry_aware.py`
- Extended physics-consistency helpers with prediction-support weighting for measurement-domain consistency.
- Added task scripts:
  - `scripts/run_pc_training_P2A.sh`
  - `scripts/run_pc_training_P2B.sh`
  - `scripts/run_p2_eval_main.sh`
  - `scripts/run_p2_eval_ood.sh`
  - `scripts/render_p2_comparison_viz.sh`
  - `scripts/update_git_and_record_007b.sh`
- Scoped the comparison strictly to `Baseline-Ours`, `Ours-PC-P1`, and `Ours-PC-P2A`, with `P2B` kept as an explicit placeholder path only.
