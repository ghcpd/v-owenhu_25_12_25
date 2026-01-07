#!/usr/bin/env bash
set -euo pipefail
LOG_DIR=logs
mkdir -p "$LOG_DIR"
FILE=${1:-all}

run_one(){
  local target="$1"
  echo "-----" >> "$LOG_DIR/test_run.log"
  echo "$(date --iso-8601=seconds) - START - $target" >> "$LOG_DIR/test_run.log"
  # Run under SAFE_TEST and include tests/ in PYTHONPATH so sitecustomize can stub dangerous ops
  set +e
  SAFE_TEST=1 PYTHONPATH=tests python "$target" > "$LOG_DIR/${target}.out" 2>&1
  local rc=$?
  set -e
  cat "$LOG_DIR/${target}.out" >> "$LOG_DIR/test_run.log"
  if [ $rc -eq 0 ]; then
    echo "$(date --iso-8601=seconds) - $target - TEST PASSED" >> "$LOG_DIR/test_run.log"
  else
    echo "$(date --iso-8601=seconds) - $target - TEST FAILED (exit $rc)" >> "$LOG_DIR/test_run.log"
  fi
  return $rc
}

if [ "$FILE" = "all" ]; then
  run_one "input_backup.py"
  run_one "input.py"
else
  run_one "$FILE"
fi
