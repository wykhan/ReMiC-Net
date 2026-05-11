#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TIMESTAMP="${1:-$(date '+%Y%m%d_%H%M%S')}"
OUTPUT_ROOT="${2:-${PROJECT_ROOT}/exp/task_real_005_shape_family_et/${TIMESTAMP}}"
LOG_DIR="${OUTPUT_ROOT}/logs"
mkdir -p "${LOG_DIR}"

echo "[generate_et_shape_family_dataset] output_root=${OUTPUT_ROOT}" | tee "${LOG_DIR}/generate_et_shape_family_dataset.log"
PYTHONPATH="${PROJECT_ROOT}" python -m workspace.data.et_shape_family_builder \
  --output-root "${OUTPUT_ROOT}" \
  --project-root "${PROJECT_ROOT}" | tee -a "${LOG_DIR}/generate_et_shape_family_dataset.log"

PYTHONPATH="${PROJECT_ROOT}" python -m workspace.sim.forward_cylindrical_point \
  --output-root "${OUTPUT_ROOT}" | tee -a "${LOG_DIR}/generate_et_shape_family_dataset.log"
