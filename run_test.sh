#!/usr/bin/env bash
set -euo pipefail

# Wrapper that asserts: input_backup.py is VULNERABLE and input.py is SECURE.
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON=${PYTHON:-python}

echo "Running static security checks..."

$PYTHON "$ROOT_DIR/run_tests.py" input_backup.py || true
BACKUP_EXIT=$?
$PYTHON "$ROOT_DIR/run_tests.py" input.py || true
FIXED_EXIT=$?

echo "input_backup.py exit: $BACKUP_EXIT (expected non-zero)"
echo "input.py exit: $FIXED_EXIT (expected 0)"

# success only if backup is vulnerable (non-zero) AND fixed passes (zero)
if [ "$BACKUP_EXIT" -ne 0 ] && [ "$FIXED_EXIT" -eq 0 ]; then
  echo "TESTS OK: backup shows vulnerabilities and fixed file is clean"
  exit 0
else
  echo "TESTS FAILED: expectations not met"
  exit 2
fi
