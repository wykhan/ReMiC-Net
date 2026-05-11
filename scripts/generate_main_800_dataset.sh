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
  OUTPUT_ROOT="${PROJECT_ROOT}/exp/task_real_006d_800_formal/$1"
fi
mkdir -p "${OUTPUT_ROOT}/logs"
echo "[generate_main_800_dataset] output_root=${OUTPUT_ROOT}" | tee "${OUTPUT_ROOT}/logs/generate_main_800_dataset.log"
PYTHONPATH="${PROJECT_ROOT}" python -m workspace.eval.task_real_006d_pipeline \
  --output-root "${OUTPUT_ROOT}" \
  --stage generate_main | tee -a "${OUTPUT_ROOT}/logs/generate_main_800_dataset.log"
