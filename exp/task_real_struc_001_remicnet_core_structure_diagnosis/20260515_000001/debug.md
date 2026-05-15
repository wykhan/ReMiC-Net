# debug

- First-pass diagnostic intentionally uses a deterministic subset and one seed to keep S01-S08 comparable and tractable in this run.
- OOD S01-S08 evaluation was not run; `metrics_ood.csv` records this limitation.
- Generic FiLM uses bounded tanh gamma/beta without RSB envelope; RSB-FiLM uses the frozen envelope only for feature modulation strength.
