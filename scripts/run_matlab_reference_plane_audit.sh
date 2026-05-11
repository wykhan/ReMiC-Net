#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TIMESTAMP="${1:-$(date '+%Y%m%d_%H%M%S')}"
OUTPUT_ROOT="${2:-${PROJECT_ROOT}/exp/task_real_004_accelerated_point_validation/${TIMESTAMP}}"
LOG_DIR="${OUTPUT_ROOT}/logs"
mkdir -p "${LOG_DIR}"

echo "[run_matlab_reference_plane_audit] output_root=${OUTPUT_ROOT}" | tee "${LOG_DIR}/run_matlab_reference_plane_audit.log"
MATLAB_SCRIPT="${PROJECT_ROOT}/scripts/matlab_reference_plane_audit.m"
~/software/MATLAB_R2018b/bin/matlab -batch "output_root='${OUTPUT_ROOT}'; run('${MATLAB_SCRIPT}');" | tee -a "${LOG_DIR}/run_matlab_reference_plane_audit.log"
