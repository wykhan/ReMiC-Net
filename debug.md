# debug

## 2026-04-15 task_real_001

- Path recognition:
  - Current code working path: `/home/superws/2026_Projects/Codex_reference_plane_real/workspace`
  - Parent path contains both `CONTEXT/` and `workspace/`
  - Resolved `PROJECT_ROOT`: `/home/superws/2026_Projects/Codex_reference_plane_real`
- Git status on entry:
  - Existing repository detected at `PROJECT_ROOT/.git`
  - Branch reported as `master`
  - No prior commit existed
- Issues encountered:
  - None blocking
  - Repository was structurally minimal and required full bootstrap scaffolding
- Permissions / path ambiguity:
  - No permission issues observed
  - No path ambiguity after applying the parent-directory rule
- Bootstrap check:
  - Actual status: pass
  - Log path: `exp/task_real_001_bootstrap/20260415_151328/bootstrap_check.log`
  - Formal simulation and training intentionally not started

## 2026-04-15 task_real_002

- Task path:
  - `PROJECT_ROOT`: `/home/superws/2026_Projects/Codex_reference_plane_real`
  - artifact root: `exp/task_real_002_point_chain/20260415_154500`
- Protocol use:
  - reused existing master, simulation, reference-surface, and project brief documents without editing them
  - added `CONTEXT/dataset_protocol.md` to freeze point-target dataset rules
- Implementation notes:
  - forward simulation stores sparse echo bundles instead of dense `Na x Nr x Nh` tensors to keep artifacts tractable
  - baseline smoke reconstruction uses deterministic visibility subsampling during matched-filter accumulation for runtime control, while forward simulation remains protocol-v1 compliant
- Smoke execution status:
  - dataset generation: pass
  - forward simulation: pass
  - baseline chain: pass on 8 test samples
  - learning smoke: pass
- Known caveats:
  - current baseline runtime table mixes measured wall time with reference-count runtime proxy because the smoke evaluator is an analytic point-scene verifier rather than the final production FFT implementation
  - current SSIM is a global 3D statistic, not a windowed skimage implementation
