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

## 2026-04-15 task_real_003

- Artifact root:
  - `exp/task_real_003_faithful_point_validation/20260415_165500`
- What changed:
  - replaced the old point-scene analytic verifier as the main path with an echo-driven faithful reconstruction path
  - built a controlled point-target dataset for rho sweep, azimuth control, and height control
  - added proof files for true 3D cylindrical simulation origin
- Execution status:
  - controlled dataset build: pass
  - true cylindrical forward simulation for controlled set: pass
  - faithful baseline chain: pass
  - radial mismatch analysis: pass
  - standardized visualization generation: pass
- Important limitation:
  - quality ordering remains physically reasonable, but wall-time separation between `ref3/ref5/ref7/ref9/BP` is still weak because the current faithful implementation is echo-driven matched filtering with modest observation decimation, not yet a production-grade accelerated FFT reference-surface engine
- ET readiness judgment:
  - not fully ready for ET main experiments yet; the traditional front-end quality trend is credible, but the fast-runtime story still needs a stronger implementation

## 2026-04-15 task_real_004

- Artifact root:
  - `exp/task_real_004_accelerated_point_validation/20260415_190000`
- MATLAB audit status:
  - first audit attempt failed due to a MATLAB temporary-array shape mismatch inside the synthetic replay script
  - fixed by replacing ambiguous `Temp(:, :) = ...` assignments with explicitly shaped local matrices
  - rerun passed and wrote `matlab_engine_notes.md`
- Accelerated engine notes:
  - replaced the old local matched-filter main path with a reference-surface stack builder plus geometry-correction stage
  - runtime now scales with reference count and produces clear separation between `ref3/ref5/ref7/ref9/BP`
  - local active azimuth-height windows are still used to keep the controlled validation tractable
- Additional issue fixed during rerun:
  - angle-wrap samples near `-pi/pi` initially broke `RegularGridInterpolator` because the azimuth grid contained duplicate endpoints
  - fixed by dropping repeated unwrapped angle entries before interpolation
- Remaining limitation:
  - `ref9` is not strictly better than `ref7` on every azimuth-edge control sample, so the accelerated engine is strong enough for ET skeleton work but still needs wrap-edge cleanup before final paper-grade claims
- ET readiness judgment:
  - ready for ET front-end skeleton use with a real speed-quality story
  - recommended follow-up is to stabilize azimuth-wrap edge cases before treating `ref7/ref9` ordering as fully final

## 2026-04-15 task_real_004b

- Artifact root:
  - `exp/task_real_004b_wrap_hardening/20260415_210500`
- Stress-set execution:
  - built a minimal seam-coverage stress set with 6 samples covering all required seam offsets plus three radius and three height groups
  - true cylindrical forward simulation completed successfully on the stress set
- Engine hardening:
  - split geometry correction out of the fast engine to avoid `RegularGridInterpolator` memory blow-up under dense-global mode
  - added explicit `active` and `dense_global` tensor modes plus `linear` and `sinc` geometry modes
  - vectorized reference-surface matching across the reference axis to make dense-global comparisons tractable
- Runtime observations:
  - `active + linear` and `active + sinc` remained sub-second for `ref7/ref9` and about 1 second for BP
  - `dense_global` variants were extremely expensive: about 45 seconds for `ref9` and about 165 seconds for BP on the 6-sample stress set
- Stability findings:
  - geometry correction was the dominant seam issue; `A -> B` improved `ref7/ref9` monotonicity from `2/6` violations to `1/6`
  - `dense_global` variants (`C/D`) were much worse numerically on the stress set and are not suitable as default mode
- Issues encountered:
  - the first wrap-viz pass failed because a representative sample id no longer existed after shrinking the stress set; fixed by updating the representative-id list
- ET readiness judgment:
  - default front-end should move to `active + sinc`
  - `dense_global` should remain audit/debug-only
  - readiness for shape-family ET is `conditional`, pending one broader rerun with the new default geometry correction

## 2026-04-16 task_real_004c

- Artifact root:
  - `exp/task_real_004c_variantB_confirmation/20260416_003500`
- Front-end freeze:
  - changed the default reconstruction call from `geom_mode=linear` to `geom_mode=sinc`
  - updated docs so Variant B is the repository-default accelerated path and `dense_global` is audit/debug-only
- Broader suite:
  - built a 70-sample controlled point suite:
    - `rho_sweep = 31`
    - `azimuth_control = 21`
    - `height_control = 10`
    - `double_point_control = 8`
  - ensured seam control includes both sides of the wrap so symmetry metrics are meaningful
- Execution status:
  - broader controlled suite build: pass
  - true cylindrical forward simulation: pass
  - Variant B baseline chain `ref3/ref5/ref7/ref9/BP`: pass
  - stability analysis: pass
  - visualization/report generation: pass
- Main result:
  - average ordering still holds: `ref3 < ref5 < ref7 < ref9 < BP` in quality and `ref3 < ref5 < ref7 < ref9 < BP` in runtime
  - but monotonicity violations remain nontrivial:
    - `all_samples = 16/70`
    - `seam_subset = 4/20`
    - `non_seam_subset = 12/50`
  - therefore `ref7/ref9` crossing is not yet a seam-only residual effect
- ET readiness judgment:
  - Variant B freeze: pass
  - broader confirmation run: pass
  - final front-end status: `conditional`
  - proceeding to ET is possible only with explicit acknowledgment that `ref7/ref9` local monotonicity is not fully cleaned

## 2026-04-16 task_real_005

- Artifact root:
  - `exp/task_real_005_shape_family_et/20260416_111500`
- Protocol freeze:
  - added `CONTEXT/et_dataset_protocol.md`
  - froze six required ET families:
    - `line`
    - `cross`
    - `L-shape`
    - `double-line`
    - `small_rect_edge`
    - `point_cluster`
  - executed ET-1 scale:
    - per family `train=16`, `val=4`, `test=4`
- External borrowing audit:
  - inspected the Manisali paper and the `Efficient-Learned-3D-Near-Field-MIMO-Imaging` git repository
  - borrowed dataset/handoff organization and 3D visualization style only
  - did not adopt the planar/MIMO first-stage front-end
- Execution status:
  - ET dataset build: pass
  - true cylindrical sparse echo generation: pass
  - Variant B baseline chain `ref3/ref5/ref7/ref9/BP`: pass
  - failure taxonomy generation: pass
  - ET visualization generation: pass
  - learning handoff manifest generation: pass
  - report generation: pass
- Main ET metrics:
  - quality ordering held on averages:
    - `ref3 -> ref5 -> ref7 -> ref9 -> BP`
  - mean wall time:
    - `ref3 = 0.3311 s`
    - `ref5 = 0.4455 s`
    - `ref7 = 0.5599 s`
    - `ref9 = 0.6733 s`
    - `BP = 1.9703 s`
  - mean speedup vs BP:
    - `ref3 = 5.9513x`
    - `ref5 = 4.4231x`
    - `ref7 = 3.5188x`
    - `ref9 = 2.9264x`
- Learning-stage guidance:
  - hardest `ref3` ET families were:
    - `point_cluster`
    - `line`
    - `L-shape`
  - readiness for `task_real_006`: `conditional`
- Issues encountered:
  - a parallel smoke attempt started ET forward simulation before the dataset index was written; reran sequentially and the issue disappeared
  - the first failure-taxonomy threshold for `F1` over-tagged almost every sample; tightened the heuristic before the formal ET run

## 2026-04-16 task_real_006

- Artifact root:
  - `exp/task_real_006_two_stage_learning/20260416_120500`
- Executed dataset scale:
  - shape-family ET:
    - train = `576`
    - val = `144`
    - test = `144`
  - random ET supplement:
    - train = `192`
    - val = `48`
    - test = `48`
  - full handoff total = `1152`
- Execution status:
  - shape-family full dataset build: pass
  - random ET dataset build: pass
  - true cylindrical sparse echo generation: pass
  - full `ref3` handoff generation: pass
  - `M1` formal training: pass
  - `M2` comparative training: pass
  - `M3` hard-family emphasized training: pass
  - learning visualization/report generation: pass
- Main results:
  - `M1`:
    - `ref3_nmse_mean = 5.7337`
    - `learned_nmse_mean = 0.8579`
    - `nmse_gain_vs_ref3 = 4.8757`
    - `learned_ssim_mean = 0.6009`
  - `M2`:
    - `learned_nmse_mean = 0.8159`
    - `nmse_gain_vs_ref3 = 4.9534`
  - `M3`:
    - `learned_nmse_mean = 0.8448`
    - `nmse_gain_vs_ref3 = 4.8888`
  - hardest-family gains from `M1`:
    - `point_cluster = 10.3027`
    - `line = 4.2414`
    - `L-shape = 4.5389`
  - failure-mode improvement versus `ref3`:
    - `M1`: `F2 -56`, `F3 -37`, `F4 -29`
    - `M2`: `F2 -45`, `F3 -37`, `F4 -29`
    - `M3`: `F2 -50`, `F3 -37`, `F4 -28`
- Manisali borrowing notes:
  - reused the coarse-to-GT two-stage organization, 3D U-Net second-stage role, and projection/slice reporting style
  - retained the frozen cylindrical `Variant B ref3` as the first stage instead of the repository's planar/MIMO adjoint route
- Issues encountered:
  - `render_learning_viz.py` initially assumed every mode had every family row, but `M2` intentionally excludes `random_et`; fixed by making the family plot robust to missing rows
- Final readiness judgment:
  - the learned second-stage mainline is usable
  - because the executed ET-2 dataset is still below the master-document target scale, readiness for physics-consistency is `conditional`

## 2026-04-17 task_real_006b

- Artifact root:
  - `exp/task_real_006b_fullscale_mainline/20260417_000500`
- Frozen Mainline definition:
  - front-end = `Variant B`
  - physics backbone = `ref3`
  - second stage = `3D U-Net`
  - default training data = `shape-family full-scale only`
- Dataset status reused from `task_real_006`:
  - shape-family full = `576 / 144 / 144`
  - random ET resource = `192 / 48 / 48`
  - therefore formal-scale completion remains below `5000 / 1000 / 1000`
- Execution status:
  - frozen-mainline handoff build: pass
  - frozen-mainline training: pass
  - unified comparison vs `ref3/ref5/ref7/ref9/BP`: pass
  - visualization/report generation: pass
- Mainline-vs-baselines overall results:
  - `ref3`: `nmse=5.7693`, `psnr=23.9163`, `ssim=0.1970`, `time=0.3908 s`
  - `ref5`: `nmse=3.4733`, `psnr=25.5765`, `ssim=0.2845`, `time=0.5072 s`
  - `ref7`: `nmse=2.9676`, `psnr=26.1291`, `ssim=0.3242`, `time=0.6265 s`
  - `ref9`: `nmse=2.8954`, `psnr=26.2436`, `ssim=0.3336`, `time=0.7427 s`
  - `BP`: `nmse=2.6771`, `psnr=26.4858`, `ssim=0.3616`, `time=2.0582 s`
  - `ref3 + learning`: `nmse=0.8281`, `psnr=30.9922`, `ssim=0.6265`, `time=0.3919 s`
- Positioning judgment:
  - Frozen Mainline runtime stays in the `ref3` band
  - Frozen Mainline quality is stronger than all traditional baselines on the executed scale and is closest to `BP` among the traditional tiers
- Hardest-family summary:
  - `point_cluster`: `11.3377 -> 1.0151`
  - `line`: `5.0251 -> 0.7919`
  - `L-shape`: `5.3249 -> 0.7937`
- Failure-mode summary:
  - `F2`: `66 -> 23`
  - `F3`: `37 -> 1`
  - `F4`: `29 -> 0`
- Issues encountered:
  - initial `006b` runtime accounting for `ref3+learning` only counted network inference time; fixed by adding the measured `ref3` front-end time back into the unified comparison
  - `render_learning_viz.py` had previously been hardened to tolerate modes that omit `random_et`; no new issue there
- Final readiness judgment:
  - Frozen Mainline is a usable formal learned mainline
  - because the dataset still does not meet master-document scale, readiness for physics-consistency remains `conditional`

## 2026-04-19 task_real_006c

- Artifact root:
  - `exp/task_real_006c_formal_validation/20260419_000500`
- Formal-scale gate result:
  - shape-family current counts:
    - `train = 576`
    - `val = 144`
    - `test = 144`
  - shape-family target counts:
    - `train = 30000`
    - `val = 6000`
    - `test = 6000`
  - random ET current counts:
    - `train = 192`
    - `val = 48`
    - `test = 48`
  - random ET target counts:
    - `train = 5000`
    - `val = 1000`
    - `test = 1000`
  - formal-scale completion = `fail`
- Hard rule applied:
  - no new Frozen Mainline formal training was run
  - no formal unified comparison was run
  - no OOD suite was run
  - reason: `task_real_006c` explicitly forbids training before formal-scale completion
- Split-integrity audit on the currently available shape-family set:
  - duplicate scene-hash count = `0`
  - duplicate parameter-signature count = `158`
  - nearest train-test distance mean = `0.228101`
  - nearest train-test distance min = `0.060051`
  - interpretation:
    - no exact scene-level leakage was detected
    - parameter signatures repeat heavily because the current generator uses a relatively small discrete parameter vocabulary
    - therefore credibility is still limited even though exact-duplicate leakage was not found
- Model audit:
  - model = `UNet3DSmall`
  - total params = `85017`
  - trainable params = `85017`
  - input shape = `[1, 1, 24, 24, 24]`
  - output shape = `[1, 1, 24, 24, 24]`
  - FLOPs and memory were not fully measured in this CPU-side audit
- Resource blocker observed:
  - filesystem free space at audit time was about `20G`
  - current task_real_006 datasets already occupy about:
    - `shape_family_full = 6.8G`
    - `random_et = 5.6G`
  - simple linear extrapolation shows the formal target would require far more storage and compute than are currently available in this workspace
- Final readiness judgment:
  - `task_real_006c` = `fail`
  - `Ready for Physics-Consistency Stage?` = `no`
  - `task_real_007` should not start until formal-scale ET data generation is actually completed

## 2026-04-19 task_real_006d

- output_root: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006d_800_formal/20260419_112717`
- target main split: 800/100/100 with family-aware allocation
- OOD sets: unseen-parameter 100, leave-one-family-out focused 100, random-ET 100
- model: UNet3DSmall base_channels=8
- report: `task_real_006d_report.md`

## 2026-04-19 task_real_006e

- output_root: `/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006e_comprehensive_eval/20260419_190046`
- comprehensive evaluation completed across 4 datasets and 6 methods.

## 2026-04-19 task_real_007

- planned output_root:
  - `exp/task_real_007_physics_consistency/<timestamp>`
- frozen baseline reuse:
  - training/evaluation source checkpoint comes from `task_real_006d`
  - runtime / baseline-Ours comparison reference comes from `task_real_006e`
- implementation scope:
  - `P1` only changes the loss to `L_image + lambda_pc * L_echo`
  - no data protocol change
  - no Variant B / `ref3` / `UNet3DSmall` architecture change
- execution notes:
  - `P2` remains optional and is expected to be skipped unless `P1` shows clear benefit
  - 007 evaluation writes aggregate comparison CSVs across main test plus all three OOD sets
