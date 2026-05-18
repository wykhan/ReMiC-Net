#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

python -m workspace.eval.task_real_struc_003a_table1
