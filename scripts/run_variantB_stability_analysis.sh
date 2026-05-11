#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TIMESTAMP="${1:-$(date '+%Y%m%d_%H%M%S')}"
OUTPUT_ROOT="${2:-${PROJECT_ROOT}/exp/task_real_004c_variantB_confirmation/${TIMESTAMP}}"
LOG_DIR="${OUTPUT_ROOT}/logs"
mkdir -p "${LOG_DIR}"

echo "[run_variantB_stability_analysis] output_root=${OUTPUT_ROOT}" | tee "${LOG_DIR}/run_variantB_stability_analysis.log"
PYTHONPATH="${PROJECT_ROOT}" python -m workspace.eval.variantB_stability_analysis \
  --output-root "${OUTPUT_ROOT}" | tee -a "${LOG_DIR}/run_variantB_stability_analysis.log"
