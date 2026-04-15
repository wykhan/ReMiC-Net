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
