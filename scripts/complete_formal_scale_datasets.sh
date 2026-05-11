#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TIMESTAMP="${1:-$(date '+%Y%m%d_%H%M%S')}"
OUTPUT_ROOT="${2:-${PROJECT_ROOT}/exp/task_real_006c_formal_validation/${TIMESTAMP}}"
LOG_DIR="${OUTPUT_ROOT}/logs"
mkdir -p "${LOG_DIR}"

echo "[complete_formal_scale_datasets] output_root=${OUTPUT_ROOT}" | tee "${LOG_DIR}/complete_formal_scale_datasets.log"
PYTHONPATH="${PROJECT_ROOT}" python -m workspace.eval.formal_scale_validation \
  --output-root "${OUTPUT_ROOT}" | tee -a "${LOG_DIR}/complete_formal_scale_datasets.log"
