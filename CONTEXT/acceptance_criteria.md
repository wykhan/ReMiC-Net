# acceptance_criteria

`task_real_001` is complete only if all of the following are true:

- Project structure contains `CONTEXT/`, `PROMPTS/`, `scripts/`, `exp/`, `doc/`, and `workspace/`
- Git is usable at `PROJECT_ROOT`
- `.gitignore` ignores transient caches and large training artifacts without excluding governance documents
- Bootstrap scripts exist and `scripts/bootstrap_check.sh` is executable
- Four project-level `CONTEXT/` governance documents are present
- `PROMPTS/task_real_001.md` exists as an internal task record
- `README.md` explains project purpose, protocol entry points, and bootstrap usage
- `exp/task_real_001_bootstrap/<timestamp>/` contains the task report, tree, Git status, and bootstrap log
- The repository explicitly records that formal simulation, benchmark runs, and training have not started
