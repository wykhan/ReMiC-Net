#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TIMESTAMP="${1:-$(date '+%Y%m%d_%H%M%S')}"
OUTPUT_ROOT="${2:-${PROJECT_ROOT}/exp/task_real_006_two_stage_learning/${TIMESTAMP}}"
DATA_ROOT="${OUTPUT_ROOT}/datasets/shape_family_full"
LOG_DIR="${OUTPUT_ROOT}/logs"
mkdir -p "${LOG_DIR}"

echo "[generate_et_fullscale_dataset] output_root=${OUTPUT_ROOT}" | tee "${LOG_DIR}/generate_et_fullscale_dataset.log"
PYTHONPATH="${PROJECT_ROOT}" python -m workspace.data.et_shape_family_builder \
  --output-root "${DATA_ROOT}" \
  --project-root "${PROJECT_ROOT}" \
  --train-per-family 96 \
  --val-per-family 24 \
  --test-per-family 24 | tee -a "${LOG_DIR}/generate_et_fullscale_dataset.log"

PYTHONPATH="${PROJECT_ROOT}" python -m workspace.sim.forward_cylindrical_point \
  --output-root "${DATA_ROOT}" | tee -a "${LOG_DIR}/generate_et_fullscale_dataset.log"
