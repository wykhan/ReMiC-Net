#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TIMESTAMP="${1:-$(date '+%Y%m%d_%H%M%S')}"
OUTPUT_ROOT="${2:-${PROJECT_ROOT}/exp/task_real_002_point_chain/${TIMESTAMP}}"
SPLIT="${3:-test}"
MAX_SAMPLES="${4:-8}"
LOG_DIR="${OUTPUT_ROOT}/logs"
mkdir -p "${LOG_DIR}"

echo "[run_point_baselines] output_root=${OUTPUT_ROOT} split=${SPLIT} max_samples=${MAX_SAMPLES}" | tee "${LOG_DIR}/run_point_baselines.log"
PYTHONPATH="${PROJECT_ROOT}" python -m workspace.eval.eval_point_baselines \
  --output-root "${OUTPUT_ROOT}" \
  --split "${SPLIT}" \
  --max-samples "${MAX_SAMPLES}" | tee -a "${LOG_DIR}/run_point_baselines.log"
