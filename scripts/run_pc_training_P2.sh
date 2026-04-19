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
  OUTPUT_ROOT="${PROJECT_ROOT}/exp/task_real_007_physics_consistency/$1"
fi
mkdir -p "${OUTPUT_ROOT}/logs"
echo "[run_pc_training_P2] skipped_by_design" | tee "${OUTPUT_ROOT}/logs/run_pc_training_P2.log"
