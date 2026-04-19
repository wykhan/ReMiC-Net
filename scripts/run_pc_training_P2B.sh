#!/usr/bin/env bash
set -euo pipefail
if [[ $# -lt 1 ]]; then
  echo "usage: $0 <timestamp-or-output-root>"
  exit 1
fi
echo "[run_pc_training_P2B] skipped_by_design"
