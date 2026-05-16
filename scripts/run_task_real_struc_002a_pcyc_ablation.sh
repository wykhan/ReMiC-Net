#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

python -m workspace.eval.task_real_struc_002a_pcyc_ablation \
  --epochs 50 \
  --min-epochs 50 \
  --seeds 0 1 2
