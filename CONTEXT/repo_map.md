# repo_map

## Directory Roles

- `CONTEXT/`: frozen project knowledge, protocols, and governance references
- `PROMPTS/`: Codex operating rules, self-review checklist, and task records
- `scripts/`: shell entry points for bootstrap, future baselines, evaluation, and experiment orchestration
- `exp/`: versioned task reports and future experiment outputs
- `doc/`: assumptions, unresolved questions, and supporting internal notes
- `workspace/`: implementation area for code written in later tasks

## Root Files

- `README.md`: project overview and bootstrap usage
- `CHANGELOG_DEV.md`: development action log
- `debug.md`: execution notes and environment findings
- `.gitignore`: repository hygiene rules

## Single Sources Of Authority

- `CONTEXT/simulation_protocol.md` is the only effective geometry, sampling, and simulation protocol entry
- `CONTEXT/reference_surface_strategy.md` is the only effective reference-surface strategy entry
- `CONTEXT/real_cylindrical_master_document_with_physics_consistency.md` is the only top-level master document

## Expected Future Contents

- `scripts/` should remain the only supported path for reproducible task execution
- `exp/` should store reports, metrics, and retained lightweight artifacts, while large caches and checkpoints remain ignored
- `workspace/` should host implementation modules once `task_real_002` begins point-target chain validation
