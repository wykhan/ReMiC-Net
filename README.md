# Real Cylindrical Physics-Guided Learned 3D Imaging

This repository bootstraps a reproducible research workspace for a real cylindrical physics-guided learned 3D imaging project.

Current stage: `Phase 0 / bootstrap only`.

Project governance entry points:
- Master document: `CONTEXT/real_cylindrical_master_document_with_physics_consistency.md`
- Geometry and simulation protocol: `CONTEXT/simulation_protocol.md`
- Reference-surface protocol: `CONTEXT/reference_surface_strategy.md`

This task does not start formal simulation, dataset generation, benchmarking, or network training.

## Repository Layout

- `CONTEXT/`: frozen project knowledge and protocol documents
- `PROMPTS/`: Codex working rules, review checklist, and task records
- `scripts/`: bootstrap and future experiment entry points
- `doc/`: assumptions and open questions
- `exp/`: task reports and later experiment outputs
- `workspace/`: implementation workspace for later tasks

## Bootstrap Check

Run:

```bash
bash scripts/bootstrap_check.sh
```

The script validates the required directory layout, key protocol documents, and Git availability, then writes a log under `exp/task_real_001_bootstrap/<timestamp>/`.

## Status

- Bootstrap structure: prepared
- Formal simulation: not started
- Formal training: not started
- Formal benchmark: not started
