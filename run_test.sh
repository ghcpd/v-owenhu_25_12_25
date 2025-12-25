#!/usr/bin/env bash
set -euo pipefail
MODULE_PATH="$1"
PYTHON=${PYTHON:-python}

echo "Running security checks for ${MODULE_PATH}"
${PYTHON} -u tests/runner.py "${MODULE_PATH}"