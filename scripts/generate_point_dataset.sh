#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TIMESTAMP="${1:-$(date '+%Y%m%d_%H%M%S')}"
OUTPUT_ROOT="${2:-${PROJECT_ROOT}/exp/task_real_002_point_chain/${TIMESTAMP}}"
MODE="${3:-smoke}"
LOG_DIR="${OUTPUT_ROOT}/logs"
mkdir -p "${LOG_DIR}"

echo "[generate_point_dataset] output_root=${OUTPUT_ROOT}" | tee "${LOG_DIR}/generate_point_dataset.log"
PYTHONPATH="${PROJECT_ROOT}" python -m workspace.data.point_dataset_builder \
  --output-root "${OUTPUT_ROOT}" \
  --mode "${MODE}" | tee -a "${LOG_DIR}/generate_point_dataset.log"

PYTHONPATH="${PROJECT_ROOT}" python -m workspace.sim.forward_cylindrical_point \
  --output-root "${OUTPUT_ROOT}" | tee -a "${LOG_DIR}/generate_point_dataset.log"

cp "${PROJECT_ROOT}/CONTEXT/dataset_protocol.md" "${OUTPUT_ROOT}/dataset_protocol_snapshot.md"
