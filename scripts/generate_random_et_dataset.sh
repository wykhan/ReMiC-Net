#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
if [[ $# -lt 1 ]]; then
  echo "usage: $0 <timestamp-or-output-root>"
  exit 1
fi

if [[ "$1" = /* ]]; then
  OUTPUT_ROOT="$1"
else
  OUTPUT_ROOT="${PROJECT_ROOT}/exp/task_real_006_two_stage_learning/$1"
fi
DATA_ROOT="${OUTPUT_ROOT}/datasets/random_et"
LOG_DIR="${OUTPUT_ROOT}/logs"
mkdir -p "${LOG_DIR}"

echo "[generate_random_et_dataset] output_root=${OUTPUT_ROOT}" | tee "${LOG_DIR}/generate_random_et_dataset.log"
PYTHONPATH="${PROJECT_ROOT}" python -m workspace.data.random_et_builder \
  --output-root "${DATA_ROOT}" \
  --project-root "${PROJECT_ROOT}" \
  --train-count 192 \
  --val-count 48 \
  --test-count 48 | tee -a "${LOG_DIR}/generate_random_et_dataset.log"

PYTHONPATH="${PROJECT_ROOT}" python -m workspace.sim.forward_cylindrical_point \
  --output-root "${DATA_ROOT}" | tee -a "${LOG_DIR}/generate_random_et_dataset.log"
