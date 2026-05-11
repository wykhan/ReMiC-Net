#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
if [[ $# -lt 1 ]]; then
  echo "usage: $0 <timestamp-or-output-root>"
  exit 1
fi

if [[ "$1" = /* ]]; then
  OUTPUT_ROOT="$1"
else
  OUTPUT_ROOT="${PROJECT_ROOT}/exp/task_real_006_two_stage_learning/$1"
fi
LOG_DIR="${OUTPUT_ROOT}/logs"
mkdir -p "${LOG_DIR}"

echo "[run_two_stage_training_M3] output_root=${OUTPUT_ROOT}" | tee "${LOG_DIR}/run_two_stage_training_M3.log"
PYTHONPATH="${PROJECT_ROOT}" python -m workspace.train.train_two_stage_et \
  --output-root "${OUTPUT_ROOT}" \
  --mode M3 \
  --epochs 5 \
  --batch-size 4 \
  --smoke-limit 16 | tee -a "${LOG_DIR}/run_two_stage_training_M3.log"
