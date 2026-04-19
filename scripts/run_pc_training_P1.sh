#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
if [[ $# -lt 1 ]]; then
  echo "usage: $0 <timestamp-or-output-root> [baseline-root]"
  exit 1
fi
if [[ "$1" = /* ]]; then
  OUTPUT_ROOT="$1"
else
  OUTPUT_ROOT="${PROJECT_ROOT}/exp/task_real_007_physics_consistency/$1"
fi
BASELINE_ROOT="${2:-${PROJECT_ROOT}/exp/task_real_006d_800_formal/20260419_112717}"
mkdir -p "${OUTPUT_ROOT}/logs"
echo "[run_pc_training_P1] output_root=${OUTPUT_ROOT} baseline_root=${BASELINE_ROOT}" | tee "${OUTPUT_ROOT}/logs/run_pc_training_P1.log"
PYTHONPATH="${PROJECT_ROOT}" python -m workspace.train.train_pc_p1 \
  --output-root "${OUTPUT_ROOT}" \
  --source-root "${BASELINE_ROOT}" \
  --epochs 3 \
  --batch-size 2 \
  --lr 5e-4 \
  --lambda-pc 0.05 \
  --active-cells 12 \
  --freq-count 24 | tee -a "${OUTPUT_ROOT}/logs/run_pc_training_P1.log"
