#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TIMESTAMP="${1:-$(date '+%Y%m%d_%H%M%S')}"
OUTPUT_ROOT="${2:-${PROJECT_ROOT}/exp/task_real_003_faithful_point_validation/${TIMESTAMP}}"
LOG_DIR="${OUTPUT_ROOT}/logs"
mkdir -p "${LOG_DIR}"

echo "[run_radial_mismatch_analysis] output_root=${OUTPUT_ROOT}" | tee "${LOG_DIR}/run_radial_mismatch_analysis.log"
PYTHONPATH="${PROJECT_ROOT}" python -m workspace.eval.radial_mismatch_analysis \
  --output-root "${OUTPUT_ROOT}" | tee -a "${LOG_DIR}/run_radial_mismatch_analysis.log"
