#!/usr/bin/env bash

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TIMESTAMP="${1:-$(date '+%Y%m%d_%H%M%S')}"
REPORT_DIR="${PROJECT_ROOT}/exp/task_real_001_bootstrap/${TIMESTAMP}"
LOG_FILE="${REPORT_DIR}/bootstrap_check.log"

mkdir -p "${REPORT_DIR}"

log() {
    printf '%s\n' "$1" | tee -a "${LOG_FILE}"
}

STATUS="PASS"

log "[bootstrap_check] PROJECT_ROOT=${PROJECT_ROOT}"

required_dirs=(
    "CONTEXT"
    "PROMPTS"
    "scripts"
    "exp"
    "doc"
    "workspace"
)

for dir in "${required_dirs[@]}"; do
    if [[ -d "${PROJECT_ROOT}/${dir}" ]]; then
        log "[ok] directory exists: ${dir}"
    else
        log "[missing] directory missing: ${dir}"
        STATUS="FAIL"
    fi
done

required_context=(
    "CONTEXT/real_cylindrical_master_document_with_physics_consistency.md"
    "CONTEXT/reference_surface_strategy.md"
    "CONTEXT/simulation_protocol.md"
)

for path in "${required_context[@]}"; do
    if [[ -f "${PROJECT_ROOT}/${path}" ]]; then
        log "[ok] required context exists: ${path}"
    else
        log "[missing] required context missing: ${path}"
        STATUS="FAIL"
    fi
done

if git -C "${PROJECT_ROOT}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    log "[ok] git repository available"
else
    log "[missing] git repository unavailable"
    STATUS="FAIL"
fi

log "[bootstrap_check] status=${STATUS}"

if [[ "${STATUS}" == "PASS" ]]; then
    exit 0
fi

exit 1
