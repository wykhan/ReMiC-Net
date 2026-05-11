# split_integrity_report_800

- total samples audited: 1000
- counts by split: {'train': 800, 'val': 100, 'test': 100}
- duplicate scene-hash count: 0
- duplicate parameter-signature count: 168
- nearest train-test distance mean: 1.445870
- nearest train-test distance min: 0.299341

Current judgment: no exact scene-level leakage if duplicate scene-hash count is zero; repeated family parameter signatures remain a soft warning, not direct proof of leakage.
