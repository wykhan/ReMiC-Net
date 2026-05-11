#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TIMESTAMP="${1:-$(date '+%Y%m%d_%H%M%S')}"
OUTPUT_ROOT="${2:-${PROJECT_ROOT}/exp/task_real_006b_fullscale_mainline/${TIMESTAMP}}"
LOG_DIR="${OUTPUT_ROOT}/logs"
mkdir -p "${LOG_DIR}"

echo "[generate_shape_family_fullscale] output_root=${OUTPUT_ROOT}" | tee "${LOG_DIR}/generate_shape_family_fullscale.log"
PYTHONPATH="${PROJECT_ROOT}" python -m workspace.eval.build_frozen_mainline_handoff \
  --output-root "${OUTPUT_ROOT}" | tee -a "${LOG_DIR}/generate_shape_family_fullscale.log"
