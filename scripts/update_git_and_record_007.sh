#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
if [[ $# -lt 1 ]]; then
  echo "usage: $0 <timestamp-or-output-root> [baseline-root] [eval006e-root]"
  exit 1
fi
if [[ "$1" = /* ]]; then
  OUTPUT_ROOT="$1"
else
  OUTPUT_ROOT="${PROJECT_ROOT}/exp/task_real_007_physics_consistency/$1"
fi
BASELINE_ROOT="${2:-${PROJECT_ROOT}/exp/task_real_006d_800_formal/20260419_112717}"
EVAL006E_ROOT="${3:-${PROJECT_ROOT}/exp/task_real_006e_comprehensive_eval/20260419_190046}"
mkdir -p "${OUTPUT_ROOT}/logs"
echo "[update_git_and_record_007] output_root=${OUTPUT_ROOT}" | tee "${OUTPUT_ROOT}/logs/update_git_and_record_007.log"
PYTHONPATH="${PROJECT_ROOT}" python -m workspace.eval.task_real_007_pc_comparison \
  --output-root "${OUTPUT_ROOT}" \
  --baseline-root "${BASELINE_ROOT}" \
  --eval006e-root "${EVAL006E_ROOT}" \
  --stage git | tee -a "${OUTPUT_ROOT}/logs/update_git_and_record_007.log"
