#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TIMESTAMP="${1:-$(date '+%Y%m%d_%H%M%S')}"
OUTPUT_ROOT="${2:-${PROJECT_ROOT}/exp/task_real_002_point_chain/${TIMESTAMP}}"
LOG_DIR="${OUTPUT_ROOT}/logs"
mkdir -p "${LOG_DIR}"

echo "[run_point_learning_smoke] output_root=${OUTPUT_ROOT}" | tee "${LOG_DIR}/run_point_learning_smoke.log"
PYTHONPATH="${PROJECT_ROOT}" python -m workspace.train.train_point_smoke \
  --output-root "${OUTPUT_ROOT}" \
  --train-limit 8 \
  --val-limit 4 \
  --epochs 3 | tee -a "${LOG_DIR}/run_point_learning_smoke.log"
