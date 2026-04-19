#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
if [[ $# -lt 1 ]]; then
  echo "usage: $0 <timestamp-or-output-root> [baseline-root] [p1-root]"
  exit 1
fi
if [[ "$1" = /* ]]; then
  OUTPUT_ROOT="$1"
else
  OUTPUT_ROOT="${PROJECT_ROOT}/exp/task_real_007b_geometry_aware_consistency/$1"
fi
BASELINE_ROOT="${2:-${PROJECT_ROOT}/exp/task_real_006d_800_formal/20260419_112717}"
P1_ROOT="${3:-${PROJECT_ROOT}/exp/task_real_007_physics_consistency/20260419_201254}"
mkdir -p "${OUTPUT_ROOT}/logs"
echo "[run_pc_training_P2A] output_root=${OUTPUT_ROOT} baseline_root=${BASELINE_ROOT} p1_root=${P1_ROOT}" | tee "${OUTPUT_ROOT}/logs/run_pc_training_P2A.log"
PYTHONPATH="${PROJECT_ROOT}" python -m workspace.train.train_pc_p2a \
  --output-root "${OUTPUT_ROOT}" \
  --source-root "${BASELINE_ROOT}" \
  --p1-root "${P1_ROOT}" \
  --epochs 2 \
  --batch-size 2 \
  --lr 2e-4 \
  --lambda-pc 0.06 \
  --active-cells 12 \
  --freq-count 24 \
  --support-threshold-ratio 0.18 \
  --dilation-radius 1 \
  --support-weight 2.0 \
  --boundary-weight 1.35 | tee -a "${OUTPUT_ROOT}/logs/run_pc_training_P2A.log"
