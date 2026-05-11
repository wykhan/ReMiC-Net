#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TIMESTAMP="${1:-$(date '+%Y%m%d_%H%M%S')}"
OUTPUT_ROOT="${2:-${PROJECT_ROOT}/exp/task_real_004_accelerated_point_validation/${TIMESTAMP}}"
LOG_DIR="${OUTPUT_ROOT}/logs"
mkdir -p "${LOG_DIR}"

echo "[run_accelerated_radial_mismatch_analysis] output_root=${OUTPUT_ROOT}" | tee "${LOG_DIR}/run_accelerated_radial_mismatch_analysis.log"
PYTHONPATH="${PROJECT_ROOT}" python -m workspace.eval.radial_mismatch_analysis_accelerated \
  --output-root "${OUTPUT_ROOT}" | tee -a "${LOG_DIR}/run_accelerated_radial_mismatch_analysis.log"
