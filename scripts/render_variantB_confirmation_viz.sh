#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TIMESTAMP="${1:-$(date '+%Y%m%d_%H%M%S')}"
OUTPUT_ROOT="${2:-${PROJECT_ROOT}/exp/task_real_004c_variantB_confirmation/${TIMESTAMP}}"
LOG_DIR="${OUTPUT_ROOT}/logs"
mkdir -p "${LOG_DIR}"

echo "[render_variantB_confirmation_viz] output_root=${OUTPUT_ROOT}" | tee "${LOG_DIR}/render_variantB_confirmation_viz.log"
PYTHONPATH="${PROJECT_ROOT}" python -m workspace.eval.render_variantB_confirmation_viz \
  --output-root "${OUTPUT_ROOT}" | tee -a "${LOG_DIR}/render_variantB_confirmation_viz.log"

PYTHONPATH="${PROJECT_ROOT}" python -m workspace.eval.generate_task_real_004c_report \
  --output-root "${OUTPUT_ROOT}" | tee -a "${LOG_DIR}/render_variantB_confirmation_viz.log"
