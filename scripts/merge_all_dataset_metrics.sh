#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
if [[ $# -lt 1 ]]; then
  echo "usage: $0 <timestamp-or-output-root> [source-root]"
  exit 1
fi
if [[ "$1" = /* ]]; then
  OUTPUT_ROOT="$1"
else
  OUTPUT_ROOT="${PROJECT_ROOT}/exp/task_real_006e_comprehensive_eval/$1"
fi
SOURCE_ROOT="${2:-${PROJECT_ROOT}/exp/task_real_006d_800_formal/20260419_112717}"
mkdir -p "${OUTPUT_ROOT}/logs"
echo "[merge_all_dataset_metrics] output_root=${OUTPUT_ROOT} source_root=${SOURCE_ROOT}" | tee "${OUTPUT_ROOT}/logs/merge_all_dataset_metrics.log"
PYTHONPATH="${PROJECT_ROOT}" python -m workspace.eval.task_real_006e_comprehensive_eval \
  --output-root "${OUTPUT_ROOT}" \
  --source-root "${SOURCE_ROOT}" \
  --stage merge | tee -a "${OUTPUT_ROOT}/logs/merge_all_dataset_metrics.log"
PYTHONPATH="${PROJECT_ROOT}" python -m workspace.eval.task_real_006e_comprehensive_eval \
  --output-root "${OUTPUT_ROOT}" \
  --source-root "${SOURCE_ROOT}" \
  --stage positioning | tee -a "${OUTPUT_ROOT}/logs/merge_all_dataset_metrics.log"
