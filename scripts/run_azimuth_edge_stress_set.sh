#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TIMESTAMP="${1:-$(date '+%Y%m%d_%H%M%S')}"
OUTPUT_ROOT="${2:-${PROJECT_ROOT}/exp/task_real_004b_wrap_hardening/${TIMESTAMP}}"
LOG_DIR="${OUTPUT_ROOT}/logs"
mkdir -p "${LOG_DIR}"

echo "[run_azimuth_edge_stress_set] output_root=${OUTPUT_ROOT}" | tee "${LOG_DIR}/run_azimuth_edge_stress_set.log"
PYTHONPATH="${PROJECT_ROOT}" python -m workspace.data.azimuth_edge_stress_builder \
  --output-root "${OUTPUT_ROOT}" \
  --project-root "${PROJECT_ROOT}" | tee -a "${LOG_DIR}/run_azimuth_edge_stress_set.log"

PYTHONPATH="${PROJECT_ROOT}" python -m workspace.sim.forward_cylindrical_point \
  --output-root "${OUTPUT_ROOT}" | tee -a "${LOG_DIR}/run_azimuth_edge_stress_set.log"
