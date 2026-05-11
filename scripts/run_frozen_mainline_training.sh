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
  OUTPUT_ROOT="${PROJECT_ROOT}/exp/task_real_006b_fullscale_mainline/$1"
fi
LOG_DIR="${OUTPUT_ROOT}/logs"
mkdir -p "${LOG_DIR}"

echo "[run_frozen_mainline_training] output_root=${OUTPUT_ROOT}" | tee "${LOG_DIR}/run_frozen_mainline_training.log"
PYTHONPATH="${PROJECT_ROOT}" python -m workspace.train.train_frozen_mainline \
  --output-root "${OUTPUT_ROOT}" \
  --epochs 5 \
  --batch-size 4 \
  --smoke-limit 16 | tee -a "${LOG_DIR}/run_frozen_mainline_training.log"
