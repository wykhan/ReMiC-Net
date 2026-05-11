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
  OUTPUT_ROOT="${PROJECT_ROOT}/exp/task_real_006b_fullscale_mainline/$1"
fi
LOG_DIR="${OUTPUT_ROOT}/logs"
mkdir -p "${LOG_DIR}"

echo "[build_frozen_mainline_handoff] output_root=${OUTPUT_ROOT}" | tee "${LOG_DIR}/build_frozen_mainline_handoff.log"
PYTHONPATH="${PROJECT_ROOT}" python -m workspace.eval.build_frozen_mainline_handoff \
  --output-root "${OUTPUT_ROOT}" | tee -a "${LOG_DIR}/build_frozen_mainline_handoff.log"
