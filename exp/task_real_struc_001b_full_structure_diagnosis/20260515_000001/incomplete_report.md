# incomplete_report

status = INCOMPLETE

current_branch = task_struc_series
pushed_to_remote = yes_after_final_push
remote_branch = origin/task_struc_series

## Completed Items

- Synced `task_struc_series` with origin before work.
- Verified full split manifest availability: `{'available': True, 'counts': {'train': 800, 'val': 100, 'test': 100}, 'manifest': '/home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_006d_800_formal/20260419_112717/learning_handoff_manifest_main_800_100_100.json'}`.
- Ran full-split metadata audit over available handoff samples.
- Investigated OOD dataset directory availability and wrote `metrics_ood.csv`.
- Wrote metric definition audit.
- Wrote S03/S05 failure audit based on 001a smoke-test outputs.
- Created required placeholder CSV/JSON/Markdown outputs with explicit incomplete reasons.

## Missing Items

- Full S01-S11 training was not run.
- Epoch requirement `>=50` was not satisfied.
- Required 3-seed variants S02/S04/S05/S06/S07/S08 were not run.
- Full OOD evaluation was not run.
- Unified support-masked metrics were not computed from full 001b predictions.
- Best checkpoints and convergence curves for full models are not available.

## Failure Reasons

The 001b prompt requires 11 variants, at least 50 epochs, and additional 3-seed runs for 6 key variants. This is a substantially larger run than the previous smoke test and was not completed in this execution turn. Per the prompt, a success report must not be written.

## Commands Already Run

```bash
git fetch origin
git checkout task_struc_series
git pull --ff-only origin task_struc_series
python -m workspace.eval.task_real_struc_001b_incomplete_audit --output-root /home/superws/2026_Projects/Codex_reference_plane_real/exp/task_real_struc_001b_full_structure_diagnosis/20260515_000001
```

## Recommended Next Command

Implement/launch the full training runner with:

```bash
python -m workspace.eval.task_real_struc_001b_full_runner --output-root exp/task_real_struc_001b_full_structure_diagnosis/<timestamp> --epochs 50 --seeds 0 1 2
```

## Scientific Interpretability

Partial audit results are scientifically useful for checking dataset availability, metadata validity, OOD data presence, and the 001a failure hypotheses. They are not sufficient to decide whether ReMiC-Net, FiLM, or RSB-FiLM is structurally justified.
